"""Testes do handoff humano da Ana — unittest stdlib.

Todos os textos são FICTÍCIOS, inventados para o teste. Nenhum texto
real de cliente aparece aqui (regra do repo: sem dado de comprador).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import handoff  # noqa: E402


class TestDetectarHandoff(unittest.TestCase):
    def test_humano_explicito(self):
        casos = [
            "Quero falar com um humano, por favor",
            "Posso falar com um atendente?",
            "Me transfere para uma pessoa real",
            "Preciso falar com o José",
            "Me passa para o produtor",
            "Tem alguém aí que possa me ajudar?",
            "Quero atendimento humano",
            "Quero falar com uma pessoa de verdade",
        ]
        for texto in casos:
            with self.subTest(texto=texto):
                achado = handoff.detectar_handoff(texto)
                self.assertIsNotNone(achado, texto)
                self.assertEqual(achado["motivo"], "humano-explicito")
                self.assertIn("regra", achado)

    def test_produtor_confirma_nao_dispara(self):
        # "o produtor confirma" é conversa normal de preço/frete,
        # não pedido de humano.
        for texto in [
            "o produtor confirma o valor",
            "o produtor confirma o valor do frete?",
            "O produtor vai confirmar a cor antes do prazo",
        ]:
            self.assertIsNone(handoff.detectar_handoff(texto), texto)

    def test_amostra_fisica(self):
        casos = [
            "Vocês mandam uma amostra física?",
            "Quero uma amostra real da fita",
            "Manda uma amostra pra eu ver como fica",
            "Pode mandar uma amostra de verdade?",
        ]
        for texto in casos:
            with self.subTest(texto=texto):
                achado = handoff.detectar_handoff(texto)
                self.assertIsNotNone(achado, texto)
                self.assertEqual(achado["motivo"], "amostra-fisica")

    def test_amostra_em_imagem_nao_dispara(self):
        # A prévia em imagem (Modo A) é atendimento normal da Ana.
        for texto in [
            "Quero ver uma amostra de como fica",
            "Quer que eu monte uma prévia?",
            "Me mostra uma amostra da fita dourada",
        ]:
            self.assertIsNone(handoff.detectar_handoff(texto), texto)

    def test_suspeita_golpe(self):
        casos = [
            "Mercado Livre: alerta de segurança, confira seu acesso",
            "Recebi um alerta do Mercado Livre sobre minha conta",
            "Me passa o código pra pagar no pix agora, é urgente",
            "Paga com esse código no pix imediatamente",
        ]
        for texto in casos:
            with self.subTest(texto=texto):
                achado = handoff.detectar_handoff(texto)
                self.assertIsNotNone(achado, texto)
                self.assertEqual(achado["motivo"], "suspeita-golpe")

    def test_golpe_so_ancora_nao_dispara(self):
        self.assertIsNone(
            handoff.detectar_handoff("Comprei uma fita no Mercado Livre"))
        self.assertIsNone(
            handoff.detectar_handoff("Qual é o código da cor da fita?"))
        self.assertIsNone(
            handoff.detectar_handoff("O código do pedido é 12345"))

    def test_pos_venda(self):
        casos = [
            "Meu pedido não chegou",
            "Onde está meu pedido?",
            "Cadê meu pedido?",
            "Tem rastreio do meu pedido?",
            "Não recebi meu pedido ainda",
        ]
        for texto in casos:
            with self.subTest(texto=texto):
                achado = handoff.detectar_handoff(texto)
                self.assertIsNotNone(achado, texto)
                self.assertEqual(achado["motivo"], "pos-venda")

    def test_saudacao_e_preco_nao_disparam(self):
        for texto in [
            "Oi, bom dia!",
            "Olá, tudo bem?",
            "Quanto custa a fita de 15 mm com 10 m?",
            "Qual o valor da fita dourada?",
            "Vocês fazem fita para aniversário de criança?",
            "Qual a cor da fita que vocês têm?",
            "",
            "   ",
        ]:
            self.assertIsNone(handoff.detectar_handoff(texto), texto)

    def test_golpe_tem_prioridade_sobre_humano(self):
        achado = handoff.detectar_handoff(
            "Alerta do Mercado Livre, quero falar com um humano")
        self.assertEqual(achado["motivo"], "suspeita-golpe")


class TestAplicarHandoff(unittest.TestCase):
    """Guarda de ignorados + passos, com client falso em sys.modules."""

    def setUp(self):
        self.chamadas = []
        chamadas = self.chamadas

        class ClienteFalso:
            def obter_conversa(self, conv_id):
                chamadas.append(("obter_conversa", conv_id))
                return {"id": conv_id, "meta": {"sender": {
                    "phone_number": self.telefone,
                    "identifier": self.identifier,
                    "name": "Contato Ficticio"}}}

            def obter_contato(self, contact_id):
                chamadas.append(("obter_contato", contact_id))
                return None

            def criar_etiqueta(self, title):
                chamadas.append(("criar_etiqueta", title))
                return True

            def etiquetar_conversa(self, conv_id, labels):
                chamadas.append(("etiquetar_conversa", conv_id, labels))
                return True

            def atribuir_conversa(self, conv_id, assignee_id):
                chamadas.append(("atribuir_conversa", conv_id, assignee_id))
                return True

            def adicionar_nota(self, conv_id, content):
                chamadas.append(("adicionar_nota", conv_id, content))
                return True

        class IgnoradosFalsos:
            def is_ignorado(self, telefone=None, identifier=None, nome=None):
                if identifier == "id-mercado-livre-ficticio":
                    return "Mercado Livre"
                if telefone == "+5511999990002":
                    return "Mercado Livre"
                return None

        import types
        self.mod_client = types.ModuleType("chatwoot_client")
        self.cliente = ClienteFalso()
        self.cliente.telefone = "+5588999990005"
        self.cliente.identifier = "id-ficticio-qualquer"
        for nome in ("obter_conversa", "obter_contato", "criar_etiqueta",
                     "etiquetar_conversa", "atribuir_conversa",
                     "adicionar_nota"):
            setattr(self.mod_client, nome, getattr(self.cliente, nome))
        self.mod_ignorados = types.ModuleType("ignorados")
        self.mod_ignorados.is_ignorado = IgnoradosFalsos().is_ignorado
        sys.modules["chatwoot_client"] = self.mod_client
        sys.modules["ignorados"] = self.mod_ignorados

    def tearDown(self):
        sys.modules.pop("chatwoot_client", None)
        sys.modules.pop("ignorados", None)

    def test_contato_ignorado_nao_aplica_nada(self):
        self.cliente.identifier = "id-mercado-livre-ficticio"
        resultado = handoff.aplicar_handoff(8, "suspeita-golpe")
        self.assertTrue(resultado["ignorado"])
        self.assertEqual(resultado["empresa"], "Mercado Livre")
        self.assertFalse(resultado["aplicado"])
        acoes = [c[0] for c in self.chamadas]
        self.assertNotIn("criar_etiqueta", acoes)
        self.assertNotIn("etiquetar_conversa", acoes)
        self.assertNotIn("atribuir_conversa", acoes)
        self.assertNotIn("adicionar_nota", acoes)

    def test_contato_ignorado_por_telefone(self):
        self.cliente.telefone = "+5511999990002"
        resultado = handoff.aplicar_handoff(8, "suspeita-golpe")
        self.assertTrue(resultado["ignorado"])
        self.assertFalse(resultado["aplicado"])

    def test_aplica_todos_os_passos_para_cliente_normal(self):
        resultado = handoff.aplicar_handoff(6, "humano-explicito")
        self.assertFalse(resultado["ignorado"])
        self.assertTrue(resultado["aplicado"])
        self.assertEqual(resultado["etiqueta"], "handoff-humano")
        self.assertEqual(resultado["assignee_id"], 2)
        self.assertTrue(resultado["etiquetada"])
        self.assertTrue(resultado["atribuida"])
        self.assertTrue(resultado["nota"])
        acoes = [c[0] for c in self.chamadas]
        for passo in ("criar_etiqueta", "etiquetar_conversa",
                      "atribuir_conversa", "adicionar_nota"):
            self.assertIn(passo, acoes)
        # A nota registra motivo + data, nunca texto do cliente.
        nota = [c for c in self.chamadas if c[0] == "adicionar_nota"][0][2]
        self.assertIn("humano-explicito", nota)
        self.assertIn("Registrado em", nota)

    def test_nenhuma_funcao_de_envio_existe(self):
        # O handoff nunca envia mensagem ao cliente.
        self.assertFalse(hasattr(handoff, "enviar_mensagem"))
        self.assertFalse(hasattr(self.mod_client, "enviar_mensagem"))

    def test_conversa_inexistente(self):
        self.cliente.obter_conversa = lambda conv_id: None
        self.mod_client.obter_conversa = self.cliente.obter_conversa
        resultado = handoff.aplicar_handoff(999999, "pos-venda")
        self.assertFalse(resultado["aplicado"])
        self.assertEqual(resultado["erro"], "conversa-nao-encontrada")

    def test_resultado_e_dict_e_booleano(self):
        # Contrato duplo: dict (o que foi feito) e verdade booleana
        # para o ouvinte, que usa `if aplicado:` (interface do stub).
        aplicado = handoff.aplicar_handoff(6, "humano-explicito")
        self.assertIsInstance(aplicado, dict)
        self.assertTrue(bool(aplicado))
        self.cliente.identifier = "id-mercado-livre-ficticio"
        ignorado = handoff.aplicar_handoff(8, "suspeita-golpe")
        self.assertIsInstance(ignorado, dict)
        self.assertFalse(bool(ignorado))


if __name__ == "__main__":
    unittest.main()
