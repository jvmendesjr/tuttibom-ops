"""Backend de operação do Chatwoot 4.20.1 CE sobre loopback local."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib
import http.client
import json
import logging
import os
from pathlib import Path
import re
import secrets
import stat
from urllib.parse import urlsplit

from tuttibom.contratos.pii import detectar_pii

from .atendimento import EnvioNaoEfetuado
from .erros import ErroOps

_ID_CONTA = re.compile(r"^[1-9][0-9]{0,8}$")
_ID_MSG = re.compile(r"^[1-9][0-9]{0,17}$")
_REF_MIDIA = re.compile(r"^anexo-[1-9][0-9]{0,17}$")
_TIPO_LIMPO = re.compile(r"^[a-z0-9_]{1,24}$")
_CAMINHO_SEGURO = re.compile(r"^/[A-Za-z0-9._~%/=-]+$")
_QUERY_SEGURA = re.compile(r"^[A-Za-z0-9._~%=&+-]+$")
_FALHA_CONHECIDA = frozenset({400, 401, 403, 404, 406, 415, 422})
_INCERTO_HTTP = frozenset({0, 408, 409, 425, 429, 500, 502, 503, 504})
_REDIRECIONA = frozenset({301, 302, 303, 307, 308})
_TIPOS_MENSAGEM = {0: "incoming", 1: "outgoing", "incoming": "incoming", "outgoing": "outgoing"}
_MAX_TEXTO = 4_000
_MAX_PAGINAS = 5
_PAGINA = 20
_MAX_SALTOS = 4

log = logging.getLogger("tuttibom.mcp_ops.chatwoot_canal")


def detectar_mime_imagem(conteudo: bytes) -> tuple[str, str] | None:
    if not isinstance(conteudo, (bytes, bytearray)):
        return None
    bruto = bytes(conteudo)
    if bruto.startswith(b"\x89PNG\r\n\x1a\n") and len(bruto) > 8:
        return ("image/png", "png")
    if bruto.startswith(b"\xff\xd8\xff") and len(bruto) > 4:
        return ("image/jpeg", "jpg")
    if len(bruto) > 12 and bruto[:4] == b"RIFF" and bruto[8:12] == b"WEBP":
        return ("image/webp", "webp")
    return None


class LeituraCanal(ErroOps):
    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__()


class EnvioIncertoCanal(Exception):
    def __init__(self, codigo: str = "envio_incerto") -> None:
        self.codigo = codigo if isinstance(codigo, str) and codigo else "envio_incerto"
        super().__init__(self.codigo)


@dataclass(frozen=True)
class _RespostaHttp:
    status: int
    corpo: bytes
    enviada: bool
    redirecionamento: str | None = None


def _log_seguro(evento: str, **campos: object) -> None:
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
        linha = "chatwoot_canal evento=suprimido"
    log.info("%s", linha)


def _ler_pat_privado(arquivo: Path) -> str:
    if not isinstance(arquivo, Path) or not arquivo.is_absolute():
        raise ValueError("credencial_canal_invalida")
    try:
        fd = os.open(arquivo, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise ValueError("credencial_canal_invalida") from exc
    with os.fdopen(fd, "r", encoding="utf-8") as fh:
        info = os.fstat(fh.fileno())
        if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.getuid()):
            raise ValueError("credencial_canal_invalida")
        bruto = fh.read(513)
    token = bruto.rstrip("\r\n")
    if (not token or len(token) > 512
            or any(c.isspace() or ord(c) < 32 for c in token)):
        raise ValueError("credencial_canal_invalida")
    return token


def _caminho_active_storage(referencia: object) -> str:
    if not isinstance(referencia, str) or not referencia.strip():
        raise LeituraCanal("midia_indisponivel")
    texto = referencia.strip()
    partes = urlsplit(texto)
    if partes.scheme:
        if partes.scheme not in {"http", "https"} or partes.username or partes.password or not partes.hostname:
            raise LeituraCanal("origem_recusada")
    elif partes.netloc:
        raise LeituraCanal("origem_recusada")
    if partes.fragment:
        raise LeituraCanal("origem_recusada")
    caminho = partes.path
    if (not caminho.startswith("/rails/active_storage/")
            or "//" in caminho
            or ".." in caminho.split("/")
            or "@" in caminho
            or _CAMINHO_SEGURO.fullmatch(caminho) is None):
        raise LeituraCanal("origem_recusada")
    if partes.query:
        if _QUERY_SEGURA.fullmatch(partes.query) is None:
            raise LeituraCanal("origem_recusada")
        return f"{caminho}?{partes.query}"
    return caminho


def _multipart_imagem(
    campos: list[tuple[str, str]],
    *,
    nome_arquivo: str,
    mime: str,
    conteudo: bytes,
) -> tuple[bytes, str]:
    limite = "tb" + secrets.token_hex(8)
    while limite.encode("ascii") in conteudo:
        limite = "tb" + secrets.token_hex(8)
    pedacos: list[bytes] = []
    for nome, valor in campos:
        pedacos.append(
            f'--{limite}\r\nContent-Disposition: form-data; name="{nome}"\r\n\r\n{valor}\r\n'.encode("utf-8")
        )
    pedacos.append(
        (
            f'--{limite}\r\nContent-Disposition: form-data; '
            f'name="attachments[]"; filename="{nome_arquivo}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode("utf-8")
        + conteudo
        + b"\r\n"
    )
    pedacos.append(f"--{limite}--\r\n".encode("ascii"))
    return b"".join(pedacos), f"multipart/form-data; boundary={limite}"


def _versao_63(itens: tuple[str, ...]) -> int:
    digest = hashlib.sha256("\n".join(itens).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def _digitos(valor: object) -> str:
    return re.sub(r"\D", "", str(valor or ""))


class BackendChatwootCanal:
    """Leitura multimídia (PNG/JPEG/WebP + áudio) e envio aprovado no Chatwoot real."""

    def __init__(
        self,
        *,
        conta_id: str,
        inbox_id: str,
        pat_arquivo: Path,
        porta_loopback: int = 3001,
        ignorados_arquivo: Path | None = None,
        conversas_ignoradas: frozenset[str] = frozenset(),
        max_imagem_bytes: int = 5 * 1024 * 1024,
        max_audio_bytes: int = 8 * 1024 * 1024,
        abertura_http: Callable[[], http.client.HTTPConnection] | None = None,
    ) -> None:
        if not isinstance(conta_id, str) or _ID_CONTA.fullmatch(conta_id) is None:
            raise ValueError("conta_id_invalida")
        if not isinstance(inbox_id, str) or _ID_CONTA.fullmatch(inbox_id) is None:
            raise ValueError("inbox_id_invalido")
        if type(porta_loopback) is not int or not 1 <= porta_loopback <= 65535:
            raise ValueError("porta_invalida")
        if type(max_imagem_bytes) is not int or max_imagem_bytes <= 16:
            raise ValueError("limite_midia_invalido")
        if type(max_audio_bytes) is not int or max_audio_bytes <= 16:
            raise ValueError("limite_midia_invalido")
        if ignorados_arquivo is not None and (
            not isinstance(ignorados_arquivo, Path) or not ignorados_arquivo.is_absolute()
        ):
            raise ValueError("ignorados_arquivo_invalido")
        _ler_pat_privado(pat_arquivo)
        self.conta_id = conta_id
        self.inbox_id = inbox_id
        self._pat_arquivo = pat_arquivo
        self._porta = porta_loopback
        self._ignorados_arquivo = ignorados_arquivo
        self._conversas_ignoradas = frozenset(str(x) for x in conversas_ignoradas)
        self._max_imagem = max_imagem_bytes
        self._max_audio = max_audio_bytes
        self._abrir = abertura_http or self._abrir_padrao
        self._imagens: dict[str, bytes] = {}
        self._audios: dict[str, bytes] = {}
        self._ultima_conversa: str | None = None

    def __repr__(self) -> str:
        return f"BackendChatwootCanal(conta={self.conta_id!r}, inbox={self.inbox_id!r})"

    def _abrir_padrao(self) -> http.client.HTTPConnection:
        return http.client.HTTPConnection("127.0.0.1", self._porta, timeout=15)

    def _chamar(
        self,
        metodo: str,
        caminho: str,
        *,
        corpo: bytes | None = None,
        tipo: str | None = None,
        autenticar: bool = False,
    ) -> _RespostaHttp:
        cabecalhos = {"Accept": "application/json, image/*, audio/*, */*"}
        if tipo:
            cabecalhos["Content-Type"] = tipo
        if autenticar:
            try:
                cabecalhos["api_access_token"] = _ler_pat_privado(self._pat_arquivo)
            except ValueError:
                return _RespostaHttp(0, b"", False, None)
        try:
            conexao = self._abrir()
        except Exception:
            return _RespostaHttp(0, b"", False, None)
        enviada = False
        try:
            conexao.connect()
            enviada = True
            conexao.request(metodo, caminho, body=corpo, headers=cabecalhos)
            resposta = conexao.getresponse()
            bruto = resposta.read()
            local = resposta.getheader("Location")
            return _RespostaHttp(int(resposta.status), bruto, True, local)
        except Exception:
            return _RespostaHttp(0, b"", enviada, None)
        finally:
            try:
                conexao.close()
            except Exception:
                pass

    def ler_mensagens(self, conversa_ref: str) -> list[dict] | None:
        if not isinstance(conversa_ref, str) or _ID_CONTA.fullmatch(conversa_ref) is None:
            return None
        if conversa_ref in self._conversas_ignoradas:
            raise LeituraCanal("conversa_ignorada")
        snap = self._snapshot(conversa_ref)
        if snap is None:
            return None
        self._ultima_conversa = conversa_ref
        _log_seguro("ler_mensagens", conversa_ref=conversa_ref, n_mensagens=len(snap[0]))
        return snap[0]

    def geracao(self, conversa_ref: str) -> int:
        if not isinstance(conversa_ref, str) or _ID_CONTA.fullmatch(conversa_ref) is None:
            raise LeituraCanal("conversa_invalida")
        if conversa_ref in self._conversas_ignoradas:
            raise LeituraCanal("conversa_ignorada")
        snap = self._snapshot(conversa_ref)
        if snap is None:
            raise LeituraCanal("conversa_desconhecida")
        return _versao_63(snap[1])

    def obter_imagem(self, midia_ref: str) -> bytes:
        if not isinstance(midia_ref, str) or _REF_MIDIA.fullmatch(midia_ref) is None:
            raise KeyError("midia_invalida")
        if midia_ref not in self._imagens and self._ultima_conversa is not None:
            self.ler_mensagens(self._ultima_conversa)
        conteudo = self._imagens.get(midia_ref)
        if conteudo is None or detectar_mime_imagem(conteudo) is None:
            raise KeyError(midia_ref)
        return bytes(conteudo)

    def obter_audio(self, midia_ref: str) -> bytes:
        if not isinstance(midia_ref, str) or _REF_MIDIA.fullmatch(midia_ref) is None:
            raise KeyError("midia_invalida")
        if midia_ref not in self._audios and self._ultima_conversa is not None:
            self.ler_mensagens(self._ultima_conversa)
        conteudo = self._audios.get(midia_ref)
        if not conteudo:
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
        del idempotency_key
        if not isinstance(conversa_ref, str) or _ID_CONTA.fullmatch(conversa_ref) is None:
            raise EnvioNaoEfetuado("conversa_invalida")
        if conversa_ref in self._conversas_ignoradas:
            raise EnvioNaoEfetuado("conversa_ignorada")
        if not isinstance(texto, str) or not texto.strip() or len(texto) > _MAX_TEXTO:
            raise EnvioNaoEfetuado("argumento_invalido")
        meta_imagem: tuple[str, str] | None = None
        bruto_imagem: bytes | None = None
        if imagem is not None:
            if not isinstance(imagem, (bytes, bytearray)):
                raise EnvioNaoEfetuado("argumento_invalido")
            bruto_imagem = bytes(imagem)
            if len(bruto_imagem) > self._max_imagem:
                raise EnvioNaoEfetuado("argumento_invalido")
            meta_imagem = detectar_mime_imagem(bruto_imagem)
            if meta_imagem is None:
                raise EnvioNaoEfetuado("argumento_invalido")
        try:
            status_conv = self._validar_conversa(conversa_ref)
        except LeituraCanal as exc:
            raise EnvioNaoEfetuado(exc.codigo) from None
        if status_conv == "nao_encontrada":
            raise EnvioNaoEfetuado("conversa_desconhecida")

        caminho = f"/api/v1/accounts/{self.conta_id}/conversations/{conversa_ref}/messages"
        if bruto_imagem is None:
            corpo = json.dumps({"content": texto, "message_type": "outgoing"}).encode("utf-8")
            tipo = "application/json"
        else:
            assert meta_imagem is not None
            mime, ext = meta_imagem
            corpo, tipo = _multipart_imagem(
                [("message_type", "outgoing"), ("content", texto)],
                nome_arquivo=f"resposta.{ext}",
                mime=mime,
                conteudo=bruto_imagem,
            )
        resposta = self._chamar("POST", caminho, corpo=corpo, tipo=tipo, autenticar=True)
        if not resposta.enviada:
            raise EnvioNaoEfetuado("transporte_indisponivel")
        if resposta.status in _FALHA_CONHECIDA:
            raise EnvioNaoEfetuado("envio_falhou")
        if resposta.status in _INCERTO_HTTP or resposta.status not in {200, 201}:
            raise EnvioIncertoCanal("envio_incerto")
        dados = self._json_dict(resposta.corpo)
        if dados is None or type(dados.get("id")) is not int or dados["id"] <= 0:
            raise EnvioIncertoCanal("envio_incerto")
        if "inbox_id" in dados and str(dados.get("inbox_id")) != self.inbox_id:
            raise EnvioIncertoCanal("inbox_divergente")
        _log_seguro("enviar", conversa_ref=conversa_ref, status=resposta.status, bytes=len(corpo))
        return {"ok": True, "envio_ref": f"msg-{dados['id']}"}

    def _snapshot(self, conversa_ref: str) -> tuple[list[dict], tuple[str, ...]] | None:
        status_conv = self._validar_conversa(conversa_ref)
        if status_conv == "nao_encontrada":
            return None
        brutas = self._paginar_mensagens(conversa_ref)
        mensagens: list[dict] = []
        tokens_versao: list[str] = []
        imagens = dict(self._imagens)
        audios = dict(self._audios)
        for item in brutas:
            if item.get("inbox_id") is not None and str(item.get("inbox_id")) != self.inbox_id:
                raise LeituraCanal("inbox_divergente")
            if item.get("private") is not False:
                continue
            direcao = _TIPOS_MENSAGEM.get(item.get("message_type"))
            if direcao is None:
                continue
            msg_id_raw = item.get("id")
            if type(msg_id_raw) is not int or msg_id_raw <= 0:
                raise LeituraCanal("leitura_falhou")
            msg_id = str(msg_id_raw)
            texto = item.get("content")
            if texto is None:
                texto = ""
            if not isinstance(texto, str):
                raise LeituraCanal("leitura_falhou")
            anexos_saida: list[dict] = []
            marcadores_extras: list[str] = []
            partes_anexo_versao: list[str] = []
            for anexo in item.get("attachments") or ():
                if not isinstance(anexo, Mapping) or type(anexo.get("id")) is not int or anexo["id"] <= 0:
                    raise LeituraCanal("midia_indisponivel")
                att_id = anexo["id"]
                ref = f"anexo-{att_id}"
                tipo = str(anexo.get("file_type") or "").strip().lower()
                if tipo == "image":
                    conteudo = self._baixar_anexo(anexo.get("data_url"), self._max_imagem)
                    if detectar_mime_imagem(conteudo) is None:
                        raise LeituraCanal("midia_indisponivel")
                    imagens[ref] = conteudo
                    anexos_saida.append({"file_type": "image", "midia_ref": ref})
                    partes_anexo_versao.append(f"img:{att_id}:{len(conteudo)}")
                elif tipo == "audio":
                    conteudo = self._baixar_anexo(anexo.get("data_url"), self._max_audio)
                    audios[ref] = conteudo
                    anexos_saida.append({"file_type": "audio", "midia_ref": ref})
                    partes_anexo_versao.append(f"aud:{att_id}:{len(conteudo)}")
                else:
                    rotulo = tipo if _TIPO_LIMPO.fullmatch(tipo) else "outro"
                    marcadores_extras.append(f"[anexo nao suportado: {rotulo}]")
                    partes_anexo_versao.append(f"extra:{att_id}:{rotulo}")
            if marcadores_extras:
                sufixo = "\n".join(marcadores_extras)
                texto = f"{texto}\n{sufixo}" if texto else sufixo
            mensagens.append({"direcao": direcao, "texto": texto, "anexos": anexos_saida})
            tokens_versao.append(f"{msg_id}:{direcao}:{','.join(partes_anexo_versao)}")
        self._imagens = imagens
        self._audios = audios
        return mensagens, tuple(tokens_versao)

    def _validar_conversa(self, conversa_ref: str) -> str:
        resposta = self._chamar(
            "GET",
            f"/api/v1/accounts/{self.conta_id}/conversations/{conversa_ref}",
            autenticar=True,
        )
        if not resposta.enviada:
            raise LeituraCanal("transporte_indisponivel")
        if resposta.status == 404:
            return "nao_encontrada"
        if resposta.status in _INCERTO_HTTP:
            raise LeituraCanal("leitura_incerta")
        if resposta.status != 200:
            raise LeituraCanal("leitura_falhou")
        bruto = self._json_dict(resposta.corpo)
        if bruto is None:
            raise LeituraCanal("leitura_falhou")
        dados = bruto.get("data") if isinstance(bruto.get("data"), Mapping) and "id" in bruto.get("data") else bruto
        if not isinstance(dados, Mapping):
            raise LeituraCanal("leitura_falhou")
        if (str(dados.get("id")) != conversa_ref
                or str(dados.get("account_id")) != self.conta_id
                or str(dados.get("inbox_id")) != self.inbox_id):
            raise LeituraCanal("inbox_divergente")
        self._validar_contato(dados)
        return "ok"

    def _validar_contato(self, dados: Mapping) -> None:
        meta = dados.get("meta") if isinstance(dados.get("meta"), Mapping) else {}
        sender = meta.get("sender") if isinstance(meta.get("sender"), Mapping) else {}
        contato = dados.get("contact") if isinstance(dados.get("contact"), Mapping) else {}
        identifier = str(sender.get("identifier") or contato.get("identifier") or "").strip()
        telefone = str(
            sender.get("phone_number") or sender.get("phone")
            or contato.get("phone_number") or contato.get("phone") or ""
        ).strip()
        nome = str(sender.get("name") or contato.get("name") or "").strip()
        for candidato in (identifier, telefone):
            if candidato.lower().endswith("@g.us"):
                raise LeituraCanal("grupo_nao_suportado")
        if self._ignorados_arquivo is None:
            return
        try:
            regras = json.loads(self._ignorados_arquivo.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, ValueError) as exc:
            raise LeituraCanal("config_ignorados_invalida") from exc
        if not isinstance(regras, Mapping):
            raise LeituraCanal("config_ignorados_invalida")
        por_id = regras.get("por_identifier") or {}
        if identifier and isinstance(por_id, Mapping) and identifier in por_id:
            raise LeituraCanal("contato_ignorado")
        por_tel = regras.get("por_telefone") or {}
        if telefone and isinstance(por_tel, Mapping):
            dig = _digitos(telefone)
            for ref_num in por_tel:
                ref_dig = _digitos(ref_num)
                if dig and ref_dig and (dig.endswith(ref_dig) or ref_dig.endswith(dig)):
                    raise LeituraCanal("contato_ignorado")
        por_nome = regras.get("por_nome") or []
        if nome and isinstance(por_nome, list):
            alvo = nome.lower()
            if any(isinstance(n, str) and n.strip().lower() == alvo for n in por_nome):
                raise LeituraCanal("contato_ignorado")

    def _paginar_mensagens(self, conversa_ref: str) -> list[Mapping]:
        todas: list[Mapping] = []
        antes = ""
        visto: int | None = None
        for _ in range(_MAX_PAGINAS):
            caminho = f"/api/v1/accounts/{self.conta_id}/conversations/{conversa_ref}/messages"
            if antes:
                caminho = f"{caminho}?before={antes}"
            resposta = self._chamar("GET", caminho, autenticar=True)
            if not resposta.enviada:
                raise LeituraCanal("transporte_indisponivel")
            if resposta.status in _INCERTO_HTTP:
                raise LeituraCanal("leitura_incerta")
            if resposta.status != 200:
                raise LeituraCanal("leitura_falhou")
            dados = self._json_dict(resposta.corpo)
            payload = dados.get("payload") if isinstance(dados, Mapping) else None
            if not isinstance(payload, list):
                raise LeituraCanal("leitura_falhou")
            lote: list[Mapping] = []
            for item in payload:
                if not isinstance(item, Mapping) or type(item.get("id")) is not int:
                    raise LeituraCanal("leitura_falhou")
                lote.append(item)
            lote.sort(key=lambda m: m["id"])
            if lote and lote[0]["id"] == visto:
                break
            todas = lote + todas if antes else lote
            if len(lote) < _PAGINA:
                break
            primeiro = lote[0]["id"]
            if antes == str(primeiro):
                break
            antes = str(primeiro)
            visto = primeiro
        return todas

    def _baixar_anexo(self, referencia: object, max_bytes: int) -> bytes:
        caminho = _caminho_active_storage(referencia)
        for _ in range(_MAX_SALTOS):
            resposta = self._chamar("GET", caminho, autenticar=False)
            if not resposta.enviada:
                raise LeituraCanal("midia_indisponivel")
            if resposta.status in _REDIRECIONA:
                if not resposta.redirecionamento:
                    raise LeituraCanal("origem_recusada")
                caminho = _caminho_active_storage(resposta.redirecionamento)
                continue
            if resposta.status != 200 or not (0 < len(resposta.corpo) <= max_bytes):
                raise LeituraCanal("midia_indisponivel")
            return resposta.corpo
        raise LeituraCanal("origem_recusada")

    @staticmethod
    def _json_dict(corpo: bytes) -> dict | None:
        if not corpo:
            return None
        try:
            dados = json.loads(corpo.decode("utf-8"))
        except (UnicodeError, ValueError):
            return None
        return dados if isinstance(dados, dict) else None


__all__ = [
    "BackendChatwootCanal",
    "EnvioIncertoCanal",
    "LeituraCanal",
    "detectar_mime_imagem",
]
