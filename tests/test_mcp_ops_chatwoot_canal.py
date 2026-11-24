"""Testes unitários e de integração local do BackendChatwootCanal."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import pytest

from tuttibom.mcp_ops.atendimento import (
    AdaptadorAtendimento,
    AuditoriaLaboratorio,
    EnvioNaoEfetuado,
    VerificadorAprovacaoServidor,
)
from tuttibom.mcp_ops.chatwoot_canal import (
    BackendChatwootCanal,
    EnvioIncertoCanal,
    LeituraCanal,
    detectar_mime_imagem,
)
from tuttibom.mcp_ops.entregas_duraveis import DiarioEntregas
from tuttibom.mcp_ops.fila_persistente import FilaPersistente

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)
JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
WEBP = b"RIFF\x1a\x00\x00\x00WEBPVP8 \x0e\x00\x00\x00\x30\x01\x00\x9d\x01\x2a\x01\x00\x01\x00\x00\x00\x00\x00"
OGG = b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04OpusHead"


@dataclass
class _RespFake:
    status: int
    corpo: bytes
    headers: dict[str, str]

    def read(self) -> bytes:
        return self.corpo

    def getheader(self, nome: str) -> str | None:
        return self.headers.get(nome)


class _ConnFake:
    def __init__(self, roteador, chamadas: list[dict], *, falhar_connect=False, falhar_request=False):
        self._roteador = roteador
        self._chamadas = chamadas
        self._falhar_connect = falhar_connect
        self._falhar_request = falhar_request
        self._resp: _RespFake | None = None

    def connect(self) -> None:
        if self._falhar_connect:
            raise ConnectionRefusedError("sem_conexao")

    def request(self, metodo: str, caminho: str, body: bytes | None = None, headers: dict | None = None) -> None:
        self._chamadas.append({
            "metodo": metodo,
            "caminho": caminho,
            "corpo": body,
            "headers": dict(headers or {}),
        })
        if self._falhar_request:
            raise TimeoutError("timeout_apos_escrita")
        self._resp = self._roteador(metodo, caminho, body, headers or {})

    def getresponse(self) -> _RespFake:
        assert self._resp is not None
        return self._resp

    def close(self) -> None:
        pass


def _pat(tmp_path: Path, conteudo: str = "segredo_pat_isolado\n", modo: int = 0o600) -> Path:
    arq = tmp_path / "pat.txt"
    arq.write_text(conteudo, encoding="utf-8")
    os.chmod(arq, modo)
    return arq


def test_detectar_mime_imagem_formatos():
    assert detectar_mime_imagem(PNG) == ("image/png", "png")
    assert detectar_mime_imagem(JPEG) == ("image/jpeg", "jpg")
    assert detectar_mime_imagem(WEBP) == ("image/webp", "webp")
    assert detectar_mime_imagem(b"nao-e-imagem") is None
    assert detectar_mime_imagem(b"") is None


def test_pat_exige_arquivo_regular_0600_absoluto(tmp_path: Path):
    aberto = _pat(tmp_path, modo=0o644)
    with pytest.raises(ValueError, match="credencial_canal_invalida"):
        BackendChatwootCanal(conta_id="2", inbox_id="1", pat_arquivo=aberto)
    with pytest.raises(ValueError, match="credencial_canal_invalida"):
        BackendChatwootCanal(conta_id="2", inbox_id="1", pat_arquivo=Path("relativo.txt"))
    com_espaco = _pat(tmp_path, conteudo="token invalido\n", modo=0o600)
    with pytest.raises(ValueError, match="credencial_canal_invalida"):
        BackendChatwootCanal(conta_id="2", inbox_id="1", pat_arquivo=com_espaco)


def test_conversa_ignorada_recusa_sem_chamada_http(tmp_path: Path):
    pat = _pat(tmp_path)
    chamadas: list[dict] = []
    backend = BackendChatwootCanal(
        conta_id="2", inbox_id="1", pat_arquivo=pat,
        conversas_ignoradas=frozenset({"8"}),
        abertura_http=lambda: _ConnFake(lambda *_: _RespFake(200, b"{}", {}), chamadas),
    )
    with pytest.raises(LeituraCanal) as exc_l:
        backend.ler_mensagens("8")
    assert exc_l.value.codigo == "conversa_ignorada"
    with pytest.raises(EnvioNaoEfetuado, match="conversa_ignorada"):
        backend.enviar(conversa_ref="8", texto="Oi", imagem=None, idempotency_key="k1")
    assert chamadas == []


def test_grupo_whatsapp_e_contato_ignorado_recusados(tmp_path: Path):
    pat = _pat(tmp_path)
    ign = tmp_path / "ignorados.json"
    ign.write_text(json.dumps({
        "por_identifier": {"ml-uuid": "Mercado Livre"},
        "por_telefone": {"+5511999990013": "Empresa X"},
        "por_nome": ["Canal Oficial"],
    }))

    def roteador(_m, caminho, _b, _h):
        if caminho.endswith("/conversations/10"):
            return _RespFake(200, json.dumps({
                "id": 10, "account_id": 2, "inbox_id": 1,
                "meta": {"sender": {"identifier": "1203630@g.us"}},
            }).encode(), {})
        if caminho.endswith("/conversations/11"):
            return _RespFake(200, json.dumps({
                "id": 11, "account_id": 2, "inbox_id": 1,
                "meta": {"sender": {"phone_number": "5511999990013"}},
            }).encode(), {})
        return _RespFake(404, b"{}", {})

    backend = BackendChatwootCanal(
        conta_id="2", inbox_id="1", pat_arquivo=pat, ignorados_arquivo=ign,
        abertura_http=lambda: _ConnFake(roteador, []),
    )
    with pytest.raises(LeituraCanal) as g:
        backend.ler_mensagens("10")
    assert g.value.codigo == "grupo_nao_suportado"

    with pytest.raises(LeituraCanal) as c:
        backend.ler_mensagens("11")
    assert c.value.codigo == "contato_ignorado"
    with pytest.raises(EnvioNaoEfetuado, match="contato_ignorado"):
        backend.enviar(conversa_ref="11", texto="Oi", imagem=None, idempotency_key="k")


def test_leitura_multimidia_jpeg_webp_audio_e_anexo_nao_suportado(tmp_path: Path):
    pat = _pat(tmp_path)
    chamadas: list[dict] = []

    def roteador(metodo, caminho, _b, headers):
        if caminho.startswith("/api/"):
            assert headers.get("api_access_token") == "segredo_pat_isolado"
        if caminho == "/api/v1/accounts/2/conversations/25":
            return _RespFake(200, json.dumps({
                "id": 25, "account_id": 2, "inbox_id": 1,
                "meta": {"sender": {"identifier": "cliente-ok"}},
            }).encode(), {})
        if caminho == "/api/v1/accounts/2/conversations/25/messages":
            return _RespFake(200, json.dumps({
                "payload": [
                    {
                        "id": 100, "inbox_id": 1, "message_type": 0, "private": False,
                        "content": "Foto e audio",
                        "attachments": [
                            {
                                "id": 1, "file_type": "image",
                                "data_url": "https://chatwoot.petemcasa.com/rails/active_storage/blobs/redirect/b1/f.jpg",
                            },
                            {
                                "id": 2, "file_type": "audio",
                                "data_url": "https://chatwoot.petemcasa.com/rails/active_storage/blobs/redirect/b2/a.ogg",
                            },
                            {
                                "id": 3, "file_type": "location",
                                "data_url": None,
                            },
                        ],
                    },
                    {
                        "id": 101, "inbox_id": 1, "message_type": 1, "private": True,
                        "content": "Nota interna secreta",
                        "attachments": [],
                    },
                ],
            }).encode(), {})
        if caminho == "/rails/active_storage/blobs/redirect/b1/f.jpg":
            return _RespFake(302, b"", {"Location": "http://127.0.0.1:3001/rails/active_storage/disk/d1/f.jpg"})
        if caminho == "/rails/active_storage/disk/d1/f.jpg":
            return _RespFake(200, JPEG, {})
        if caminho == "/rails/active_storage/blobs/redirect/b2/a.ogg":
            return _RespFake(200, OGG, {})
        return _RespFake(404, b"{}", {})

    backend = BackendChatwootCanal(
        conta_id="2", inbox_id="1", pat_arquivo=pat,
        abertura_http=lambda: _ConnFake(roteador, chamadas),
    )
    msgs = backend.ler_mensagens("25")
    assert msgs is not None and len(msgs) == 1
    assert "Nota interna" not in json.dumps(msgs)
    assert msgs[0]["texto"] == "Foto e audio\n[anexo nao suportado: location]"
    assert msgs[0]["anexos"] == [
        {"file_type": "image", "midia_ref": "anexo-1"},
        {"file_type": "audio", "midia_ref": "anexo-2"},
    ]
    assert backend.obter_imagem("anexo-1") == JPEG
    assert backend.obter_audio("anexo-2") == OGG
    assert isinstance(backend.geracao("25"), int)


def test_envio_webp_e_classificacao_falha_vs_incerto(tmp_path: Path):
    pat = _pat(tmp_path)
    chamadas: list[dict] = []
    status_post = {"code": 200, "body": json.dumps({"id": 555, "inbox_id": 1}).encode()}

    def roteador(metodo, caminho, _b, _h):
        if metodo == "GET":
            return _RespFake(200, json.dumps({"id": 30, "account_id": 2, "inbox_id": 1}).encode(), {})
        return _RespFake(status_post["code"], status_post["body"], {})

    backend = BackendChatwootCanal(
        conta_id="2", inbox_id="1", pat_arquivo=pat,
        abertura_http=lambda: _ConnFake(roteador, chamadas),
    )
    ok = backend.enviar(conversa_ref="30", texto="Segue prévia", imagem=WEBP, idempotency_key="k1")
    assert ok == {"ok": True, "envio_ref": "msg-555"}
    assert b"Content-Type: image/webp" in chamadas[-1]["corpo"]
    assert b'filename="resposta.webp"' in chamadas[-1]["corpo"]

    status_post["code"] = 422
    with pytest.raises(EnvioNaoEfetuado, match="envio_falhou"):
        backend.enviar(conversa_ref="30", texto="Segue", imagem=None, idempotency_key="k2")

    status_post["code"] = 502
    with pytest.raises(EnvioIncertoCanal, match="envio_incerto"):
        backend.enviar(conversa_ref="30", texto="Segue", imagem=None, idempotency_key="k3")


def test_integracao_adaptador_atendimento_com_audio_e_diario(tmp_path: Path):
    pat = _pat(tmp_path)

    def roteador(metodo, caminho, _b, _h):
        if caminho == "/api/v1/accounts/2/conversations/50":
            return _RespFake(200, json.dumps({"id": 50, "account_id": 2, "inbox_id": 1}).encode(), {})
        if caminho.startswith("/api/v1/accounts/2/conversations/50/messages") and metodo == "GET":
            return _RespFake(200, json.dumps({
                "payload": [{
                    "id": 700, "inbox_id": 1, "message_type": 0, "private": False, "content": None,
                    "attachments": [{"id": 9, "file_type": "audio",
                                     "data_url": "/rails/active_storage/disk/k/voz.ogg"}],
                }],
            }).encode(), {})
        if caminho == "/rails/active_storage/disk/k/voz.ogg":
            return _RespFake(200, OGG, {})
        if metodo == "POST":
            return _RespFake(200, json.dumps({"id": 701, "inbox_id": 1}).encode(), {})
        return _RespFake(404, b"{}", {})

    class _TranscritorFake:
        def transcrever(self, audio: bytes, *, idioma: str = "pt") -> str:
            assert audio == OGG and idioma == "pt"
            return "Preciso de orçamento de fita de cetim."

    fila = FilaPersistente(tmp_path / "fila.sqlite", inbox_ref="canal-2-1")
    fila.registrar(message_id="700", conversation_id="50")
    diario = DiarioEntregas(tmp_path / "entregas.sqlite")
    backend = BackendChatwootCanal(
        conta_id="2", inbox_id="1", pat_arquivo=pat,
        abertura_http=lambda: _ConnFake(roteador, []),
    )
    verificador = VerificadorAprovacaoServidor()
    adaptador = AdaptadorAtendimento(
        fila=fila, chatwoot=backend, simulador=backend,
        transcritor=_TranscritorFake(), verificador=verificador,
        auditoria=AuditoriaLaboratorio(), diario=diario,
    )
    lido = adaptador.ler_conversa("50")
    assert lido["ok"] is True
    assert lido["mensagens"][0]["anexos"][0]["transcricao"] == "Preciso de orçamento de fita de cetim."
    prep = adaptador.preparar_resposta(
        conversa_ref="50", texto="Claro! Qual largura e quantidade?",
        idempotency_key="aud-1", message_ids=["700"],
    )
    aprov = verificador.registrar(texto="Claro! Qual largura e quantidade?")
    resp = adaptador.responder(rascunho_ref=prep["rascunho_ref"], aprovacao_ref=aprov)
    assert resp["ok"] is True and resp["acked"] == ["700"]
