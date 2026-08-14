import os
import sys
import tkinter as tk
from pathlib import Path

# Inyección del directorio raíz del módulo en sys.path para importaciones relativas
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.controllers.app_controller import AppController
from src.views.cotizador_view import CotizadorView


def main() -> None:
    """Punto de entrada principal para el Cotizador Exprés (COMPIPRO).

    Configura la ventana principal de Tkinter, aplica el centrado en pantalla,
    inicializa el patrón de diseño MVC y ejecuta el ciclo principal de eventos.
    """
    root = tk.Tk()
    root.title("Cotizador Exprés 2026 — COMPIPRO")

    window_width = 850
    window_height = 480
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_coord = (screen_width // 2) - (window_width // 2)
    y_coord = (screen_height // 2) - (window_height // 2)

    root.geometry(f"{window_width}x{window_height}+{x_coord}+{y_coord}")
    root.resizable(False, False)

    controller = AppController(root)
    view = CotizadorView(root, controller)
    controller.set_view(view)

    print("==================================================")
    print("COTIZADOR EXPRÉS 2026 INICIALIZADO CORRECTAMENTE")
    print("==================================================")

    root.mainloop()


if __name__ == "__main__":
    main()