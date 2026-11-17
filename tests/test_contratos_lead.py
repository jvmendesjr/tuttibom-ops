"""Lead — estágio, próxima ação, follow-up, sem dado pessoal, sem preço inventado."""

import pytest
from pydantic import ValidationError

from tuttibom.contratos import Lead

ESTAGIOS = [
    "Novo",
    "Contatado",
    "Qualificado",
    "Proposta enviada",
    "Produção / Retirada",
    "Fechado",
    "Perdido",
    "Adormecido",
]


def _ficha(base, estagio):
    dados = dict(base)
    dados["estagio"] = estagio
    if estagio == "Perdido":
        dados["motivo_perda"] = "sem resposta"
    return dados


@pytest.mark.parametrize("estagio", ESTAGIOS)
def test_estagios_do_crm_local_passam(lead_novo, estagio):
    ficha = Lead.model_validate(_ficha(lead_novo, estagio))
    assert ficha.estagio.value == estagio
    assert ficha.proxima_acao
    assert str(ficha.data_followup) == "2026-11-18"


def test_nome_do_funil_deskcomm_nao_entra(lead_novo):
    lead_novo["estagio"] = "Novo contato"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "estagio" in str(excinfo.value)


def test_estagio_inventado_falha(lead_novo):
    lead_novo["estagio"] = "Ganhou"
    with pytest.raises(ValidationError):
        Lead.model_validate(lead_novo)


def test_proxima_acao_obrigatoria(lead_novo):
    assert Lead.model_validate(lead_novo).proxima_acao.startswith("Confirmar")
    del lead_novo["proxima_acao"]
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "proxima_acao" in str(excinfo.value)


def test_proxima_acao_curta_demais_falha(lead_novo):
    lead_novo["proxima_acao"] = "ok"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "proxima_acao" in str(excinfo.value)


def test_data_de_followup_obrigatoria(lead_novo):
    del lead_novo["data_followup"]
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "data_followup" in str(excinfo.value)


def test_data_de_followup_fora_do_iso_falha(lead_novo):
    lead_novo["data_followup"] = "18/11/2026"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "data_followup" in str(excinfo.value)


def test_medida_cidade_e_data_nao_sao_dado_pessoal(lead_novo):
    ficha = Lead.model_validate(lead_novo)
    assert "Juazeiro" in ficha.observacao
    assert ficha.produto == "FITA-22-50-PRETO"


def test_email_no_texto_falha(lead_novo):
    lead_novo["observacao"] = "responder teste@example.com"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "e-mail" in str(excinfo.value)


def test_telefone_no_texto_falha(lead_novo):
    lead_novo["observacao"] = "chamar (88) 99999-0000"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "telefone" in str(excinfo.value)


def test_cpf_no_texto_falha(lead_novo):
    lead_novo["observacao"] = "documento 123.456.789-09"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "CPF" in str(excinfo.value)


def test_endereco_no_texto_falha(lead_novo):
    lead_novo["observacao"] = "entregar na Rua Exemplo, 100"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "endereço" in str(excinfo.value)


def test_campo_extra_de_contato_falha(lead_novo):
    lead_novo["email"] = "teste@example.com"
    with pytest.raises(ValidationError):
        Lead.model_validate(lead_novo)


def test_referencia_com_nome_falha(lead_novo):
    lead_novo["referencia"] = "Maria Silva"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "referencia" in str(excinfo.value)


def test_perdido_sem_motivo_falha(lead_novo):
    lead_novo["estagio"] = "Perdido"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "motivo" in str(excinfo.value)


def test_perdido_com_motivo_passa(lead_novo):
    lead_novo["estagio"] = "Perdido"
    lead_novo["motivo_perda"] = "sem resposta"
    assert Lead.model_validate(lead_novo).motivo_perda == "sem resposta"


def test_valor_do_catalogo_passa(lead_novo):
    lead_novo["valor_catalogo"] = "R$ 71,90"
    assert Lead.model_validate(lead_novo).valor_catalogo == "R$ 71,90"


def test_valor_omitido_passa(lead_novo):
    assert Lead.model_validate(lead_novo).valor_catalogo is None


def test_preco_inventado_no_valor_falha(lead_novo):
    lead_novo["valor_catalogo"] = "R$ 99,90"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "catálogo" in str(excinfo.value)


def test_preco_inventado_na_observacao_falha(lead_novo):
    lead_novo["observacao"] = "fechar por R$ 99,90"
    with pytest.raises(ValidationError) as excinfo:
        Lead.model_validate(lead_novo)
    assert "catálogo" in str(excinfo.value)


def test_preco_do_catalogo_na_observacao_passa(lead_novo):
    lead_novo["observacao"] = "valor de catálogo R$ 71,90"
    ficha = Lead.model_validate(lead_novo)
    assert "71,90" in ficha.observacao
