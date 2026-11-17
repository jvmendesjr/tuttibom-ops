"""Criativo — formato, texto legível, zona segura, botões A/B."""

import pytest
from pydantic import ValidationError

from tuttibom.contratos import Criativo
from tuttibom.contratos.publicacao import TEXTO_PILOTO


def test_criativo_9_16_do_piloto_passa(criativo_piloto):
    criativo = Criativo.model_validate(criativo_piloto)
    assert criativo.formato.value == "9:16"
    assert criativo.botao_a.rotulo.startswith("A:")
    assert criativo.botao_b.legivel is True
    assert criativo.zonas_seguras.texto_na_zona_morta is False


def test_formato_4_5_com_margem_declarada_passa(criativo_piloto):
    criativo_piloto["formato"] = "4:5"
    criativo_piloto["zonas_seguras"] = {
        "topo_px": 48,
        "base_px": 48,
        "direita_px": 48,
        "texto_na_zona_morta": False,
    }
    assert Criativo.model_validate(criativo_piloto).formato.value == "4:5"


def test_formato_invalido_falha(criativo_piloto):
    criativo_piloto["formato"] = "1:1"
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "formato" in str(excinfo.value)


def test_texto_legivel_curto_passa_e_vazio_falha(criativo_piloto):
    assert Criativo.model_validate(criativo_piloto).textos[0].conteudo == "Ateliê Celebra"
    criativo_piloto["textos"] = [{"conteudo": "   ", "legivel": True}]
    with pytest.raises(ValidationError):
        Criativo.model_validate(criativo_piloto)


def test_texto_marcado_ilegivel_falha(criativo_piloto):
    criativo_piloto["textos"] = [{"conteudo": "Ateliê Celebra", "legivel": False}]
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "legivel" in str(excinfo.value)


def test_legenda_do_piloto_nao_cabe_como_overlay(criativo_piloto):
    criativo_piloto["textos"] = [{"conteudo": TEXTO_PILOTO, "legivel": True}]
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "conteudo" in str(excinfo.value)


def test_lista_de_textos_vazia_falha(criativo_piloto):
    criativo_piloto["textos"] = []
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "textos" in str(excinfo.value)


def test_zona_9_16_abaixo_do_piso_falha(criativo_piloto):
    criativo_piloto["zonas_seguras"]["direita_px"] = 100
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "140" in str(excinfo.value)


def test_texto_na_zona_morta_falha(criativo_piloto):
    criativo_piloto["zonas_seguras"]["texto_na_zona_morta"] = True
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "texto_na_zona_morta" in str(excinfo.value)


def test_4_5_sem_margem_declarada_falha(criativo_piloto):
    criativo_piloto["formato"] = "4:5"
    criativo_piloto["zonas_seguras"] = {
        "topo_px": 0,
        "base_px": 0,
        "direita_px": 0,
        "texto_na_zona_morta": False,
    }
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "4:5" in str(excinfo.value)


def test_botoes_a_e_b_diferentes_passam(criativo_piloto):
    criativo = Criativo.model_validate(criativo_piloto)
    assert criativo.botao_a.rotulo != criativo.botao_b.rotulo


def test_botao_b_ausente_falha(criativo_piloto):
    del criativo_piloto["botao_b"]
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "botao_b" in str(excinfo.value)


def test_botoes_iguais_falham(criativo_piloto):
    criativo_piloto["botao_b"] = {"rotulo": "a: dourado metalizado", "legivel": True}
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "diferentes" in str(excinfo.value)


def test_botao_ilegivel_falha(criativo_piloto):
    criativo_piloto["botao_a"] = {"rotulo": "A: Dourado Metalizado", "legivel": False}
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "legivel" in str(excinfo.value)


def test_preco_no_botao_falha(criativo_piloto):
    criativo_piloto["botao_a"] = {"rotulo": "A: por R$ 10,00", "legivel": True}
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "preço" in str(excinfo.value)


def test_preco_no_overlay_falha(criativo_piloto):
    criativo_piloto["textos"] = [{"conteudo": "por 20,00 reais", "legivel": True}]
    with pytest.raises(ValidationError) as excinfo:
        Criativo.model_validate(criativo_piloto)
    assert "preço" in str(excinfo.value)
