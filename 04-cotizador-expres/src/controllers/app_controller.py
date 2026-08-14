import os
import threading
from pathlib import Path
from tkinter import messagebox
from typing import Any, Dict, List, Optional

from src.services.data_engine import DataEngine
from src.services.excel_exporter import ExcelExporter


class AppController:
    """Controlador principal del patrón MVC para el módulo de Cotizador Exprés.

    Orquesta el flujo de interacción entre la interfaz gráfica (Tkinter)
    y los servicios de cálculo/exportación, gestionando la concurrencia
    en segundo plano para preservar la responsividad de la UI.
    """

    def __init__(self, root: Any) -> None:
        """Inicializa el controlador y sus servicios dependientes.

        Args:
            root: Ventana raíz de Tkinter para la sincronización de hilos (Event Loop).
        """
        self.root = root
        self.view: Optional[Any] = None

        self.data_engine: DataEngine = DataEngine()
        self.excel_exporter: ExcelExporter = ExcelExporter()
        self.categorias_map: Dict[str, str] = self.data_engine.get_categorias()

    def set_view(self, view: Any) -> None:
        """Vincula la instancia de la vista al controlador."""
        self.view = view

    def obtener_categorias_disponibles(self) -> Dict[str, str]:
        """Retorna el mapeo de nombres comerciales a claves de arquetipo."""
        return self.categorias_map

    def obtener_subproductos_por_categoria(self, nombre_categoria_comercial: str) -> List[str]:
        """Obtiene la lista de subproductos asociados a una categoría comercial.

        Args:
            nombre_categoria_comercial: Etiqueta visible de la categoría en la UI.

        Returns:
            Lista de nombres de subproductos disponibles o fallback predeterminado.
        """
        cat_key = self.categorias_map.get(nombre_categoria_comercial)
        if not cat_key:
            return ["Todos (Categoría Completa)"]
        return self.data_engine.get_subproductos(cat_key)

    def procesar_cotizacion_asincrona(self, pedidos_raw: List[Dict[str, Any]]) -> None:
        """Inicia el procesamiento de la cotización en un hilo secundario tipo daemon.

        Args:
            pedidos_raw: Lista de diccionarios con los parámetros de entrada de la UI.
        """
        if self.view:
            self.view.set_loading_state(True, "Buscando en datasets prioritarios y calculando márgenes...")

        worker = threading.Thread(
            target=self._worker_procesar,
            args=(pedidos_raw,),
            daemon=True
        )
        worker.start()

    def _worker_procesar(self, pedidos_raw: List[Dict[str, Any]]) -> None:
        """Ejecuta la búsqueda jerárquica y generación del archivo Excel fuera del Main Thread.

        Args:
            pedidos_raw: Parámetros brutos extraídos desde la vista.
        """
        try:
            bloques_productos: List[Dict[str, Any]] = []

            for item in pedidos_raw:
                cat_nombre = item["categoria_nombre"]
                subproducto = item["subproducto"]
                cantidad = item["cantidad"]

                cat_key = self.categorias_map.get(cat_nombre)
                if not cat_key:
                    continue

                opciones = self.data_engine.buscar_opciones_proveedores(
                    cat_key=cat_key,
                    cantidad_solicitada=cantidad,
                    subproducto_nombre=subproducto
                )

                prod_nombre = (
                    subproducto
                    if subproducto != "Todos (Categoría Completa)"
                    else cat_nombre
                )

                bloques_productos.append({
                    "producto_nombre": prod_nombre,
                    "cantidad": cantidad,
                    "opciones": opciones
                })

            if not any(bloque["opciones"] for bloque in bloques_productos):
                raise ValueError("No se encontraron coincidencias de proveedores en los datasets configurados.")

            archivo_excel = self.excel_exporter.exportar_cotizacion_completa(bloques_productos)
            self.root.after(0, self._on_exito, archivo_excel)

        except Exception as exc:
            self.root.after(0, self._on_error, str(exc))

    def _on_exito(self, archivo_creado: str) -> None:
        """Maneja la respuesta exitosa en el hilo principal de Tkinter."""
        if self.view:
            self.view.set_loading_state(False, "¡Cotización generada con éxito!")

        path_absoluto = os.path.abspath(archivo_creado)
        messagebox.showinfo(
            "Operación Exitosa",
            f"Cotización generada correctamente en:\n\n{path_absoluto}"
        )

    def _on_error(self, error_msg: str) -> None:
        """Maneja las excepciones capturadas y notifica al usuario vía diálogo de error."""
        if self.view:
            self.view.set_loading_state(False, "Error en la generación.")

        messagebox.showerror(
            "Error al Cotizar",
            f"Ocurrió un problema durante el procesamiento:\n\n{error_msg}"
        )