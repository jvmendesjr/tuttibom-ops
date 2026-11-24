"""Transporte do Chatwoot 4.20.1 CE de laboratório.

Assinatura
----------
``ChatwootIsolado(transporte, *, conta_id, inbox_id, validador=None)``

- ``transporte`` implementa ``TransporteLab.chamar(metodo, caminho, *, corpo, tipo, autenticar)``
  e devolve ``RespostaTransporte``. O caminho pode conter o marcador
  ``{inbox_identifier}``. Quem substitui o marcador é o transporte, dentro
  do namespace isolado. O adaptador não recebe token, identificador do
  inbox nem socket Docker.
- ``conta_id`` e ``inbox_id`` fixam a conta e o inbox. Outra conta ou
  outro inbox é recusado.
- ``validador`` padrão: ``ValidadorOrigemLab`` (origem
  ``http://127.0.0.1:3000``). Chamadas da API só entram em
  ``/api/v1/accounts/<conta>/`` ou ``/public/api/v1/inboxes/{inbox_identifier}/``.
  URL vinda do Chatwoot (anexo e redirecionamento) só entra em
  ``/rails/active_storage/``. O adaptador não segue redirecionamento
  sozinho: pede o próximo caminho apenas se o validador aceitar.

A aprovação do texto e da imagem exatos continua em
``VerificadorAprovacaoServidor`` (``atendimento.py``). Este módulo não
aprova conteúdo.

O Chatwoot 4.20.1 CE não deduplica ``POST`` de mensagem. Este adaptador
não envia chave de idempotência e não grava envio. Duas chamadas aceitas
criam duas mensagens. Persistência da chave é outra frente.

Falha conhecida (``envio_falhou``, ``incerto`` falso): a resposta HTTP
é 400, 401, 403, 404, 406, 415 ou 422. O pedido foi recusado.
Envio incerto (``envio_incerto``, ``incerto`` verdadeiro): timeout depois
do envio, queda no meio, 408, 409, 429 ou 5xx, ou 200 sem id. Não dá
para afirmar que a mensagem não ficou gravada.
Transporte parado antes do envio (``transporte_indisponivel``,
``incerto`` falso): a conexão nem chegou a sair.

``TransporteHttpLoopback`` é o cliente HTTP para um processo que já está
no namespace em que ``127.0.0.1:3000`` é este lab. Ele não segue
redirecionamento, não abre outra porta e lê o token só do arquivo local
quando ``autenticar`` é verdadeiro.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from tuttibom.contratos.pii import detectar_pii

ORIGEM_LAB = "http://127.0.0.1:3000"
VALIDADOR = "ValidadorOrigemLab"
NOME_CONTATO_FICTICIO = "Pessoa Ficticia Lab"
_CONTA = re.compile(r"^[1-9][0-9]{0,8}$")
_REF = re.compile(r"^[a-z0-9-]{1,80}$")
_FALHA_CONHECIDA = frozenset({400, 401, 403, 404, 406, 415, 422})
_INCERTO_HTTP = frozenset({408, 409, 425, 429, 500, 502, 503, 504})
_REDIRECIONA = frozenset({301, 302, 303, 307, 308})
_TIPOS_MENSAGEM = {0: "incoming", 1: "outgoing"}
_PNG = b"\x89PNG\r\n\x1a\n"
_MAX_IMAGEM = 1_048_576
_MAX_TEXTO = 4_000
_MAX_PAGINAS = 5
_PAGINA = 20
_MAX_SALTOS = 4

log = logging.getLogger("tuttibom.mcp_ops.chatwoot_isolado")


class RecusaChatwootIsolado(Exception):
    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(codigo)


@dataclass(frozen=True)
class RespostaTransporte:
    """Resposta crua. ``enviada`` diz se o pedido chegou a sair."""

    status: int
    corpo: bytes
    enviada: bool
    redirecionamento: str | None = None


class TransporteLab(Protocol):
    def chamar(
        self,
        metodo: str,
        caminho: str,
        *,
        corpo: bytes | None = None,
        tipo: str | None = None,
        autenticar: bool = False,
    ) -> RespostaTransporte: ...


class ValidadorOrigemLab:
    """Aceita só o loopback do lab e os caminhos de API ou de anexo."""

    def __init__(self, origem: str = ORIGEM_LAB, conta_id: str = "") -> None:
        partes = urlsplit(origem)
        if (
            partes.scheme != "http"
            or partes.hostname != "127.0.0.1"
            or partes.port != 3000
            or partes.username
            or partes.password
            or partes.path not in ("", "/")
            or partes.query
            or partes.fragment
        ):
            raise RecusaChatwootIsolado("origem_invalida")
        if conta_id and not _CONTA.fullmatch(conta_id):
            raise RecusaChatwootIsolado("argumento_invalido")
        self.origem = origem
        self.conta_id = conta_id

    def caminho(self, referencia: str, *, anexo: bool = False) -> str:
        texto = referencia.strip()
        if texto.startswith("/") and "://" not in texto:
            bruto = texto
        else:
            bruto = self._absoluto(texto)
        partes = urlsplit(bruto)
        if partes.scheme or partes.netloc or partes.fragment:
            raise RecusaChatwootIsolado("origem_recusada")
        caminho = partes.path
        if (
            not caminho.startswith("/")
            or "//" in caminho
            or ".." in caminho.split("/")
            or "@" in caminho
        ):
            raise RecusaChatwootIsolado("origem_recusada")
        permitido = caminho.startswith("/rails/active_storage/") if anexo else self._prefixo(caminho)
        if not permitido:
            raise RecusaChatwootIsolado("origem_recusada")
        if partes.query and not re.fullmatch(r"[A-Za-z0-9._~%=&+-]+", partes.query):
            raise RecusaChatwootIsolado("origem_recusada")
        if partes.query:
            return f"{caminho}?{partes.query}"
        return caminho

    def _absoluto(self, referencia: str) -> str:
        partes = urlsplit(referencia)
        if (
            partes.scheme != "http"
            or partes.hostname != "127.0.0.1"
            or partes.port != 3000
            or partes.username
            or partes.password
            or partes.fragment
        ):
            raise RecusaChatwootIsolado("origem_recusada")
        consulta = f"?{partes.query}" if partes.query else ""
        return f"{partes.path}{consulta}"

    def _prefixo(self, caminho: str) -> bool:
        if caminho.startswith("/rails/active_storage/"):
            return True
        if caminho.startswith("/public/api/v1/inboxes/"):
            resto = caminho.removeprefix("/public/api/v1/inboxes/")
            return resto.startswith("{inbox_identifier}/") or re.match(r"^[A-Za-z0-9]{8,}/", resto) is not None
        prefixo = f"/api/v1/accounts/{self.conta_id}/"
        return bool(self.conta_id) and caminho.startswith(prefixo)


def _linha(evento: str, **campos: object) -> None:
    partes = [evento]
    for chave in sorted(campos):
        valor = campos[chave]
        if isinstance(valor, bool):
            partes.append(f"{chave}={'sim' if valor else 'nao'}")
        elif isinstance(valor, int):
            partes.append(f"{chave}={valor}")
        else:
            texto = str(valor)
            if detectar_pii(texto) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", texto):
                texto = "oculto"
            partes.append(f"{chave}={texto}")
    linha = " ".join(partes)
    if detectar_pii(linha):
        linha = "chatwoot_isolado evento=suprimido"
    log.info("%s", linha)


def _resultado(ok: bool, codigo: str | None, *, incerto: bool, **campos: object) -> dict:
    saida: dict = {"ok": ok, "codigo": codigo, "incerto": incerto, "deduplicado": False}
    saida.update(campos)
    return saida


def _multipart(campos: list[tuple[str, str]], arquivo: tuple[str, bytes] | None) -> tuple[bytes, str]:
    conteudo = b"" if arquivo is None else arquivo[1]
    limite = "tb" + secrets.token_hex(8)
    while limite.encode() in conteudo:
        limite = "tb" + secrets.token_hex(8)
    pedacos: list[bytes] = []
    for nome, valor in campos:
        pedacos.append(
            f"--{limite}\r\nContent-Disposition: form-data; name=\"{nome}\"\r\n\r\n{valor}\r\n".encode()
        )
    if arquivo is not None:
        nome, conteudo = arquivo
        pedacos.append(
            (
                f"--{limite}\r\nContent-Disposition: form-data; "
                f"name=\"attachments[]\"; filename=\"{nome}\"\r\n"
                f"Content-Type: image/png\r\n\r\n"
            ).encode()
            + conteudo
            + b"\r\n"
        )
    pedacos.append(f"--{limite}--\r\n".encode())
    return b"".join(pedacos), f"multipart/form-data; boundary={limite}"


class TransporteHttpLoopback:
    """HTTP só para 127.0.0.1:3000. Não segue redirecionamento."""

    def __init__(self, arquivo: str, abertura=None) -> None:
        self._arquivo = arquivo
        self._abrir = abertura or self._abrir_padrao

    def _abrir_padrao(self):
        import http.client

        return http.client.HTTPConnection("127.0.0.1", 3000, timeout=15)

    def chamar(
        self,
        metodo: str,
        caminho: str,
        *,
        corpo: bytes | None = None,
        tipo: str | None = None,
        autenticar: bool = False,
    ) -> RespostaTransporte:
        try:
            caminho = self._substituir(caminho)
        except RecusaChatwootIsolado:
            return RespostaTransporte(0, b"", False, None)
        if metodo not in {"GET", "POST", "DELETE"}:
            return RespostaTransporte(0, b"", False, None)
        cabecalhos = {"Accept": "application/json, image/png, */*"}
        if tipo:
            cabecalhos["Content-Type"] = tipo
        if autenticar:
            try:
                cabecalhos["api_access_token"] = self._segredo("token")
            except RecusaChatwootIsolado:
                return RespostaTransporte(0, b"", False, None)
        conexao = self._abrir()
        try:
            conexao.request(metodo, caminho, body=corpo, headers=cabecalhos)
            resposta = conexao.getresponse()
            bruto = resposta.read()
            local = resposta.getheader("Location")
            return RespostaTransporte(int(resposta.status), bruto, True, local)
        except Exception:
            # request() pode falhar depois de começar a escrita no socket.
            return RespostaTransporte(0, b"", True, None)
        finally:
            try:
                conexao.close()
            except Exception:
                pass

    def _substituir(self, caminho: str) -> str:
        if "{inbox_identifier}" not in caminho:
            return caminho
        ident = self._segredo("inbox_identifier")
        if not re.fullmatch(r"[A-Za-z0-9]{8,}", ident):
            raise RecusaChatwootIsolado("origem_recusada")
        return caminho.replace("{inbox_identifier}", ident)

    def _segredo(self, campo: str) -> str:
        try:
            with open(self._arquivo, encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except (OSError, ValueError, TypeError):
            raise RecusaChatwootIsolado("transporte_indisponivel") from None
        valor = dados.get(campo) if isinstance(dados, dict) else None
        if not isinstance(valor, str) or valor == "":
            raise RecusaChatwootIsolado("transporte_indisponivel")
        return valor


class ChatwootIsolado:
    """Lê o histórico e envia texto ou PNG na conta e no inbox fixos."""

    def __init__(
        self,
        transporte: TransporteLab,
        *,
        conta_id: str,
        inbox_id: str,
        validador: ValidadorOrigemLab | None = None,
    ) -> None:
        if not _CONTA.fullmatch(conta_id) or not _CONTA.fullmatch(inbox_id):
            raise RecusaChatwootIsolado("argumento_invalido")
        self._transporte = transporte
        self.conta_id = conta_id
        self.inbox_id = inbox_id
        self.validador = validador or ValidadorOrigemLab(conta_id=conta_id)

    def __repr__(self) -> str:
        return f"ChatwootIsolado(conta={self.conta_id} inbox={self.inbox_id})"

    def abrir_conversa(self, contato_ref: str) -> dict:
        if not _REF.fullmatch(contato_ref):
            return self._falha("argumento_invalido", incerto=False)
        corpo = json.dumps({
            "name": NOME_CONTATO_FICTICIO,
            "identifier": contato_ref,
            "source_id": contato_ref,
        }).encode()
        resposta = self._pedir(
            "POST",
            "/public/api/v1/inboxes/{inbox_identifier}/contacts",
            corpo=corpo,
            tipo="application/json",
            autenticar=False,
        )
        dados = self._json_objeto(resposta)
        if resposta is None or dados is None or resposta.status not in (200, 201):
            return self._classificar_leitura(resposta, "abertura_falhou")
        if dados.get("source_id") != contato_ref:
            return self._falha("abertura_falhou", incerto=False)
        conversa = self._pedir(
            "POST",
            f"/public/api/v1/inboxes/{{inbox_identifier}}/contacts/{contato_ref}/conversations",
            corpo=b"{}",
            tipo="application/json",
            autenticar=False,
        )
        criado = self._json_objeto(conversa)
        if conversa is None or criado is None or conversa.status not in (200, 201):
            return self._classificar_leitura(conversa, "abertura_falhou")
        if str(criado.get("inbox_id")) != self.inbox_id:
            return self._falha("inbox_divergente", incerto=True)
        ref = criado.get("id")
        if not isinstance(ref, int):
            return self._falha("abertura_falhou", incerto=True)
        _linha("abrir_conversa", conversa_ref=str(ref), status=conversa.status)
        return _resultado(True, None, incerto=False, conversa_ref=str(ref), contato_ref=contato_ref)

    def enviar_entrada_imagem(self, *, contato_ref: str, conversa_ref: str, imagem: bytes) -> dict:
        if not _REF.fullmatch(contato_ref) or not _CONTA.fullmatch(conversa_ref):
            return self._falha("argumento_invalido", incerto=False)
        png = self._png(imagem)
        if png is None:
            return self._falha("argumento_invalido", incerto=False)
        corpo, tipo = _multipart([], ("lab.png", png))
        return self._enviar(
            "POST",
            (
                "/public/api/v1/inboxes/{inbox_identifier}/contacts/"
                f"{contato_ref}/conversations/{conversa_ref}/messages"
            ),
            corpo,
            tipo,
            autenticar=False,
            conversa_ref=conversa_ref,
        )

    def enviar(self, conversa_ref: str, *, texto: str | None = None, imagem: bytes | None = None) -> dict:
        if not _CONTA.fullmatch(conversa_ref):
            return self._falha("argumento_invalido", incerto=False)
        if texto is not None and (not isinstance(texto, str) or texto == "" or len(texto) > _MAX_TEXTO):
            return self._falha("argumento_invalido", incerto=False)
        png = None
        if imagem is not None:
            png = self._png(imagem)
            if png is None:
                return self._falha("argumento_invalido", incerto=False)
        if texto is None and png is None:
            return self._falha("argumento_invalido", incerto=False)
        validacao = self._validar_conversa(conversa_ref)
        if validacao is not None:
            # Ainda não houve POST, independentemente da causa da falha de leitura.
            return self._falha(validacao["codigo"], incerto=False)
        caminho = f"/api/v1/accounts/{self.conta_id}/conversations/{conversa_ref}/messages"
        if png is None:
            corpo = json.dumps({"content": texto, "message_type": "outgoing"}).encode()
            tipo = "application/json"
        else:
            campos = [("message_type", "outgoing")]
            if texto is not None:
                campos.append(("content", texto))
            corpo, tipo = _multipart(campos, ("previa.png", png))
        return self._enviar("POST", caminho, corpo, tipo, autenticar=True, conversa_ref=conversa_ref)

    def ler_historico(self, conversa_ref: str) -> dict:
        if not _CONTA.fullmatch(conversa_ref):
            return self._falha("argumento_invalido", incerto=False)
        validacao = self._validar_conversa(conversa_ref)
        if validacao is not None:
            return validacao
        try:
            brutas = self._paginar(conversa_ref)
        except RecusaChatwootIsolado as exc:
            return self._falha(exc.codigo, incerto=exc.codigo == "leitura_incerta")
        mensagens = []
        try:
            for item in brutas:
                if str(item.get("inbox_id")) != self.inbox_id:
                    return self._falha("inbox_divergente", incerto=False)
                direcao = _TIPOS_MENSAGEM.get(item.get("message_type"))
                if item["private"] or direcao is None:
                    continue
                texto = item.get("content")
                if texto is None:
                    texto = ""
                if not isinstance(texto, str):
                    return self._falha("leitura_falhou", incerto=False)
                anexos = []
                for anexo in item.get("anexos") or ():
                    if anexo.get("file_type") != "image":
                        return self._falha("midia_indisponivel", incerto=False)
                    conteudo = self._baixar_imagem(anexo.get("data_url"))
                    anexos.append({
                        "file_type": "image",
                        "midia_ref": f"anexo-{anexo['id']}",
                        "bytes": len(conteudo),
                        "sha256": hashlib.sha256(conteudo).hexdigest(),
                        "conteudo": conteudo,
                    })
                mensagens.append({
                    "id": str(item["id"]),
                    "direcao": direcao,
                    "texto": texto,
                    "anexos": anexos,
                })
        except RecusaChatwootIsolado as exc:
            return self._falha(exc.codigo, incerto=False)
        _linha("ler_historico", conversa_ref=conversa_ref, n_mensagens=len(mensagens))
        return _resultado(True, None, incerto=False, conversa_ref=conversa_ref, mensagens=mensagens)

    def _validar_conversa(self, conversa_ref: str) -> dict | None:
        resposta = self._pedir(
            "GET",
            f"/api/v1/accounts/{self.conta_id}/conversations/{conversa_ref}",
            autenticar=True,
        )
        dados = self._json_objeto(resposta)
        if resposta is None or dados is None or resposta.status != 200:
            return self._classificar_leitura(resposta, "leitura_falhou")
        if (
            str(dados.get("id")) != conversa_ref or str(dados.get("account_id")) != self.conta_id
            or str(dados.get("inbox_id")) != self.inbox_id
        ):
            return self._falha("inbox_divergente", incerto=False)
        return None

    def _enviar(
        self,
        metodo: str,
        caminho: str,
        corpo: bytes,
        tipo: str,
        *,
        autenticar: bool,
        conversa_ref: str,
    ) -> dict:
        resposta = self._pedir(metodo, caminho, corpo=corpo, tipo=tipo, autenticar=autenticar)
        if resposta is None:
            return self._falha("envio_incerto", incerto=True, conversa_ref=conversa_ref)
        if not resposta.enviada:
            return self._falha("transporte_indisponivel", incerto=False, status=resposta.status)
        if resposta.status in _FALHA_CONHECIDA:
            return self._falha("envio_falhou", incerto=False, status=resposta.status)
        if resposta.status in _INCERTO_HTTP or resposta.status == 0:
            return self._falha("envio_incerto", incerto=True, status=resposta.status)
        dados = self._json_objeto(resposta)
        if resposta.status not in (200, 201) or dados is None or not isinstance(dados.get("id"), int):
            return self._falha("envio_incerto", incerto=True, status=resposta.status)
        if "inbox_id" in dados and str(dados.get("inbox_id")) != self.inbox_id:
            return self._falha("inbox_divergente", incerto=True, status=resposta.status)
        _linha("enviar", conversa_ref=conversa_ref, status=resposta.status, bytes=len(corpo))
        return _resultado(
            True,
            None,
            incerto=False,
            conversa_ref=conversa_ref,
            message_ref=f"msg-{dados['id']}",
            status=resposta.status,
        )

    def _paginar(self, conversa_ref: str) -> list[dict]:
        todas: list[dict] = []
        antes = ""
        visto = ""
        for _ in range(_MAX_PAGINAS):
            caminho = f"/api/v1/accounts/{self.conta_id}/conversations/{conversa_ref}/messages"
            if antes:
                caminho = f"{caminho}?before={antes}"
            resposta = self._pedir("GET", caminho, autenticar=True)
            if resposta is None or not resposta.enviada or resposta.status in _INCERTO_HTTP or resposta.status == 0:
                raise RecusaChatwootIsolado("leitura_incerta")
            if resposta.status in _FALHA_CONHECIDA or resposta.status not in (200, 201):
                raise RecusaChatwootIsolado("leitura_falhou")
            dados = self._json_objeto(resposta)
            payload = dados.get("payload") if isinstance(dados, dict) else None
            if not isinstance(payload, list):
                raise RecusaChatwootIsolado("leitura_falhou")
            lote = [self._mensagem_reduzida(item) for item in payload]
            if lote and lote[0]["id"] == visto:
                break
            todas = lote + todas if antes else lote
            if len(lote) < _PAGINA:
                break
            primeiro = min(int(item["id"]) for item in lote)
            if antes == str(primeiro):
                break
            antes = str(primeiro)
            visto = lote[0]["id"]
        return todas

    def _mensagem_reduzida(self, item: object) -> dict:
        if not isinstance(item, Mapping) or not isinstance(item.get("id"), int):
            raise RecusaChatwootIsolado("leitura_falhou")
        privado = item.get("private", False) is not False
        anexos = []
        for anexo in (() if privado else item.get("attachments") or ()):
            if not isinstance(anexo, Mapping) or not isinstance(anexo.get("id"), int):
                raise RecusaChatwootIsolado("midia_indisponivel")
            anexos.append({
                "id": anexo["id"],
                "file_type": anexo.get("file_type"),
                "data_url": anexo.get("data_url"),
            })
        return {
            "id": str(item["id"]),
            "inbox_id": item.get("inbox_id"),
            "message_type": item.get("message_type"),
            "private": privado,
            "content": None if privado else item.get("content"),
            "anexos": anexos,
        }

    def _baixar_imagem(self, referencia: object) -> bytes:
        if not isinstance(referencia, str) or referencia == "":
            raise RecusaChatwootIsolado("midia_indisponivel")
        try:
            caminho = self.validador.caminho(referencia, anexo=True)
        except RecusaChatwootIsolado:
            raise RecusaChatwootIsolado("origem_recusada") from None
        for _ in range(_MAX_SALTOS):
            resposta = self._pedir("GET", caminho, autenticar=False)
            if resposta is None or not resposta.enviada:
                raise RecusaChatwootIsolado("midia_indisponivel")
            if resposta.status in _REDIRECIONA:
                if not resposta.redirecionamento:
                    raise RecusaChatwootIsolado("origem_recusada")
                try:
                    caminho = self.validador.caminho(resposta.redirecionamento, anexo=True)
                except RecusaChatwootIsolado:
                    raise RecusaChatwootIsolado("origem_recusada") from None
                continue
            if resposta.status != 200 or not resposta.corpo.startswith(_PNG) or len(resposta.corpo) > _MAX_IMAGEM:
                raise RecusaChatwootIsolado("midia_indisponivel")
            return resposta.corpo
        raise RecusaChatwootIsolado("origem_recusada")

    def _pedir(
        self,
        metodo: str,
        caminho: str,
        *,
        corpo: bytes | None = None,
        tipo: str | None = None,
        autenticar: bool,
    ) -> RespostaTransporte | None:
        try:
            seguro = self.validador.caminho(caminho)
        except RecusaChatwootIsolado:
            return RespostaTransporte(0, b"", False, None)
        try:
            return self._transporte.chamar(
                metodo,
                seguro,
                corpo=corpo,
                tipo=tipo,
                autenticar=autenticar,
            )
        except Exception:
            return None

    def _png(self, imagem: bytes) -> bytes | None:
        if not isinstance(imagem, (bytes, bytearray)):
            return None
        conteudo = bytes(imagem)
        if not conteudo.startswith(_PNG) or not 8 < len(conteudo) <= _MAX_IMAGEM:
            return None
        return conteudo

    def _json_objeto(self, resposta: RespostaTransporte | None) -> dict | None:
        if resposta is None or not resposta.corpo:
            return None
        try:
            dados = json.loads(resposta.corpo.decode("utf-8"))
        except (UnicodeError, ValueError):
            return None
        if not isinstance(dados, dict):
            return None
        return dados

    def _classificar_leitura(self, resposta: RespostaTransporte | None, codigo: str) -> dict:
        if resposta is None:
            return self._falha("leitura_incerta", incerto=True)
        if not resposta.enviada:
            return self._falha("transporte_indisponivel", incerto=False, status=resposta.status)
        if resposta.status in _FALHA_CONHECIDA:
            return self._falha(codigo, incerto=False, status=resposta.status)
        return self._falha("leitura_incerta", incerto=True, status=resposta.status)

    def _falha(self, codigo: str, *, incerto: bool, **campos: object) -> dict:
        _linha("recusa", codigo=codigo, incerto=incerto, **campos)
        return _resultado(False, codigo, incerto=incerto, **{k: v for k, v in campos.items() if k == "status"})
