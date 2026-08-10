"""Módulo Compilador Multicapa del Tarifario Maestro.

Transforma las 5 hojas de cálculo del archivo Excel de reglas (tarifario_diseno.xlsx)
en artefactos JSON estructurados (matrices_margen.json y ajustes_margen.json)
para su consumo en tiempo real por el motor de cotización expres.
"""

import json
from pathlib import Path
import unicodedata
from typing import Any, Dict, List
import pandas as pd


class ExcelCompiler:
    """Compilador multicapa para procesar la taxonomía y reglas de negocio en Excel."""

    def __init__(self, excel_path: Path, config_dir: Path) -> None:
        self.excel_path: Path = excel_path
        self.config_dir: Path = config_dir
        self.matrices_json_path: Path = config_dir / "matrices_margen.json"
        self.ajustes_json_path: Path = config_dir / "ajustes_margen.json"

    @staticmethod
    def _normalizar_texto(texto: Any) -> str:
        """Sanea y remueve diacríticos de una cadena de texto."""
        if pd.isna(texto):
            return ""
        texto_norm = unicodedata.normalize("NFD", str(texto).strip().lower())
        return "".join(c for c in texto_norm if unicodedata.category(c) != "Mn")

    def _procesar_filtros(self, excel_file: pd.ExcelFile) -> Dict[str, Dict[str, List[str]]]:
        """Procesa la Hoja 5: Diccionario de Filtros Globales."""
        diccionario_filtros: Dict[str, Dict[str, List[str]]] = {}
        sheet_name = "Diccionario_Filtros_Globales"

        if sheet_name not in excel_file.sheet_names:
            if "Diccionario_Filtros" in excel_file.sheet_names:
                sheet_name = "Diccionario_Filtros"
            else:
                print(f"[WARN] Hoja de Filtros no encontrada en {self.excel_path.name}")
                return diccionario_filtros

        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            for _, row in df.iterrows():
                if pd.isna(row.get("ID_Filtro")):
                    continue
                f_id = str(row["ID_Filtro"]).strip().upper()
                str_inc = str(row["Incluir"]) if pd.notna(row.get("Incluir")) else ""
                str_exc = str(row["Excluir"]) if pd.notna(row.get("Excluir")) else ""

                diccionario_filtros[f_id] = {
                    "inc": [t.strip().lower() for t in str_inc.split(",") if t.strip()],
                    "exc": [t.strip().lower() for t in str_exc.split(",") if t.strip()],
                }
            print(f"[SUCCESS] Filtros globales cargados ({sheet_name}): {len(diccionario_filtros)} IDs.")
        except Exception as e:
            print(f"[WARN] Error procesando hoja de Filtros: {e}")

        return diccionario_filtros

    def _procesar_categorias(self, excel_file: pd.ExcelFile) -> Dict[str, Dict[str, Any]]:
        """Procesa la Hoja 3: Diccionario de Categorías."""
        diccionario_categorias: Dict[str, Dict[str, Any]] = {}
        sheet_name = "Diccionario_Categorias"

        if sheet_name not in excel_file.sheet_names:
            print(f"[WARN] Hoja '{sheet_name}' no encontrada.")
            return diccionario_categorias

        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            for _, row in df.iterrows():
                if pd.isna(row.get("Categoria")):
                    continue
                cat_key = str(row["Categoria"]).strip().upper().replace(" ", "_")
                if not cat_key or cat_key == "NAN":
                    continue

                nombre = str(row["Nombre_Comercial"]).strip() if pd.notna(row.get("Nombre_Comercial")) else cat_key
                str_prenda = str(row["Variantes_Producto"]) if pd.notna(row.get("Variantes_Producto")) else ""
                str_material = str(row["Variantes_Material"]) if pd.notna(row.get("Variantes_Material")) else ""

                diccionario_categorias[cat_key] = {
                    "nombre_comercial": nombre,
                    "filtros_prenda": [p.strip().lower() for p in str_prenda.split(",") if p.strip()],
                    "filtros_material": [m.strip().lower() for m in str_material.split(",") if m.strip()],
                }
            print(f"[SUCCESS] Categorías procesadas: {len(diccionario_categorias)} definiciones.")
        except Exception as e:
            print(f"[ERROR] Falló procesamiento de '{sheet_name}': {e}")

        return diccionario_categorias

    def _procesar_margenes_base(
        self, excel_file: pd.ExcelFile, diccionario_categorias: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Procesa la Hoja 1: Márgenes Base y estructura las matrices finales."""
        matrices_finales: Dict[str, Dict[str, Any]] = {}
        sheet_name = "Margenes_Base"

        if sheet_name not in excel_file.sheet_names:
            print(f"[ERROR] Hoja crítica '{sheet_name}' no encontrada.")
            return matrices_finales

        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        df["Producto"] = df["Producto"].ffill()

        for producto, grupo in df.groupby("Producto"):
            if pd.isna(producto):
                continue
            cat_key = str(producto).strip().upper().replace(" ", "_")

            if cat_key in diccionario_categorias:
                cat_info = diccionario_categorias[cat_key]
                matrices_finales[cat_key] = {
                    "nombre_comercial": cat_info["nombre_comercial"],
                    "filtros_prenda": cat_info["filtros_prenda"],
                    "filtros_material": cat_info["filtros_material"],
                    "margenes": {},
                    "productos_especificos": [],
                }
            else:
                tokens = cat_key.split("_")
                matrices_finales[cat_key] = {
                    "nombre_comercial": str(producto).strip(),
                    "filtros_prenda": [tokens[0].lower()] if tokens else [cat_key.lower()],
                    "filtros_material": [tokens[1].lower()] if len(tokens) > 1 else [],
                    "margenes": {},
                    "productos_especificos": [],
                }

            for _, row in grupo.iterrows():
                if pd.notna(row.get("Cantidad")) and pd.notna(row.get("Margen")):
                    cant_key = str(int(row["Cantidad"]))
                    matrices_finales[cat_key]["margenes"][cant_key] = float(row["Margen"])

        return matrices_finales

    def _procesar_productos_especificos(
        self,
        excel_file: pd.ExcelFile,
        matrices_finales: Dict[str, Dict[str, Any]],
        diccionario_filtros: Dict[str, Dict[str, List[str]]],
    ) -> None:
        """Procesa la Hoja 4: Diccionario de Productos Específicos."""
        sheet_name = "Diccionario_Productos"
        if sheet_name not in excel_file.sheet_names:
            return

        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            contador = 0

            for _, row in df.iterrows():
                if pd.isna(row.get("Categoria_Padre")):
                    continue
                padre_key = str(row["Categoria_Padre"]).strip().upper().replace(" ", "_")

                if padre_key not in matrices_finales:
                    matrices_finales[padre_key] = {
                        "nombre_comercial": padre_key,
                        "filtros_prenda": [padre_key.lower()],
                        "filtros_material": [],
                        "margenes": {},
                        "productos_especificos": [],
                    }

                nombre_sys = str(row["Nombre_Sistema"]).strip() if pd.notna(row.get("Nombre_Sistema")) else ""
                filtro_id = str(row["Filtro_Global"]).strip().upper() if pd.notna(row.get("Filtro_Global")) else ""

                str_prod = str(row["Producto"]) if pd.notna(row.get("Producto")) else ""
                tokens_prod = [t.strip().lower() for t in str_prod.split(",") if t.strip()]

                tokens_inc, tokens_exc = [], []
                if filtro_id and filtro_id in diccionario_filtros:
                    tokens_inc = diccionario_filtros[filtro_id]["inc"]
                    tokens_exc = diccionario_filtros[filtro_id]["exc"]

                matrices_finales[padre_key]["productos_especificos"].append({
                    "nombre_sistema": nombre_sys,
                    "tokens_producto": tokens_prod,
                    "tokens_filtro_inc": tokens_inc,
                    "tokens_filtro_exc": tokens_exc,
                })
                contador += 1

            print(f"[SUCCESS] Productos específicos inyectados: {contador} ítems.")
        except Exception as e:
            print(f"[WARN] Falló procesamiento de '{sheet_name}': {e}")

    def _procesar_ajustes(self, excel_file: pd.ExcelFile) -> List[Dict[str, Any]]:
        """Procesa la Hoja 2: Reglas de Ajuste Dinámico."""
        sheet_name = "Ajustes"
        if sheet_name not in excel_file.sheet_names:
            print(f"[WARN] Hoja '{sheet_name}' no encontrada.")
            return []

        dict_ajustes: Dict[int, Dict[str, Any]] = {}
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            df["Id_Ajuste"] = df["Id_Ajuste"].ffill().astype(int)
            df = df.dropna(subset=["Producto", "Variable", "Condicion"])

            for _, row in df.iterrows():
                id_ajuste = int(row["Id_Ajuste"])
                prod_key = str(row["Producto"]).strip().upper().replace(" ", "_")
                val_ref_raw = str(row["Valor_Referencia"]).strip() if pd.notna(row.get("Valor_Referencia")) else ""
                val_ref = self._normalizar_texto(val_ref_raw)

                variable = str(row["Variable"]).strip().lower()
                if variable == "cantidad":
                    try:
                        val_ref = int(float(val_ref))
                    except ValueError:
                        pass

                if id_ajuste not in dict_ajustes:
                    dict_ajustes[id_ajuste] = {
                        "id_ajuste": id_ajuste,
                        "producto": prod_key,
                        "tipo_ajuste": str(row["Tipo_Ajuste"]).strip().lower(),
                        "valor_impacto": float(row["Valor_Impacto"]),
                        "condiciones": [],
                    }

                dict_ajustes[id_ajuste]["condiciones"].append({
                    "variable": variable,
                    "condicion": str(row["Condicion"]).strip().lower(),
                    "valor_referencia": val_ref,
                })

            print(f"[SUCCESS] Reglas de ajuste compiladas: {len(dict_ajustes)} reglas.")
        except Exception as e:
            print(f"[WARN] Error al procesar '{sheet_name}': {e}")

        return list(dict_ajustes.values())

    def compilar_todo(self) -> None:
        """Ejecuta la canalización completa de compilación de las 5 hojas."""
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Tarifario maestro no encontrado en: {self.excel_path}")

        print("==================================================")
        print("PIPELINE DE COMPILACION MULTICAPA DE TARIFARIO")
        print("==================================================")
        print(f"[INFO] Leyendo archivo maestro: {self.excel_path.name}")

        excel_file = pd.ExcelFile(self.excel_path)

        # Pipeline secuencial de extracción
        filtros = self._procesar_filtros(excel_file)
        categorias = self._procesar_categorias(excel_file)
        matrices_finales = self._procesar_margenes_base(excel_file, categorias)
        self._procesar_productos_especificos(excel_file, matrices_finales, filtros)
        ajustes_finales = self._procesar_ajustes(excel_file)

        # Persistencia en disco de artefactos JSON
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.matrices_json_path, "w", encoding="utf-8") as f:
            json.dump(matrices_finales, f, ensure_ascii=False, indent=2)

        with open(self.ajustes_json_path, "w", encoding="utf-8") as f:
            json.dump(ajustes_finales, f, ensure_ascii=False, indent=2)

        print("--------------------------------------------------")
        print(f"[SUCCESS] Artefacto de matrices exportado: {self.matrices_json_path.name}")
        print(f"[SUCCESS] Artefacto de reglas exportado: {self.ajustes_json_path.name}")
        print("==================================================")