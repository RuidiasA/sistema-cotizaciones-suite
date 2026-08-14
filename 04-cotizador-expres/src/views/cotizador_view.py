import tkinter as tk
from tkinter import ttk, messagebox


class CotizadorView(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding="15")
        self.parent = parent
        self.controller = controller

        self.filas_productos = []
        
        # Aplicamos tema visual
        style = ttk.Style()
        style.theme_use('clam')

        self._build_ui()

    def _build_ui(self):
        self.pack(fill=tk.BOTH, expand=True)

        # Encabezado Principal
        lbl_titulo = ttk.Label(
            self, 
            text="COTIZADOR EXPRÉS 2026 (COMPIPRO)", 
            font=("Arial", 14, "bold")
        )
        lbl_titulo.pack(pady=(0, 10))

        # Contenedor Dinámico de Productos
        self.frame_productos = ttk.LabelFrame(self, text="🛒 Lista de Requerimientos a Cotizar")
        self.frame_productos.pack(fill="x", pady=5, ipadx=5, ipady=10)

        # Barra de Botones Secundarios
        frame_acciones = ttk.Frame(self)
        frame_acciones.pack(fill="x", pady=5)

        self.btn_agregar = ttk.Button(
            frame_acciones, 
            text="➕ Agregar Producto", 
            command=self.agregar_fila
        )
        self.btn_agregar.pack(side="left", padx=5)

        # Label de Estado / Progreso
        self.lbl_status = ttk.Label(
            self, 
            text="Listo para cotizar.", 
            font=("Arial", 9, "italic"), 
            foreground="gray"
        )
        self.lbl_status.pack(pady=5)

        # Botón Acción Principal
        self.btn_generar = ttk.Button(
            self, 
            text="🚀 Generar Cotización Excel", 
            command=self._on_click_generar
        )
        self.btn_generar.pack(fill="x", pady=(5, 0))

        # Agregamos la primera fila por defecto al abrir
        self.agregar_fila()

    def agregar_fila(self):
        if len(self.filas_productos) >= 7:
            messagebox.showwarning("Límite Alcanzado", "Máximo 7 productos por cotización a la vez.")
            return

        fila_frame = ttk.Frame(self.frame_productos)
        fila_frame.pack(fill="x", pady=4, padx=5)

        # Categoría
        categorias_disponibles = self.controller.obtener_categorias_disponibles()
        combo_cat = ttk.Combobox(
            fila_frame, 
            values=list(categorias_disponibles.keys()), 
            state="readonly", 
            width=32
        )
        combo_cat.pack(side="left", padx=5)
        combo_cat.set("Seleccione Categoría...")

        # Subproducto
        combo_sub = ttk.Combobox(
            fila_frame, 
            values=["Todos (Categoría Completa)"], 
            state="readonly", 
            width=35
        )
        combo_sub.pack(side="left", padx=5)
        combo_sub.set("Todos (Categoría Completa)")

        # Cantidad
        ttk.Label(fila_frame, text="Cant:").pack(side="left", padx=(5, 2))
        entry_cant = ttk.Entry(fila_frame, width=8, justify="center")
        entry_cant.pack(side="left", padx=2)
        entry_cant.insert(0, "50")

        # Botón Eliminar
        btn_eliminar = ttk.Button(
            fila_frame, 
            text="❌", 
            width=3, 
            command=lambda f=fila_frame: self.eliminar_fila(f)
        )
        btn_eliminar.pack(side="left", padx=5)

        fila_dict = {
            "frame": fila_frame,
            "combo_cat": combo_cat,
            "combo_sub": combo_sub,
            "entry_cant": entry_cant
        }
        self.filas_productos.append(fila_dict)

        # Evento al seleccionar categoría -> Actualiza subproductos
        combo_cat.bind(
            "<<ComboboxSelected>>", 
            lambda e, fd=fila_dict: self._on_categoria_changed(fd)
        )

    def _on_categoria_changed(self, fila_dict):
        nombre_cat_comercial = fila_dict["combo_cat"].get()
        subproductos = self.controller.obtener_subproductos_por_categoria(nombre_cat_comercial)
        
        fila_dict["combo_sub"]['values'] = subproductos
        fila_dict["combo_sub"].current(0)

    def eliminar_fila(self, frame_a_eliminar):
        if len(self.filas_productos) > 1:
            frame_a_eliminar.destroy()
            self.filas_productos = [f for f in self.filas_productos if f["frame"] != frame_a_eliminar]
        else:
            messagebox.showinfo("Atención", "Debe haber al menos un producto en la cotización.")

    def _on_click_generar(self):
        pedidos_raw = []
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
                "cantidad": int(cant_str)
            })

        if not pedidos_raw:
            messagebox.showwarning("Lista Vacía", "Seleccione al menos una categoría válida para cotizar.")
            return

        self.controller.procesar_cotizacion_asincrona(pedidos_raw)

    def set_loading_state(self, is_loading, msg=""):
        if is_loading:
            self.btn_generar.config(state="disabled")
            self.btn_agregar.config(state="disabled")
            self.lbl_status.config(text=msg or "Generando cotización...", foreground="dark orange")
        else:
            self.btn_generar.config(state="normal")
            self.btn_agregar.config(state="normal")
            self.lbl_status.config(text=msg or "Listo.", foreground="green")