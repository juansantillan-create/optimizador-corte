"""Los tests no usan los ajustes locales de la PC (config/local/materiales.json). Si un test usa
una carpeta de configuración propia (temporal), ahí sí se usan."""

import pytest

from optimizador import configuracion


@pytest.fixture(autouse=True)
def sin_ajustes_locales(monkeypatch):
    original = configuracion.Catalogo.ajustes_locales

    def ajustes(self):
        if self.carpeta.resolve() == configuracion.CARPETA_CONFIG.resolve():
            return {}
        return original(self)

    monkeypatch.setattr(configuracion.Catalogo, "ajustes_locales", ajustes)
