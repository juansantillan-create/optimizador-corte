"""Los tests no usan los ajustes locales de la PC (config/local/materiales.json)."""

import pytest

from optimizador import configuracion


@pytest.fixture(autouse=True)
def sin_ajustes_locales(monkeypatch):
    monkeypatch.setattr(configuracion.Catalogo, "ajustes_locales", lambda self: {})
