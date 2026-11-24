"""Adaptador de laboratório da área 01 (Atendimento) do tuttibom-ops-mcp.

Cópia local da fila e do Chatwoot, com interfaces injetáveis. Não há
cliente de rede, não há leitura de token e não há abertura de porta.
O serviço de fila em produção não entra neste módulo.

Como o núcleo chama este adaptador
----------------------------------
O núcleo (servidor) faz o cadastro, emite o token, conduz o handshake
e segura o lease. Este módulo não repete isso. A orquestração da
integração chama, nesta ordem:

1. ``adaptador.listar_pendencias()``
2. ``adaptador.chamar("ops_atendimento_ler_conversa", {"conversa_ref": ...})``
3. ``adaptador.preparar_resposta(...)``
4. A integração registra no ``VerificadorAprovacaoServidor`` o texto
   exato e, quando houver, a imagem exata aprovados pela usuária.
   ``registrar`` não é ferramenta do agente.
5. ``adaptador.chamar("ops_atendimento_responder", {"rascunho_ref": ..., "aprovacao_ref": ...})``

``chamar`` é o despacho das duas ferramentas da área. Ele não recebe
token e não consulta lease. O envio ao simulador só ocorre no passo 5,
depois que o verificador confere o payload byte a byte. O ack da fila
só corre depois que o simulador aceita o envio.
"""

from __future__ import annotations

from .entregas_duraveis import DiarioEntregas, ErroEntregaDuravel

import hashlib
import hmac
import logging
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from tuttibom.contratos.pii import detectar_pii

FERRAMENTA_LER = "ops_atendimento_ler_conversa"
FERRAMENTA_RESPONDER = "ops_atendimento_responder"
FERRAMENTAS = {
    FERRAMENTA_LER: "seguro",
    FERRAMENTA_RESPONDER: "critico",
}

_TTL_PADRAO_SEGUNDOS = 24 * 60 * 60
_LIMITE_FILA_PADRAO = 20
_LIMITE_FILA_MAXIMO = 100
_CAMPOS_FILA = (
    "message_id",
    "conversation_id",
    "inbox_id",
    "contato_ref",
    "handoff",
    "recebido_em",
    "cumprimento",
)
_CAMPOS_CUMPRIMENTO = ("texto", "variante", "enviado_em")
_CHAVES_IGNORADAS = frozenset({
    "token",
    "pat",
    "api_access_token",
    "authorization",
    "segredo",
    "texto_aprovado",
    "imagem_aprovada",
    "aprovado",
    "data_url",
})
_REF_SEGURA = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")
_DIRECOES = frozenset({"incoming", "outgoing"})
_TIPOS_MIDIA = frozenset({"image", "audio"})

log = logging.getLogger("tuttibom.mcp_ops.atendimento")


class RecusaAtendimento(Exception):
    """Recusa com código estável. O texto da exceção é só o código."""

    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(codigo)


class FilaPendencias(Protocol):
    """Contrato local da fila: listar, obter e ack. Sem porta HTTP."""

    def listar_pendentes(self, limite: int = 20) -> list[dict]: ...

    def obter(self, message_id: str) -> dict | None: ...

    def marcar_entregues(self, message_ids: Sequence[str]) -> list[str]: ...


class LeituraConversa(Protocol):
    """Contrato local de leitura do Chatwoot. Sem URL e sem token."""

    def ler_mensagens(self, conversa_ref: str) -> list[dict] | None: ...

    def obter_audio(self, midia_ref: str) -> bytes: ...

    def geracao(self, conversa_ref: str) -> int: ...


class FonteImagem(Protocol):
    def obter_imagem(self, midia_ref: str) -> bytes: ...


class DestinoEnvio(Protocol):
    def enviar(
        self,
        *,
        conversa_ref: str,
        texto: str,
        imagem: bytes | None,
        idempotency_key: str,
    ) -> dict: ...


class EnvioNaoEfetuado(Exception):
    """O destino verificou que a entrega não foi executada."""


class MidiaEDestino(FonteImagem, DestinoEnvio, Protocol):
    """Fonte de mídia e destino de atendimento configurados pelo servidor."""


class Transcritor(Protocol):
    def transcrever(self, audio: bytes, *, idioma: str = "pt") -> str: ...


class VerificadorAprovacao(Protocol):
    def conferir(
        self,
        aprovacao_ref: str,
        texto: str,
        imagem: bytes | None,
    ) -> str | None: ...


def _digest_payload(texto: str, imagem: bytes | None) -> str:
    hasher = hashlib.sha256()
    bruto = texto.encode("utf-8")
    hasher.update(len(bruto).to_bytes(8, "big"))
    hasher.update(bruto)
    if imagem is None:
        hasher.update(b"\x00")
    else:
        hasher.update(b"\x01")
        hasher.update(len(imagem).to_bytes(8, "big"))
        hasher.update(imagem)
    return hasher.hexdigest()


