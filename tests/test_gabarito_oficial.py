"""Valida contra o kit OFICIAL. Roda só se KIT_DIR apontar para a pasta do kit
(o kit não vai para o repositório público): KIT_DIR=/caminho pytest
"""
import os
from decimal import Decimal as D
from pathlib import Path

import pytest

from app.adapters.input.catalogos import carregar_catalogos
from app.adapters.input.demanda_txt import decodificar, ler_demanda_txt
from app.adapters.input.tabelas import ler_ods
from app.domain.calculo import gerar_ficha

KIT = os.environ.get("KIT_DIR")
pytestmark = pytest.mark.skipif(not KIT, reason="defina KIT_DIR para testar com o kit oficial")


def test_ficha_igual_ao_gabarito():
    kit = Path(KIT)
    cat = carregar_catalogos(kit / "Entradas.ods")
    demanda = ler_demanda_txt(decodificar((kit / "demanda_000.txt").read_bytes())).demanda
    ficha = gerar_ficha(demanda, cat.elementos, cat.maquinas)

    gab = ler_ods(kit / "PO-SL-000.ods")["PO"]
    # linhas de elementos do gabarito: [codigo, descricao, freq, tempo] (colunas A, B, D, E)
    esperado = [(l[0], l[1], int(l[3]), l[4]) for l in gab[7:]]
    obtido = [(l.codigo, l.descricao, l.frequencia, l.tempo) for l in ficha.linhas]
    assert [(c, d, f) for c, d, f, _ in obtido] == [(c, d, f) for c, d, f, _ in esperado]
    for (_, _, _, t_obt), (_, _, _, t_esp) in zip(obtido, esperado):
        assert t_obt == t_esp
    # cabeçalho e RPM
    assert (ficha.rpm_inferior, ficha.rpm_padrao, ficha.rpm_superior) == (D(4500), D(5000), D(5500))
    assert ficha.maquina.tipo == gab[5][1]
    assert ficha.tp == D("0.9409")
