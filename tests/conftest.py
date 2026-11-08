from decimal import Decimal as D

import pytest

from app.domain.models import Elemento, Maquina


@pytest.fixture
def elementos():
    """Catálogo de teste PRÓPRIO (valores inventados, não é o kit oficial)."""
    return {
        "1.1": Elemento("1.1", "Costurar elemento (sem tempo)", D("0")),
        "2.1": Elemento("2.1", "Apanhar peça", D("0.2")),
        "3.1": Elemento("3.1", "Ajeitar peça", D("0.1")),
    }


@pytest.fixture
def maquinas():
    return {
        "1": Maquina("1", "Interlock", "Modelo X", D("4000"), D("0.1")),
        "2": Maquina("2", "Reta", "Modelo Y", D("5000"), D("0.0805")),
    }
