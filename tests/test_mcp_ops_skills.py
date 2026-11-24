from hashlib import sha256
from pathlib import Path
import re

import pytest

from tuttibom.mcp_ops.catalogo import CATALOGO
from tuttibom.mcp_ops.laboratorio import FUNCOES_LAB
from tuttibom.mcp_ops.skills_operacionais import papeis_para_funcoes, skills_para_funcao
from tuttibom.mcp_ops import skills_operacionais

RAIZ = Path(__file__).resolve().parents[1] / "skills"


def test_funcoes_disponiveis_tem_skills_exatas_e_sem_acesso_por_prefixo():
    esperadas = {
        "01.01": ["ops-ana-atendimento", "ops-ana-triagem"],
        "01.02": ["ops-ana-atendimento", "ops-ana-resposta"],
        "03.01": ["ops-produto-consulta"],
    }
    assert esperadas.keys() == FUNCOES_LAB
    for funcao in CATALOGO:
        assert [s.id for s in skills_para_funcao(funcao.id)] == esperadas.get(funcao.id, [])
    assert not skills_para_funcao("01.99")


def test_conteudo_publicado_e_byte_a_byte_o_skill_versionado():
    for funcao in FUNCOES_LAB:
        for skill in skills_para_funcao(funcao):
            esperado = (RAIZ / skill.id / "SKILL.md").read_bytes()
            assert skill.conteudo.encode() == esperado
            assert skill.versao == sha256(esperado).hexdigest()


def test_skills_deduplicam_papel_sem_incluir_outras_funcoes():
    assert papeis_para_funcoes(("01.01", "01.02", "03.01", "04.02", "08.01")) == [
        {"area": "01", "persona": "Ana",
         "skills": ["ops-ana-atendimento", "ops-ana-triagem", "ops-ana-resposta"]},
        {"area": "03", "persona": "Especialista de Produto e Catálogo",
         "skills": ["ops-produto-consulta"]},
    ]


def test_playbooks_planejados_cobrem_o_catalogo_sem_ser_publicados_no_ops():
    por_area = {
        "02": "ops-crm-vendas", "04": "ops-criativos-midia",
        "05": "ops-social-conteudo", "06": "ops-anuncios-aquisicao",
        "07": "ops-pedidos-producao", "08": "core-plataforma-manutencao",
    }
    for area, id_ in por_area.items():
        arquivo = (RAIZ / id_ / "SKILL.md").read_text()
        assert arquivo.startswith(f"---\nname: {id_}\ndescription:")
        for funcao in CATALOGO:
            if funcao.area != area:
                continue
            assert re.search(rf"\| `{re.escape(funcao.id)}`[^\n]*{funcao.ferramenta}[^\n]*\| {funcao.risco.value} \|", arquivo)
            assert not skills_para_funcao(funcao.id)


def test_skill_ausente_ou_symlink_nao_pode_ser_publicada(tmp_path, monkeypatch):
    raiz = tmp_path / "skills"
    raiz.mkdir()
    # Testa uma carga nova sem modificar o cache do host em outros testes.
    carregar = skills_operacionais._carregar.__wrapped__
    monkeypatch.setattr(skills_operacionais, "_RAIZ", raiz)
    id_ = "ops-ana-atendimento"
    with pytest.raises(ValueError, match="skill_operacional_invalida"):
        carregar(id_)
    (raiz / id_).symlink_to(RAIZ / id_, target_is_directory=True)
    with pytest.raises(ValueError, match="skill_operacional_invalida"):
        carregar(id_)
