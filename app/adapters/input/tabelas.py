"""Leitura genérica de planilhas (.ods, .xlsx) para listas de linhas.

Números saem como Decimal (a partir do texto da planilha, sem passar por float),
textos como str, vazios como None.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

Linhas = list[list[object]]

_CAP_REPETICAO = 100  # evita expandir milhões de células vazias repetidas


def _aparar(linha: list[object]) -> list[object]:
    while linha and linha[-1] is None:
        linha.pop()
    return linha


def ler_ods(caminho: str | Path) -> dict[str, Linhas]:
    from odf import table, teletype
    from odf.opendocument import load

    doc = load(str(caminho))
    abas: dict[str, Linhas] = {}
    for aba in doc.spreadsheet.getElementsByType(table.Table):
        linhas: Linhas = []
        for row in aba.getElementsByType(table.TableRow):
            celulas: list[object] = []
            for cel in row.childNodes:
                if cel.qname[1] not in ("table-cell", "covered-table-cell"):
                    continue
                tipo = cel.getAttribute("valuetype")
                if tipo in ("float", "percentage", "currency"):
                    valor: object = Decimal(str(cel.getAttribute("value")))
                elif tipo == "string":
                    valor = teletype.extractText(cel).strip() or None
                else:
                    valor = None
                rep = int(cel.getAttribute("numbercolumnsrepeated") or 1)
                if valor is None and rep > 1:
                    celulas.append(None)  # vazios repetidos: um basta
                else:
                    celulas.extend([valor] * min(rep, _CAP_REPETICAO))
            _aparar(celulas)
            rep_l = int(row.getAttribute("numberrowsrepeated") or 1)
            if celulas:
                linhas.extend([list(celulas) for _ in range(min(rep_l, _CAP_REPETICAO))])
            else:
                linhas.append([])
        while linhas and not linhas[-1]:
            linhas.pop()
        abas[aba.getAttribute("name")] = linhas
    return abas


def ler_xlsx(caminho: str | Path) -> dict[str, Linhas]:
    from openpyxl import load_workbook

    wb = load_workbook(str(caminho), data_only=True, read_only=True)
    abas: dict[str, Linhas] = {}
    for ws in wb.worksheets:
        linhas: Linhas = []
        for row in ws.iter_rows(values_only=True):
            linha: list[object] = []
            for v in row:
                if isinstance(v, bool) or v is None:
                    linha.append(None)
                elif isinstance(v, (int, float)):
                    linha.append(Decimal(str(v)))
                else:
                    t = str(v).strip()
                    linha.append(t or None)
            linhas.append(_aparar(linha))
        while linhas and not linhas[-1]:
            linhas.pop()
        abas[ws.title] = linhas
    wb.close()
    return abas


def ler_planilha(caminho: str | Path) -> dict[str, Linhas]:
    ext = Path(caminho).suffix.lower()
    if ext == ".ods":
        return ler_ods(caminho)
    if ext in (".xlsx", ".xlsm"):
        return ler_xlsx(caminho)
    raise ValueError(f"Formato de planilha não suportado: {ext or '(sem extensão)'}")
