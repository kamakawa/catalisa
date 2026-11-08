"""Uso rápido no terminal:

    python -m app.cli CATALOGOS.ods DEMANDA.txt [DEMANDA2.txt ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

from app.adapters.input.catalogos import carregar_catalogos
from app.adapters.input.demanda_txt import decodificar, ler_demandas_txt
from app.domain.calculo import gerar_ficha
from app.domain.erros import ValidacaoErro


def _br(valor) -> str:
    return format(valor.normalize(), "f").replace(".", ",")


def formatar_ficha(f) -> str:
    d = f.demanda
    out = [
        f"{d.titulo}  (Rev. {d.rev})",
        f"Operação: {d.operacao}",
        f"Família: {d.familia} | Tamanho: {d.tamanho} | Medidas: {d.medidas} | "
        f"Pontos/cm: {_br(d.pontos_cm)} | Perímetro: {_br(d.perimetro_m)} m",
        f"Equip.: {f.maquina.codigo} - {f.maquina.tipo} ({f.maquina.descricao}) | "
        f"RPM {_br(f.rpm_inferior)} / {_br(f.rpm_padrao)} / {_br(f.rpm_superior)}",
        "-" * 70,
    ]
    for l in f.linhas:
        out.append(f"{l.codigo:<6} {l.descricao:<45} {l.frequencia:>2}  {_br(l.tempo):>8}")
    out += ["-" * 70, f"{'TP (min)':<54} {_br(f.tp):>8}"]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cat = carregar_catalogos(argv[0])
    codigo_saida = 0
    for arq in argv[1:]:
        try:
            for r in ler_demandas_txt(decodificar(Path(arq).read_bytes())):
                for aviso in r.avisos:
                    print(f"[aviso] {aviso}")
                print(formatar_ficha(gerar_ficha(r.demanda, cat.elementos, cat.maquinas)))
                print()
        except ValidacaoErro as e:
            codigo_saida = 1
            print(f"[erro] {arq}:")
            for p in e.problemas:
                print(f"  - {p}")
    return codigo_saida


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
