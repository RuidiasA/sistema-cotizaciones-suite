"""Módulo de Limpieza Textual y Clasificación Dinámica de Arquetipos.

Consume la taxonomía maestra de constants.py (Módulo 01) para construir
las reglas de clasificación y mapear la totalidad de productos del sistema.
"""

import importlib.util
from pathlib import Path
from typing import Dict, Optional, Any
import pandas as pd

# Carga dinámica de constants.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ruta_constants = BASE_DIR / "01-escaneo-masivo-cotizaciones" / "src" / "models" / "constants.py"

if ruta_constants.exists():
    spec = importlib.util.spec_from_file_location("constants_mod", ruta_constants)
    if spec and spec.loader:
        constants_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(constants_mod)
        MACRO_CATEGORIAS = getattr(constants_mod, "MACRO_CATEGORIAS", {})
    else:
        MACRO_CATEGORIAS = {}
else:
    MACRO_CATEGORIAS = {}


def _construir_config_productos() -> Dict[str, Dict[str, Any]]:
    """Transforma la taxonomía jerárquica en un diccionario de arquetipos planos."""
    config_dinamica: Dict[str, Dict[str, Any]] = {}

    for macro, macro_data in MACRO_CATEGORIAS.items():
        exclusiones_globales = macro_data.get("global_exclude", [])
        
        for subcat, items in macro_data.get("subcategorias", {}).items():
            for idx, item in enumerate(items):
                tags = item.get("tags", [])
                if not tags:
                    continue
                
                # Tag principal como nombre representativo
                tag_principal = tags[0].upper().replace(" ", "_").replace(".", "")
                arquetipo_id = f"{tag_principal}"
                
                # Manejo de colisiones de IDs
                if arquetipo_id in config_dinamica:
                    arquetipo_id = f"{arquetipo_id}_{idx}"

                exclusiones = list(set(item.get("exclude", []) + exclusiones_globales))

                config_dinamica[arquetipo_id] = {
                    "nombre_comercial": tags[0].capitalize(),
                    "macro_categoria": macro,
                    "subcategoria": subcat,
                    "filtros_prenda": tags,
                    "filtros_material": [],
                    "exclusiones": exclusiones
                }

    return config_dinamica


CONFIG_PRODUCTOS: Dict[str, Dict[str, Any]] = _construir_config_productos()


def clasificar_producto_estricto(descripcion: Any) -> Optional[str]:
    """Evalúa la descripción comercial contra la taxonomía unificada del sistema.

    Args:
        descripcion: Texto de la fila extraída del Excel.

    Returns:
        ID del arquetipo (str) o None si no hace match.
    """
    if not descripcion or pd.isna(descripcion):
        return None

    text = str(descripcion).lower().strip()

    for arquetipo, config in CONFIG_PRODUCTOS.items():
        # 1. Control de Exclusiones
        if any(ex in text for ex in config.get("exclusiones", [])):
            continue

        # 2. Match por Tags/Tokens de la categoría
        match_tag = any(p in text for p in config["filtros_prenda"])

        if match_tag:
            return arquetipo

    return None