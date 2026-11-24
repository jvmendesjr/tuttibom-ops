"""Ponte do Chatwoot de laboratório para os protocolos do núcleo.

Envolve o ``ChatwootIsolado`` já provado. Não abre porta, não lê token,
não confirma mensagem e não fala com produção. O núcleo monta::

    BackendsAtendimento(**compor_backends_atendimento(backend, fila=fila, diario=diario))

``chat`` cumpre ``LeituraConversa`` e ``destino`` cumpre ``MidiaEDestino``.
Os dois são o mesmo objeto. ``transcritor`` fica nulo: este lab só
entrega PNG, e áudio não é fingido.

"""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Mapping
from typing import Protocol

from .atendimento import EnvioNaoEfetuado
from .chatwoot_isolado import ChatwootIsolado
from .erros import ErroOps

LIMITE_AUDIO = "audio_nao_suportado_no_lab"
CAMPOS_BACKENDS_ATENDIMENTO = ("fila", "chat", "destino", "transcritor", "diario")

_CONVERSA = re.compile(r"^[1-9][0-9]{0,8}$")
_ID_REAL = re.compile(r"^[1-9][0-9]{0,17}$")
_REF = re.compile(r"^[A-Za-z0-9_-]{1,96}$")
_PNG = b"\x89PNG\r\n\x1a\n"
_LOG = logging.getLogger("tuttibom.mcp_ops.chatwoot_backend_lab")


class EnvioIncerto(Exception):
    """A entrega pode ter ocorrido. Não é EnvioNaoEfetuado."""

    def __init__(self, codigo: str = "envio_incerto") -> None:
        self.codigo = codigo if isinstance(codigo, str) and codigo else "envio_incerto"
        super().__init__(self.codigo)


class LeituraLab(ErroOps):
    """A leitura do inbox sintético não pôde ser adaptada."""

    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__()


class LimiteAudioLab(ErroOps):
    """O lab provou PNG. Áudio não é transcrito nem substituído por bytes."""

    def __init__(self, codigo: str = LIMITE_AUDIO) -> None:
        self.codigo = codigo
        super().__init__()


class FilaDeIncoming(Protocol):
    """O que a ponte usa de ``FilaPersistente.registrar``."""

    def registrar(self, *, message_id: str, conversation_id: str) -> bool: ...


def compor_backends_atendimento(backend, *, fila, diario, transcritor=None) -> dict:
    """Campos de ``BackendsAtendimento``, por nome.

    ``transcritor`` padrão é ``None``. Passar um transcritor não faz o
    áudio existir: ``obter_audio`` continua recusando.
    """

    return {
        "fila": fila,
        "chat": backend,
        "destino": backend,
        "transcritor": transcritor,
        "diario": diario,
    }


def _versao(ids: tuple[str, ...]) -> int:
    material = "\n".join(ids).encode("ascii")
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


