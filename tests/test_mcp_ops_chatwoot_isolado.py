"""Transporte do Chatwoot de laboratório. Unidade com falso; roundtrip no lab."""

from __future__ import annotations

import ast
import base64
import json
import logging
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tuttibom.mcp_ops.chatwoot_isolado import (  # noqa: E402
    VALIDADOR,
    ChatwootIsolado,
    RespostaTransporte,
    TransporteHttpLoopback,
    ValidadorOrigemLab,
)

PNG_ENTRADA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
PNG_SAIDA = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
TEXTO = "Resposta ficticia de laboratorio sem preco."
CONTAINER = "tuttibom-chatwoot-lab-chatwoot-1"
RUBY_NAMESPACE = r"""
require "json"
require "net/http"
require "base64"
require "uri"
arquivo = ENV.fetch("TB_LAB_ATENDIMENTO_JSON")
prefixos = ["/api/v1/accounts/", "/public/api/v1/inboxes/", "/rails/active_storage/"]

def responder(status, enviada, corpo = "", location = nil)
  STDOUT.write(JSON.generate(
    "status" => status,
    "enviada" => enviada,
    "location" => location,
    "corpo_b64" => Base64.strict_encode64(corpo.to_s)
  ))
end

begin
  pedido = JSON.parse(STDIN.read)
  caminho = pedido.fetch("caminho").to_s
  if caminho.include?("{inbox_identifier}")
    ident = JSON.parse(File.read(arquivo)).fetch("inbox_identifier").to_s
    raise "identificador" unless ident.match?(/\A[A-Za-z0-9]{8,}\z/)
    caminho = caminho.sub("{inbox_identifier}", ident)
  end
  puro = caminho.split("?", 2).first
  unless caminho.start_with?("/") && !caminho.start_with?("//") && !caminho.include?("..") &&
         prefixos.any? { |p| puro.start_with?(p) }
    responder(0, false)
    exit 0
  end
  klass = {"GET" => Net::HTTP::Get, "POST" => Net::HTTP::Post}[pedido.fetch("metodo")]
  if klass.nil?
    responder(0, false)
    exit 0
  end
  req = klass.new(URI("http://127.0.0.1:3000#{caminho}"))
  if pedido["corpo_b64"]
    req.body = Base64.strict_decode64(pedido["corpo_b64"])
  end
  req["Content-Type"] = pedido["tipo"] if pedido["tipo"]
  req["Accept"] = "application/json, image/png, */*"
  req["api_access_token"] = JSON.parse(File.read(arquivo)).fetch("token") if pedido["autenticar"]
  http = Net::HTTP.new("127.0.0.1", 3000)
  http.open_timeout = 5
  http.read_timeout = 20
  enviada = false
  begin
    http.start do
      res = http.request(req)
      enviada = true
      responder(res.code.to_i, true, res.body.to_s, res["location"])
    end
  rescue Errno::ECONNREFUSED, Errno::EHOSTUNREACH, Net::OpenTimeout
    responder(0, false)
  rescue
    responder(0, enviada || true)
  end
rescue
  responder(0, false)
end
"""


