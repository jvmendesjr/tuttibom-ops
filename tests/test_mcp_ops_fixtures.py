"""Testes independentes das fixtures e da matriz de aceitação do tuttibom-ops-mcp.

Valida a integridade, esquemas, regras de negócio e contratos de segurança
para o laboratório de integração e troca de agente (Frente QA), utilizando
exclusivamente a biblioteca padrão do Python (unittest, hashlib, json).
Sem chamadas de rede, sem dados de clientes e sem dependências externas.
"""

import hashlib
import json
import re
import unittest
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "mcp_ops"


class TestMCPOpsFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected_files = [
            "catalogo_admin.json",
            "autorizacoes.json",
            "manifestos.json",
            "leases_concorrencia.json",
            "aprovacao_resposta.json",
            "idempotencia.json",
            "midia_fila_troca.json",
            "scenarios_matrix.json",
        ]
        cls.fixtures = {}
        for fname in cls.expected_files:
            fpath = FIXTURES_DIR / fname
            if not fpath.exists():
                raise FileNotFoundError(f"Fixture não encontrada: {fpath}")
            with open(fpath, "r", encoding="utf-8") as f:
                cls.fixtures[fname] = json.load(f)

    def test_todas_as_fixtures_existem_e_sao_json_valido(self):
        self.assertEqual(len(self.fixtures), 8)
        for fname in self.expected_files:
            self.assertIn(fname, self.fixtures)
            self.assertEqual(self.fixtures[fname].get("versao"), "1.0.0-lab")

    def test_catalogo_admin_invariantes_e_numeros_estaveis(self):
        cat = self.fixtures["catalogo_admin.json"]
        self.assertFalse(cat.get("visibilidade_mcp_ops"), "Catálogo global não deve ser visível no MCP operacional")
        funcoes = cat.get("funcoes", [])
        self.assertGreaterEqual(len(funcoes), 20, "Catálogo deve cobrir os setores 0 a 8")

        numeros_vistos = set()
        nomes_vistos = set()
        padrao_numero = re.compile(r"^\d{2}\.\d{2}$")

        for f in funcoes:
            num = f["numero"]
            nome = f["nome"]
            risco = f["risco"]

            self.assertTrue(padrao_numero.match(num), f"Número inválido: {num}")
            self.assertNotIn(num, numeros_vistos, f"Número duplicado: {num}")
            numeros_vistos.add(num)

            self.assertNotIn(nome, nomes_vistos, f"Nome duplicado: {nome}")
            nomes_vistos.add(nome)

            self.assertIn(risco, {"seguro", "atencao", "critico"})
            if risco == "critico":
                self.assertTrue(
                    f.get("requer_selecao_individual"),
                    f"Função crítica {nome} ({num}) deve exigir seleção individual",
                )

        # Validação do isolamento operacional (sondagens negativas)
        sondagens = cat.get("sondagens_negativas", {})
        self.assertIn("tentativa_descoberta_operacional", sondagens)
        self.assertEqual(
            sondagens["tentativa_descoberta_operacional"]["resultado_esperado"]["codigo_erro"],
            "ERR_METHOD_OR_SCOPE_RESTRICTED",
        )

    def test_autorizacoes_validas_e_cenarios_negativos(self):
        aut = self.fixtures["autorizacoes.json"]
        validas = aut.get("autorizacoes_validas", [])
        self.assertGreaterEqual(len(validas), 2)

        for a in validas:
            self.assertTrue(a["referencia"].startswith("AUTH-REF-"))
            self.assertTrue(a.get("uso_unico"))
            self.assertFalse(a.get("ativada"))
            self.assertIn("identidade_vinculada", a)
            for f_num in a["funcoes_autorizadas"]:
                self.assertRegex(f_num, r"^\d{2}\.\d{2}$")

        # Teste de cenários negativos mapeados
        negativos = {c["id"]: c for c in aut.get("cenarios_negativos", [])}

        # 1. Referência sem poder sozinha
        self.assertIn("AUT-NEG-01-SEM-IDENTIDADE", negativos)
        self.assertEqual(
            negativos["AUT-NEG-01-SEM-IDENTIDADE"]["resultado_esperado"]["codigo_erro"],
            "ERR_AUTHENTICATION_REQUIRED",
        )

        # 2. Identidade errada
        self.assertIn("AUT-NEG-02-IDENTIDADE-ERRADA", negativos)
        self.assertEqual(
            negativos["AUT-NEG-02-IDENTIDADE-ERRADA"]["resultado_esperado"]["codigo_erro"],
            "ERR_IDENTITY_MISMATCH",
        )

        # 3. Reuso de autorização consumida
        self.assertIn("AUT-NEG-03-REUSO-CONSUMIDA", negativos)
        self.assertEqual(
            negativos["AUT-NEG-03-REUSO-CONSUMIDA"]["resultado_esperado"]["codigo_erro"],
            "ERR_AUTHORIZATION_ALREADY_CONSUMED",
        )

        # 4. Concorrência com lock atômico
        self.assertIn("AUT-NEG-04-CONCORRENCIA-RACE", negativos)
        race = negativos["AUT-NEG-04-CONCORRENCIA-RACE"]["resultado_esperado"]
        self.assertEqual(race["conexao_1"]["status"], 200)
        self.assertEqual(race["conexao_2"]["codigo_erro"], "ERR_ACTIVATION_IN_PROGRESS_OR_CONSUMED")

        # 5. Pacote genérico sem especificar função crítica
        self.assertIn("AUT-NEG-05-PACOTE-SEM-CRITICO", negativos)
        self.assertEqual(
            negativos["AUT-NEG-05-PACOTE-SEM-CRITICO"]["resultado_esperado"]["codigo_erro"],
            "ERR_CRITICAL_FUNCTION_REQUIRES_EXPLICIT_NUMBER",
        )

    def test_manifesto_hash_e_handshake_flow(self):
        man_doc = self.fixtures["manifestos.json"]
        manifesto = man_doc["manifesto_ana_01"]

        # Verificação do cálculo de hash do manifesto
        payload_canonica = json.dumps(
            {
                "agente_id": manifesto["agente_id"],
                "areas_autorizadas": manifesto["areas_autorizadas"],
                "ferramentas": manifesto["ferramentas"],
                "limites": manifesto["limites"],
                "lease": manifesto["lease"],
            },
            sort_keys=True,
        )
        hash_calculado = hashlib.sha256(payload_canonica.encode("utf-8")).hexdigest()
        self.assertEqual(manifesto["hash_atribuicao_esperado"], hash_calculado)

        # Handshake positivo
        hs_pos = man_doc["handshake_positivo"]
        self.assertEqual(
            hs_pos["chamada"]["params"]["arguments"]["hash"],
            hash_calculado,
        )
        self.assertTrue(hs_pos["resposta_esperada"]["escrita_liberada"])

        # Cenários negativos de manifesto
        cenarios_neg = {c["id"]: c for c in man_doc["cenarios_negativos"]}
        self.assertEqual(
            cenarios_neg["MAN-NEG-01-ESCRITA-PRE-HANDSHAKE"]["resultado_esperado"]["codigo_erro"],
            "ERR_HANDSHAKE_PENDING_WRITES_BLOCKED",
        )
        self.assertEqual(
            cenarios_neg["MAN-NEG-02-HASH-ADULTERADO"]["resultado_esperado"]["codigo_erro"],
            "ERR_MANIFEST_HASH_MISMATCH",
        )
        self.assertEqual(
            cenarios_neg["MAN-NEG-03-INVALIDACAO-RECONEXAO"]["resultado_esperado"]["codigo_erro"],
            "ERR_MANIFEST_INVALIDATED_RECONNECT_REQUIRED",
        )

    def test_leases_concorrencia_dois_escritores_e_revogacao(self):
        leases = self.fixtures["leases_concorrencia.json"]

        # Dois escritores na mesma área gravável
        dois_escritores = leases["cenario_concorrencia_dois_escritores"]
        self.assertEqual(dois_escritores["escritor_atual"]["agente_id"], "ana-01")
        self.assertEqual(dois_escritores["escritor_atual"]["prazo"], "sem_prazo_fixo")

        tentativa = dois_escritores["tentativa_segundo_escritor"]["resultado_esperado"]
        self.assertEqual(tentativa["codigo_erro"], "ERR_AREA_OCCUPIED")
        self.assertFalse(tentativa["escrita_permitida"])
        self.assertTrue(tentativa["leitura_permitida"])

        # Revogação e sucessão
        sucessao = leases["cenario_revogacao_e_sucessao"]
        pos_rev = sucessao["estado_pos_revogacao"]
        self.assertEqual(
            pos_rev["agente_ana_01"]["chamada_teste"]["resultado_esperado"]["codigo_erro"],
            "ERR_TOKEN_REVOKED",
        )
        self.assertEqual(pos_rev["lease_area_01"]["status"], "livre")

        sucessor = sucessao["sucessao_pelo_segundo_agente"]
        self.assertEqual(sucessor["agente_id"], "ana-02")
        self.assertTrue(sucessor["resultado_esperado"]["escrita_liberada"])
        self.assertEqual(sucessor["resultado_esperado"]["novo_titular_lease"], "ana-02")

    def test_aprovacao_resposta_exata_e_tabela_precos(self):
        aprov = self.fixtures["aprovacao_resposta.json"]
        contrato = aprov["contrato_aprovacao_resposta"]

        texto = contrato["texto_exato_submetido"]
        hash_esperado = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        self.assertEqual(contrato["hash_sha256_texto_exato"], hash_esperado)
        self.assertEqual(contrato["aprovacao_registrada"]["hash_texto"], hash_esperado)

        casos = {c["id"]: c for c in aprov["casos"]}

        # Envio legítimo com texto idêntico
        self.assertEqual(casos["APR-POS-01-ENVIO-APROVADO"]["resultado_esperado"]["status"], "enviado")

        # Tentativa de envio sem aprovação
        self.assertEqual(
            casos["APR-NEG-01-SEM-APROVACAO"]["resultado_esperado"]["codigo_erro"],
            "ERR_EXACT_APPROVAL_REQUIRED",
        )

        # Texto alterado (1 caractere) diverge no hash
        texto_adulterado = casos["APR-NEG-02-TEXTO-ALTERADO"]["chamada"]["arguments"]["texto"]
        hash_adulterado = hashlib.sha256(texto_adulterado.encode("utf-8")).hexdigest()
        self.assertNotEqual(hash_adulterado, hash_esperado)
        self.assertEqual(
            casos["APR-NEG-02-TEXTO-ALTERADO"]["resultado_esperado"]["codigo_erro"],
            "ERR_APPROVED_TEXT_HASH_MISMATCH",
        )

        # Preço fora do catálogo
        self.assertEqual(
            casos["APR-NEG-03-PRECO-NAO-TABELADO"]["resultado_esperado"]["codigo_erro"],
            "ERR_PRICE_NOT_IN_CATALOG",
        )

        # Autorização de função não é aprovação de envio
        self.assertEqual(
            casos["APR-NEG-04-AUTORIZACAO-NAO-E-APROVACAO"]["resultado_esperado"]["codigo_erro"],
            "ERR_FUNCTION_AUTHORIZATION_IS_NOT_SEND_APPROVAL",
        )

    def test_idempotencia_ttl_e_conflito_de_payload(self):
        idem = self.fixtures["idempotencia.json"]
        casos = {c["id"]: c for c in idem["casos"]}

        # Primeira execução
        c1 = casos["IDEM-POS-01-PRIMEIRA-EXECUCAO"]
        self.assertFalse(c1["resposta_servidor"]["idempotente"])
        key = c1["requisicao"]["idempotency_key"]

        # Retransmissão idêntica
        c2 = casos["IDEM-POS-02-RETRANSMISSAO-IDENTICA"]
        self.assertEqual(c2["requisicao"]["idempotency_key"], key)
        self.assertTrue(c2["resposta_servidor"]["idempotente"])
        self.assertFalse(c2["processamento"]["execucao_backend"])

        # Conflito de payload para a mesma chave
        c3 = casos["IDEM-NEG-01-CONFLITO-PAYLOAD"]
        self.assertEqual(c3["requisicao"]["idempotency_key"], key)
        self.assertEqual(
            c3["resultado_esperado"]["codigo_erro"],
            "ERR_IDEMPOTENCY_PAYLOAD_MISMATCH",
        )

        # Chave ausente em operação crítica
        c4 = casos["IDEM-NEG-02-CHAVE-AUSENTE"]
        self.assertEqual(
            c4["resultado_esperado"]["codigo_erro"],
            "ERR_IDEMPOTENCY_KEY_REQUIRED",
        )

    def test_midia_obrigatoria_e_fila_troca_agente(self):
        mid = self.fixtures["midia_fila_troca.json"]
        fila = mid["conversa_ficticia"]["fila_mensagens"]

        # Conversa contém mensagem com imagem e mensagem com áudio
        tipos = [m["tipo"] for m in fila]
        self.assertIn("imagem", tipos)
        self.assertIn("audio", tipos)

        casos = {c["id"]: c for c in mid["casos"]}

        # Negativo: tentativa de envio com mídia pendente
        self.assertEqual(
            casos["MID-NEG-01-RESPOSTA-SEM-PROCESSAR-MIDIA"]["resultado_esperado"]["codigo_erro"],
            "ERR_MEDIA_PENDING_ANALYSIS",
        )

        # Positivo: fluxo completo de processamento de mídia
        pos_fluxo = casos["MID-POS-01-FLUXO-MIDIA-COMPLETO"]
        acoes = [e["acao"] for e in pos_fluxo["etapas"]]
        self.assertIn("analise_de_visao_local", acoes)
        self.assertIn("transcricao_de_audio_local", acoes)
        self.assertIn("ops_produto_consultar", acoes)

        # Continuidade de fila na troca de agente
        troca = casos["MID-POS-02-CONTINUIDADE-FILA-TROCA-AGENTE"]
        esperado = troca["entrada_agente_sucessor"]["comportamento_esperado_ana_02"]
        self.assertTrue(esperado["suprime_cumprimento_duplicado"])
        self.assertTrue(esperado["preserva_dados_midia"])
        self.assertTrue(esperado["nenhuma_perda_de_fila"])

    def test_scenarios_matrix_cobertura_dez_dominios(self):
        matrix = self.fixtures["scenarios_matrix.json"]
        dominios = matrix.get("dominios", [])
        self.assertEqual(len(dominios), 10, "A matriz deve contemplar exatamente os 10 domínios contratuais")

        nomes_esperados = [
            "Catálogo apenas administrativo",
            "Autorização de número estável",
            "Referência sem poder sozinha",
            "Identidade errada",
            "Uso único e concorrente na ativação",
            "Manifesto inválido e reconexão",
            "Dois escritores e revogação de lease",
            "Aprovação da resposta exata",
            "Idempotência com TTL e integridade de payload",
            "Mídia obrigatória e continuidade de fila na troca",
        ]

        total_cenarios = 0
        for i, dom in enumerate(dominios):
            self.assertEqual(dom["dominio_id"], i + 1)
            self.assertEqual(dom["nome"], nomes_esperados[i])
            cenarios = dom.get("cenarios", [])
            self.assertGreaterEqual(len(cenarios), 2, f"Domínio {dom['nome']} deve ter cenários positivos e negativos")

            tipos_no_dominio = {c["tipo"] for c in cenarios}
            self.assertIn("positivo", tipos_no_dominio, f"Domínio {dom['nome']} deve conter caso positivo")
            self.assertIn("negativo", tipos_no_dominio, f"Domínio {dom['nome']} deve conter caso negativo")
            total_cenarios += len(cenarios)

        self.assertGreaterEqual(total_cenarios, 25, "Matriz consolidada deve conter pelo menos 25 cenários detalhados")


if __name__ == "__main__":
    unittest.main()
