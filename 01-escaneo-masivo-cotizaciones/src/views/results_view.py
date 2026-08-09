"""Vista de Resultados, Tabla de Filas y Tarjetas KPI.

Muestra los datos extraídos en una tabla Treeview de Tkinter con alternancia de
colores por grupos, renderiza tarjetas KPI superiores y mantiene una consola compacta.

Principios aplicados:
    - Single Responsibility (SRP): Presentación de resultados y métricas.
    - DRY: Inserción limpia de filas en la tabla sin iteraciones duplicadas.
"""

import re
from tkinter import ttk
from typing import Iterable, List, Optional
import customtkinter as ctk

from ..models.entities import ScanRow


class ResultsView(ctk.CTkFrame):
    """Contenedor de resultados principales, tabla comparativa y métricas KPI."""

    def __init__(self, master: object) -> None:
        """Inicializa los componentes visuales de la vista de resultados.

        Args:
            master: Contenedor padre.
        """
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Tarjetas KPI
        self._kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._kpi_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self._card_margen = self._create_kpi_card(self._kpi_frame, "Margen", 0, "0.00%")
        self._card_precio_unit = self._create_kpi_card(self._kpi_frame, "Precio Unitario", 1, "S/. 0.00")
        self._card_total = self._create_kpi_card(self._kpi_frame, "Precio Total", 2, "S/. 0.00")

        # 2. Contenedor de Tabla
        self._table_container = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12, border_width=1, border_color="#bdc3c7")
        self._table_container.grid(row=1, column=0, sticky="nsew")
        self._table_container.grid_columnconfigure(0, weight=1)
        self._table_container.grid_rowconfigure(0, weight=1)

        self._setup_table_style()

        columns = ("fila", "articulo", "cantidad", "prov", "cli", "margen")
        self._table = ttk.Treeview(self._table_container, columns=columns, show="headings")

        # Configuración de Columnas
        self._table.heading("fila", text="CASOS")
        self._table.column("fila", width=60, minwidth=60, stretch=False, anchor="center")

        self._table.heading("articulo", text="ARTÍCULO / DETALLE")
        self._table.column("articulo", width=280, minwidth=200, stretch=True)

        self._table.heading("cantidad", text="CANT.")
        self._table.column("cantidad", width=70, minwidth=70, stretch=False, anchor="center")

        self._table.heading("prov", text="COSTO PROV.")
        self._table.column("prov", width=100, minwidth=100, stretch=False, anchor="center")

        self._table.heading("cli", text="PRECIO CLI.")
        self._table.column("cli", width=100, minwidth=100, stretch=False, anchor="center")

        self._table.heading("margen", text="MARGEN %")
        self._table.column("margen", width=90, minwidth=90, stretch=False, anchor="center")

        # Scrollbar Personalizada
        self._scrollbar = ctk.CTkScrollbar(
            self._table_container,
            orientation="vertical",
            command=self._table.yview,
            width=16,
            fg_color="transparent",
            button_color="#e67e22",
            button_hover_color="#d35400",
            corner_radius=10,
        )

        self._table.configure(yscrollcommand=self._scrollbar.set)
        self._table.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        self._scrollbar.grid(row=0, column=1, sticky="ns", padx=(2, 5), pady=15)

        # Tags de alternancia de color
        self._table.tag_configure("group_white", background="#ffffff", foreground="#2c3e50")
        self._table.tag_configure("group_gray", background="#FFCAAD", foreground="#2c3e50")

        self._group_size = 1
        self._row_batch_size = 250
        self._row_insert_job: Optional[str] = None
        self._pending_rows: List[ScanRow] = []
        self._pending_row_offset = 0

        # Consola de Logs
        self._log = ctk.CTkTextbox(self, height=100, fg_color="#ffffff", border_color="#bdc3c7", border_width=1, font=("Consolas", 11))
        self._log.grid(row=2, column=0, sticky="ew", pady=(20, 0))

    def _create_kpi_card(self, master: object, title: str, col: int, format_text: str = "0.00%") -> ctk.CTkLabel:
        card = ctk.CTkFrame(master, fg_color="#ffffff", corner_radius=12, border_width=1, border_color="#bdc3c7")
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        master.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(card, text=title, text_color="#7f8c8d", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(15, 0))
        val = ctk.CTkLabel(card, text=format_text, text_color="#e67e22", font=ctk.CTkFont(size=26, weight="bold"))
        val.pack(pady=(0, 15))
        return val

    def _setup_table_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#ffffff",
            foreground="#2c3e50",
            rowheight=35,
            fieldbackground="#ffffff",
            borderwidth=0,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Treeview.Heading",
            background="#e67e22",
            foreground="#ffffff",
            relief="flat",
            padding=5,
            font=("Segoe UI", 10, "bold"),
        )

        style.map("Treeview.Heading", background=[("active", "#d35400")], foreground=[("active", "#ffffff")])
        style.map("Treeview", background=[("selected", "#e67e22")], foreground=[("selected", "#ffffff")])

    def clear(self) -> None:
        """Limpia las entradas de la consola, la tabla y restablece los KPI."""
        self._cancel_pending_row_render()
        self._log.delete("1.0", "end")
        for item in self._table.get_children():
            self._table.delete(item)
        self.update_quote_cards(0.0, 0.0, 0.0)

    def append_log(self, text: str) -> None:
        """Añade un mensaje a la consola de logs.

        Args:
            text: Mensaje a registrar.
        """
        self._log.insert("end", f" {text}\n")
        self._log.see("end")

    def add_rows(self, rows: Iterable[ScanRow]) -> None:
        """Inserta un lote de filas en la tabla aplicando el tag de grupo.

        Args:
            rows: Colección de ScanRow a insertar.
        """
        self._cancel_pending_row_render()
        self._pending_rows = list(rows)
        self._pending_row_offset = 0
        if not self._pending_rows:
            return
        self._render_next_row_batch()

    def _cancel_pending_row_render(self) -> None:
        if self._row_insert_job is not None:
            try:
                self.after_cancel(self._row_insert_job)
            except Exception:
                pass
            self._row_insert_job = None
        self._pending_rows = []
        self._pending_row_offset = 0

    def _render_next_row_batch(self) -> None:
        batch_end = min(self._pending_row_offset + self._row_batch_size, len(self._pending_rows))
        for i in range(self._pending_row_offset, batch_end):
            row = self._pending_rows[i]
            group = (i % 2) if self._group_size <= 1 else ((i // self._group_size) % 2)
            tag = "group_gray" if group == 1 else "group_white"

            self._table.insert(
                "",
                "end",
                values=(
                    row.fila_id,
                    row.articulo,
                    row.cantidad,
                    f"S/. {row.precio_prov:.2f}",
                    f"S/. {row.precio_cli:.2f}",
                    f"{row.margen:.2f}%",
                ),
                tags=(tag,),
            )

        self._pending_row_offset = batch_end
        if self._pending_row_offset < len(self._pending_rows):
            self._row_insert_job = self.after(1, self._render_next_row_batch)
        else:
            self._row_insert_job = None
            self._pending_rows = []

    def set_group_size(self, size: int) -> None:
        """Configura la cantidad de filas consecutivas por bloque de color.

        Args:
            size: Tamaño del grupo (1 = fila a fila, 3 = cada 3 filas).
        """
        try:
            self._group_size = max(1, int(size))
            self._table.update_idletasks()
        except Exception:
            self._group_size = 1

    def set_stats_text(self, text: str) -> None:
        """Parsea la cadena de estadísticas actualizando los KPI superiores.

        Args:
            text: Texto formateado del acumulador.
        """
        try:
            matches = re.findall(r"(\d+(?:\.\d+)?)%", text)
            if len(matches) >= 3:
                self._card_margen.configure(text=f"{float(matches[0]):.2f}%")
                self._card_precio_unit.configure(text=f"{float(matches[1]):.2f}%")
                self._card_total.configure(text=f"{float(matches[2]):.2f}%")
        except Exception:
            pass

    def update_quote_cards(self, margen: float, precio_unit: float, total: float) -> None:
        """Actualiza el valor de las tarjetas KPI con los resultados de cotización.

        Args:
            margen: Porcentaje de margen.
            precio_unit: Precio unitario.
            total: Precio total.
        """
        self._card_margen.configure(text=f"{margen:.2f}%")
        self._card_precio_unit.configure(text=f"S/. {precio_unit:.2f}")
        self._card_total.configure(text=f"S/. {total:.2f}")