from decimal import Decimal as D

from openpyxl import Workbook

from app.adapters.input.catalogos import carregar_catalogos


def test_xlsx_cabecalho_por_nome_nao_por_posicao(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "qualquer nome"
    ws.append(["Descrição do elemento", "Código do agrupador", "Código do elemento", "Tempo"])
    ws.append(["Apanhar", 2, 1, 0.2])
    ws2 = wb.create_sheet("maq")
    ws2.append(["LISTAGEM QUALQUER"])
    ws2.append(["Código de máquina", "Tipo Máquina", "Descrição", "RPM", "Tempo (tempo/metro"])
    ws2.append([1, "Reta", "Y", 5000, 0.0805])
    p = tmp_path / "c.xlsx"
    wb.save(p)

    c = carregar_catalogos(p)
    assert c.elementos["2.1"].tempo == D("0.2")
    assert c.maquinas["1"].tempo_por_metro == D("0.0805")
    assert c.maquinas["1"].tipo == "Reta"
