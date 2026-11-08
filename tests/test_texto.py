from decimal import Decimal as D

import pytest

from app.adapters.input.texto import normalizar_chave, normalizar_codigo_simples, parse_decimal


@pytest.mark.parametrize(
    "bruto,esperado",
    [
        ("2,50", "2.50"), ("2.50", "2.50"), ("6,96", "6.96"), ("1.234,56", "1234.56"),
        ("1,234.56", "1234.56"), ("6,96 m", "6.96"), (" 7 ", "7"), ("1.234.567", "1234567"),
        ("-3,5", "-3.5"),
    ],
)
def test_parse_decimal(bruto, esperado):
    assert parse_decimal(bruto) == D(esperado)


@pytest.mark.parametrize("bruto", ["", "abc", "m", ","])
def test_parse_decimal_invalido(bruto):
    with pytest.raises(ValueError):
        parse_decimal(bruto)


def test_normalizar_chave():
    assert normalizar_chave("Perímetro costura (em m)") == "perimetro costura"
    assert normalizar_chave("Pontos/cm") == "pontos cm"
    assert normalizar_chave("  Cód. Eqp ") == "cod eqp"


def test_codigo_simples():
    assert normalizar_codigo_simples(D("1")) == "1"
    assert normalizar_codigo_simples(1.0) == "1"
    assert normalizar_codigo_simples("1.0") == "1"
    assert normalizar_codigo_simples(" 2.1 ") == "2.1"
