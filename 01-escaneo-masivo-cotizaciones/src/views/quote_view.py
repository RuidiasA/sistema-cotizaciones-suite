"""Vista de la Calculadora Rápida de Cotizaciones.

Captura datos de entrada (Producto, Cantidad, Costo Proveedor) y proporciona
un mecanismo ágil de disparo con teclado o ratón.

Principios aplicados:
    - Single Responsibility (SRP): Exclusivamente responsable de los inputs de cotización rápida.
    - User Experience (UX): Retroalimentación visual inmediata ante errores de tipeo.
"""

from typing import Callable
import customtkinter as ctk


class QuoteView(ctk.CTkFrame):
    """Componente de UI para el cálculo ágil de cotizaciones en la barra lateral."""

    def __init__(
        self,
        master: object,
        on_quote: Callable[[str, int, float], None],
        on_clear: Callable[[], None] = None,
    ) -> None:
        """Inicializa los campos de entrada y botones.

        Args:
            master: Contenedor padre.
            on_quote: Callback ejecutado al cotizar.
            on_clear: Callback ejecutado al limpiar el formulario.
        """
        super().__init__(master, fg_color="#ffffff", corner_radius=15)
        self._on_quote = on_quote
        self._on_clear = on_clear or (lambda: None)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure((1, 2, 3), weight=0)

        # Título y botón limpiar
        self._title = ctk.CTkLabel(
            self,
            text="⚡ Calculadora Rápida",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#e67e22",
        )
        self._title.grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 5), sticky="w")

        self._clear_button = ctk.CTkButton(
            self,
            text="🗑",
            command=self._handle_clear,
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            width=35,
            height=32,
            font=ctk.CTkFont(size=14),
        )
        self._clear_button.grid(row=0, column=3, padx=(5, 15), pady=(15, 5), sticky="e")

        # Entradas de datos
        self._producto_entry = ctk.CTkEntry(self, placeholder_text="Producto...", height=32)
        self._producto_entry.grid(row=1, column=0, padx=(15, 5), pady=10, sticky="ew")

        self._cantidad_entry = ctk.CTkEntry(self, placeholder_text="Cant.", width=55, height=32)
        self._cantidad_entry.grid(row=1, column=1, padx=5, pady=10)

        self._precio_entry = ctk.CTkEntry(self, placeholder_text="Costo S/.", width=85, height=32)
        self._precio_entry.grid(row=1, column=2, padx=5, pady=10)

        # Vincular la tecla Enter a la acción de cotizar
        self._producto_entry.bind("<Return>", lambda event: self._handle_quote())
        self._cantidad_entry.bind("<Return>", lambda event: self._handle_quote())
        self._precio_entry.bind("<Return>", lambda event: self._handle_quote())

        # Botón Ok
        self._quote_button = ctk.CTkButton(
            self,
            text="Ok",
            command=self._handle_quote,
            fg_color="#e67e22",
            hover_color="#d35400",
            width=45,
            height=32,
        )
        self._quote_button.grid(row=1, column=3, padx=(5, 15), pady=10)

    def _handle_quote(self) -> None:
        """Captura los datos, valida tipos numéricos y dispara el callback."""
        # Restablecer bordes normales
        self._cantidad_entry.configure(border_color="#979da2")
        self._precio_entry.configure(border_color="#979da2")

        prod = self._producto_entry.get().strip()
        cant_text = self._cantidad_entry.get().strip()
        prec_text = self._precio_entry.get().strip()

        if not cant_text or not prec_text:
            if not cant_text:
                self._cantidad_entry.configure(border_color="#e74c3c")
            if not prec_text:
                self._precio_entry.configure(border_color="#e74c3c")
            return

        try:
            cant = int(cant_text)
            if cant <= 0:
                self._cantidad_entry.configure(border_color="#e74c3c")
                return
        except ValueError:
            self._cantidad_entry.configure(border_color="#e74c3c")
            return

        try:
            prec = float(prec_text)
            if prec <= 0:
                self._precio_entry.configure(border_color="#e74c3c")
                return
        except ValueError:
            self._precio_entry.configure(border_color="#e74c3c")
            return

        self._on_quote(prod, cant, prec)

    def _handle_clear(self) -> None:
        """Limpia los campos y restablece el estilo predeterminado."""
        self._producto_entry.delete(0, "end")
        self._cantidad_entry.delete(0, "end")
        self._precio_entry.delete(0, "end")
        self._cantidad_entry.configure(border_color="#979da2")
        self._precio_entry.configure(border_color="#979da2")
        self._on_clear()

    def show_result(self, result: dict, known_product: bool) -> None:
        """Método de interfaz para actualizar la vista tras la cotización."""
        pass