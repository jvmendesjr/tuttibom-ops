"""Laboratório do adaptador de atendimento. Dados fictícios, sem rede.

O texto, a transcrição e as imagens existem só neste teste para o
agente conseguir ler o turno. Logs, auditoria e o resultado do envio
não podem carregá-los.
"""

from __future__ import annotations

import ast
import logging
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tuttibom.mcp_ops.atendimento import (  # noqa: E402
    FERRAMENTA_LER,
    FERRAMENTA_RESPONDER,
    FERRAMENTAS,
    AdaptadorAtendimento,
    AuditoriaLaboratorio,
    ChatwootLaboratorio,
    FilaLaboratorio,
    SimuladorAtendimento,
    VerificadorAprovacaoServidor,
    montar_laboratorio,
)

FRASE = "Oi, quero a fita dourada FRASELAB7F3A para uma festa ficticia."
TRANSCRICAO = "audio ficticio TRANSCRICAOLAB9C2E"
TEXTO = "Temos a fita dourada em estoque."
TOKEN = "opsLABNAOLOGAR"
URL = "http://laboratorio.invalid/midia-secreta-7f3a"
AUDIO = b"RIFF-audio-lab-7f3a"
IMAGEM_LEAD = b"PNG-lab-lead-IMAGEMLEAD7F3A"
IMAGEM_RESP = b"PNG-lab-previa-IMAGEMRESP7F3A"
CONV = "conv-lab-01"
MSG = "msg-lab-01"
CHAVE = "chave-lab-01"


