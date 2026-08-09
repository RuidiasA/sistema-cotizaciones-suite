"""Vista Principal de la Aplicación (Contenedor Raíz).

Ensambla la barra lateral (ScanControls + QuoteView) y la zona central
de contenido (ResultsView), actuando como fachada de comunicación entre la UI
y el AppController.

Principios aplicados:
    - Single Responsibility (SRP): Exclusivamente responsable del layout principal de Tkinter.
    - Information Exposure: Oculta la estructura interna de las sub-vistas usando métodos públicos.
"""

from typing import Callable, List
import customtkinter as ctk

from .quote_view import QuoteView
from .results_view import ResultsView
from .scan_controls import ScanControls

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class MainView(ctk.CTk):
    """Ventana principal de CustomTkinter para la gestión de cotizaciones."""

    def __init__(
        self,
        controller: object,
        categories: List[str],
        default_folder: str,
        on_scan: Callable[[str, str, str], None],
        on_quote: Callable[[str, int, float], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Inicializa la ventana principal y sus componentes hijos.

        Args:
            controller: Instancia del AppController.
            categories: Listado de categorías registradas.
            default_folder: Ruta por defecto de la carpeta de trabajo.
            on_scan: Callback para iniciar el escaneo.
            on_quote: Callback para ejecutar la cotización rápida.
            on_cancel: Callback para solicitar la parada del escaneo.
        """
        super().__init__()

        self.title("Gestión de Cotizaciones")
        self.after(0, lambda: self.state("zoomed"))
        self.configure(fg_color="#cccccc")

        # Configuración de Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR LATERAL ---
        self._sidebar = ctk.CTkFrame(self, width=300, fg_color="#d9d9d9", corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)

        # Controles de Búsqueda
        self._controls = ScanControls(
            self._sidebar,
            categories,
            default_folder,
            controller,
            on_scan,
            on_cancel,
        )
        self._controls.pack(fill="x", padx=15)

        # Calculadora Rápida
        self._quote = QuoteView(self._sidebar, on_quote, on_clear=self.clear_quote_cards)
        self._quote.pack(fill="x", padx=15, pady=10)

        # --- ÁREA DE CONTENIDO ---
        self._results = ResultsView(self)
        self._results.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")

    # --- MÉTODOS DE FACHADA Y COMUNICACIÓN ---

    def set_scanning_state(self, is_scanning: bool) -> None:
        """Propaga el estado de escaneo a la UI ajustando el grupo alternado a 1.

        Args:
            is_scanning: True si el motor está escaneando.
        """
        self._controls.set_scanning_state(is_scanning)
        if is_scanning:
            self._results.set_group_size(1)

    def set_benchmarking_state(self, is_benchmarking: bool) -> None:
        """Propaga el estado de benchmarking ajustando el grupo alternado a 3.

        Args:
            is_benchmarking: True si se está generando benchmarking.
        """
        self._controls.set_benchmarking_state(is_benchmarking)
        if is_benchmarking:
            self._results.set_group_size(3)

    def enable_export(self, enabled: bool) -> None:
        """Habilita o deshabilita el botón de exportación a Excel."""
        self._controls.enable_export(enabled)

    def set_status(self, text: str) -> None:
        """Actualiza el texto de estado en el panel de controles."""
        self._controls.set_status(text)

    def clear_results(self) -> None:
        """Limpia la tabla, las tarjetas KPI y la consola de logs."""
        self._results.clear()

    def clear_quote_cards(self) -> None:
        """Restablece los valores de las tarjetas KPI a cero mediante su API pública."""
        self._results.update_quote_cards(0.0, 0.0, 0.0)

    def append_log(self, text: str) -> None:
        """Añade una línea de mensaje a la consola de logs."""
        self._results.append_log(text)

    def add_rows(self, rows: object) -> None:
        """Agrega filas de resultados a la tabla principal."""
        self._results.add_rows(rows)

    def set_stats_text(self, text: str) -> None:
        """Actualiza las estadísticas del pie de la tabla."""
        self._results.set_stats_text(text)

    def show_quote_result(self, res: dict, known: bool) -> None:
        """Envía el resultado de cotización rápida a la vista de cálculo."""
        self._quote.show_result(res, known)

    def update_quote_cards(self, margen: float, precio_unit: float, total: float) -> None:
        """Actualiza las tarjetas de resultados en el panel principal.

        Args:
            margen: Porcentaje de margen aplicado.
            precio_unit: Precio de venta unitario.
            total: Precio total calculado.
        """
        self._results.update_quote_cards(margen, precio_unit, total)