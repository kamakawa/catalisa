from decimal import Decimal as D

import pytest

from app.domain.calculo import arredondar, gerar_ficha
from app.domain.erros import ValidacaoErro
from app.domain.models import Demanda


def demanda(**kw):
    base = dict(
        titulo="T", rev="00", operacao="op", familia="f", tamanho="t", medidas="m",
        pontos_cm=D("2.5"), perimetro_m=D("2"), cod_equipamento="1", elementos=("2.1", "1.1", "3.1"),
    )
    base.update(kw)
    return Demanda(**base)


def test_fixo_e_tp(elementos, maquinas):
    f = gerar_ficha(demanda(), elementos, maquinas)
    assert [l.codigo for l in f.linhas] == ["FIXO", "2.1", "1.1", "3.1"]
    assert f.linhas[0].tempo == D("0.2000")  # 2 m x 0,1
    assert f.tp == D("0.5000")  # 0,2 + 0,2 + 0 + 0,1


def test_limites_rpm(elementos, maquinas):
    f = gerar_ficha(demanda(), elementos, maquinas)
    assert (f.rpm_inferior, f.rpm_padrao, f.rpm_superior) == (D(3600), D(4000), D(4400))


def test_arredondamento_half_up():
    assert arredondar(D("0.00005")) == D("0.0001")
    assert arredondar(D("0.670944")) == D("0.6709")


def test_tp_soma_valores_exibidos(elementos, maquinas):
    # 3,33 m x 0,0805 = 0,268065 -> 0,2681 ; TP = 0,2681 + 0,2 = 0,4681
    f = gerar_ficha(demanda(perimetro_m=D("3.33"), cod_equipamento="2", elementos=("2.1",)), elementos, maquinas)
    assert f.linhas[0].tempo == D("0.2681")
    assert f.tp == D("0.4681")


def test_ordem_e_repeticao_de_elementos(elementos, maquinas):
    f = gerar_ficha(demanda(elementos=("3.1", "3.1")), elementos, maquinas)
    assert [l.codigo for l in f.linhas] == ["FIXO", "3.1", "3.1"]


def test_erros_acumulados(elementos, maquinas):
    with pytest.raises(ValidacaoErro) as e:
        gerar_ficha(demanda(cod_equipamento="9", elementos=("9.9", "2.1"), perimetro_m=D(0)), elementos, maquinas)
    assert len(e.value.problemas) == 3
