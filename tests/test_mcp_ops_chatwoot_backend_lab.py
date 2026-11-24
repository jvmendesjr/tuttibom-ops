"""Ponte do lab para LeituraConversa, MidiaEDestino e BackendsAtendimento.

Não abre porta, não lê token e não fala com o contêiner. O transporte
real continua em test_mcp_ops_chatwoot_isolado.

    python3 -m unittest tests.test_mcp_ops_chatwoot_backend_lab -v
"""

from __future__ import annotations

import ast
import base64
import logging
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tuttibom.mcp_ops.chatwoot_backend_lab import (  # noqa: E402
    CAMPOS_BACKENDS_ATENDIMENTO,
    LIMITE_AUDIO,
    ChatwootBackendLab,
    EnvioIncerto,
    EnvioNaoEfetuado,
    LeituraLab,
    LimiteAudioLab,
)

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
TEXTO = "frase-ficticia-da-ponte-lab"
NUCLEO = ROOT / "src/tuttibom/mcp_ops"


class _Isolado:
    def __init__(self) -> None:
        self.mensagens = [
            {
                "id": "7",
                "direcao": "incoming",
                "texto": "",
                "anexos": [{
                    "file_type": "image",
                    "midia_ref": "anexo-7",
                    "conteudo": PNG,
                    "data_url": "http://127.0.0.1:3000/rails/active_storage/blobs/x",
                    "bytes": len(PNG),
                    "sha256": "nao-sai",
                }],
            },
            {
                "id": "8",
                "direcao": "outgoing",
                "texto": TEXTO,
                "private": True,
                "anexos": [],
            },
        ]
        self.envio = {"ok": True, "incerto": False, "codigo": None, "message_ref": "msg-9"}
        self.leituras = 0
        self.envios = []

    def ler_historico(self, conversa_ref: str) -> dict:
        self.leituras += 1
        return {
            "ok": True,
            "incerto": False,
            "codigo": None,
            "mensagens": [dict(item) for item in self.mensagens],
        }

    def enviar(self, conversa_ref: str, *, texto=None, imagem=None):
        self.envios.append({"conversa_ref": conversa_ref, "texto": texto, "imagem": imagem})
        if isinstance(self.envio, Exception):
            raise self.envio
        return dict(self.envio)


class _Fila:
    def __init__(self) -> None:
        self.itens: dict[str, str] = {}
        self.acks: list[str] = []

    def registrar(self, *, message_id: str, conversation_id: str) -> bool:
        anterior = self.itens.get(message_id)
        if anterior is None:
            self.itens[message_id] = conversation_id
            return True
        if anterior != conversation_id:
            raise ValueError("mensagem_em_outra_conversa")
        return False

    def marcar_entregues(self, message_ids) -> list[str]:
        self.acks.extend(message_ids)
        return list(message_ids)


class TestPayloadEGeracao(unittest.TestCase):
    def setUp(self) -> None:
        self.isolado = _Isolado()
        self.backend = ChatwootBackendLab(self.isolado, conversa_ref="1")

    def test_historico_so_tem_o_payload_minimo(self) -> None:
        mensagens = self.backend.ler_mensagens("1")
        self.assertEqual(
            mensagens,
            [
                {
                    "direcao": "incoming",
                    "texto": "",
                    "anexos": [{"file_type": "image", "midia_ref": "anexo-7"}],
                },
                {"direcao": "outgoing", "texto": TEXTO, "anexos": []},
            ],
        )
        bruto = repr(mensagens)
        self.assertNotIn("data_url", bruto)
        self.assertNotIn("conteudo", bruto)
        self.assertNotIn("sha256", bruto)
        self.assertIsNone(self.backend.ler_mensagens("2"))
        self.assertEqual(self.isolado.leituras, 1)

    def test_imagem_opaca_devolve_os_bytes_e_nao_inventa_outra(self) -> None:
        self.backend.ler_mensagens("1")
        self.assertEqual(self.backend.obter_imagem("anexo-7"), PNG)
        with self.assertRaises(KeyError):
            self.backend.obter_imagem("anexo-999")

    def test_geracao_estavel_ate_mensagem_nova(self) -> None:
        primeira = self.backend.geracao("1")
        segunda = self.backend.geracao("1")
        self.assertIsInstance(primeira, int)
        self.assertEqual(primeira, segunda)
        self.isolado.mensagens.append({
            "id": "10",
            "direcao": "incoming",
            "texto": "nova",
            "anexos": [],
        })
        self.assertNotEqual(self.backend.geracao("1"), primeira)
        self.isolado.mensagens.pop()
        self.assertEqual(self.backend.geracao("1"), primeira)


