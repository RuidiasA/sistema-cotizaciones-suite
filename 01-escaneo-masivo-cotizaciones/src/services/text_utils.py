"""Módulo de Utilidades Textuales y Extracción Forense.

Proporciona funciones puras y optimizadas para la limpieza, normalización,
filtrado de ruido y extracción de atributos (materiales, segmentos y productos base).

Principios aplicados:
    - Single Responsibility (SRP): Utilidades de parsing y transformación textual.
    - DRY: Funciones puras reutilizables en todo el dominio de servicios.
"""

from functools import lru_cache
import re
from typing import Dict, Optional
import unicodedata

import pandas as pd

_MATERIALES_BASE = (
    "ACERO",
    "ACRILICO",
    "ALGODON",
    "ALUMINIO",
    "BIOCUERO",
    "CATIONI",
    "CERAMICA",
    "CUERINA",
    "CUERO",
    "DENIM",
    "DRILL",
    "FRANELA",
    "IMPERMEABLE",
    "JERSEY",
    "LINO SERMAT",
    "LINO",
    "LONA LABRADA",
    "MADERA",
    "METAL",
    "METALICO",
    "MICROFIBRA",
    "MICROPOROSO",
    "NOTEX",
    "NYLON",
    "PLASTICO",
    "POLIESTER",
    "PORCELANA",
    "SOFTSHELL",
    "TASLAN",
    "TELA",
    "TETRON",
    "TOCUYO",
    "VINIL",
    "VIDRIO",
)

_SEGMENTOS_CALIDAD = (
    "CORPORATIVA",
    "CORPORATIVO",
    "ECOLOGICA",
    "ECOLOGICO",
    "EJECUTIVA",
    "EJECUTIVO",
    "IMPORTADO",
    "IMPORTADOS",
    "PUBLICITARIA",
    "PUBLICITARIO",
    "PROMOCIONAL",
    "PROMOCIONALES",
)

_PALABRAS_SERVICIO = (
    "COSTO",
    "DESCRIPCION",
    "DISEÑO",
    "EMBALAJE",
    "ENVIO",
    "FLETE",
    "MOVILIDAD",
    "ROTULADO",
    "SERV",
    "SERVICE",
    "SERVICIO",
)

_RUIDO_ESPECIFICACION = (
    "ADICIONAL",
    "ALTAMURA",
    "ARMADO",
    "CAJA",
    "CAPACIDAD",
    "CARACTERISTICA",
    "COD",
    "CODIGO",
    "COLOR",
    "COTIZACION",
    "FABRICACION",
    "GRANDE",
    "INC",
    "INCLUYE",
    "MEDIANA",
    "MEDIANO",
    "MEDIDA",
    "MODELO",
    "NACIONAL",
    "PAGO",
    "PEQUENA",
    "PEQUENO",
    "PRESENTACION",
    "PROD",
    "PRODUCCION",
    "PRODUCTO",
    "PROPUESTA",
    "PROV",
    "PROVEEDOR",
    "RECOTIZACION",
    "TALLA",
    "TIPO",
    "TOTAL",
)


def limpiar_y_entero(val: object) -> int:
    """Extrae el primer entero válido de un valor heterogéneo.

    Args:
        val: Objeto o cadena a procesar.

    Returns:
        Número entero extraído o 0 si no es convertible.
    """
    try:
        if pd.isna(val):
            return 0
        s = str(val).lower().replace(",", "").strip()
        num_match = re.findall(r"\d+\.?\d*", s)
        return int(float(num_match[0])) if num_match else 0
    except Exception:
        return 0


def limpiar_precio(val: object) -> float:
    """Limpia y convierte representaciones monetarias a flotante.

    Args:
        val: Valor monetario en formato texto o numérico.

    Returns:
        Valor flotante extraído o 0.0.
    """
    try:
        if pd.isna(val):
            return 0.0
        s = str(val).lower().replace("s/.", "").replace("s/", "").replace(",", "").strip()
        matches = re.findall(r"\d+\.?\d*", s)
        return float(matches[0]) if matches else 0.0
    except Exception:
        return 0.0


@lru_cache(maxsize=4096)
def normalizar_texto(texto: str) -> str:
    """Normaliza texto removiendo tildes, caracteres especiales y convierte a minúsculas.

    Args:
        texto: Cadena original.

    Returns:
        Texto sin tildes ni caracteres especiales, separado por espacios sencillos.
    """
    base = unicodedata.normalize("NFKD", str(texto or "").lower())
    sin_tildes = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes).strip()


def recortar_detalle(valor: object, max_len: int = 70) -> str:
    """Recorta cadenas de texto largas agregando puntos suspensivos.

    Args:
        valor: Texto a recortar.
        max_len: Longitud máxima permitida.

    Returns:
        Texto recortado.
    """
    if pd.isna(valor):
        return ""
    texto = re.sub(r"\s+", " ", str(valor)).strip()
    if len(texto) <= max_len:
        return texto
    return texto[: max_len - 3].rstrip() + "..."


