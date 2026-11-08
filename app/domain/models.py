"""Entidades do domínio de Tempos e Métodos (T&M).

Tudo aqui é puro Python: nenhuma dependência de web, planilha ou arquivo.
Valores numéricos usam Decimal para o cálculo ser determinístico.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Elemento:
    """Linha da MATRIZ DE ELEMENTOS (MTM)."""

    codigo: str  # ex.: "2.1" (agrupador.elemento)
    descricao: str
    tempo: Decimal  # minutos


@dataclass(frozen=True)
class Maquina:
    """Linha da aba TEMPO-CM."""

    codigo: str  # ex.: "1"
    tipo: str  # ex.: "Interlock"  (aparece em "Equipamento" na PO)
    descricao: str  # ex.: "Jack C4"
    rpm: Decimal  # RPM padrão
    tempo_por_metro: Decimal  # min/m


@dataclass(frozen=True)
class Demanda:
    """Dados de entrada de uma operação (ex.: demanda_000.txt)."""

    titulo: str
    rev: str
    operacao: str
    familia: str
    tamanho: str
    medidas: str  # mantido como texto, ex.: "1,80 x 2,50"
    pontos_cm: Decimal
    perimetro_m: Decimal
    cod_equipamento: str
    elementos: tuple[str, ...]  # códigos MTM, na ordem


@dataclass(frozen=True)
class LinhaPO:
    codigo: str  # "FIXO" ou código MTM
    descricao: str
    frequencia: int
    tempo: Decimal  # minutos, já arredondado (4 casas)


@dataclass(frozen=True)
class FichaPO:
    """Ficha de Processo Operacional pronta para exibir/exportar."""

    demanda: Demanda
    maquina: Maquina
    rpm_inferior: Decimal
    rpm_padrao: Decimal
    rpm_superior: Decimal
    linhas: tuple[LinhaPO, ...]
    tp: Decimal  # tempo total da operação (min)