class ChatwootBackendLab:
    """Leitura e envio de uma conversa do inbox sintético."""

    def __init__(self, chatwoot: ChatwootIsolado, *, conversa_ref: str) -> None:
        if not isinstance(conversa_ref, str) or _CONVERSA.fullmatch(conversa_ref) is None:
            raise ValueError("conversa_invalida")
        self._chat = chatwoot
        self.conversa_ref = conversa_ref
        self._imagens: dict[str, bytes] = {}

    def __repr__(self) -> str:
        return f"ChatwootBackendLab(conversa_ref={self.conversa_ref!r})"

    def compor(self, *, fila, diario) -> dict:
        return compor_backends_atendimento(self, fila=fila, diario=diario)

    def ler_mensagens(self, conversa_ref: str) -> list[dict] | None:
        snap = self._snapshot(conversa_ref)
        if snap is None:
            return None
        _LOG.info("ler n=%s", len(snap[0]))
        return snap[0]

    def obter_audio(self, midia_ref: str) -> bytes:
        raise LimiteAudioLab(LIMITE_AUDIO)

    def geracao(self, conversa_ref: str) -> int:
        snap = self._snapshot(conversa_ref)
        if snap is None:
            raise LeituraLab("conversa_desconhecida")
        return _versao(snap[1])

    def obter_imagem(self, midia_ref: str) -> bytes:
        if not isinstance(midia_ref, str) or midia_ref == "":
            raise KeyError("midia_ausente")
        if midia_ref not in self._imagens:
            self.ler_mensagens(self.conversa_ref)
        conteudo = self._imagens.get(midia_ref)
        if not isinstance(conteudo, bytes) or not conteudo.startswith(_PNG):
            raise KeyError(midia_ref)
        return bytes(conteudo)

    def enviar(
        self,
        *,
        conversa_ref: str,
        texto: str,
        imagem: bytes | None,
        idempotency_key: str,
    ) -> dict:
        del idempotency_key  # o diário do núcleo é quem deduplica; o Chatwoot não
        if conversa_ref != self.conversa_ref:
            raise EnvioNaoEfetuado("conversa_fora_do_inbox")
        if not isinstance(texto, str) or (imagem is not None and not isinstance(imagem, bytes)):
            raise EnvioNaoEfetuado("argumento_invalido")
        try:
            resultado = self._chat.enviar(
                conversa_ref,
                texto=texto if texto else None,
                imagem=imagem,
            )
        except EnvioNaoEfetuado:
            raise
        except Exception as exc:
            raise EnvioIncerto("envio_incerto") from exc
        return self._classificar_envio(resultado)

    def importar_incoming_publicos(self, fila: FilaDeIncoming) -> dict:
        """Registra só IDs incoming públicos já lidos. Não confirma."""

        snap = self._snapshot(self.conversa_ref)
        if snap is None:
            raise LeituraLab("conversa_desconhecida")
        incoming = snap[2]
        for message_id in incoming:
            if _ID_REAL.fullmatch(message_id) is None:
                raise LeituraLab("id_nao_real")
        vistos: list[str] = []
        inseridos = 0
        existentes = 0
        for message_id in dict.fromkeys(incoming):
            if fila.registrar(message_id=message_id, conversation_id=self.conversa_ref):
                inseridos += 1
            else:
                existentes += 1
            vistos.append(message_id)
        _LOG.info("importar inseridos=%s existentes=%s", inseridos, existentes)
        return {
            "ok": True,
            "inseridos": inseridos,
            "existentes": existentes,
            "ids": tuple(vistos),
        }

    def _snapshot(self, conversa_ref: str):
        if conversa_ref != self.conversa_ref:
            return None
        bruto = self._chat.ler_historico(conversa_ref)
        if not isinstance(bruto, Mapping) or bruto.get("ok") is not True or bruto.get("incerto") is not False:
            codigo = bruto.get("codigo") if isinstance(bruto, Mapping) else None
            raise LeituraLab(codigo if isinstance(codigo, str) and codigo else "leitura_incerta")
        mensagens: list[dict] = []
        ids: list[str] = []
        incoming: list[str] = []
        imagens: dict[str, bytes] = {}
        for item in bruto.get("mensagens") or ():
            if not isinstance(item, Mapping):
                raise LeituraLab("leitura_falhou")
            message_id = item.get("id")
            direcao = item.get("direcao")
            texto = item.get("texto")
            if not isinstance(message_id, str) or _ID_REAL.fullmatch(message_id) is None:
                raise LeituraLab("leitura_falhou")
            if direcao not in {"incoming", "outgoing"} or not isinstance(texto, str):
                raise LeituraLab("leitura_falhou")
            anexos = []
            for anexo in item.get("anexos") or ():
                anexos.append(self._anexo(anexo, imagens))
            mensagens.append({"direcao": direcao, "texto": texto, "anexos": anexos})
            ids.append(message_id)
            if direcao == "incoming" and item.get("private") is not True and item.get("privado") is not True:
                incoming.append(message_id)
        self._imagens = imagens
        return mensagens, tuple(ids), tuple(incoming)

    def _anexo(self, anexo: object, imagens: dict[str, bytes]) -> dict:
        if not isinstance(anexo, Mapping):
            raise LeituraLab("leitura_falhou")
        tipo = str(anexo.get("file_type") or "").lower()
        if tipo == "audio":
            raise LimiteAudioLab(LIMITE_AUDIO)
        if tipo != "image":
            raise LeituraLab("midia_indisponivel")
        ref = anexo.get("midia_ref")
        conteudo = anexo.get("conteudo")
        if not isinstance(ref, str) or _REF.fullmatch(ref) is None:
            raise LeituraLab("midia_indisponivel")
        if not isinstance(conteudo, bytes) or not conteudo.startswith(_PNG):
            raise LeituraLab("midia_indisponivel")
        if ref in imagens and imagens[ref] != conteudo:
            raise LeituraLab("midia_indisponivel")
        imagens[ref] = bytes(conteudo)
        return {"file_type": "image", "midia_ref": ref}

    def _classificar_envio(self, resultado: object) -> dict:
        if not isinstance(resultado, Mapping):
            raise EnvioIncerto("envio_incerto")
        if resultado.get("ok") is True and resultado.get("incerto") is False:
            ref = resultado.get("message_ref")
            if isinstance(ref, str) and _REF.fullmatch(ref):
                return {"ok": True, "envio_ref": ref}
            raise EnvioIncerto("envio_incerto")
        if resultado.get("ok") is not True and resultado.get("incerto") is False:
            codigo = resultado.get("codigo")
            if not isinstance(codigo, str) or codigo == "":
                codigo = "envio_falhou"
            raise EnvioNaoEfetuado(codigo)
        raise EnvioIncerto("envio_incerto")


__all__ = [
    "CAMPOS_BACKENDS_ATENDIMENTO",
    "ChatwootBackendLab",
    "EnvioIncerto",
    "EnvioNaoEfetuado",
    "LIMITE_AUDIO",
    "LeituraLab",
    "LimiteAudioLab",
    "compor_backends_atendimento",
]