class _Coletor(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.linhas: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.linhas.append(record.getMessage())


class _Relogio:
    def __init__(self) -> None:
        self.agora = datetime(2026, 11, 23, 15, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.agora


class _Transcritor:
    def __init__(self, texto: str = TRANSCRICAO, erro: BaseException | None = None) -> None:
        self.texto = texto
        self.erro = erro
        self.chamadas: list[tuple[bytes, str]] = []

    def transcrever(self, audio: bytes, *, idioma: str = "pt") -> str:
        self.chamadas.append((bytes(audio), idioma))
        if self.erro is not None:
            raise self.erro
        return self.texto


class _VerificadorBooleano:
    def conferir(self, aprovacao_ref: str, texto: str, imagem: bytes | None) -> bool:
        return True


class _FilaExtra(FilaLaboratorio):
    def listar_pendentes(self, limite: int = 20) -> list[dict]:
        itens = super().listar_pendentes(limite)
        for item in itens:
            item["texto"] = FRASE
            item["token"] = TOKEN
            item["data_url"] = URL
        return itens


class _FilaAckInstavel(FilaLaboratorio):
    def __init__(self) -> None:
        super().__init__()
        self.falhar = True

    def marcar_entregues(self, message_ids):
        if self.falhar:
            raise RuntimeError(FRASE)
        return super().marcar_entregues(message_ids)


class _FilaTrilha(FilaLaboratorio):
    def __init__(self, trilha: list[str]) -> None:
        super().__init__()
        self.trilha = trilha

    def marcar_entregues(self, message_ids):
        marcados = super().marcar_entregues(message_ids)
        self.trilha.append("ack")
        return marcados


class _SimuladorTrilha(SimuladorAtendimento):
    def __init__(self, trilha: list[str]) -> None:
        super().__init__()
        self.trilha = trilha

    def enviar(self, *, conversa_ref, texto, imagem, idempotency_key):
        resultado = super().enviar(
            conversa_ref=conversa_ref,
            texto=texto,
            imagem=imagem,
            idempotency_key=idempotency_key,
        )
        self.trilha.append("envio")
        return resultado


class _SimuladorExplode(SimuladorAtendimento):
    def enviar(self, *, conversa_ref, texto, imagem, idempotency_key):
        raise RuntimeError(FRASE + TOKEN + URL)


class _ChatwootComUrl:
    def geracao(self, conversa_ref: str) -> int:
        return 1

    def ler_mensagens(self, conversa_ref: str) -> list[dict]:
        return [{
            "direcao": "incoming",
            "texto": FRASE,
            "anexos": [{
                "file_type": "image",
                "midia_ref": "img-lab-01",
                "data_url": URL,
                "token": TOKEN,
            }],
        }]

    def obter_audio(self, midia_ref: str) -> bytes:
        raise KeyError(midia_ref)


class TestVerificador(unittest.TestCase):
    def test_so_confere_texto_e_imagem_exatos(self):
        verificador = VerificadorAprovacaoServidor()
        ref = verificador.registrar(texto=TEXTO, imagem=IMAGEM_RESP)
        self.assertEqual(
            verificador.conferir(ref, TEXTO, IMAGEM_RESP),
            verificador.conferir(ref, TEXTO, IMAGEM_RESP),
        )
        self.assertIsNone(verificador.conferir(ref, TEXTO + " ", IMAGEM_RESP))
        self.assertIsNone(verificador.conferir(ref, TEXTO, IMAGEM_RESP + b"x"))
        self.assertIsNone(verificador.conferir(ref, TEXTO, None))
        self.assertIsNone(verificador.conferir("apr-ausente", TEXTO, IMAGEM_RESP))
        self.assertNotIn(TEXTO, repr(verificador))
        self.assertNotIn("IMAGEMRESP7F3A", repr(verificador))


class TestAdaptadorAtendimento(unittest.TestCase):
    def setUp(self) -> None:
        self.coletor = _Coletor()
        self.logger = logging.getLogger("tuttibom.mcp_ops.atendimento")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.coletor)
        self.transcritor = _Transcritor()
        self._montar()

    def tearDown(self) -> None:
        self.logger.removeHandler(self.coletor)

    def _montar(self, **trocas) -> None:
        self.fila = trocas.get("fila") or FilaLaboratorio()
        self.chatwoot = trocas.get("chatwoot") or ChatwootLaboratorio()
        self.simulador = trocas.get("simulador") or SimuladorAtendimento()
        self.verificador = trocas.get("verificador") or VerificadorAprovacaoServidor()
        self.auditoria = trocas.get("auditoria") or AuditoriaLaboratorio()
        self.adaptador = AdaptadorAtendimento(
            fila=self.fila,
            chatwoot=self.chatwoot,
            simulador=self.simulador,
            transcritor=trocas.get("transcritor", self.transcritor),
            verificador=self.verificador,
            auditoria=self.auditoria,
            relogio=trocas.get("relogio"),
            ttl_segundos=trocas.get("ttl", 60),
        )

    def _semear(self, *, mensagem_extra: str | None = None) -> None:
        self.fila.enfileirar(
            message_id=MSG,
            conversation_id=CONV,
            inbox_id="inbox-lab",
            contato_ref="contato-lab-01",
            handoff=None,
            recebido_em="2026-11-23T15:00:00-03:00",
            cumprimento={"texto": "Aguarde um instante.", "variante": 1, "enviado_em": "t"},
        )
        self.chatwoot.registrar_audio("aud-lab-01", AUDIO)
        self.chatwoot.registrar_mensagem(
            CONV,
            direcao="incoming",
            texto=FRASE,
            anexos=(
                {"file_type": "image", "midia_ref": "img-lab-01", "data_url": URL},
                {"file_type": "audio", "midia_ref": "aud-lab-01"},
            ),
        )
        if mensagem_extra is not None:
            self.chatwoot.registrar_mensagem(CONV, direcao="incoming", texto=mensagem_extra)
        self.simulador.registrar_imagem("img-lab-01", IMAGEM_LEAD)
        self.simulador.registrar_imagem("img-resp-01", IMAGEM_RESP)

    def _ler(self) -> dict:
        return self.adaptador.chamar(FERRAMENTA_LER, {
            "conversa_ref": CONV,
            "token": TOKEN,
            "texto_aprovado": True,
            "data_url": URL,
        })

    def _preparar(self, texto: str = TEXTO, chave: str = CHAVE, ids=(MSG,), imagem="img-resp-01") -> dict:
        return self.adaptador.preparar_resposta(
            conversa_ref=CONV,
            texto=texto,
            idempotency_key=chave,
            message_ids=ids,
            imagem_ref=imagem,
        )

    def _enviar(self, rascunho_ref: str, texto: str = TEXTO, imagem: bytes | None = IMAGEM_RESP) -> dict:
        aprovacao = self.verificador.registrar(texto=texto, imagem=imagem)
        return self.adaptador.chamar(FERRAMENTA_RESPONDER, {
            "rascunho_ref": rascunho_ref,
            "aprovacao_ref": aprovacao,
            "token": TOKEN,
            "texto_aprovado": True,
            "aprovado": True,
        })

    def _rastro(self) -> str:
        return "\n".join(self.coletor.linhas) + "\n" + repr(self.auditoria.eventos)

    def test_nucleo_chama_sem_cadastro_token_ou_lease(self):
        self.assertEqual(set(FERRAMENTAS), {FERRAMENTA_LER, FERRAMENTA_RESPONDER})
        for nome in ("emitir_token", "criar_lease", "cadastrar_agente", "autorizar"):
            self.assertFalse(hasattr(self.adaptador, nome))
        self.assertTrue(callable(self.adaptador.listar_pendencias))
        self.assertTrue(callable(self.adaptador.chamar))
        self.assertTrue(callable(self.adaptador.preparar_resposta))

    def test_lista_pendencias_e_esconde_campo_estranho(self):
        fila = _FilaExtra()
        self._montar(fila=fila)
        self._semear()
        fila.enfileirar(
            message_id="msg-lab-02",
            conversation_id=CONV,
            inbox_id="inbox-lab",
            contato_ref="contato-lab-01",
            recebido_em="2026-11-23T15:01:00-03:00",
        )
        resultado = self.adaptador.listar_pendencias(limite=1)
        self.assertTrue(resultado["ok"])
        self.assertEqual([item["message_id"] for item in resultado["pendencias"]], [MSG])
        item = resultado["pendencias"][0]
        self.assertEqual(item["cumprimento"]["texto"], "Aguarde um instante.")
        self.assertNotIn("texto", item)
        self.assertNotIn("token", item)
        self.assertNotIn(FRASE, repr(resultado))
        self.assertNotIn(TOKEN, self._rastro())
        self.assertNotIn("Aguarde um instante.", self._rastro())
        self.assertEqual(self.adaptador.listar_pendencias(limite=0)["codigo"], "argumento_invalido")

    def test_le_conversa_por_referencia_opaca_com_midia_do_simulador(self):
        self._semear()
        leitura = self._ler()
        self.assertTrue(leitura["ok"], leitura)
        mensagem = leitura["mensagens"][0]
        self.assertEqual(mensagem["texto"], FRASE)
        imagem, audio = mensagem["anexos"]
        self.assertEqual(imagem["conteudo"], IMAGEM_LEAD)
        self.assertEqual(imagem["midia_ref"], "img-lab-01")
        self.assertNotIn("data_url", imagem)
        self.assertEqual(audio["transcricao"], TRANSCRICAO)
        self.assertNotIn("conteudo", audio)
        self.assertEqual(self.transcritor.chamadas, [(AUDIO, "pt")])
        self.assertEqual(len(self.simulador.envios), 0)
        self.assertEqual(self.fila.obter(MSG)["estado"], "pendente")
        self.assertNotIn(URL, repr(leitura))
        self.assertNotIn(TOKEN, repr(leitura))

    def test_data_url_injetada_nao_sai_na_leitura_nem_no_log(self):
        self._montar(chatwoot=_ChatwootComUrl())
        self.simulador.registrar_imagem("img-lab-01", IMAGEM_LEAD)
        leitura = self._ler()
        self.assertTrue(leitura["ok"], leitura)
        self.assertEqual(leitura["mensagens"][0]["anexos"][0]["conteudo"], IMAGEM_LEAD)
        self.assertNotIn("data_url", repr(leitura))
        self.assertNotIn("midia-secreta-7f3a", repr(leitura))
        self.assertNotIn("midia-secreta-7f3a", self._rastro())
        self.assertNotIn(TOKEN, self._rastro())

    def test_audio_sem_transcricao_bloqueia_o_rascunho(self):
        self._montar(transcritor=None)
        self._semear()
        leitura = self._ler()
        self.assertEqual(leitura["codigo"], "transcricao_ausente")
        rascunho = self._preparar()
        self.assertEqual(rascunho["codigo"], "leitura_obrigatoria")
        self.assertEqual(self.simulador.envios, [])

    def test_erro_do_transcritor_nao_vaza(self):
        self._montar(transcritor=_Transcritor(erro=RuntimeError(FRASE + URL)))
        self._semear()
        leitura = self._ler()
        self.assertEqual(leitura["codigo"], "transcricao_ausente")
        self.assertNotIn("FRASELAB7F3A", repr(leitura))
        self.assertNotIn("FRASELAB7F3A", self._rastro())
        self.assertNotIn("midia-secreta-7f3a", self._rastro())

    def test_preparar_nao_envia_nem_confirma_fila(self):
        self._semear()
        self.assertTrue(self._ler()["ok"])
        rascunho = self._preparar()
        self.assertTrue(rascunho["ok"], rascunho)
        self.assertNotIn(TEXTO, repr(rascunho))
        self.assertNotIn("IMAGEMRESP7F3A", repr(rascunho))
        self.assertEqual(self.simulador.envios, [])
        self.assertEqual(self.fila.obter(MSG)["estado"], "pendente")

    def test_recusa_aprovacao_diferente_antes_do_simulador(self):
        self._semear()
        self.assertTrue(self._ler()["ok"])
        rascunho = self._preparar()
        aprovacao = self.verificador.registrar(texto=TEXTO + " ", imagem=IMAGEM_RESP)
        resposta = self.adaptador.responder(
            rascunho_ref=rascunho["rascunho_ref"],
            aprovacao_ref=aprovacao,
        )
        self.assertEqual(resposta["codigo"], "aprovacao_recusada")
        self.assertEqual(self.simulador.envios, [])
        self.assertEqual(self.fila.obter(MSG)["estado"], "pendente")

        aprovacao_imagem = self.verificador.registrar(texto=TEXTO, imagem=IMAGEM_RESP + b"x")
        resposta = self.adaptador.responder(
            rascunho_ref=rascunho["rascunho_ref"],
            aprovacao_ref=aprovacao_imagem,
        )
        self.assertEqual(resposta["codigo"], "aprovacao_recusada")
        self.assertEqual(self.simulador.envios, [])

    def test_booleano_do_agente_nao_aprova(self):
        self._semear()
        self.assertTrue(self._ler()["ok"])
        rascunho = self._preparar()
        self._montar(
            fila=self.fila,
            chatwoot=self.chatwoot,
            simulador=self.simulador,
            verificador=_VerificadorBooleano(),
        )
        self.assertTrue(self._ler()["ok"])
        rascunho = self._preparar()
        resposta = self.adaptador.chamar(FERRAMENTA_RESPONDER, {
            "rascunho_ref": rascunho["rascunho_ref"],
            "aprovacao_ref": "apr-1",
            "texto_aprovado": True,
            "aprovado": True,
        })
        self.assertEqual(resposta["codigo"], "aprovacao_recusada")
        self.assertEqual(self.simulador.envios, [])

    def test_envio_aprovado_ack_depois_e_so_a_mensagem_do_turno(self):
        trilha: list[str] = []
        self._montar(fila=_FilaTrilha(trilha), simulador=_SimuladorTrilha(trilha))
        self._semear()
        self.fila.enfileirar(
            message_id="msg-lab-02",
            conversation_id=CONV,
            inbox_id="inbox-lab",
            contato_ref="contato-lab-01",
            recebido_em="2026-11-23T15:02:00-03:00",
        )
        self.assertTrue(self._ler()["ok"])
        rascunho = self._preparar()
        resposta = self._enviar(rascunho["rascunho_ref"])
        self.assertTrue(resposta["ok"], resposta)
        self.assertEqual(resposta["acked"], [MSG])
        self.assertEqual(trilha, ["envio", "ack"])
        envio = self.simulador.envios[0]
        self.assertEqual(envio["texto"], TEXTO)
        self.assertEqual(envio["imagem"], IMAGEM_RESP)
        self.assertEqual(self.fila.obter(MSG)["estado"], "entregue")
        self.assertEqual(self.fila.obter("msg-lab-02")["estado"], "pendente")
        repetido = self.adaptador.responder(
            rascunho_ref=rascunho["rascunho_ref"],
            aprovacao_ref=self.verificador.registrar(texto=TEXTO, imagem=IMAGEM_RESP),
        )
        self.assertTrue(repetido["replay"])
        self.assertEqual(len(self.simulador.envios), 1)
        self.assertEqual(trilha, ["envio", "ack"])

    def test_falha_de_envio_nao_confirma_fila_e_nao_vaza(self):
        self._montar(simulador=_SimuladorExplode())
        self._semear()
        self.assertTrue(self._ler()["ok"])
        rascunho = self._preparar()
        resposta = self._enviar(rascunho["rascunho_ref"])
        self.assertEqual(resposta["codigo"], "envio_falhou")
        self.assertNotIn("enviado", resposta)
        self.assertEqual(self.simulador.envios, [])
        self.assertEqual(self.fila.obter(MSG)["estado"], "pendente")
        self.assertNotIn("FRASELAB7F3A", repr(resposta))
        self.assertNotIn("FRASELAB7F3A", self._rastro())
        self.assertNotIn(TOKEN, self._rastro())
        self.assertNotIn("midia-secreta-7f3a", self._rastro())

    def test_ack_falho_nao_reenvia(self):
        fila = _FilaAckInstavel()
        self._montar(fila=fila)
        self._semear()
        self.assertTrue(self._ler()["ok"])
        rascunho = self._preparar()
        primeira = self._enviar(rascunho["rascunho_ref"])
        self.assertEqual(primeira["codigo"], "ack_falhou")
        self.assertTrue(primeira["enviado"])
        self.assertEqual(len(self.simulador.envios), 1)
        self.assertEqual(self.fila.obter(MSG)["estado"], "pendente")
        self.assertNotIn("FRASELAB7F3A", repr(primeira))
        self.assertNotIn("FRASELAB7F3A", self._rastro())
        fila.falhar = False
        segunda = self.adaptador.responder(
            rascunho_ref=rascunho["rascunho_ref"],
            aprovacao_ref=self.verificador.registrar(texto=TEXTO, imagem=IMAGEM_RESP),
        )
        self.assertTrue(segunda["ok"], segunda)
        self.assertTrue(segunda["replay"])
        self.assertEqual(len(self.simulador.envios), 1)
        self.assertEqual(self.fila.obter(MSG)["estado"], "entregue")

    def test_idempotencia_conflito_e_expiracao(self):
        relogio = _Relogio()
        self._montar(relogio=relogio, ttl=60)
        self._semear()
        self.assertTrue(self._ler()["ok"])
        primeiro = self._preparar()
        conflito = self._preparar(texto=TEXTO + "!", chave=CHAVE)
        self.assertEqual(conflito["codigo"], "idempotencia_conflito")
        de_novo = self._preparar()
        self.assertEqual(de_novo["rascunho_ref"], primeiro["rascunho_ref"])
        self.assertTrue(self._enviar(primeiro["rascunho_ref"])["ok"])
        self.assertEqual(len(self.simulador.envios), 1)
        relogio.agora += timedelta(seconds=61)
        expirado = self.adaptador.responder(
            rascunho_ref=primeiro["rascunho_ref"],
            aprovacao_ref=self.verificador.registrar(texto=TEXTO, imagem=IMAGEM_RESP),
        )
        self.assertEqual(expirado["codigo"], "idempotencia_expirada")
        self.assertEqual(len(self.simulador.envios), 1)
        self.fila.enfileirar(
            message_id="msg-lab-02",
            conversation_id=CONV,
            inbox_id="inbox-lab",
            contato_ref="contato-lab-01",
            recebido_em="2026-11-23T16:00:00-03:00",
        )
        novo = self._preparar(chave=CHAVE, ids=("msg-lab-02",))
        self.assertTrue(novo["ok"], novo)
        self.assertTrue(self._enviar(novo["rascunho_ref"])["ok"])
        self.assertEqual(len(self.simulador.envios), 2)

    def test_nao_ack_de_outra_conversa(self):
        self._semear()
        self.fila.enfileirar(
            message_id="msg-lab-02",
            conversation_id="conv-lab-02",
            inbox_id="inbox-lab",
            contato_ref="contato-lab-02",
            recebido_em="2026-11-23T15:03:00-03:00",
        )
        self.assertTrue(self._ler()["ok"])
        rascunho = self._preparar(ids=("msg-lab-02",))
        resposta = self._enviar(rascunho["rascunho_ref"])
        self.assertEqual(resposta["codigo"], "ack_conversa_divergente")
        self.assertEqual(self.simulador.envios, [])
        self.assertEqual(self.fila.obter("msg-lab-02")["estado"], "pendente")

    def test_leitura_obrigatoria_e_obsoleta(self):
        self._semear()
        self.assertEqual(self._preparar()["codigo"], "leitura_obrigatoria")
        self.assertTrue(self._ler()["ok"])
        self.chatwoot.registrar_mensagem(CONV, direcao="incoming", texto="mais uma frase ficticia")
        self.assertEqual(self._preparar(chave="chave-lab-02")["codigo"], "leitura_obsoleta")
        self.assertEqual(self.simulador.envios, [])
        self.assertTrue(self._ler()["ok"])
        self.simulador.registrar_imagem("img-lab-01", IMAGEM_LEAD + b"y")
        self.assertEqual(self._preparar(chave="chave-lab-03")["codigo"], "leitura_obsoleta")

    def test_mensagem_recebida_durante_leitura_invalida_o_resultado(self):
        class MudancaDuranteLeitura(ChatwootLaboratorio):
            def ler_mensagens(self, conversa_ref):
                versao_original = super().ler_mensagens(conversa_ref)
                self.registrar_mensagem(conversa_ref, direcao="incoming", texto="Nova entrada fictícia")
                return versao_original

        self._montar(chatwoot=MudancaDuranteLeitura())
        self._semear()
        leitura = self._ler()
        self.assertEqual(leitura["codigo"], "leitura_obsoleta")
        self.assertNotIn("mensagens", leitura)
        self.assertEqual(self._preparar()["codigo"], "leitura_obrigatoria")

    def test_fluxo_completo_nao_vaza_em_log_nem_auditoria(self):
        self._semear()
        self.adaptador.listar_pendencias()
        leitura = self._ler()
        self.assertIn("FRASELAB7F3A", leitura["mensagens"][0]["texto"])
        rascunho = self._preparar(chave="FRASELAB7F3A")
        resposta = self._enviar(rascunho["rascunho_ref"])
        self.assertTrue(resposta["ok"], resposta)
        rastro = self._rastro()
        for segredo in (
            "FRASELAB7F3A",
            "TRANSCRICAOLAB9C2E",
            "IMAGEMLEAD7F3A",
            "IMAGEMRESP7F3A",
            TOKEN,
            "midia-secreta-7f3a",
            TEXTO,
            URL,
        ):
            self.assertNotIn(segredo, rastro)
            self.assertNotIn(segredo, repr(resposta))
            self.assertNotIn(segredo, repr(rascunho))
        for objeto in (
            self.adaptador,
            self.fila,
            self.chatwoot,
            self.simulador,
            self.verificador,
            self.auditoria,
        ):
            self.assertNotIn("FRASELAB7F3A", repr(objeto))

    def test_ferramenta_fora_da_area_e_recusada(self):
        resposta = self.adaptador.chamar("ops_social_publicar", {"token": TOKEN})
        self.assertEqual(resposta["codigo"], "ferramenta_desconhecida")
        self.assertNotIn(TOKEN, self._rastro())

    def test_modulo_nao_importa_rede_nem_ouvinte(self):
        fonte = (ROOT / "src/tuttibom/mcp_ops/atendimento.py").read_text(encoding="utf-8")
        arvore = ast.parse(fonte)
        modulos = []
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                modulos.extend(alias.name for alias in no.names)
            elif isinstance(no, ast.ImportFrom) and no.module:
                modulos.append(no.module)
        proibidos = ("urllib", "socket", "http", "requests", "listener", "chatwoot_client", "elevenlabs")
        for modulo in modulos:
            for proibido in proibidos:
                self.assertNotIn(proibido, modulo)
        self.assertFalse(any("chatwoot_client" in nome or nome.endswith(".listener") for nome in sys.modules))

    def test_montar_laboratorio_devolve_as_pecas_locais(self):
        adaptador, fila, chatwoot, simulador, verificador, auditoria = montar_laboratorio(
            transcritor=self.transcritor
        )
        self.assertIsInstance(adaptador, AdaptadorAtendimento)
        self.assertIsInstance(fila, FilaLaboratorio)
        self.assertIsInstance(chatwoot, ChatwootLaboratorio)
        self.assertIsInstance(simulador, SimuladorAtendimento)
        self.assertIsInstance(verificador, VerificadorAprovacaoServidor)
        self.assertIsInstance(auditoria, AuditoriaLaboratorio)


if __name__ == "__main__":
    unittest.main()