class _Coletor(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.linhas: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.linhas.append(record.getMessage())


class _Falso:
    def __init__(self) -> None:
        self.chamadas: list[dict] = []
        self.fila: list[RespostaTransporte] = []
        self.erros = 0

    def chamar(self, metodo, caminho, *, corpo=None, tipo=None, autenticar=False):
        self.chamadas.append({
            "metodo": metodo,
            "caminho": caminho,
            "corpo": corpo,
            "tipo": tipo,
            "autenticar": autenticar,
        })
        if self.erros:
            self.erros -= 1
            raise RuntimeError(TEXTO)
        if not self.fila:
            raise AssertionError("transporte sem resposta")
        return self.fila.pop(0)


class _Conexao:
    def __init__(self) -> None:
        self.pedidos: list[tuple] = []
        self.status = 200
        self.corpo = b"{}"
        self.cabecalhos: dict[str, str] = {}
        self.falha = None

    def request(self, metodo, caminho, body=None, headers=None):
        if self.falha == "antes":
            raise ConnectionRefusedError()
        self.pedidos.append((metodo, caminho, body, headers or {}))
        if self.falha == "depois":
            raise TimeoutError()

    def getresponse(self):
        return _Http(self.status, self.corpo, self.cabecalhos)

    def close(self) -> None:
        pass


class _Http:
    def __init__(self, status: int, corpo: bytes, cabecalhos: dict[str, str]) -> None:
        self.status = status
        self._corpo = corpo
        self._cabecalhos = cabecalhos

    def read(self) -> bytes:
        return self._corpo

    def getheader(self, nome: str) -> str | None:
        return self._cabecalhos.get(nome)


def _json(dados: dict) -> RespostaTransporte:
    return RespostaTransporte(200, json.dumps(dados).encode(), True, None)


def _conversa_lab() -> RespostaTransporte:
    return _json({"id": 1, "account_id": 1, "inbox_id": 1})


class TestValidador(unittest.TestCase):
    def setUp(self) -> None:
        self.validador = ValidadorOrigemLab(conta_id="1")

    def test_nome_do_validador(self):
        self.assertEqual(VALIDADOR, "ValidadorOrigemLab")

    def test_aceita_anexo_no_loopback_e_recusa_o_que_sai(self):
        caminho = self.validador.caminho(
            "http://127.0.0.1:3000/rails/active_storage/disk/abc/lab.png?content_type=image%2Fpng&disposition=inline",
            anexo=True,
        )
        self.assertTrue(caminho.startswith("/rails/active_storage/disk/abc/lab.png?"))
        for referencia in (
            "https://exemplo.invalid/a.png",
            "http://127.0.0.1:3001/rails/active_storage/a",
            "http://usuario:segredo@127.0.0.1:3000/rails/active_storage/a",
            "http://127.0.0.1:3000/api/v1/accounts/1/conversations/1",
            "//exemplo.invalid/a.png",
            "/rails/active_storage/../etc/passwd",
        ):
            with self.assertRaises(Exception):
                self.validador.caminho(referencia, anexo=True)

    def test_api_fica_na_conta_configurada(self):
        self.assertTrue(
            self.validador.caminho("/api/v1/accounts/1/conversations/4/messages").endswith("/messages")
        )
        with self.assertRaises(Exception):
            self.validador.caminho("/api/v1/accounts/2/conversations/4")
        self.assertIn(
            "{inbox_identifier}",
            self.validador.caminho("/public/api/v1/inboxes/{inbox_identifier}/contacts"),
        )


class TestAdaptador(unittest.TestCase):
    def setUp(self) -> None:
        self.falso = _Falso()
        self.adaptador = ChatwootIsolado(self.falso, conta_id="1", inbox_id="1")
        self.coletor = _Coletor()
        self.logger = logging.getLogger("tuttibom.mcp_ops.chatwoot_isolado")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.coletor)

    def tearDown(self) -> None:
        self.logger.removeHandler(self.coletor)

    def test_falha_conhecida_nao_e_incerta_e_nao_vaza_corpo(self):
        self.falso.fila.extend([_conversa_lab(), RespostaTransporte(422, TEXTO.encode(), True, None)])
        resultado = self.adaptador.enviar("1", texto="Oi laboratorio")
        self.assertEqual(resultado["codigo"], "envio_falhou")
        self.assertFalse(resultado["incerto"])
        self.assertFalse(resultado["deduplicado"])
        self.assertNotIn(TEXTO, repr(resultado))
        self.assertNotIn(TEXTO, "\n".join(self.coletor.linhas))

    def test_separa_envio_incerto_de_transporte_parado(self):
        self.falso.fila.extend([_conversa_lab(), RespostaTransporte(503, b"", True, None)])
        incerto = self.adaptador.enviar("1", texto="Oi laboratorio")
        self.assertEqual(incerto["codigo"], "envio_incerto")
        self.assertTrue(incerto["incerto"])
        self.falso.fila.extend([_conversa_lab(), RespostaTransporte(0, b"", False, None)])
        parado = self.adaptador.enviar("1", texto="Oi laboratorio")
        self.assertEqual(parado["codigo"], "transporte_indisponivel")
        self.assertFalse(parado["incerto"])

    def test_excecao_depois_do_pedido_e_incerta(self):
        self.falso.fila.append(_conversa_lab())
        self.falso.chamar = self._falhar_post(self.falso.chamar)
        resultado = self.adaptador.enviar("1", texto="Oi laboratorio")
        self.assertEqual(resultado["codigo"], "envio_incerto")
        self.assertNotIn(TEXTO, repr(resultado))

    @staticmethod
    def _falhar_post(chamar):
        def simular(metodo, caminho, **kwargs):
            if metodo == "POST":
                raise RuntimeError(TEXTO)
            return chamar(metodo, caminho, **kwargs)
        return simular

    def test_nao_deduplica_e_nao_segue_url_externa(self):
        self.falso.fila.extend([
            _conversa_lab(),
            _json({"id": 10, "inbox_id": 1}),
            _conversa_lab(),
            _json({"id": 11, "inbox_id": 1}),
        ])
        primeiro = self.adaptador.enviar("1", texto="Oi laboratorio")
        segundo = self.adaptador.enviar("1", texto="Oi laboratorio")
        self.assertEqual([primeiro["message_ref"], segundo["message_ref"]], ["msg-10", "msg-11"])
        self.assertFalse(primeiro["deduplicado"])
        self.assertEqual([c["metodo"] for c in self.falso.chamadas], ["GET", "POST", "GET", "POST"])
        self.falso.fila.extend([
            _json({"id": 1, "account_id": 1, "inbox_id": 1, "meta": {"sender": {"phone_number": "+5500999990014"}}}),
            _json({"payload": [{
                "id": 7,
                "content": None,
                "inbox_id": 1,
                "message_type": 0,
                "sender": {"email": "pessoa@example.invalid", "name": "Pessoa Ficticia Lab"},
                "attachments": [{
                    "id": 3,
                    "file_type": "image",
                    "data_url": "http://127.0.0.1:3000/rails/active_storage/blobs/redirect/abc/lab.png",
                }],
            }]}),
            RespostaTransporte(302, b"", True, "https://exemplo.invalid/a.png"),
        ])
        leitura = self.adaptador.ler_historico("1")
        self.assertEqual(leitura["codigo"], "origem_recusada")
        self.assertFalse(any("exemplo.invalid" in chamada["caminho"] for chamada in self.falso.chamadas))
        self.assertNotIn("example.invalid", repr(leitura))

    def test_imagem_sem_legenda_volta_em_bytes_sem_url(self):
        self.falso.fila.extend([
            _json({"id": 1, "account_id": 1, "inbox_id": 1}),
            _json({"payload": [{
                "id": 7,
                "content": None,
                "inbox_id": 1,
                "message_type": 0,
                "attachments": [{
                    "id": 3,
                    "file_type": "image",
                    "data_url": "http://127.0.0.1:3000/rails/active_storage/blobs/redirect/abc/lab.png",
                }],
            }]}),
            RespostaTransporte(
                302, b"", True,
                "http://127.0.0.1:3000/rails/active_storage/disk/abc/lab.png?disposition=inline",
            ),
            RespostaTransporte(200, PNG_ENTRADA, True, None),
        ])
        leitura = self.adaptador.ler_historico("1")
        self.assertTrue(leitura["ok"], leitura)
        mensagem = leitura["mensagens"][0]
        self.assertEqual(mensagem["texto"], "")
        self.assertEqual(mensagem["anexos"][0]["conteudo"], PNG_ENTRADA)
        self.assertNotIn("data_url", repr(leitura))
        self.assertNotIn("127.0.0.1", repr(leitura))

    def test_envio_recusa_outro_inbox_antes_de_postar(self):
        self.falso.fila.extend([
            _json({"id": 1, "account_id": 1, "inbox_id": 9}),
            _json({"id": 10, "inbox_id": 9}),
        ])
        resultado = self.adaptador.enviar("1", texto="Mensagem sintética")
        self.assertEqual(resultado["codigo"], "inbox_divergente")
        self.assertFalse(resultado["incerto"])
        self.assertEqual([c["metodo"] for c in self.falso.chamadas], ["GET"])

    def test_historico_ignora_nota_privada_sem_tentar_baixar_anexo(self):
        self.falso.fila.extend([
            _json({"id": 1, "account_id": 1, "inbox_id": 1}),
            _json({"payload": [
                {"id": 7, "inbox_id": 1, "message_type": 1, "private": True,
                 "content": "Nota interna", "attachments": [{"id": 3, "file_type": "file"}]},
                {"id": 8, "inbox_id": 1, "message_type": 0, "content": "Entrada sintética"},
            ]}),
        ])
        resultado = self.adaptador.ler_historico("1")
        self.assertTrue(resultado["ok"], resultado)
        self.assertEqual([m["id"] for m in resultado["mensagens"]], ["8"])
        self.assertEqual(len(self.falso.chamadas), 2)

    def test_inbox_divergente_nao_devolve_texto(self):
        self.falso.fila.append(_json({
            "id": 1, "account_id": 1, "inbox_id": 9,
            "messages": [{"content": TEXTO}],
        }))
        leitura = self.adaptador.ler_historico("1")
        self.assertEqual(leitura["codigo"], "inbox_divergente")
        self.assertNotIn(TEXTO, repr(leitura))
        self.assertNotIn("mensagens", leitura)

    def test_cliente_loopback_nao_expoe_segredo(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "lab.json"
            arquivo.write_text(json.dumps({
                "token": "tok-lab-nao-imprimir",
                "inbox_identifier": "identificadordolab01",
            }), encoding="utf-8")
            conexao = _Conexao()
            transporte = TransporteHttpLoopback(str(arquivo), abertura=lambda: conexao)
            resposta = transporte.chamar(
                "POST",
                "/public/api/v1/inboxes/{inbox_identifier}/contacts",
                corpo=b"{}",
                tipo="application/json",
                autenticar=True,
            )
            self.assertEqual(resposta.status, 200)
            metodo, caminho, _corpo, cabecalhos = conexao.pedidos[0]
            self.assertEqual(metodo, "POST")
            self.assertIn("/inboxes/identificadordolab01/contacts", caminho)
            self.assertEqual(cabecalhos["api_access_token"], "tok-lab-nao-imprimir")
            self.assertNotIn("tok-lab-nao-imprimir", repr(transporte))

    def test_modulo_nao_importa_docker_nem_socket(self):
        fonte = (ROOT / "src/tuttibom/mcp_ops/chatwoot_isolado.py").read_text(encoding="utf-8")
        arvore = ast.parse(fonte)
        modulos = []
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                modulos.extend(alias.name for alias in no.names)
            elif isinstance(no, ast.ImportFrom) and no.module:
                modulos.append(no.module)
        for modulo in modulos:
            for proibido in ("subprocess", "socket", "docker", "urllib.request"):
                self.assertNotIn(proibido, modulo)


class TransporteNamespace:
    def __init__(self) -> None:
        self.erros: list[str] = []
        self.arquivo = os.environ.get("TB_LAB_ATENDIMENTO_JSON")
        if not self.arquivo:
            raise RuntimeError("config_lab_ausente")

    def chamar(self, metodo, caminho, *, corpo=None, tipo=None, autenticar=False):
        pedido = json.dumps({
            "metodo": metodo,
            "caminho": caminho,
            "corpo_b64": None if corpo is None else base64.b64encode(corpo).decode(),
            "tipo": tipo,
            "autenticar": autenticar,
        }).encode()
        proc = subprocess.run(
            ["docker", "--context", "default", "exec", "-i",
             "-e", f"TB_LAB_ATENDIMENTO_JSON={self.arquivo}",
             CONTAINER, "ruby", "-e", RUBY_NAMESPACE],
            input=pedido,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if proc.stderr:
            self.erros.append(proc.stderr.decode("utf-8", "replace"))
        try:
            dados = json.loads(proc.stdout.decode())
        except ValueError:
            return RespostaTransporte(0, b"", True, None)
        corpo = base64.b64decode(dados.get("corpo_b64") or "")
        return RespostaTransporte(
            int(dados.get("status") or 0),
            corpo,
            bool(dados.get("enviada")),
            dados.get("location"),
        )

    def limpar_configuracao(self) -> None:
        subprocess.run(
            ["docker", "--context", "default", "exec",
             "-e", f"TB_LAB_ATENDIMENTO_JSON={self.arquivo}",
             CONTAINER, "ruby", "-e",
             'File.unlink(ENV.fetch("TB_LAB_ATENDIMENTO_JSON"))'],
            capture_output=True, timeout=20, check=False,
        )


def preparar_chatwoot() -> tuple[str, str]:
    arquivo = f"/tmp/tb-lab-{uuid.uuid4().hex}.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/preparar_chatwoot_lab.py")],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env={**os.environ, "TB_LAB_ATENDIMENTO_JSON": arquivo},
    )
    linha = next((item for item in proc.stdout.splitlines() if item.startswith("preparado ")), "")
    if proc.returncode != 0 or "conta=" not in linha:
        raise AssertionError(linha or "erro=fixture_sem_resumo")
    partes = dict(par.split("=", 1) for par in linha.split() if "=" in par)
    os.environ["TB_LAB_ATENDIMENTO_JSON"] = arquivo
    return partes["conta"], partes["inbox"]