def _digest_envio(
    conversa_ref: str,
    texto: str,
    imagem: bytes | None,
    message_ids: Sequence[str],
) -> str:
    hasher = hashlib.sha256()
    hasher.update(_digest_payload(texto, imagem).encode("ascii"))
    hasher.update(b"\0")
    hasher.update(conversa_ref.encode("utf-8"))
    hasher.update(b"\0")
    for mid in message_ids:
        hasher.update(mid.encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


def _igual(esquerda: str, direita: str) -> bool:
    if len(esquerda) != len(direita):
        return False
    return hmac.compare_digest(esquerda, direita)


def _ref_publica(valor: object) -> str:
    texto = str(valor)
    if _REF_SEGURA.fullmatch(texto) and detectar_pii(texto) is None:
        return texto
    return "oculto"


def _linha_log(evento: str, **campos: object) -> str:
    partes = [evento]
    for chave in sorted(campos):
        valor = campos[chave]
        if isinstance(valor, (bytes, bytearray)):
            partes.append(f"{chave}=bytes:{len(valor)}")
            continue
        if isinstance(valor, bool):
            partes.append(f"{chave}={'sim' if valor else 'nao'}")
            continue
        if isinstance(valor, int) and chave.startswith(("n_", "chars", "bytes")):
            partes.append(f"{chave}={valor}")
            continue
        partes.append(f"{chave}={_ref_publica(valor)}")
    linha = " ".join(partes)
    if detectar_pii(linha):
        return "atendimento evento=suprimido"
    return linha


def _log(evento: str, **campos: object) -> None:
    log.info("%s", _linha_log(evento, **campos))


def _falha(codigo: str, **campos: object) -> dict:
    _log("recusa", codigo=codigo, **campos)
    return {"ok": False, "codigo": codigo}


def _sha256(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def _copiar_cumprimento(valor: object) -> dict | None:
    if valor is None:
        return None
    if not isinstance(valor, Mapping):
        return None
    return {campo: valor[campo] for campo in _CAMPOS_CUMPRIMENTO if campo in valor}


def _item_publico(item: Mapping) -> dict:
    publico = {}
    for campo in _CAMPOS_FILA:
        if campo not in item:
            continue
        if campo == "cumprimento":
            publico[campo] = _copiar_cumprimento(item[campo])
        else:
            publico[campo] = item[campo]
    return publico


@dataclass
class _Leitura:
    geracao: int
    imagens: dict[str, str]
    audios: dict[str, str]
    completa: bool


@dataclass
class _Rascunho:
    ref: str
    conversa_ref: str
    texto: str
    imagem: bytes | None
    imagem_ref: str | None
    message_ids: tuple[str, ...]
    idempotency_key: str
    digest: str
    geracao: int


@dataclass
class _Idempotencia:
    digest: str
    expira_em: datetime
    estado: str
    envio_ref: str | None = None
    ack_ok: bool = False


class FilaLaboratorio:
    """Cópia em memória do contrato pending/ack. Não importa o ouvinte."""

    def __init__(self) -> None:
        self._itens: dict[str, dict] = {}

    def __repr__(self) -> str:
        return f"FilaLaboratorio(n={len(self._itens)})"

    def enfileirar(
        self,
        *,
        message_id: str,
        conversation_id: str,
        inbox_id: str,
        contato_ref: str,
        handoff: str | None = None,
        recebido_em: str,
        cumprimento: dict | None = None,
    ) -> None:
        if message_id in self._itens:
            raise RecusaAtendimento("argumento_invalido")
        self._itens[message_id] = {
            "message_id": message_id,
            "conversation_id": conversation_id,
            "inbox_id": inbox_id,
            "contato_ref": contato_ref,
            "handoff": handoff,
            "recebido_em": recebido_em,
            "cumprimento": _copiar_cumprimento(cumprimento),
            "estado": "pendente",
        }

    def listar_pendentes(self, limite: int = _LIMITE_FILA_PADRAO) -> list[dict]:
        pendentes = [
            _item_publico(item)
            for item in self._itens.values()
            if item["estado"] == "pendente"
        ]
        pendentes.sort(key=lambda item: str(item["message_id"]))
        return pendentes[:limite]

    def obter(self, message_id: str) -> dict | None:
        item = self._itens.get(message_id)
        if item is None:
            return None
        publico = _item_publico(item)
        publico["estado"] = item["estado"]
        return publico

    def marcar_entregues(self, message_ids: Sequence[str]) -> list[str]:
        marcados = []
        for message_id in message_ids:
            item = self._itens.get(message_id)
            if item is None or item["estado"] != "pendente":
                continue
            item["estado"] = "entregue"
            marcados.append(message_id)
        return marcados


class ChatwootLaboratorio:
    """Cópia local só de leitura da conversa e do áudio. Sem rede."""

    def __init__(self) -> None:
        self._mensagens: dict[str, list[dict]] = {}
        self._audios: dict[str, bytes] = {}
        self._geracao: dict[str, int] = {}

    def __repr__(self) -> str:
        return f"ChatwootLaboratorio(conversas={len(self._mensagens)})"

    def abrir(self, conversa_ref: str) -> None:
        self._mensagens.setdefault(conversa_ref, [])
        self._geracao.setdefault(conversa_ref, 0)

    def _tocar(self, conversa_ref: str) -> None:
        self.abrir(conversa_ref)
        self._geracao[conversa_ref] += 1

    def registrar_mensagem(
        self,
        conversa_ref: str,
        *,
        direcao: str,
        texto: str = "",
        anexos: Sequence[Mapping] | None = None,
    ) -> None:
        self._tocar(conversa_ref)
        limpos = []
        for anexo in anexos or ():
            limpos.append({
                "file_type": str(anexo.get("file_type") or "").lower(),
                "midia_ref": str(anexo.get("midia_ref") or ""),
            })
        self._mensagens[conversa_ref].append({
            "direcao": direcao,
            "texto": texto,
            "anexos": limpos,
        })

    def registrar_audio(self, midia_ref: str, conteudo: bytes) -> None:
        self._audios[midia_ref] = bytes(conteudo)
        for conversa_ref, mensagens in self._mensagens.items():
            if any(
                anexo["midia_ref"] == midia_ref
                for mensagem in mensagens
                for anexo in mensagem["anexos"]
            ):
                self._geracao[conversa_ref] += 1

    def ler_mensagens(self, conversa_ref: str) -> list[dict] | None:
        if conversa_ref not in self._mensagens:
            return None
        return [
            {
                "direcao": item["direcao"],
                "texto": item["texto"],
                "anexos": [dict(anexo) for anexo in item["anexos"]],
            }
            for item in self._mensagens[conversa_ref]
        ]

    def obter_audio(self, midia_ref: str) -> bytes:
        if midia_ref not in self._audios:
            raise KeyError(midia_ref)
        return self._audios[midia_ref]

    def geracao(self, conversa_ref: str) -> int:
        if conversa_ref not in self._geracao:
            raise KeyError(conversa_ref)
        return self._geracao[conversa_ref]


class SimuladorAtendimento:
    """Fornece a imagem e recebe o envio. Não abre conexão."""

    def __init__(self) -> None:
        self._imagens: dict[str, bytes] = {}
        self.envios: list[dict] = []
        self._falha = False
        self._seq = 0

    def __repr__(self) -> str:
        return (
            f"SimuladorAtendimento(imagens={len(self._imagens)} "
            f"envios={len(self.envios)})"
        )

    def registrar_imagem(self, midia_ref: str, conteudo: bytes) -> None:
        self._imagens[midia_ref] = bytes(conteudo)

    def obter_imagem(self, midia_ref: str) -> bytes:
        if midia_ref not in self._imagens:
            raise KeyError(midia_ref)
        return self._imagens[midia_ref]

    def falhar_envio(self, falhar: bool = True) -> None:
        self._falha = falhar

    def enviar(
        self,
        *,
        conversa_ref: str,
        texto: str,
        imagem: bytes | None,
        idempotency_key: str,
    ) -> dict:
        if self._falha:
            raise RecusaAtendimento("envio_falhou")
        self._seq += 1
        envio_ref = f"env-{self._seq}"
        self.envios.append({
            "envio_ref": envio_ref,
            "conversa_ref": conversa_ref,
            "texto": texto,
            "imagem": None if imagem is None else bytes(imagem),
            "idempotency_key": idempotency_key,
        })
        return {"ok": True, "envio_ref": envio_ref}


class VerificadorAprovacaoServidor:
    """Componente do servidor. Confere texto e imagem exatos.

    A integração registra a aprovação da usuária. O adaptador só pergunta
    se o rascunho é idêntico ao que foi registrado. Um booleano do agente
    não passa por aqui.
    """

    def __init__(self) -> None:
        self._registros: dict[str, tuple[str, bytes | None]] = {}
        self._seq = 0

    def __repr__(self) -> str:
        return f"VerificadorAprovacaoServidor(n={len(self._registros)})"

    def registrar(self, *, texto: str, imagem: bytes | None = None) -> str:
        if not isinstance(texto, str) or texto == "":
            raise RecusaAtendimento("argumento_invalido")
        if imagem is not None:
            if not isinstance(imagem, (bytes, bytearray)) or len(imagem) == 0:
                raise RecusaAtendimento("argumento_invalido")
            imagem = bytes(imagem)
        self._seq += 1
        ref = f"apr-{self._seq}"
        self._registros[ref] = (texto, imagem)
        return ref

    def conferir(
        self,
        aprovacao_ref: str,
        texto: str,
        imagem: bytes | None,
    ) -> str | None:
        guardado = self._registros.get(aprovacao_ref)
        if guardado is None or not isinstance(texto, str):
            return None
        texto_ok, imagem_ok = guardado
        if texto != texto_ok:
            return None
        if imagem_ok is None and imagem is None:
            return _digest_payload(texto, None)
        if imagem_ok is None or imagem is None:
            return None
        imagem = bytes(imagem)
        if len(imagem_ok) != len(imagem):
            return None
        if not hmac.compare_digest(imagem_ok, imagem):
            return None
        return _digest_payload(texto, imagem)


class AuditoriaLaboratorio:
    """Registro sanitizado das chamadas. Sem texto, mídia ou segredo."""

    def __init__(self) -> None:
        self.eventos: list[dict] = []

    def __repr__(self) -> str:
        return f"AuditoriaLaboratorio(n={len(self.eventos)})"

    def registrar(self, evento: Mapping) -> None:
        limpo = {}
        for chave, valor in evento.items():
            if isinstance(valor, (bytes, bytearray)):
                continue
            if isinstance(valor, str):
                if detectar_pii(valor) or not _REF_SEGURA.fullmatch(valor):
                    limpo[chave] = "oculto"
                else:
                    limpo[chave] = valor
                continue
            if isinstance(valor, (int, bool)) or valor is None:
                limpo[chave] = valor
        self.eventos.append(limpo)


class AdaptadorAtendimento:
    """Área 01 em laboratório. O núcleo chama ``listar_pendencias``,
    ``chamar``, ``preparar_resposta`` e de novo ``chamar``.
    """

    def __init__(
        self,
        *,
        fila: FilaPendencias,
        chatwoot: LeituraConversa,
        simulador: MidiaEDestino,
        transcritor: Transcritor | None,
        verificador: VerificadorAprovacao,
        auditoria: AuditoriaLaboratorio | None = None,
        relogio: Callable[[], datetime] | None = None,
        ttl_segundos: int = _TTL_PADRAO_SEGUNDOS,
        diario: DiarioEntregas | None = None,
    ) -> None:
        if ttl_segundos <= 0:
            raise RecusaAtendimento("argumento_invalido")
        self._fila = fila
        self._chatwoot = chatwoot
        self._simulador = simulador
        self._transcritor = transcritor
        self._verificador = verificador
        self._auditoria = auditoria or AuditoriaLaboratorio()
        self._relogio = relogio or (lambda: datetime.now(timezone.utc))
        self._ttl = timedelta(seconds=ttl_segundos)
        self._leituras: dict[str, _Leitura] = {}
        self._rascunhos: dict[str, _Rascunho] = {}
        self._rascunho_por_chave: dict[str, str] = {}
        self._idem: dict[str, _Idempotencia] = {}
        self._seq_rascunho = 0
        self._diario = diario

    def __repr__(self) -> str:
        return "AdaptadorAtendimento(laboratorio)"

    def _recusar(self, codigo: str, **campos: object) -> dict:
        ferramenta = campos.get("ferramenta", "atendimento")
        self._auditar(str(ferramenta), ok=False, codigo=codigo)
        return _falha(codigo, **campos)

    def listar_pendencias(self, limite: int = _LIMITE_FILA_PADRAO) -> dict:
        if not isinstance(limite, int) or not 1 <= limite <= _LIMITE_FILA_MAXIMO:
            return self._recusar("argumento_invalido", ferramenta="listar_pendencias")
        try:
            bruto = self._fila.listar_pendentes(limite)
        except Exception:
            return self._recusar("fila_indisponivel", ferramenta="listar_pendencias")
        itens = [_item_publico(item) for item in bruto if isinstance(item, Mapping)]
        self._auditar("listar_pendencias", ok=True, n_pendencias=len(itens))
        _log("listar_pendencias", n_pendencias=len(itens))
        return {"ok": True, "codigo": None, "pendencias": itens}

    def ler_conversa(self, conversa_ref: str) -> dict:
        if not isinstance(conversa_ref, str) or conversa_ref == "":
            return self._recusar("argumento_invalido", ferramenta=FERRAMENTA_LER)
        self._leituras.pop(conversa_ref, None)
        try:
            geracao = self._chatwoot.geracao(conversa_ref)
            mensagens = self._chatwoot.ler_mensagens(conversa_ref)
        except Exception:
            return self._recusar(
                "conversa_desconhecida",
                ferramenta=FERRAMENTA_LER,
                conversa_ref=conversa_ref,
            )
        if mensagens is None:
            return self._recusar(
                "conversa_desconhecida",
                ferramenta=FERRAMENTA_LER,
                conversa_ref=conversa_ref,
            )
        saida = []
        imagens: dict[str, str] = {}
        audios: dict[str, str] = {}
        try:
            for mensagem in mensagens:
                saida.append(self._ler_mensagem(mensagem, imagens, audios))
        except RecusaAtendimento as exc:
            self._leituras[conversa_ref] = _Leitura(geracao, {}, {}, False)
            return self._recusar(
                exc.codigo,
                ferramenta=FERRAMENTA_LER,
                conversa_ref=conversa_ref,
            )
        try:
            atual = self._chatwoot.geracao(conversa_ref) == geracao
        except Exception:
            atual = False
        if not atual:
            return self._recusar(
                "leitura_obsoleta", ferramenta=FERRAMENTA_LER, conversa_ref=conversa_ref,
            )
        self._leituras[conversa_ref] = _Leitura(
            geracao=geracao,
            imagens=imagens,
            audios=audios,
            completa=True,
        )
        self._auditar(
            FERRAMENTA_LER,
            ok=True,
            conversa_ref=conversa_ref,
            n_mensagens=len(saida),
            n_imagens=len(imagens),
            n_audios=len(audios),
        )
        _log(
            "ler_conversa",
            conversa_ref=conversa_ref,
            n_mensagens=len(saida),
            n_imagens=len(imagens),
            n_audios=len(audios),
        )
        return {
            "ok": True,
            "codigo": None,
            "conversa_ref": conversa_ref,
            "mensagens": saida,
        }

    def geracao_lida(self, conversa_ref: str) -> int:
        """Geração do histórico entregue, não a geração de uma consulta posterior."""
        return self._leituras[conversa_ref].geracao

    def preparar_resposta(
        self,
        *,
        conversa_ref: str,
        texto: str,
        idempotency_key: str,
        message_ids: Sequence[str] = (),
        imagem_ref: str | None = None,
    ) -> dict:
        if (
            not isinstance(conversa_ref, str)
            or conversa_ref == ""
            or not isinstance(texto, str)
            or texto == ""
            or not isinstance(idempotency_key, str)
            or idempotency_key == ""
        ):
            return self._recusar("argumento_invalido", ferramenta="preparar_resposta")
        codigo = self._exigir_leitura(conversa_ref)
        if codigo:
            return self._recusar(codigo, ferramenta="preparar_resposta", conversa_ref=conversa_ref)
        ids = tuple(str(item) for item in message_ids)
        imagem: bytes | None = None
        if imagem_ref is not None:
            try:
                imagem = bytes(self._simulador.obter_imagem(imagem_ref))
            except Exception:
                return self._recusar(
                    "midia_indisponivel",
                    ferramenta="preparar_resposta",
                    conversa_ref=conversa_ref,
                    midia_ref=imagem_ref,
                )
            if len(imagem) == 0:
                return self._recusar(
                    "midia_indisponivel",
                    ferramenta="preparar_resposta",
                    conversa_ref=conversa_ref,
                )
        digest = _digest_envio(conversa_ref, texto, imagem, ids)
        self._expirar(idempotency_key)
        existente_ref = self._rascunho_por_chave.get(idempotency_key)
        if existente_ref is not None:
            existente = self._rascunhos[existente_ref]
            if existente.digest != digest:
                return self._recusar(
                    "idempotencia_conflito",
                    ferramenta="preparar_resposta",
                    conversa_ref=conversa_ref,
                )
            return self._resultado_rascunho(existente)
        registro = self._idem.get(idempotency_key)
        if registro is not None and registro.digest != digest:
            return self._recusar(
                "idempotencia_conflito",
                ferramenta="preparar_resposta",
                conversa_ref=conversa_ref,
            )
        leitura = self._leituras[conversa_ref]
        self._seq_rascunho += 1
        ref = f"ras-{self._seq_rascunho}"
        rascunho = _Rascunho(
            ref=ref,
            conversa_ref=conversa_ref,
            texto=texto,
            imagem=imagem,
            imagem_ref=imagem_ref,
            message_ids=ids,
            idempotency_key=idempotency_key,
            digest=digest,
            geracao=leitura.geracao,
        )
        self._rascunhos[ref] = rascunho
        self._rascunho_por_chave[idempotency_key] = ref
        self._auditar(
            "preparar_resposta",
            ok=True,
            conversa_ref=conversa_ref,
            rascunho_ref=ref,
            chars=len(texto),
            bytes=0 if imagem is None else len(imagem),
        )
        _log(
            "preparar_resposta",
            conversa_ref=conversa_ref,
            rascunho_ref=ref,
            chars=len(texto),
            bytes=0 if imagem is None else len(imagem),
        )
        return self._resultado_rascunho(rascunho)

    def responder(self, *, rascunho_ref: str, aprovacao_ref: str) -> dict:
        if not isinstance(rascunho_ref, str) or not isinstance(aprovacao_ref, str):
            return self._recusar("argumento_invalido", ferramenta=FERRAMENTA_RESPONDER)
        rascunho = self._rascunhos.get(rascunho_ref)
        if rascunho is None:
            return self._recusar("rascunho_ausente", ferramenta=FERRAMENTA_RESPONDER)
        codigo_leitura = self._exigir_leitura(rascunho.conversa_ref)
        if codigo_leitura:
            return self._recusar(
                codigo_leitura,
                ferramenta=FERRAMENTA_RESPONDER,
                conversa_ref=rascunho.conversa_ref,
            )
        if not self._aprovado(aprovacao_ref, rascunho.texto, rascunho.imagem):
            return self._recusar(
                "aprovacao_recusada",
                ferramenta=FERRAMENTA_RESPONDER,
                conversa_ref=rascunho.conversa_ref,
                rascunho_ref=rascunho.ref,
            )
        if self._diario is not None:
            try:
                return self._enviar_duravel(rascunho)
            except ErroEntregaDuravel as exc:
                return self._recusar(exc.codigo, ferramenta=FERRAMENTA_RESPONDER)
        if self._expirar(rascunho.idempotency_key):
            return self._recusar(
                "idempotencia_expirada",
                ferramenta=FERRAMENTA_RESPONDER,
                conversa_ref=rascunho.conversa_ref,
            )
        registro = self._idem.get(rascunho.idempotency_key)
        if registro is not None and registro.digest != rascunho.digest:
            return self._recusar(
                "idempotencia_conflito",
                ferramenta=FERRAMENTA_RESPONDER,
                conversa_ref=rascunho.conversa_ref,
            )
        if registro is not None and registro.estado == "em_andamento":
            return self._recusar(
                "em_andamento",
                ferramenta=FERRAMENTA_RESPONDER,
                conversa_ref=rascunho.conversa_ref,
            )
        if registro is not None and registro.estado == "sucesso":
            return self._replay(rascunho, registro, aprovacao_ref)
        codigo = self._validar_pendentes(rascunho)
        if codigo:
            return self._recusar(
                codigo,
                ferramenta=FERRAMENTA_RESPONDER,
                conversa_ref=rascunho.conversa_ref,
            )
        self._idem[rascunho.idempotency_key] = _Idempotencia(
            digest=rascunho.digest,
            expira_em=self._agora() + self._ttl,
            estado="em_andamento",
        )
        try:
            envio = self._simulador.enviar(
                conversa_ref=rascunho.conversa_ref,
                texto=rascunho.texto,
                imagem=rascunho.imagem,
                idempotency_key=rascunho.idempotency_key,
            )
        except Exception:
            self._idem.pop(rascunho.idempotency_key, None)
            return self._recusar(
                "envio_falhou",
                ferramenta=FERRAMENTA_RESPONDER,
                conversa_ref=rascunho.conversa_ref,
            )
        envio_ref = envio.get("envio_ref") if isinstance(envio, Mapping) else None
        if not isinstance(envio, Mapping) or not envio.get("ok") or not isinstance(envio_ref, str):
            self._idem.pop(rascunho.idempotency_key, None)
            return self._recusar(
                "envio_falhou",
                ferramenta=FERRAMENTA_RESPONDER,
                conversa_ref=rascunho.conversa_ref,
            )
        registro = _Idempotencia(
            digest=rascunho.digest,
            expira_em=self._agora() + self._ttl,
            estado="sucesso",
            envio_ref=envio_ref,
        )
        self._idem[rascunho.idempotency_key] = registro
        acked, codigo_ack = self._concluir_ack(rascunho, registro)
        ack_ok = codigo_ack is None
        self._auditar(
            FERRAMENTA_RESPONDER,
            ok=ack_ok,
            conversa_ref=rascunho.conversa_ref,
            rascunho_ref=rascunho.ref,
            aprovacao_ref=aprovacao_ref,
            envio_ref=_ref_publica(envio_ref),
            n_acks=len(acked),
            replay=False,
        )
        _log(
            "responder",
            conversa_ref=rascunho.conversa_ref,
            rascunho_ref=rascunho.ref,
            envio_ref=_ref_publica(envio_ref),
            n_acks=len(acked),
            replay=False,
        )
        return {
            "ok": ack_ok,
            "codigo": codigo_ack,
            "enviado": True,
            "envio_ref": envio_ref,
            "acked": acked,
            "replay": False,
            "ack_ok": ack_ok,
        }

    def chamar(self, ferramenta: str, argumentos: Mapping | None = None) -> dict:
        """Despacho das ferramentas da área. Sem token e sem lease."""
        if ferramenta not in FERRAMENTAS:
            return self._recusar("ferramenta_desconhecida", ferramenta=_ref_publica(ferramenta))
        bruto = dict(argumentos or {})
        for chave in list(bruto):
            if chave in _CHAVES_IGNORADAS:
                bruto.pop(chave)
        if ferramenta == FERRAMENTA_LER:
            return self.ler_conversa(bruto.get("conversa_ref", ""))
        return self.responder(
            rascunho_ref=bruto.get("rascunho_ref", ""),
            aprovacao_ref=bruto.get("aprovacao_ref", ""),
        )

    def _enviar_duravel(self, rascunho: _Rascunho) -> dict:
        diario = self._diario
        assert diario is not None
        # Cada ID precisa pertencer à conversa, incluindo os que já têm ACK.
        # Só o diário decide se esta operação pode voltar a enviar.
        for msg in rascunho.message_ids:
            item = self._fila.obter(msg)
            if item is None or item["conversation_id"] != rascunho.conversa_ref:
                return self._recusar("ack_ausente", ferramenta=FERRAMENTA_RESPONDER)
            if item["estado"] != "pendente":
                anterior = diario.consultar_mensagem(msg)
                if item["estado"] != "entregue" or not anterior or anterior["estado"] not in {"aceito", "concluido"}:
                    return self._recusar("ack_ausente", ferramenta=FERRAMENTA_RESPONDER)
        registro = diario.reservar_envio(
            message_ids=rascunho.message_ids, idempotency_key=rascunho.idempotency_key,
            digest=rascunho.digest,
        )
        acao = registro["acao"]
        if not registro["ok"]:
            return self._recusar(registro["codigo"], ferramenta=FERRAMENTA_RESPONDER)
        if acao == "enviar":
            tentativa = registro["tentativa_id"]
            try:
                envio = self._simulador.enviar(
                    conversa_ref=rascunho.conversa_ref, texto=rascunho.texto,
                    imagem=rascunho.imagem, idempotency_key=rascunho.idempotency_key,
                )
                if not isinstance(envio, Mapping) or envio.get("ok") is not True:
                    raise ValueError("resultado_envio_invalido")
                registro = diario.confirmar_envio(tentativa_id=tentativa, envio_ref=envio["envio_ref"])
            except EnvioNaoEfetuado:
                diario.registrar_falha_envio(tentativa_id=tentativa, comprovadamente_nao_enviado=True)
                return self._recusar("envio_falhou", ferramenta=FERRAMENTA_RESPONDER)
            except Exception:
                diario.registrar_falha_envio(tentativa_id=tentativa, comprovadamente_nao_enviado=False)
                return self._recusar("entrega_incerta", ferramenta=FERRAMENTA_RESPONDER)
        if not registro["enviado"]:
            return self._recusar(registro["codigo"] or "entrega_incerta", ferramenta=FERRAMENTA_RESPONDER)
        return self._ack_duravel(registro, replay=acao != "enviar")

    def _ack_duravel(self, registro: Mapping, *, replay: bool) -> dict:
        diario = self._diario
        assert diario is not None
        tentativa = registro["tentativa_id"]
        pendentes = registro["ack_pendentes"]
        acked = set(registro["message_ids"]) - set(pendentes)
        try:
            if pendentes:
                self._fila.marcar_entregues(pendentes)
            for msg in pendentes:
                item = self._fila.obter(msg)
                if item and item.get("estado") == "entregue":
                    ack = diario.registrar_ack(tentativa_id=tentativa, message_id=msg)
                    if ack["ok"]:
                        acked.add(msg)
        except Exception:
            pass  # Aceite já persistido. A reconciliação só repete o ACK.
        ok = len(acked) == len(registro["message_ids"])
        if not ok:
            diario.registrar_falha_ack(tentativa_id=tentativa)
        return {
            "ok": ok, "codigo": None if ok else "ack_falhou",
            "enviado": True, "replay": replay, "envio_ref": registro["envio_ref"],
            "acked": sorted(acked), "ack_ok": ok,
        }

    def reconciliar_acks(self) -> dict:
        """Somente administração: termina ACK de entregas aceitas; não envia."""
        if self._diario is None:
            return self._recusar("diario_indisponivel")
        resultados = []
        incertos = 0
        for registro in self._diario.listar_acoes_pendentes():
            if registro["acao"] == "somente_ack":
                resultados.append(self._ack_duravel(registro, replay=True))
            else:
                incertos += 1
        return {"ok": all(resp["ok"] for resp in resultados), "resultados": resultados,
                "incertos": incertos}

    def _ler_mensagem(
        self,
        mensagem: Mapping,
        imagens: dict[str, str],
        audios: dict[str, str],
    ) -> dict:
        direcao = str(mensagem.get("direcao") or "")
        if direcao not in _DIRECOES:
            raise RecusaAtendimento("argumento_invalido")
        texto = mensagem.get("texto", "")
        if not isinstance(texto, str):
            raise RecusaAtendimento("argumento_invalido")
        anexos_saida = []
        for anexo in mensagem.get("anexos") or ():
            if not isinstance(anexo, Mapping):
                raise RecusaAtendimento("argumento_invalido")
            tipo = str(anexo.get("file_type") or "").lower()
            midia_ref = str(anexo.get("midia_ref") or "")
            if tipo not in _TIPOS_MIDIA or midia_ref == "":
                raise RecusaAtendimento("midia_indisponivel")
            if tipo == "image":
                conteudo = self._obter_imagem(midia_ref)
                digest = _sha256(conteudo)
                imagens[midia_ref] = digest
                anexos_saida.append({
                    "file_type": "image",
                    "midia_ref": midia_ref,
                    "bytes": len(conteudo),
                    "sha256": digest,
                    "conteudo": conteudo,
                })
            else:
                conteudo = self._obter_audio(midia_ref)
                transcricao = self._transcrever(conteudo)
                audios[midia_ref] = _sha256(conteudo)
                anexos_saida.append({
                    "file_type": "audio",
                    "midia_ref": midia_ref,
                    "bytes": len(conteudo),
                    "sha256": audios[midia_ref],
                    "transcricao": transcricao,
                })
        return {"direcao": direcao, "texto": texto, "anexos": anexos_saida}

    def _obter_imagem(self, midia_ref: str) -> bytes:
        try:
            conteudo = bytes(self._simulador.obter_imagem(midia_ref))
        except Exception:
            raise RecusaAtendimento("midia_indisponivel") from None
        if len(conteudo) == 0:
            raise RecusaAtendimento("midia_indisponivel")
        return conteudo

    def _obter_audio(self, midia_ref: str) -> bytes:
        try:
            conteudo = bytes(self._chatwoot.obter_audio(midia_ref))
        except Exception:
            raise RecusaAtendimento("midia_indisponivel") from None
        if len(conteudo) == 0:
            raise RecusaAtendimento("midia_indisponivel")
        return conteudo

    def _transcrever(self, audio: bytes) -> str:
        if self._transcritor is None:
            raise RecusaAtendimento("transcricao_ausente")
        try:
            transcricao = self._transcritor.transcrever(audio, idioma="pt")
        except Exception:
            raise RecusaAtendimento("transcricao_ausente") from None
        if not isinstance(transcricao, str) or transcricao.strip() == "":
            raise RecusaAtendimento("transcricao_ausente")
        return transcricao

    def _exigir_leitura(self, conversa_ref: str) -> str | None:
        leitura = self._leituras.get(conversa_ref)
        if leitura is None or not leitura.completa:
            return "leitura_obrigatoria"
        try:
            geracao = self._chatwoot.geracao(conversa_ref)
        except Exception:
            return "leitura_obsoleta"
        if geracao != leitura.geracao:
            return "leitura_obsoleta"
        try:
            for midia_ref, digest in leitura.imagens.items():
                if _sha256(self._obter_imagem(midia_ref)) != digest:
                    return "leitura_obsoleta"
            for midia_ref, digest in leitura.audios.items():
                if _sha256(self._obter_audio(midia_ref)) != digest:
                    return "leitura_obsoleta"
        except RecusaAtendimento:
            return "leitura_obsoleta"
        return None

    def _aprovado(self, aprovacao_ref: str, texto: str, imagem: bytes | None) -> bool:
        try:
            conferido = self._verificador.conferir(aprovacao_ref, texto, imagem)
        except Exception:
            return False
        if not isinstance(conferido, str):
            return False
        return _igual(conferido, _digest_payload(texto, imagem))

    def _validar_pendentes(self, rascunho: _Rascunho) -> str | None:
        for message_id in rascunho.message_ids:
            try:
                item = self._fila.obter(message_id)
            except Exception:
                return "ack_ausente"
            if not isinstance(item, Mapping):
                return "ack_ausente"
            if item.get("estado") != "pendente":
                return "ack_ausente"
            if item.get("conversation_id") != rascunho.conversa_ref:
                return "ack_conversa_divergente"
        return None

    def _concluir_ack(
        self,
        rascunho: _Rascunho,
        registro: _Idempotencia,
    ) -> tuple[list[str], str | None]:
        ids = list(rascunho.message_ids)
        if not ids:
            registro.ack_ok = True
            return [], None
        try:
            faltam = []
            for message_id in ids:
                item = self._fila.obter(message_id)
                if not isinstance(item, Mapping):
                    registro.ack_ok = False
                    return [], "ack_falhou"
                if item.get("conversation_id") != rascunho.conversa_ref:
                    registro.ack_ok = False
                    return [], "ack_falhou"
                estado = item.get("estado")
                if estado == "pendente":
                    faltam.append(message_id)
                elif estado != "entregue":
                    registro.ack_ok = False
                    return [], "ack_falhou"
            if faltam:
                self._fila.marcar_entregues(faltam)
            for message_id in ids:
                item = self._fila.obter(message_id)
                if not isinstance(item, Mapping) or item.get("estado") != "entregue":
                    registro.ack_ok = False
                    return [], "ack_falhou"
        except Exception:
            registro.ack_ok = False
            return [], "ack_falhou"
        registro.ack_ok = True
        return ids, None

    def _replay(
        self,
        rascunho: _Rascunho,
        registro: _Idempotencia,
        aprovacao_ref: str,
    ) -> dict:
        acked, codigo_ack = self._concluir_ack(rascunho, registro)
        ack_ok = codigo_ack is None
        envio_ref = _ref_publica(registro.envio_ref)
        self._auditar(
            FERRAMENTA_RESPONDER,
            ok=ack_ok,
            conversa_ref=rascunho.conversa_ref,
            rascunho_ref=rascunho.ref,
            aprovacao_ref=aprovacao_ref,
            envio_ref=envio_ref,
            n_acks=len(acked),
            replay=True,
        )
        _log(
            "responder",
            conversa_ref=rascunho.conversa_ref,
            envio_ref=envio_ref,
            n_acks=len(acked),
            replay=True,
        )
        return {
            "ok": ack_ok,
            "codigo": codigo_ack,
            "enviado": True,
            "envio_ref": registro.envio_ref,
            "acked": acked,
            "replay": True,
            "ack_ok": ack_ok,
        }

    def _resultado_rascunho(self, rascunho: _Rascunho) -> dict:
        return {
            "ok": True,
            "codigo": None,
            "rascunho_ref": rascunho.ref,
            "conversa_ref": rascunho.conversa_ref,
            "chars": len(rascunho.texto),
            "imagem_sha256": None if rascunho.imagem is None else _sha256(rascunho.imagem),
        }

    def _expirar(self, chave: str) -> bool:
        registro = self._idem.get(chave)
        if registro is None or registro.expira_em > self._agora():
            return False
        if registro.estado == "sucesso" and not registro.ack_ok:
            # Enquanto o ACK não foi reconciliado, nunca transformar um envio
            # aceito em outro envio por expiração do registro.
            return False
        self._idem.pop(chave, None)
        ref = self._rascunho_por_chave.pop(chave, None)
        if ref is not None:
            self._rascunhos.pop(ref, None)
        return True

    def _agora(self) -> datetime:
        agora = self._relogio()
        if agora.tzinfo is None:
            return agora.replace(tzinfo=timezone.utc)
        return agora

    def _auditar(self, ferramenta: str, **campos: object) -> None:
        evento = {"ferramenta": ferramenta}
        evento.update(campos)
        self._auditoria.registrar(evento)


def montar_laboratorio(
    *,
    transcritor: Transcritor | None,
    relogio: Callable[[], datetime] | None = None,
    ttl_segundos: int = _TTL_PADRAO_SEGUNDOS,
) -> tuple[
    AdaptadorAtendimento,
    FilaLaboratorio,
    ChatwootLaboratorio,
    SimuladorAtendimento,
    VerificadorAprovacaoServidor,
    AuditoriaLaboratorio,
]:
    """Liga as cópias locais. Não cadastra agente, não emite token e não cria lease."""
    fila = FilaLaboratorio()
    chatwoot = ChatwootLaboratorio()
    simulador = SimuladorAtendimento()
    verificador = VerificadorAprovacaoServidor()
    auditoria = AuditoriaLaboratorio()
    adaptador = AdaptadorAtendimento(
        fila=fila,
        chatwoot=chatwoot,
        simulador=simulador,
        transcritor=transcritor,
        verificador=verificador,
        auditoria=auditoria,
        relogio=relogio,
        ttl_segundos=ttl_segundos,
    )
    return adaptador, fila, chatwoot, simulador, verificador, auditoria
