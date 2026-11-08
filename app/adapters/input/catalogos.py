"""Carga dos cadastros de apoio (MATRIZ DE ELEMENTOS e TEMPO-CM).

As abas e as colunas são localizadas pelo CABEÇALHO, não pela posição nem pelo
nome da aba, então pequenas mudanças no arquivo da organização não quebram.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from app.domain.erros import ValidacaoErro
from app.domain.models import Elemento, Maquina

from .tabelas import Linhas, ler_planilha
from .texto import normalizar_chave, normalizar_codigo_simples


@dataclass(frozen=True)
class Catalogos:
    elementos: dict[str, Elemento]
    maquinas: dict[str, Maquina]


def _achar_cabecalho(linhas: Linhas, obrigatorias: list[str]):
    """Procura a linha cujo cabeçalho contém todas as colunas obrigatórias."""
    for i, linha in enumerate(linhas):
        chaves = [normalizar_chave(c) if isinstance(c, str) else "" for c in linha]
        if all(any(c.startswith(o) for c in chaves) for o in obrigatorias):
            return i, chaves
    return None


def _col(chaves: list[str], prefixo: str) -> int:
    return next(i for i, c in enumerate(chaves) if c.startswith(prefixo))


def _num(valor) -> Decimal:
    if isinstance(valor, Decimal):
        return valor
    from .texto import parse_decimal

    return parse_decimal(str(valor))


def _ler_elementos(linhas: Linhas) -> dict[str, Elemento] | None:
    achado = _achar_cabecalho(linhas, ["descricao do elemento", "tempo"])
    if not achado:
        return None
    i0, ch = achado
    c_desc, c_tempo = _col(ch, "descricao do elemento"), _col(ch, "tempo")
    c_agr = next((i for i, c in enumerate(ch) if c.startswith("codigo do agrupador")), None)
    c_el = next((i for i, c in enumerate(ch) if c.startswith("codigo do elemento")), None)
    c_cod = next((i for i, c in enumerate(ch) if c.startswith("elemento agrupador")), None)

    def cel(linha, i):
        return linha[i] if i is not None and i < len(linha) else None

    resultado: dict[str, Elemento] = {}
    for linha in linhas[i0 + 1 :]:
        desc, tempo = cel(linha, c_desc), cel(linha, c_tempo)
        if desc is None or tempo is None:
            continue
        codigo = cel(linha, c_cod)
        if codigo is None:  # monta "agrupador.elemento"
            agr, el = cel(linha, c_agr), cel(linha, c_el)
            if agr is None or el is None:
                continue
            codigo = f"{normalizar_codigo_simples(agr)}.{normalizar_codigo_simples(el)}"
        codigo = normalizar_codigo_simples(codigo)
        resultado[codigo] = Elemento(codigo, str(desc), _num(tempo))
    return resultado


def _ler_maquinas(linhas: Linhas) -> dict[str, Maquina] | None:
    achado = _achar_cabecalho(linhas, ["codigo de maquina", "rpm", "tempo"])
    if not achado:
        return None
    i0, ch = achado
    c_cod = _col(ch, "codigo de maquina")
    c_tipo = next((i for i, c in enumerate(ch) if c.startswith("tipo")), None)
    c_desc = next((i for i, c in enumerate(ch) if c.startswith("descricao")), None)
    c_rpm, c_tempo = _col(ch, "rpm"), _col(ch, "tempo")

    def cel(linha, i):
        return linha[i] if i is not None and i < len(linha) else None

    resultado: dict[str, Maquina] = {}
    for linha in linhas[i0 + 1 :]:
        cod, rpm, tempo = cel(linha, c_cod), cel(linha, c_rpm), cel(linha, c_tempo)
        if cod is None or rpm is None or tempo is None:
            continue
        codigo = normalizar_codigo_simples(cod)
        resultado[codigo] = Maquina(
            codigo=codigo,
            tipo=str(cel(linha, c_tipo) or ""),
            descricao=str(cel(linha, c_desc) or ""),
            rpm=_num(rpm),
            tempo_por_metro=_num(tempo),
        )
    return resultado


def carregar_catalogos(caminho: str | Path) -> Catalogos:
    abas = ler_planilha(caminho)
    elementos = maquinas = None
    for linhas in abas.values():
        elementos = elementos or _ler_elementos(linhas)
        maquinas = maquinas or _ler_maquinas(linhas)
    problemas = []
    if not elementos:
        problemas.append("Não encontrei a MATRIZ DE ELEMENTOS (cabeçalho 'Descrição do elemento' + 'Tempo').")
    if not maquinas:
        problemas.append("Não encontrei o cadastro de máquinas (cabeçalho 'Código de máquina', 'RPM', 'Tempo').")
    if problemas:
        raise ValidacaoErro(problemas)
    return Catalogos(elementos, maquinas)