class TestEnvio(unittest.TestCase):
    def setUp(self) -> None:
        self.isolado = _Isolado()
        self.backend = ChatwootBackendLab(self.isolado, conversa_ref="1")

    def test_falha_comprovada_e_envio_nao_efetuado(self) -> None:
        for codigo in ("envio_falhou", "transporte_indisponivel", "argumento_invalido"):
            with self.subTest(codigo=codigo):
                self.isolado.envio = {"ok": False, "incerto": False, "codigo": codigo}
                with self.assertRaises(EnvioNaoEfetuado) as ctx:
                    self.backend.enviar(
                        conversa_ref="1",
                        texto=TEXTO,
                        imagem=None,
                        idempotency_key="chave-que-nao-vai-ao-chatwoot",
                    )
                self.assertNotIsInstance(ctx.exception, EnvioIncerto)
                self.assertIn(codigo, repr(ctx.exception))

    def test_demais_resultados_sao_incertos_e_o_sucesso_so_devolve_a_ref(self) -> None:
        self.isolado.envio = {"ok": False, "incerto": True, "codigo": "envio_incerto"}
        with self.assertRaises(EnvioIncerto):
            self.backend.enviar(conversa_ref="1", texto=TEXTO, imagem=None, idempotency_key="k")
        self.isolado.envio = TimeoutError("depois do post")
        with self.assertRaises(EnvioIncerto) as ctx:
            self.backend.enviar(conversa_ref="1", texto=TEXTO, imagem=None, idempotency_key="k")
        self.assertNotIsInstance(ctx.exception, EnvioNaoEfetuado)
        self.isolado.envio = {"ok": True, "incerto": False, "codigo": None, "message_ref": "msg-9"}
        envio = self.backend.enviar(
            conversa_ref="1", texto="", imagem=PNG, idempotency_key="chave-local",
        )
        self.assertEqual(envio, {"ok": True, "envio_ref": "msg-9"})
        self.assertIsNone(self.isolado.envios[-1]["texto"])
        self.assertEqual(self.isolado.envios[-1]["imagem"], PNG)
        self.assertNotIn("chave-local", repr(self.isolado.envios))
        with self.assertRaises(EnvioNaoEfetuado):
            self.backend.enviar(conversa_ref="2", texto=TEXTO, imagem=None, idempotency_key="k")
        self.assertTrue(all(item["conversa_ref"] == "1" for item in self.isolado.envios))


class TestImportacao(unittest.TestCase):
    def test_so_incoming_publico_e_idempotente_sem_ack(self) -> None:
        isolado = _Isolado()
        isolado.mensagens.append({
            "id": "11",
            "direcao": "incoming",
            "texto": "nota",
            "private": True,
            "anexos": [],
        })
        isolado.mensagens.append({
            "id": "12",
            "direcao": "incoming",
            "texto": "publico",
            "anexos": [],
        })
        backend = ChatwootBackendLab(isolado, conversa_ref="1")
        fila = _Fila()
        primeiro = backend.importar_incoming_publicos(fila)
        self.assertEqual(primeiro["ids"], ("7", "12"))
        self.assertEqual(primeiro["inseridos"], 2)
        self.assertEqual(primeiro["existentes"], 0)
        segundo = backend.importar_incoming_publicos(fila)
        self.assertEqual(segundo["inseridos"], 0)
        self.assertEqual(segundo["existentes"], 2)
        self.assertEqual(set(fila.itens), {"7", "12"})
        self.assertEqual(fila.acks, [])
        self.assertNotIn(TEXTO, repr(primeiro))

    def test_id_que_nao_e_real_nao_grava(self) -> None:
        isolado = _Isolado()
        isolado.mensagens.append({
            "id": "msg-inventado",
            "direcao": "incoming",
            "texto": "",
            "anexos": [],
        })
        backend = ChatwootBackendLab(isolado, conversa_ref="1")
        fila = _Fila()
        with self.assertRaises(LeituraLab):
            backend.importar_incoming_publicos(fila)
        self.assertEqual(fila.itens, {})
        self.assertEqual(fila.acks, [])


