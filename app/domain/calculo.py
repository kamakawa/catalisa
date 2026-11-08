"""Motor de cálculo de T&M.

Regras (regulamento, itens 3.3 e 4):
  * Tempo FIXO (min) = Perímetro de costura (m) x Tempo/metro da máquina
  * Elementos manuais: descrição e tempo vêm da matriz MTM pelo código
  * TP = soma de todos os elementos (FIXO + MTM)

Decisões de arredondamento (ver README):
  * Cada linha é arredondada a 4 casas (ROUND_HALF_UP), como no gabarito
    (FIXO = 0,6709 para 0,670944).
  * TP = soma das linhas JÁ arredondadas, para que a ficha seja auditável:
    quem somar à mão os valores exibidos obtém o mesmo TP.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Mapping

from .erros import ValidacaoErro
from .models import Demanda, Elemento, FichaPO, LinhaPO, Maquina

CASAS = Decimal("0.0001")
LIMITE_INFERIOR = Decimal("0.9")  # RPM padrão x 0,9 (fórmula do gabarito)
LIMITE_SUPERIOR = Decimal("1.1")  # RPM padrão x 1,1 (fórmula do gabarito)


def arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(CASAS, rounding=ROUND_HALF_UP)


def _limpo(valor: Decimal) -> Decimal:
    """4500.0 -> 4500 ; 4512.5 -> 4512.5 (para exibição)."""
    if valor == valor.to_integral_value():
        return valor.quantize(Decimal(1))
    return valor.normalize()


def tempo_fixo(perimetro_m: Decimal, maquina: Maquina) -> Decimal:
    return arredondar(perimetro_m * maquina.tempo_por_metro)


def validar(
    demanda: Demanda,
    elementos: Mapping[str, Elemento],
    maquinas: Mapping[str, Maquina],
) -> list[str]:
    problemas: list[str] = []
    if demanda.perimetro_m <= 0:
        problemas.append("Perímetro de costura deve ser maior que zero.")
    if demanda.pontos_cm <= 0:
        problemas.append("Pontos/cm deve ser maior que zero.")
    if demanda.cod_equipamento not in maquinas:
        validos = ", ".join(sorted(maquinas)) or "nenhuma cadastrada"
        problemas.append(
            f"Máquina '{demanda.cod_equipamento}' não encontrada "
            f"(códigos disponíveis: {validos})."
        )
    if not demanda.elementos:
        problemas.append("Nenhum elemento MTM informado.")
    for codigo in demanda.elementos:
        if codigo not in elementos:
            problemas.append(f"Elemento MTM '{codigo}' não existe na matriz.")
    return problemas


def gerar_ficha(
    demanda: Demanda,
    elementos: Mapping[str, Elemento],
    maquinas: Mapping[str, Maquina],
) -> FichaPO:
    problemas = validar(demanda, elementos, maquinas)
    if problemas:
        raise ValidacaoErro(problemas)

    maquina = maquinas[demanda.cod_equipamento]
    linhas = [
        LinhaPO("FIXO", "Tempo de costura", 1, tempo_fixo(demanda.perimetro_m, maquina))
    ]
    for codigo in demanda.elementos:
        el = elementos[codigo]
        linhas.append(LinhaPO(el.codigo, el.descricao, 1, arredondar(el.tempo)))

    tp = sum((l.tempo * l.frequencia for l in linhas), Decimal(0))
    return FichaPO(
        demanda=demanda,
        maquina=maquina,
        rpm_inferior=_limpo(maquina.rpm * LIMITE_INFERIOR),
        rpm_padrao=_limpo(maquina.rpm),
        rpm_superior=_limpo(maquina.rpm * LIMITE_SUPERIOR),
        linhas=tuple(linhas),
        tp=arredondar(tp),
    )
