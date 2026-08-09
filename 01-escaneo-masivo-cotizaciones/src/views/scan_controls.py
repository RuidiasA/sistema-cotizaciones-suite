"""Panel de Controles de Escaneo y Filtros.

Contiene los botones de selección de carpeta, menús desplegables de categoría,
campo de palabra clave y acciones para iniciar/cancelar escaneos o exportar.

Principios aplicados:
    - Single Responsibility (SRP): Exclusivamente responsable de capturar los comandos del usuario.
    - Defensive Programming: Valida rutas existentes en disco antes de enviar peticiones al controlador.
"""

import os
from tkinter import filedialog
from typing import Callable, List
import customtkinter as ctk


class ScanControls(ctk.CTkFrame):
    """Componente lateral con los botones de acción y parámetros de escaneo."""

    def __init__(
        self,
        master: object,
        categories: List[str],
        default_folder: str,
        controller: object,
        on_scan: Callable[[str, str, str], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Inicializa los controles del panel lateral.

        Args:
            master: Contenedor padre.
            categories: Lista de categorías disponibles.
            default_folder: Ubicación inicial por defecto.
            controller: Instancia del AppController.
            on_scan: Callback de inicio de escaneo.
            on_cancel: Callback de cancelación.
        """
        super().__init__(master, fg_color="#d9d9d9", corner_radius=0)
        self._controller = controller
        self._on_scan = on_scan
        self._on_cancel = on_cancel
        self._is_scanning = False
        self._is_benchmarking = False

        # --- SECCIÓN: CARPETA ---
        self._section_folder = ctk.CTkLabel(
            self, text="📁 UBICACIÓN DE DATOS", font=ctk.CTkFont(size=11, weight="bold"), text_color="#555555"
        )
        self._section_folder.pack(anchor="w", padx=15, pady=(20, 5))

        self._folder_entry = ctk.CTkEntry(self, placeholder_text="Ruta del Excel...", height=35)
        self._folder_entry.insert(0, default_folder)
        self._folder_entry.pack(fill="x", padx=15, pady=5)

        self._browse_button = ctk.CTkButton(
            self, text="Cambiar Carpeta", command=self._browse, fg_color="#7f8c8d", hover_color="#95a5a6"
        )
        self._browse_button.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(self, text="", height=1).pack(pady=10)

        # --- SECCIÓN: FILTROS ---
        self._section_filter = ctk.CTkLabel(
            self, text="🔍 FILTROS DE BÚSQUEDA", font=ctk.CTkFont(size=11, weight="bold"), text_color="#555555"
        )
        self._section_filter.pack(anchor="w", padx=15, pady=(0, 5))

        self._category_menu = ctk.CTkOptionMenu(
            self,
            values=["Todas"] + categories,
            fg_color="#e67e22",
            button_color="#d35400",
            button_hover_color="#e67e22",
            height=35,
            command=self._handle_category_change,
        )
        self._category_menu.set("Todas")
        self._category_menu.pack(fill="x", padx=15, pady=5)

        self._keyword_entry = ctk.CTkEntry(self, placeholder_text="Palabra clave (ej. casaca)...", height=35)
        self._keyword_entry.pack(fill="x", padx=15, pady=5)

        # --- BOTONES DE ACCIÓN ---
        self._scan_button = ctk.CTkButton(
            self,
            text="INICIAR ESCANEO",
            command=self._handle_scan,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#e67e22",
            hover_color="#d35400",
            height=45,
        )
        self._scan_button.pack(fill="x", padx=15, pady=(20, 5))

        self._cancel_button = ctk.CTkButton(
            self,
            text="CANCELAR ESCANEO",
            command=self._on_cancel,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#A02020",
            hover_color="#601010",
            height=35,
            state="disabled",
        )
        self._cancel_button.pack(fill="x", padx=15, pady=5)

        self._benchmarking_button = ctk.CTkButton(
            self,
            text="📊 Generar Benchmarking",
            command=self._handle_benchmarking,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2c3e50",
            hover_color="#34495e",
            height=38,
        )
        self._benchmarking_button.pack(fill="x", padx=15, pady=(12, 5))

        self._export_button = ctk.CTkButton(
            self,
            text="📥 Exportar Excel",
            command=self._handle_export,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#e67e22",
            hover_color="#d35400",
            height=35,
            state="disabled",
        )
        self._export_button.pack(fill="x", padx=15, pady=5)

        # --- ETIQUETA DE ESTADO ---
        self._status_label = ctk.CTkLabel(
            self, text="● Sistema Listo", font=ctk.CTkFont(size=16, slant="italic"), text_color="#27ae60"
        )
        self._status_label.pack(side="bottom", pady=5)

    def set_scanning_state(self, is_scanning: bool) -> None:
        """Ajusta el estado de los botones durante un escaneo activo."""
        self._is_scanning = is_scanning

        if is_scanning:
            self._scan_button.configure(state="disabled", text="ESCANEANDO...")
            self._cancel_button.configure(state="normal")
            self._browse_button.configure(state="disabled")
            self._benchmarking_button.configure(state="disabled")
            self._export_button.configure(state="disabled")
            return

        self._scan_button.configure(state="normal", text="INICIAR ESCANEO")
        self._cancel_button.configure(state="disabled")
        self._browse_button.configure(state="normal")
        self._benchmarking_button.configure(state="normal")

        if self._is_benchmarking:
            self._benchmarking_button.configure(state="disabled", text="📊 Generando...")
            self._scan_button.configure(state="disabled", text="PROCESANDO...")
            self._browse_button.configure(state="disabled")
            self._export_button.configure(state="disabled")

    def set_benchmarking_state(self, is_benchmarking: bool) -> None:
        """Ajusta el estado de los botones durante la generación de benchmarking."""
        self._is_benchmarking = is_benchmarking
        if is_benchmarking:
            self._benchmarking_button.configure(state="disabled", text="📊 Generando...")
            self._scan_button.configure(state="disabled", text="PROCESANDO...")
            self._browse_button.configure(state="disabled")
            self._cancel_button.configure(state="disabled")
            self._export_button.configure(state="disabled")
            return

        self._benchmarking_button.configure(state="normal", text="📊 Generar Benchmarking")
        if not self._is_scanning:
            self._scan_button.configure(state="normal", text="INICIAR ESCANEO")
            self._browse_button.configure(state="normal")
            self._cancel_button.configure(state="disabled")

    def enable_export(self, enabled: bool) -> None:
        """Habilita o deshabilita el botón de exportación."""
        state = "normal" if enabled else "disabled"
        self._export_button.configure(state=state)

    def _browse(self) -> None:
        """Abre un diálogo nativo para seleccionar el directorio de datos."""
        folder = filedialog.askdirectory()
        if folder:
            self._folder_entry.delete(0, "end")
            self._folder_entry.insert(0, folder)

    def _handle_scan(self) -> None:
        """Valida el directorio e inicia la tarea de escaneo."""
        folder = self._folder_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            self.set_status("Error: Carpeta inválida")
            return

        categoria = self._category_menu.get()
        if categoria == "Todas":
            categoria = ""
        keyword = self._keyword_entry.get().strip()
        self._on_scan(folder, categoria, keyword)

    def _handle_benchmarking(self) -> None:
        """Dispara la generación de benchmarking para la categoría actual."""
        categoria = self._category_menu.get()
        if categoria == "Todas":
            categoria = ""
        self._controller.handle_benchmarking(categoria)

    def _handle_category_change(self, categoria: str) -> None:
        """Responde a cambios en la categoría del desplegable."""
        if self._is_scanning or self._is_benchmarking:
            return
        if not hasattr(self._controller, "has_scan_data") or not self._controller.has_scan_data():
            return

        cat_clean = "" if categoria == "Todas" else categoria
        self._controller.handle_benchmarking(cat_clean)

    def _handle_export(self) -> None:
        """Dispara la exportación de la matriz de benchmarking."""
        folder_path = self._folder_entry.get().strip()
        if not folder_path or not os.path.isdir(folder_path):
            self.set_status("Error: Carpeta de destino inválida")
            return
        self._controller.handle_export_benchmarking(folder_path)

    def set_status(self, text: str) -> None:
        """Actualiza el texto del indicador de estado.

        Args:
            text: Mensaje a mostrar.
        """
        color = "#e67e22" if "Error" in text else "#27ae60"
        self._status_label.configure(text=f"● {text}", text_color=color)