@lru_cache(maxsize=2048)
def extraer_material(texto: str) -> Optional[str]:
    """Identifica el material predominante presente en el texto.

    Args:
        texto: Descripción del producto.

    Returns:
        Nombre del material en mayúsculas o None.
    """
    texto_norm = normalizar_texto(texto)
    if not texto_norm:
        return None

    materiales_ordenados = sorted(_MATERIALES_BASE, key=len, reverse=True)
    for material in materiales_ordenados:
        material_norm = normalizar_texto(material)
        if re.search(rf"\b{re.escape(material_norm)}\b", texto_norm):
            return material
    return None


@lru_cache(maxsize=2048)
def extraer_segmento_calidad(texto: str) -> Optional[str]:
    """Extrae el segmento o tier de calidad comercial del texto.

    Args:
        texto: Descripción del producto.

    Returns:
        Nombre del segmento o None.
    """
    texto_norm = normalizar_texto(texto)
    if not texto_norm:
        return None

    for segmento in _SEGMENTOS_CALIDAD:
        segmento_norm = normalizar_texto(segmento)
        if re.search(rf"\b{re.escape(segmento_norm)}s?\b", texto_norm):
            return segmento
        if segmento_norm.endswith("a"):
            plural_femenino = f"{segmento_norm[:-1]}as"
            if re.search(rf"\b{re.escape(plural_femenino)}\b", texto_norm):
                return segmento
    return None


@lru_cache(maxsize=2048)
def remover_ruido_de_especificacion(texto: str) -> str:
    """Elimina números, adjetivos irrelevantes y palabras de relleno de la descripción.

    Args:
        texto: Cadena original.

    Returns:
        Texto limpio en mayúsculas listo para agrupamiento.
    """
    texto_norm = normalizar_texto(texto)
    if not texto_norm:
        return ""

    texto_sin_numeros = re.sub(r"\d+", "", texto_norm)
    texto_sin_numeros = re.sub(r"\s+", " ", texto_sin_numeros).strip()
    tokens = texto_sin_numeros.split()
    ruido_norm = {normalizar_texto(p) for p in _RUIDO_ESPECIFICACION}
    tokens_filtrados = [tok for tok in tokens if tok not in ruido_norm]
    return " ".join(tokens_filtrados).upper().strip()


@lru_cache(maxsize=1)
def _build_canonical_tag_map() -> Dict[str, str]:
    from ..models.constants import MACRO_CATEGORIAS

    canonical_map: Dict[str, str] = {}
    for macro_info in MACRO_CATEGORIAS.values():
        subcategorias = macro_info.get("subcategorias", {})
        for clusters in subcategorias.values():
            for cluster in clusters:
                tags = cluster.get("tags", [])
                if not tags:
                    continue
                canonical_name = str(tags[0]).strip().upper()
                for tag in tags:
                    tag_norm = normalizar_texto(tag)
                    if tag_norm:
                        canonical_map[tag_norm] = canonical_name
    return canonical_map


def extraer_producto_base(texto_limpio: str) -> str:
    """Asigna la raíz canónica oficial del producto según la taxonomía.

    Args:
        texto_limpio: Descripción filtrada.

    Returns:
        Nombre canónico en mayúsculas o cadena vacía.
    """
    texto_norm = normalizar_texto(texto_limpio)
    if not texto_norm:
        return ""

    from ..models.constants import MACRO_CATEGORIAS

    scores_subcat: Dict[str, int] = {}
    match_canonicos: Dict[str, str] = {}
    tokens_texto = set(texto_norm.split())

    for macro_info in MACRO_CATEGORIAS.values():
        for subcat, clusters in macro_info.get("subcategorias", {}).items():
            for cluster in clusters:
                tags = cluster.get("tags", [])
                exclusions = {normalizar_texto(ex) for ex in cluster.get("exclude", [])}

                if not tags or tokens_texto.intersection(exclusions):
                    continue

                canonical_name = str(tags[0]).strip().upper()

                for tag in tags:
                    tag_norm = normalizar_texto(tag)
                    if not tag_norm:
                        continue

                    palabras_tag = set(tag_norm.split())
                    if palabras_tag.issubset(tokens_texto):
                        scores_subcat[subcat] = scores_subcat.get(subcat, 0) + 10
                        match_canonicos[subcat] = canonical_name

                        for otro_tag in tags:
                            otro_norm = normalizar_texto(otro_tag)
                            if otro_norm != tag_norm and set(otro_norm.split()).issubset(tokens_texto):
                                scores_subcat[subcat] += 5

    if not scores_subcat:
        return ""

    subcat_ganadora = max(scores_subcat, key=scores_subcat.get)
    return match_canonicos[subcat_ganadora]


def es_servicio_o_logistica(texto: str) -> bool:
    """Evalúa si una descripción pertenece a un rubro logístico o no tangible.

    Args:
        texto: Descripción a verificar.

    Returns:
        True si es un servicio o flete, False en caso contrario.
    """
    texto_norm = normalizar_texto(texto)
    if not texto_norm:
        return False

    for keyword in _PALABRAS_SERVICIO:
        kw_norm = normalizar_texto(keyword)
        if re.search(rf"\b{re.escape(kw_norm)}\b", texto_norm):
            return True
    return False