@unittest.skipUnless(os.environ.get("TUTTIBOM_TEST_CHATWOOT_LAB") == "1", "Chatwoot isolado opt-in")
class TestRoundtripLab(unittest.TestCase):
    def test_roundtrip_de_texto_e_imagem_sem_legenda(self):
        conta, inbox = preparar_chatwoot()
        transporte = TransporteNamespace()
        adaptador = ChatwootIsolado(transporte, conta_id=conta, inbox_id=inbox)
        coletor = _Coletor()
        logger = logging.getLogger("tuttibom.mcp_ops.chatwoot_isolado")
        logger.setLevel(logging.INFO)
        logger.addHandler(coletor)
        try:
            contato = "pessoa-lab-" + uuid.uuid4().hex[:8]
            abertura = adaptador.abrir_conversa(contato)
            self.assertTrue(abertura["ok"], abertura)
            entrada = adaptador.enviar_entrada_imagem(
                contato_ref=contato,
                conversa_ref=abertura["conversa_ref"],
                imagem=PNG_ENTRADA,
            )
            self.assertTrue(entrada["ok"], entrada)
            self.assertFalse(entrada["deduplicado"])
            leitura = adaptador.ler_historico(abertura["conversa_ref"])
            self.assertTrue(leitura["ok"], leitura)
            imagem = next(m for m in leitura["mensagens"] if m["anexos"])
            self.assertEqual(imagem["texto"], "")
            self.assertEqual(imagem["direcao"], "incoming")
            self.assertEqual(imagem["anexos"][0]["conteudo"], PNG_ENTRADA)
            texto = adaptador.enviar(abertura["conversa_ref"], texto=TEXTO)
            png = adaptador.enviar(abertura["conversa_ref"], imagem=PNG_SAIDA)
            repetido = adaptador.enviar(abertura["conversa_ref"], texto=TEXTO)
            self.assertTrue(texto["ok"] and png["ok"] and repetido["ok"])
            self.assertNotEqual(texto["message_ref"], repetido["message_ref"])
            final = adaptador.ler_historico(abertura["conversa_ref"])
            textos = [m["texto"] for m in final["mensagens"]]
            self.assertEqual(textos.count(TEXTO), 2)
            saidas = [m for m in final["mensagens"] if m["direcao"] == "outgoing" and m["anexos"]]
            self.assertEqual(saidas[0]["texto"], "")
            self.assertEqual(saidas[0]["anexos"][0]["conteudo"], PNG_SAIDA)
            bruto = repr(final) + "\n" + "\n".join(coletor.linhas) + "\n" + "".join(transporte.erros)
            for segredo in (TEXTO, "Pessoa Ficticia Lab", "data_url", "api_access_token", "example.invalid"):
                self.assertNotIn(segredo, "\n".join(coletor.linhas) + "".join(transporte.erros))
            self.assertNotIn("data_url", repr(final))
            self.assertNotIn("api_access_token", bruto)
        finally:
            logger.removeHandler(coletor)
            transporte.limpar_configuracao()


if __name__ == "__main__":
    unittest.main()
