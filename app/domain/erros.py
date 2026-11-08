"""Erros do domínio, com mensagens pensadas para o usuário final."""
from __future__ import annotations


class ValidacaoErro(Exception):
    """Um ou mais problemas nos dados. Guarda todos, não só o primeiro."""

    def __init__(self, problemas: list[str]):
        self.problemas = list(problemas)
        super().__init__("; ".join(self.problemas))