class TestAudio(unittest.TestCase):
    def test_audio_marca_limite_e_nao_devolve_bytes(self) -> None:
        isolado = _Isolado()
        isolado.mensagens = [{
            "id": "3",
            "direcao": "incoming",
            "texto": "",
            "anexos": [{
                "file_type": "audio",
                "midia_ref": "audio-3",
                "conteudo": b"RIFF-falso-nao-e-audio-real",
            }],
        }]
        backend = ChatwootBackendLab(isolado, conversa_ref="1")
        with self.assertRaises(LimiteAudioLab) as ctx:
            backend.ler_mensagens("1")
        self.assertEqual(ctx.exception.codigo, LIMITE_AUDIO)
        with self.assertRaises(LimiteAudioLab) as direto:
            backend.obter_audio("audio-3")
        self.assertEqual(direto.exception.codigo, LIMITE_AUDIO)
        self.assertNotIsInstance(direto.exception.args[0], bytes)


class TestComposicao(unittest.TestCase):
    def test_campos_batem_com_backends_atendimento(self) -> None:
        laboratorio = (NUCLEO / "laboratorio.py").read_text(encoding="utf-8")
        atendimento = (NUCLEO / "atendimento.py").read_text(encoding="utf-8")
        arvore_lab = ast.parse(laboratorio)
        arvore_at = ast.parse(atendimento)
        campos = _campos(arvore_lab, "BackendsAtendimento")
        self.assertEqual(campos, CAMPOS_BACKENDS_ATENDIMENTO)
        leitura = set(_metodos(arvore_at, "LeituraConversa"))
        destino = set(_metodos(arvore_at, "FonteImagem")) | set(_metodos(arvore_at, "DestinoEnvio"))
        self.assertTrue({"ler_mensagens", "obter_audio", "geracao"} <= leitura)
        self.assertTrue({"obter_imagem", "enviar"} <= destino)
        backend = ChatwootBackendLab(_Isolado(), conversa_ref="1")
        fila = _Fila()
        diario = object()
        composto = backend.compor(fila=fila, diario=diario)
        self.assertEqual(tuple(composto), CAMPOS_BACKENDS_ATENDIMENTO)
        self.assertIs(composto["chat"], backend)
        self.assertIs(composto["destino"], backend)
        self.assertIs(composto["fila"], fila)
        self.assertIs(composto["diario"], diario)
        self.assertIsNone(composto["transcritor"])


class TestHigiene(unittest.TestCase):
    def test_log_e_repr_nao_levam_o_texto(self) -> None:
        isolado = _Isolado()
        backend = ChatwootBackendLab(isolado, conversa_ref="1")
        registros = []

        class _Coletor(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                registros.append(record.getMessage())

        log = logging.getLogger("tuttibom.mcp_ops.chatwoot_backend_lab")
        coletor = _Coletor()
        log.addHandler(coletor)
        log.setLevel(logging.INFO)
        try:
            backend.ler_mensagens("1")
            backend.importar_incoming_publicos(_Fila())
        finally:
            log.removeHandler(coletor)
        self.assertNotIn(TEXTO, "\n".join(registros))
        self.assertNotIn(TEXTO, repr(backend))

    def test_modulo_nao_abre_rede_nem_confirma(self) -> None:
        fonte = (ROOT / "src/tuttibom/mcp_ops/chatwoot_backend_lab.py").read_text(encoding="utf-8")
        arvore = ast.parse(fonte)
        proibidos = {"subprocess", "socket", "docker", "urllib", "http", "requests"}
        importados = set()
        chamadas = set()
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                importados.update(alias.name.split(".")[0] for alias in no.names)
            elif isinstance(no, ast.ImportFrom) and no.module:
                importados.add(no.module.split(".")[0])
            elif isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute):
                chamadas.add(no.func.attr)
        self.assertTrue(proibidos.isdisjoint(importados))
        self.assertNotIn("marcar_entregues", chamadas)
        self.assertNotIn("ack", chamadas)


def _classe(arvore: ast.AST, nome: str) -> ast.ClassDef:
    for no in arvore.body:  # type: ignore[attr-defined]
        if isinstance(no, ast.ClassDef) and no.name == nome:
            return no
    raise AssertionError(nome)


def _campos(arvore: ast.AST, nome: str) -> tuple[str, ...]:
    return tuple(
        item.target.id
        for item in _classe(arvore, nome).body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    )


def _metodos(arvore: ast.AST, nome: str) -> tuple[str, ...]:
    return tuple(
        item.name
        for item in _classe(arvore, nome).body
        if isinstance(item, ast.FunctionDef)
    )


if __name__ == "__main__":
    unittest.main()
