import os
import threading
from pathlib import Path
from tkinter import messagebox

from src.services.data_engine import DataEngine
from src.services.excel_exporter import ExcelExporter


class AppController:
    def __init__(self, root):
        self.root = root
        
        # Inicializamos el DataEngine local con la prioridad de búsqueda
        self.data_engine = DataEngine()
        self.excel_exporter = ExcelExporter()

        # Cargar categorías del tarifario
        self.categorias_map = self.data_engine.get_categorias()

    def set_view(self, view):
        self.view = view

    def obtener_categorias_disponibles(self):
        return self.categorias_map

    def obtener_subproductos_por_categoria(self, nombre_categoria_comercial):
        cat_key = self.categorias_map.get(nombre_categoria_comercial)
        if not cat_key:
            return ["Todos (Categoría Completa)"]
        return self.data_engine.get_subproductos(cat_key)

    def procesar_cotizacion_asincrona(self, pedidos_raw):
        self.view.set_loading_state(True, "Buscando en datasets prioritarios y calculando márgenes...")
        
        t = threading.Thread(target=self._worker_procesar, args=(pedidos_raw,))
        t.daemon = True
        t.start()

    def _worker_procesar(self, pedidos_raw):
        try:
            bloques_productos = []

            for p in pedidos_raw:
                cat_nombre = p["categoria_nombre"]
                sub = p["subproducto"]
                cant = p["cantidad"]

                cat_key = self.categorias_map.get(cat_nombre)
                if not cat_key:
                    continue

                # Ejecuta la búsqueda jerárquica (Reciente -> Histórico)
                opciones = self.data_engine.buscar_opciones_proveedores(
                    cat_key=cat_key,
                    cantidad_solicitada=cant,
                    subproducto_nombre=sub
                )

                prod_nombre = sub if sub != "Todos (Categoría Completa)" else cat_nombre

                bloques_productos.append({
                    "producto_nombre": prod_nombre,
                    "cantidad": cant,
                    "opciones": opciones
                })

            # Validación de seguridad: si no se halló ningún proveedor en ningún dataset
            if not any(b["opciones"] for b in bloques_productos):
                raise ValueError("No se encontraron coincidencias de proveedores en los archivos de data/input/.")

            # Genera el Excel en data/output/
            archivo_excel = self.excel_exporter.exportar_cotizacion_completa(bloques_productos)

            self.root.after(0, self._on_exito, archivo_excel)

        except Exception as e:
            self.root.after(0, self._on_error, str(e))

    def _on_exito(self, archivo_creado):
        self.view.set_loading_state(False, "¡Cotización generada con éxito!")
        path_absoluto = os.path.abspath(archivo_creado)
        messagebox.showinfo(
            "Éxito Total", 
            f"Cotización generada correctamente en:\n\n{path_absoluto}"
        )

    def _on_error(self, error_msg):
        self.view.set_loading_state(False, "Error en la generación.")
        messagebox.showerror("Error al Cotizar", f"Ocurrió un problema:\n\n{error_msg}")