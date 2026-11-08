"""Leitor tolerante do formato `Chave: valor` (ex.: demanda_000.txt).

Tolerâncias: BOM, CRLF, maiúsculas/minúsculas, acentos, espaços extras, aspas
comuns/tipográficas, vírgula ou ponto decimal, unidades coladas ("6,96 m"),
ordem livre das chaves, apelidos de chave e vários blocos no mesmo arquivo
(um novo bloco começa quando "Título" aparece de novo).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.erros import ValidacaoErro
from app.domain.models import Demanda

from .texto import limpar_valor, normalizar_chave, parse_decimal

# chave normalizada -> campo canônico
_ALIASES: dict[str, str] = {
    "titulo": "titulo",
    "codigo po": "titulo",
    "po": "titulo",
    "rev": "rev",
    "revisao": "rev",
    "operacao": "operacao",
    "agrupamento familia": "familia",
    "agrupamento": "familia",
    "familia": "familia",
    "tamanho": "tamanho",
    "medidas da peca": "medidas",
    "medidas": "medidas",
    "pontos cm": "pontos_cm",
    "densidade de pontos": "pontos_cm",
    "pontos por cm": "pontos_cm",
    "perimetro costura": "perimetro",
    "perimetro de costura": "perimetro",
    "perimetro": "perimetro",
    "cod eqp": "equipamento",
    "cod equipamento": "equipamento",
    "codigo equipamento": "equipamento",
    "codigo da maquina": "equipamento",
    "codigo de maquina": "equipamento",
    "cod maquina": "equipamento",
    "maquina": "equipamento",
    "equipamento": "equipamento",
    "elementos": "elementos",
    "roteiro": "elementos",
    "sequencia": "elementos",
}

_OBRIGATORIOS = {
    "titulo": "Título",
    "operacao": "Operação",
    "perimetro": "Perímetro costura (em m)",
    "equipamento": "Cód. Eqp",
    "elementos": "Elementos",
}

_CODIGO_MTM = re.compile(r"\d+\.\d+")


@dataclass(frozen=True)
class ResultadoLeitura:
    demanda: Demanda
    avisos: tuple[str, ...] = ()


def decodificar(dados: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return dados.decode(enc)
        except UnicodeDecodeError:
            continue
    return dados.decode("utf-8", errors="replace")


def _dividir_blocos(texto: str) -> list[tuple[list[tuple[str, str]], list[str]]]:
    """Devolve [(pares(chave_canonica, valor), avisos)] por bloco."""
    blocos: list[tuple[list[tuple[str, str]], list[str]]] = []
    pares: list[tuple[str, str]] = []
    avisos: list[str] = []
    for n, linha in enumerate(texto.replace("\r", "\n").split("\n"), start=1):
        if not linha.strip():
            continue
        if ":" not in linha:
            avisos.append(f"Linha {n} ignorada (sem ':'): {linha.strip()[:40]!r}")
            continue
        chave_bruta, valor = linha.split(":", 1)
        chave = _ALIASES.get(normalizar_chave(chave_bruta))
        if chave is None:
            avisos.append(f"Campo desconhecido ignorado: {chave_bruta.strip()!r}")
            continue
        if chave == "titulo" and any(c == "titulo" for c, _ in pares):
            blocos.append((pares, avisos))
            pares, avisos = [], []
        pares.append((chave, limpar_valor(valor)))
    if pares or not blocos:
        blocos.append((pares, avisos))
    return blocos


def _montar(pares: list[tuple[str, str]], avisos: list[str]) -> ResultadoLeitura:
    campos = dict(pares)  # se repetir a chave, vale a última
    problemas = [
        f"Campo obrigatório ausente: {rotulo}."
        for chave, rotulo in _OBRIGATORIOS.items()
        if not campos.get(chave)
    ]

    def numero(chave: str, rotulo: str, padrao=None):
        bruto = campos.get(chave)
        if bruto in (None, ""):
            return padrao
        try:
            return parse_decimal(bruto)
        except ValueError:
            problemas.append(f"{rotulo}: valor numérico inválido ({bruto!r}).")
            return padrao

    perimetro = numero("perimetro", "Perímetro costura")
    pontos = numero("pontos_cm", "Pontos/cm", padrao=None)
    if pontos is None:
        avisos.append("Pontos/cm não informado; usando 0 (campo apenas informativo).")
        from decimal import Decimal

        pontos = Decimal(0)

    elementos: list[str] = []
    for token in re.split(r"[;,\s]+", campos.get("elementos", "")):
        if not token:
            continue
        if _CODIGO_MTM.fullmatch(token):
            elementos.append(token)
        else:
            problemas.append(
                f"Código de elemento inválido: {token!r} (use o formato 2.1, 1.1, 3.1)."
            )

    if problemas:
        titulo = campos.get("titulo", "?")
        raise ValidacaoErro([f"[{titulo}] {p}" for p in problemas])

    demanda = Demanda(
        titulo=campos["titulo"],
        rev=campos.get("rev", "00"),
        operacao=campos["operacao"],
        familia=campos.get("familia", ""),
        tamanho=campos.get("tamanho", ""),
        medidas=campos.get("medidas", ""),
        pontos_cm=pontos,
        perimetro_m=perimetro,
        cod_equipamento=re.sub(r"\.0+$", "", campos["equipamento"]),
        elementos=tuple(elementos),
    )
    return ResultadoLeitura(demanda, tuple(avisos))


def ler_demandas_txt(texto: str) -> list[ResultadoLeitura]:
    """Lê um ou mais blocos de demanda do texto."""
    return [_montar(p, a) for p, a in _dividir_blocos(texto)]


def ler_demanda_txt(texto: str) -> ResultadoLeitura:
    """Lê exatamente uma demanda (a primeira, se houver várias)."""
    return ler_demandas_txt(texto)[0]
