"""Punto de Entrada Principal de la Suite de Cotizaciones.

Inicializa e invoca el ciclo de vida del AppController para lanzar la interfaz de usuario.

Principios aplicados:
    - Single Responsibility (SRP): Exclusivamente responsable del arranque de la aplicación.
"""

import sys
from src.controllers.app_controller import AppController


def main() -> None:
    """Punto de entrada principal de la aplicación."""
    try:
        app = AppController()
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()