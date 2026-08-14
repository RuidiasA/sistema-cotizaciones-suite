import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd


class DataEngine:
    """Motor de datos y analítica comercial para el Módulo de Cotizaciones.

    Gestiona la ingesta de datasets históricos en memoria RAM bajo una estrategia
    jerárquica de búsqueda en cascada (Priority Fallback), resuelve la interpolación
    de márgenes base, evalúa reglas condicionales de negocio y realiza la
    consolidación multilínea de proveedores.
    """

    def __init__(
        self,
        data_dir: Optional[Union[str, Path]] = None,
        priority_files: Optional[List[str]] = None,
        config_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """Inicializa las rutas del sistema, carga la configuración y precarga datasets.

        Args:
            data_dir: Directorio contenedor de los Data Lakes en Excel.
            priority_files: Lista ordenada de archivos Excel para la búsqueda jerárquica.
            config_dir: Directorio de artefactos JSON generados por el Módulo 03.
        """
        base_module_dir = Path(__file__).resolve().parent.parent.parent

        self.data_dir = Path(data_dir) if data_dir else base_module_dir / "data" / "input"
        self.output_dir = base_module_dir / "data" / "output"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        self.priority_files = priority_files or [
            "debug_scan_raw_recent.xlsx",
            "debug_scan_raw.xlsx",
        ]

        if config_dir is None:
            local_config = base_module_dir / "config"
            m03_config = base_module_dir.parent / "03-motor-ajustes-dinamicos" / "config"
            self.config_dir = local_config if (local_config / "matrices_margen.json").exists() else m03_config
        else:
            self.config_dir = Path(config_dir)

        self.matrices_path = self.config_dir / "matrices_margen.json"
        self.ajustes_path = self.config_dir / "ajustes_margen.json"

        self.matrices_data: Dict[str, Any] = self._load_json(self.matrices_path)
        self.ajustes_data: List[Dict[str, Any]] = self._load_json(self.ajustes_path)

        self.datasets: Dict[str, pd.DataFrame] = self._load_all_priority_datasets()

    def _load_json(self, path: Path) -> Any:
        """Lee y deserializa un archivo JSON de configuración.

        Args:
            path: Ruta del archivo JSON a cargar.

        Returns:
            Estructura de datos deserializada (dict o list).
        """
        if not path.exists():
            return {} if "matrices" in path.name else []
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _load_all_priority_datasets(self) -> Dict[str, pd.DataFrame]:
        """Carga en memoria RAM todos los datasets de entrada disponibles con texto saneado."""
        loaded: Dict[str, pd.DataFrame] = {}
        for filename in self.priority_files:
            file_path = self.data_dir / filename
            if file_path.exists():
                try:
                    df = pd.read_excel(file_path)
                    if "Descripcion / Articulo" in df.columns:
                        df["Desc_Lower"] = df["Descripcion / Articulo"].astype(str).str.lower().str.strip()
                    else:
                        df["Desc_Lower"] = ""
                    loaded[filename] = df
                except Exception as exc:
                    print(f"[WARN] Error al precargar dataset {filename}: {exc}")
        return loaded

    def get_categorias(self) -> Dict[str, str]:
        """Retorna el mapeo ordenado de nombres comerciales a claves de arquetipo."""
        categorias: Dict[str, str] = {}
        for key, data in self.matrices_data.items():
            nombre_comercial = data.get("nombre_comercial", key)
            categorias[nombre_comercial] = key
        return dict(sorted(categorias.items()))

    def get_subproductos(self, cat_key: str) -> List[str]:
        """Obtiene las variantes específicas de producto registradas para una categoría.

        Args:
            cat_key: Clave técnica de la categoría/arquetipo comercial.

        Returns:
            Lista con las opciones de subproductos disponibles.
        """
        if cat_key not in self.matrices_data:
            return ["Todos (Categoría Completa)"]
        especificos = self.matrices_data[cat_key].get("productos_especificos", [])
        if especificos:
            return ["Todos (Categoría Completa)"] + [sp["nombre_sistema"] for sp in especificos]
        return ["Todos (Categoría Completa)"]

    def _calcular_bracket_volumen(self, qty: int, escalas_json: Dict[str, Any]) -> Tuple[int, Union[int, float]]:
        """Calcula el rango de volumen [q_min, q_max] donde se ubica la cantidad solicitada.

        Args:
            qty: Cantidad solicitada por el usuario.
            escalas_json: Mapeo de escalas de cantidad definidas en la matriz de márgenes.

        Returns:
            Tupla con los límites inferior y superior del bracket comercial.
        """
        escalas = sorted([int(q) for q in escalas_json.keys()])
        if not escalas:
            return 0, float("inf")
        if qty <= escalas[0]:
            return 0, escalas[0]
        if qty >= escalas[-1]:
            return escalas[-1], float("inf")

        for i in range(len(escalas) - 1):
            if escalas[i] <= qty < escalas[i + 1]:
                return escalas[i], escalas[i + 1] - 1
        return 0, float("inf")

    def _interpolate_margin(self, qty: int, margin_scale: Dict[str, Any]) -> float:
        """Determina el margen base aplicable según el algoritmo de escalón duro (Piso Comercial).

        Args:
            qty: Cantidad solicitada por el usuario.
            margin_scale: Mapeo de márgenes porcentuales por escala de volumen.

        Returns:
            Margen comercial base en porcentaje.
        """
        sorted_quantities = sorted([int(q) for q in margin_scale.keys()])
        if not sorted_quantities:
            return 30.0

        if qty <= sorted_quantities[0]:
            return float(margin_scale[str(sorted_quantities[0])])

        target_qty = sorted_quantities[0]
        for q in sorted_quantities:
            if qty >= q:
                target_qty = q
            else:
                break
        return float(margin_scale[str(target_qty)])

    def _filtrar_df(self, df_source: pd.DataFrame, cat_key: str, subproducto_nombre: str) -> pd.DataFrame:
        """Aplica filtros taxonómicos y reglas de inclusión/exclusión de tokens sobre el DataFrame.

        Args:
            df_source: DataFrame fuente sobre el cual filtrar.
            cat_key: Clave técnica de la categoría seleccionada.
            subproducto_nombre: Subproducto específico o bandera global de categoría.

        Returns:
            DataFrame filtrado con los registros compatibles.
        """
        if df_source.empty or cat_key not in self.matrices_data:
            return pd.DataFrame()

        prod_config = self.matrices_data[cat_key]
        filtros_p = [str(f).lower().strip() for f in prod_config.get("filtros_prenda", [])]
        filtros_m = [str(f).lower().strip() for f in prod_config.get("filtros_material", [])]

        def _get_head(texto: str) -> str:
            return " ".join(str(texto)[:250].split()[:8])

        mask_p = (
            df_source["Desc_Lower"].apply(lambda x: any(f in _get_head(x) for f in filtros_p))
            if filtros_p
            else pd.Series(True, index=df_source.index)
        )
        mask_m = (
            df_source["Desc_Lower"].apply(lambda x: any(f in _get_head(x) for f in filtros_m))
            if filtros_m
            else pd.Series(True, index=df_source.index)
        )

        df_res = df_source[mask_p & mask_m].copy()

        if subproducto_nombre != "Todos (Categoría Completa)" and not df_res.empty:
            prod_especifico = next(
                (sp for sp in prod_config.get("productos_especificos", []) if sp["nombre_sistema"] == subproducto_nombre),
                None,
            )
            if prod_especifico:
                t_prod = prod_especifico.get("tokens_producto", [])
                f_inc = prod_especifico.get("tokens_filtro_inc", [])
                f_exc = prod_especifico.get("tokens_filtro_exc", [])

                if t_prod:
                    df_res = df_res[df_res["Desc_Lower"].apply(lambda x: any(t in str(x) for t in t_prod))]
                if f_inc:
                    df_res = df_res[df_res["Desc_Lower"].apply(lambda x: any(t in str(x) for t in f_inc))]
                if f_exc:
                    df_res = df_res[df_res["Desc_Lower"].apply(lambda x: not any(t in str(x) for t in f_exc))]

        return df_res

    def buscar_opciones_proveedores(
        self,
        cat_key: str,
        cantidad_solicitada: int,
        subproducto_nombre: str = "Todos (Categoría Completa)",
    ) -> List[Dict[str, Any]]:
        """Ejecuta el pipeline de cotización: búsqueda en cascada, márgenes y consolidación multilínea.

        Args:
            cat_key: Clave técnica del arquetipo.
            cantidad_solicitada: Volumen de unidades a cotizar.
            subproducto_nombre: Variante seleccionada o categoría global.

        Returns:
            Lista de opciones consolidadas por proveedor ordenadas por costo unitario cliente.
        """
        df_producto = pd.DataFrame()

        for filename in self.priority_files:
            if filename in self.datasets:
                df_candidato = self._filtrar_df(self.datasets[filename], cat_key, subproducto_nombre)
                if not df_candidato.empty:
                    df_producto = df_candidato
                    break

        if df_producto.empty:
            return []

        prod_config = self.matrices_data[cat_key]
        margin_scale = prod_config.get("margenes", {})

        q_min, q_max = self._calcular_bracket_volumen(cantidad_solicitada, margin_scale)
        df_filtrado = df_producto[
            (df_producto["Cantidad Detectada"] >= q_min) & (df_producto["Cantidad Detectada"] <= q_max)
        ].copy()

        if df_filtrado.empty:
            df_filtrado = df_producto.copy()

        df_filtrado["Proveedor_Clean"] = (
            df_filtrado["Proveedor"].astype(str).apply(lambda x: re.sub(r"\s+", " ", x).strip().upper())
        )
        df_filtrado["Descripcion / Articulo"] = df_filtrado["Descripcion / Articulo"].astype(str).str.strip()

        df_filtrado = df_filtrado.drop_duplicates(
            subset=["Proveedor_Clean", "Descripcion / Articulo", "Cantidad Detectada", "Costo Prov", "Precio Cli"]
        )

        sep_control = "\n" + "-" * 15 + "\n"
        resultados_proveedores: List[Dict[str, Any]] = []
        nombre_final = (
            subproducto_nombre
            if subproducto_nombre != "Todos (Categoría Completa)"
            else prod_config.get("nombre_comercial", cat_key)
        )

        grouped = df_filtrado.groupby(["Proveedor_Clean", "Descripcion / Articulo"])

        for (prov_name, detalle_texto), g in grouped:
            g = g.sort_values(by="Cantidad Detectada")

            cants_str = sep_control.join(g["Cantidad Detectada"].astype(str))
            costos_str = sep_control.join(g["Costo Prov"].map(lambda x: f"S/. {float(x):,.2f}"))
            precios_str = sep_control.join(g["Precio Cli"].map(lambda x: f"S/. {float(x):,.2f}"))

            idx_closest = (g["Cantidad Detectada"] - cantidad_solicitada).abs().idxmin()
            row_closest = g.loc[idx_closest]
            costo_taller = float(row_closest["Costo Prov"])

            margen_calc = self._interpolate_margin(cantidad_solicitada, margin_scale)

            texto_norm = detalle_texto.lower()
            for regla in self.ajustes_data:
                if regla.get("producto") != cat_key and regla.get("producto") != "TODOS":
                    continue

                cumple = True
                for cond in regla.get("condiciones", []):
                    var = cond.get("variable")
                    op = cond.get("condicion")
                    ref = cond.get("valor_referencia")

                    if var == "cantidad":
                        try:
                            val_act = float(cantidad_solicitada)
                            val_ref = float(ref)
                            if ("menor o igual" in op or "<=" in op) and not (val_act <= val_ref):
                                cumple = False
                            elif ("mayor o igual" in op or ">=" in op) and not (val_act >= val_ref):
                                cumple = False
                            elif ("menor" in op or "<" in op) and not (val_act < val_ref):
                                cumple = False
                            elif ("mayor" in op or ">" in op) and not (val_act > val_ref):
                                cumple = False
                            elif ("igual" in op or "==" in op) and not (val_act == val_ref):
                                cumple = False
                        except ValueError:
                            cumple = False

                    elif var in ["descripcion", "detalle", "texto"]:
                        token = str(ref).lower()
                        if "contiene" in op and token not in texto_norm:
                            cumple = False
                        elif "no contiene" in op and token in texto_norm:
                            cumple = False

                if cumple and regla.get("condiciones"):
                    tipo = regla.get("tipo_ajuste")
                    impacto = float(regla.get("valor_impacto", 0))
                    if tipo == "margen fijo":
                        margen_calc = impacto
                    elif tipo == "sumar puntos":
                        margen_calc += impacto
                    elif tipo == "restar puntos":
                        margen_calc -= impacto

            factor = 1.0 + (margen_calc / 100.0)
            costo_uni_cliente = round(costo_taller * factor, 2)
            costo_total_cliente = round(costo_uni_cliente * cantidad_solicitada, 2)

            tiempo_entrega = str(row_closest.get("Tiempo Entrega", "Entrega Inmediata"))
            if pd.isna(tiempo_entrega) or tiempo_entrega.strip().lower() in ["nan", "none", ""]:
                tiempo_entrega = "Entrega Inmediata"

            resultados_proveedores.append({
                "N°": 1,
                "Proveedor": prov_name,
                "Producto": nombre_final,
                "Foto": "Imagen Referencial",
                "Cant.": cantidad_solicitada,
                "Costo uni. NO IGV (S/.)": costo_uni_cliente,
                "Tiempo Entrega": tiempo_entrega,
                "Detalle": detalle_texto,
                "Costo TOTAL NO IGV (S/.)": costo_total_cliente,
                "Cantidad_Multilinea": cants_str,
                "Costo_Prov_Multilinea": costos_str,
                "Precio_Cli_Original_2026": precios_str,
            })

        resultados_proveedores.sort(key=lambda x: x["Costo uni. NO IGV (S/.)"])
        for idx, res in enumerate(resultados_proveedores, start=1):
            res["N°"] = idx

        return resultados_proveedores