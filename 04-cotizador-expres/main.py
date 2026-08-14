import sys
import os
import tkinter as tk

# Aseguramos la ruta del proyecto en PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.controllers.app_controller import AppController
from src.views.cotizador_view import CotizadorView


def main():
    root = tk.Tk()
    root.title("Cotizador Exprès 2026 — COMPIPRO")

    # Centramos la ventana en pantalla
    window_width = 850
    window_height = 480
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_coor = (screen_width // 2) - (window_width // 2)
    y_coor = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x_coor}+{y_coor}")
    root.resizable(False, False)

    # Inicialización MVC
    controller = AppController(root)
    view = CotizadorView(root, controller)
    controller.set_view(view)

    print("==================================================")
    print("COTIZADOR EXPRÉS 2026 INICIALIZADO CORRECTAMENTE")
    print("==================================================")

    root.mainloop()


if __name__ == "__main__":
    main()