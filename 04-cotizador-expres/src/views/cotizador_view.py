import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional


class CotizadorView(ttk.Frame):
    """Componente de vista principal para la interfaz gráfica del Cotizador Exprés.

    Provee un formulario dinámico que permite configurar múltiples requerimientos
    de cotización (categoría, subproducto y cantidad) y sincronizar su estado con
    el controlador del patrón MVC.
    """

    def __init__(self, parent: tk.Tk, controller: Any) -> None:
        """Inicializa el marco contenedor y construye los elementos gráficos.

        Args:
            parent: Ventana principal contenedora de Tkinter.
            controller: Instancia del controlador que gestiona la lógica de negocio.
        """
        super().__init__(parent, padding="15")
        self.parent = parent
        self.controller = controller

        self.filas_productos: List[Dict[str, Any]] = []

        style = ttk.Style()
        style.theme_use("clam")

        self._build_ui()

    def _build_ui(self) -> None:
        """Construye la disposición espacial de los widgets principales."""
        self.pack(fill=tk.BOTH, expand=True)

        lbl_titulo = ttk.Label(
            self,
            text="COTIZADOR EXPRÉS 2026 (COMPIPRO)",
            font=("Arial", 14, "bold"),
        )
        lbl_titulo.pack(pady=(0, 10))

        self.frame_productos = ttk.LabelFrame(self, text="🛒 Lista de Requerimientos a Cotizar")
        self.frame_productos.pack(fill="x", pady=5, ipadx=5, ipady=10)

        frame_acciones = ttk.Frame(self)
        frame_acciones.pack(fill="x", pady=5)

        self.btn_agregar = ttk.Button(
            frame_acciones,
            text="➕ Agregar Producto",
            command=self.agregar_fila,
        )
        self.btn_agregar.pack(side="left", padx=5)

        self.lbl_status = ttk.Label(
            self,
            text="Listo para cotizar.",
            font=("Arial", 9, "italic"),
            foreground="gray",
        )
        self.lbl_status.pack(pady=5)

        self.btn_generar = ttk.Button(
            self,
            text="🚀 Generar Cotización Excel",
            command=self._on_click_generar,
        )
        self.btn_generar.pack(fill="x", pady=(5, 0))

        self.agregar_fila()

    def agregar_fila(self) -> None:
        """Añade una nueva fila de requerimiento con validación de límite máximo (7 ítems)."""
        if len(self.filas_productos) >= 7:
            messagebox.showwarning("Límite Alcanzado", "Máximo 7 productos por cotización a la vez.")
            return

        fila_frame = ttk.Frame(self.frame_productos)
        fila_frame.pack(fill="x", pady=4, padx=5)

        categorias_disponibles = self.controller.obtener_categorias_disponibles()
        combo_cat = ttk.Combobox(
            fila_frame,
            values=list(categorias_disponibles.keys()),
            state="readonly",
            width=32,
        )
        combo_cat.pack(side="left", padx=5)
        combo_cat.set("Seleccione Categoría...")

        combo_sub = ttk.Combobox(
            fila_frame,
            values=["Todos (Categoría Completa)"],
            state="readonly",
            width=35,
        )
        combo_sub.pack(side="left", padx=5)
        combo_sub.set("Todos (Categoría Completa)")

        ttk.Label(fila_frame, text="Cant:").pack(side="left", padx=(5, 2))
        entry_cant = ttk.Entry(fila_frame, width=8, justify="center")
        entry_cant.pack(side="left", padx=2)
        entry_cant.insert(0, "50")

        btn_eliminar = ttk.Button(
            fila_frame,
            text="❌",
            width=3,
            command=lambda f=fila_frame: self.eliminar_fila(f),
        )
        btn_eliminar.pack(side="left", padx=5)

        fila_dict = {
            "frame": fila_frame,
            "combo_cat": combo_cat,
            "combo_sub": combo_sub,
            "entry_cant": entry_cant,
        }
        self.filas_productos.append(fila_dict)

        combo_cat.bind(
            "<<ComboboxSelected>>",
            lambda event, fd=fila_dict: self._on_categoria_changed(fd),
        )

    def _on_categoria_changed(self, fila_dict: Dict[str, Any]) -> None:
        """Actualiza las opciones del Combobox de subproductos al seleccionar una categoría.

        Args:
            fila_dict: Diccionario con las referencias a los widgets de la fila activa.
        """
        nombre_cat_comercial = fila_dict["combo_cat"].get()
        subproductos = self.controller.obtener_subproductos_por_categoria(nombre_cat_comercial)

        fila_dict["combo_sub"]["values"] = subproductos
        fila_dict["combo_sub"].current(0)

    def eliminar_fila(self, frame_a_eliminar: ttk.Frame) -> None:
        """Elimina una fila de la vista asegurando la persistencia de al menos un registro.

        Args:
            frame_a_eliminar: Contenedor gráfico de la fila que se desea remover.
        """
        if len(self.filas_productos) > 1:
            frame_a_eliminar.destroy()
            self.filas_productos = [f for f in self.filas_productos if f["frame"] != frame_a_eliminar]
        else:
            messagebox.showinfo("Atención", "Debe haber al menos un producto en la cotización.")

    def _on_click_generar(self) -> None:
        """Valida las entradas de usuario y delega la ejecución asíncrona al controlador."""
        pedidos_raw: List[Dict[str, Any]] = []
        for fila in self.filas_productos:
            cat_nombre = fila["combo_cat"].get()
            sub = fila["combo_sub"].get()
            cant_str = fila["entry_cant"].get()

            if cat_nombre == "Seleccione Categoría...":
                continue

            if not cant_str.isdigit() or int(cant_str) <= 0:
                messagebox.showwarning("Cantidad Inválida", f"Ingrese un número mayor a 0 para: {cat_nombre}")
                return

            pedidos_raw.append({
                "categoria_nombre": cat_nombre,
                "subproducto": sub,
                "cantidad": int(cant_str),
            })

        if not pedidos_raw:
            messagebox.showwarning("Lista Vacía", "Seleccione al menos una categoría válida para cotizar.")
            return

        self.controller.procesar_cotizacion_asincrona(pedidos_raw)

    def set_loading_state(self, is_loading: bool, msg: Optional[str] = "") -> None:
        """Alterna el estado de interactividad de los controles y actualiza la etiqueta de progreso.

        Args:
            is_loading: Indica si el sistema está ejecutando una tarea en segundo plano.
            msg: Mensaje informativo visible para el usuario.
        """
        if is_loading:
            self.btn_generar.config(state="disabled")
            self.btn_agregar.config(state="disabled")
            self.lbl_status.config(text=msg or "Generando cotización...", foreground="dark orange")
        else:
            self.btn_generar.config(state="normal")
            self.btn_agregar.config(state="normal")
            self.lbl_status.config(text=msg or "Listo.", foreground="green")