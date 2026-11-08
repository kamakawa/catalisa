"""Utilitários de normalização de texto e números (padrão brasileiro e internacional)."""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation

_ASPAS = "\"'“”‘’«»`´"


def normalizar_chave(texto: str) -> str:
    """'Perímetro costura (em m)' -> 'perimetro costura'; 'Pontos/cm' -> 'pontos cm'."""
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"\([^)]*\)", " ", t)  # remove "(em m)"
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()


def limpar_valor(texto: str) -> str:
    t = str(texto).replace(" ", " ").strip()
    return t.strip(_ASPAS + " \t").strip()


def parse_decimal(texto: str) -> Decimal:
    """Aceita '2,50', '2.50', '1.234,56', '1,234.56', '6,96 m'. Levanta ValueError."""
    t = limpar_valor(texto)
    t = re.sub(r"[^\d,.\-]", "", t)  # tira unidade (m, cm...) e espaços
    if not t or not re.search(r"\d", t):
        raise ValueError(f"número inválido: {texto!r}")
    ultimo_virgula, ultimo_ponto = t.rfind(","), t.rfind(".")
    if ultimo_virgula != -1 and ultimo_ponto != -1:
        # o último separador é o decimal; o outro é milhar
        if ultimo_virgula > ultimo_ponto:
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    else:
        t = t.replace(",", ".")
        if t.count(".") > 1:  # '1.234.567' -> milhar
            t = t.replace(".", "")
    try:
        return Decimal(t)
    except InvalidOperation as exc:
        raise ValueError(f"número inválido: {texto!r}") from exc


def normalizar_codigo_simples(valor) -> str:
    """Código de máquina/elemento vindo de planilha: 1.0 -> '1', ' 2.1 ' -> '2.1'."""
    if isinstance(valor, Decimal):
        if valor == valor.to_integral_value():
            return str(int(valor))
        return str(valor.normalize())
    if isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() else str(valor)
    t = limpar_valor(valor)
    if re.fullmatch(r"\d+\.0+", t):
        t = t.split(".")[0]
    return t
