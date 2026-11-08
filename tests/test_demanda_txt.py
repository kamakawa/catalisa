from decimal import Decimal as D

import pytest

from app.adapters.input.demanda_txt import ler_demanda_txt, ler_demandas_txt
from app.domain.erros import ValidacaoErro

BASE = """Título: PO-X-001
REV: 00
Operação: "Bainhar teste"
Agrupamento família: Sobre-lençol
Tamanho: Solteiro
Medidas da peça (em m): 1,80 x 2,50
Pontos/cm: 2,50
Perímetro costura (em m): 6,96
Cód. Eqp: 1
Elementos: 2.1, 1.1, 3.1
"""


def test_formato_oficial():
    d = ler_demanda_txt(BASE).demanda
    assert d.titulo == "PO-X-001"
    assert d.operacao == "Bainhar teste"
    assert d.medidas == "1,80 x 2,50"
    assert d.pontos_cm == D("2.50")
    assert d.perimetro_m == D("6.96")
    assert d.cod_equipamento == "1"
    assert d.elementos == ("2.1", "1.1", "3.1")


def test_tolerancias():
    sujo = "﻿" + BASE.replace("\n", "\r\n").upper().replace("PO-X-001", "PO-X-001")
    sujo = sujo.replace("2,50", "2.50").replace("6,96", "6.96 m")
    sujo = sujo.replace('"BAINHAR TESTE"', "“Bainhar teste”")
    # chaves fora de ordem, espaços e separadores diferentes
    desordenado = "  elementos :  2.1;1.1  3.1 \nCOD. EQP: 1.0\n" + sujo.split("\r\n", 1)[0].lstrip("﻿") + "\nperímetro costura: 6,96\nOperação: x\n"
    d = ler_demanda_txt(desordenado).demanda
    assert d.elementos == ("2.1", "1.1", "3.1")
    assert d.cod_equipamento == "1"
    assert d.perimetro_m == D("6.96")


def test_campo_desconhecido_vira_aviso():
    r = ler_demanda_txt(BASE + "Cor: Azul\n")
    assert any("Cor" in a for a in r.avisos)


def test_campos_obrigatorios_ausentes():
    with pytest.raises(ValidacaoErro) as e:
        ler_demanda_txt("Título: A\nOperação: B\n")
    msg = " ".join(e.value.problemas)
    assert "Perímetro" in msg and "Elementos" in msg and "Eqp" in msg


def test_numero_e_codigo_invalidos():
    ruim = BASE.replace("6,96", "abc").replace("2.1, 1.1, 3.1", "2.1, xx")
    with pytest.raises(ValidacaoErro) as e:
        ler_demanda_txt(ruim)
    assert len(e.value.problemas) == 2


def test_varios_blocos_no_mesmo_arquivo():
    dois = BASE + "\n" + BASE.replace("PO-X-001", "PO-X-002")
    rs = ler_demandas_txt(dois)
    assert [r.demanda.titulo for r in rs] == ["PO-X-001", "PO-X-002"]
