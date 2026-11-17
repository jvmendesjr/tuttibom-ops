"""Publicacao — uma regra positiva e uma negativa por trava."""

import pytest
from pydantic import ValidationError

from tuttibom.contratos import Publicacao
from tuttibom.contratos.publicacao import TEXTO_PILOTO


def test_texto_do_piloto_passa(publicacao_piloto):
    peca = Publicacao.model_validate(publicacao_piloto)
    assert peca.texto_exato == TEXTO_PILOTO
    assert peca.texto_aprovado is True
    assert peca.schema_version == "1.0.0"
    assert peca.rotulo_ia is True
    assert peca.foto_de_cliente is False


def test_texto_vazio_falha(publicacao_piloto):
    publicacao_piloto["texto_exato"] = "   "
    with pytest.raises(ValidationError):
        Publicacao.model_validate(publicacao_piloto)


def test_texto_nao_aprovado_falha(publicacao_piloto):
    publicacao_piloto["texto_aprovado"] = False
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "texto_aprovado" in str(excinfo.value)


def test_arte_presente_passa_e_vazia_falha(publicacao_piloto):
    assert Publicacao.model_validate(publicacao_piloto).arte == "piloto-feed-2026-11-01"
    publicacao_piloto["arte"] = " "
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "arte" in str(excinfo.value)


@pytest.mark.parametrize("formato", ["9:16", "4:5"])
def test_formatos_da_peca_passam(publicacao_piloto, formato):
    publicacao_piloto["formato"] = formato
    assert Publicacao.model_validate(publicacao_piloto).formato.value == formato


def test_formato_fora_da_lista_falha(publicacao_piloto):
    publicacao_piloto["formato"] = "1:1"
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "formato" in str(excinfo.value)


@pytest.mark.parametrize("rede", ["facebook", "instagram"])
def test_redes_passam(publicacao_piloto, rede):
    publicacao_piloto["rede"] = rede
    assert Publicacao.model_validate(publicacao_piloto).rede.value == rede


def test_rede_desconhecida_falha(publicacao_piloto):
    publicacao_piloto["rede"] = "tiktok"
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "rede" in str(excinfo.value)


def test_data_iso_passa_e_ausente_falha(publicacao_piloto):
    assert str(Publicacao.model_validate(publicacao_piloto).data) == "2026-11-01"
    del publicacao_piloto["data"]
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "data" in str(excinfo.value)


def test_rotulo_de_ia_desligado_falha(publicacao_piloto):
    publicacao_piloto["rotulo_ia"] = False
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "rotulo_ia" in str(excinfo.value)


def test_foto_de_cliente_falha(publicacao_piloto):
    publicacao_piloto["foto_de_cliente"] = True
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "foto_de_cliente" in str(excinfo.value)


def test_medida_e_prazo_nao_sao_preco(publicacao_piloto):
    publicacao_piloto["texto_exato"] = (
        "Fita de cetim 15 mm ou 22 mm. Produção em 3 a 5 dias úteis."
    )
    peca = Publicacao.model_validate(publicacao_piloto)
    assert "15 mm" in peca.texto_exato


def test_preco_inventado_falha(publicacao_piloto):
    publicacao_piloto["texto_exato"] = TEXTO_PILOTO + " Por apenas R$ 99,90."
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "preço" in str(excinfo.value)


def test_preco_do_catalogo_tambem_falha_na_peca_publica(publicacao_piloto):
    publicacao_piloto["texto_exato"] = "Rolo de 22 mm por R$ 71,90."
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "preço" in str(excinfo.value)


def test_preco_em_reais_falha(publicacao_piloto):
    publicacao_piloto["texto_exato"] = "Leva por 50 reais hoje."
    with pytest.raises(ValidationError) as excinfo:
        Publicacao.model_validate(publicacao_piloto)
    assert "preço" in str(excinfo.value)


def test_schema_errado_falha(publicacao_piloto):
    publicacao_piloto["schema_version"] = "9.9.9"
    with pytest.raises(ValidationError):
        Publicacao.model_validate(publicacao_piloto)
