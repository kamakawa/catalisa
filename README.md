# Auto-T&M — Gerador de Ficha de Processo Operacional (PO)

Hackathon Auto-T&M Karsten. Lê os cadastros (Matriz MTM e Máquinas) e uma demanda
de operação, calcula os tempos e gera a ficha PO.

## Estado atual (núcleo pronto)
- `app/domain` — regras de T&M (FIXO, TP, limites de RPM), sem dependências externas
- `app/adapters/input` — parser tolerante do `demanda_*.txt`, leitor de `.ods`/`.xlsx`, carga dos catálogos
- `app/cli.py` — uso rápido no terminal
- `tests/` — 29 testes (o teste do kit oficial roda com `KIT_DIR`)

## Como executar
```bash
pip install -r requirements.txt
python -m app.cli CATALOGOS.ods samples/demanda_exemplo.txt   # veja a ficha no terminal
pytest -q                                                      # testes
KIT_DIR=/caminho/do/kit pytest -q                              # inclui comparação com o gabarito oficial
```

## Regras de cálculo adotadas
| Item | Regra |
|---|---|
| FIXO | `perímetro (m) × tempo/metro`, arredondado a 4 casas (ROUND_HALF_UP) |
| Elementos MTM | descrição e tempo buscados pelo código na matriz, na ordem informada |
| TP | soma das linhas **já arredondadas** (auditável) |
| RPM | inferior = padrão × 0,9; superior = padrão × 1,1 (fórmula do gabarito) |
| Precisão | `Decimal` em todo o cálculo, nunca `float` |

## Pendências a confirmar com a organização
1. O gabarito não tem linha de TP; a ficha gerada inclui.
2. Pontos/cm e RPM são informativos (não entram no FIXO).
3. A coluna "Frequência" é sempre 1 no exemplo; o modelo já a suporta.
