"""Servicio de Gestión de Variaciones y Circularidad Semántica.

Maneja los clústeres de sinónimos, tags y exclusiones por categoría para
garantizar la circularidad en la búsqueda (Sacos Semánticos).

Principios aplicados:
    - Single Responsibility (SRP): Gestión exclusiva de variaciones de la taxonomía.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from .text_utils import normalizar_texto


class VariationService:
    """Gestor de variaciones y clústeres de palabras clave."""

    def __init__(self, variaciones_por_categoria: Dict[str, Dict[str, Any]]) -> None:
        """Inicializa el servicio cargando la taxonomía de constantes.

        Args:
            variaciones_por_categoria: Estructura de constantes MACRO_CATEGORIAS.
        """
        self._variaciones = variaciones_por_categoria
        self._cached_global_pack: Optional[Dict[str, List[str]]] = None
        self._cached_all_variations: Optional[List[str]] = None
        self._cached_category_packs: Dict[str, Dict[str, Any]] = {}

    def get_categories(self) -> List[str]:
        """Obtiene la lista formateada de categorías para la interfaz gráfica.

        Returns:
            Lista de categorías principales y compuestas ("Macro > Sub").
        """
        categorias: List[str] = []
        for macro in sorted(self._variaciones.keys()):
            categorias.append(macro)
            subcategorias = self._variaciones.get(macro, {}).get("subcategorias", {})
            for sub in sorted(subcategorias.keys()):
                categorias.append(f"{macro} > {sub}")
        return categorias

    def _resolve_category(self, categoria: str) -> Tuple[Optional[str], Optional[str]]:
        categoria = (categoria or "").strip()
        if not categoria:
            return None, None

        if ">" in categoria:
            parts = [part.strip() for part in categoria.split(">", 1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                return parts[0], parts[1]

        if categoria in self._variaciones:
            return categoria, None

        for macro, info in self._variaciones.items():
            if categoria in info.get("subcategorias", {}):
                return macro, categoria

        return None, None

    def _get_clusters(self, categoria: str) -> List[Dict[str, Any]]:
        macro, sub = self._resolve_category(categoria)
        if not macro:
            return []

        subcategorias = self._variaciones.get(macro, {}).get("subcategorias", {})
        if sub:
            return subcategorias.get(sub, [])

        clusters: List[Dict[str, Any]] = []
        for sub_clusters in subcategorias.values():
            clusters.extend(sub_clusters)
        return clusters

    def get_variations(self, categoria: str, keyword: str) -> Dict[str, List[str]]:
        """Busca el clúster semántico para una palabra clave o categoría.

        Args:
            categoria: Categoría seleccionada.
            keyword: Término de búsqueda.

        Returns:
            Search pack con 'tags' y 'exclude'.
        """
        keyword_norm = normalizar_texto(keyword or "")
        clusters = self._get_clusters(categoria)

        if keyword_norm:
            for cluster in clusters:
                tags_norm = [normalizar_texto(t) for t in cluster.get("tags", [])]
                if keyword_norm in tags_norm:
                    return {"tags": cluster.get("tags", []), "exclude": cluster.get("exclude", [])}
            return {"tags": [keyword.strip()], "exclude": []}

        if clusters:
            all_tags = []
            for cluster in clusters:
                all_tags.extend(cluster.get("tags", []))
            return {"tags": all_tags, "exclude": []}

        return {"tags": [], "exclude": []}

    def get_global_search_pack(self) -> Dict[str, List[str]]:
        """Genera un pack global de tags unificados en caché.

        Returns:
            Search pack global con todos los tags únicos de la taxonomía.
        """
        if self._cached_global_pack is not None:
            return self._cached_global_pack

        tags_unicos: List[str] = []
        vistos = set()

        for subcategorias in self._variaciones.values():
            for clusters in subcategorias.get("subcategorias", {}).values():
                for cluster in clusters:
                    for tag in cluster.get("tags", []):
                        tag_norm = normalizar_texto(tag)
                        if tag_norm and tag_norm not in vistos:
                            vistos.add(tag_norm)
                            tags_unicos.append(tag)

        self._cached_global_pack = {"tags": tags_unicos, "exclude": []}
        return self._cached_global_pack

    def _compile_pattern(self, terms: List[str]) -> Optional[re.Pattern]:
        normalized_terms = sorted({normalizar_texto(term) for term in terms if term}, key=len, reverse=True)
        if not normalized_terms:
            return None
        pattern = r"\b(?:" + "|".join(map(re.escape, normalized_terms)) + r")\b"
        return re.compile(pattern)

    def _get_category_pack(self, categoria: str) -> Dict[str, Any]:
        category_key = (categoria or "").strip()
        if category_key in self._cached_category_packs:
            return self._cached_category_packs[category_key]

        clusters = self._get_clusters(category_key)
        macro, _ = self._resolve_category(category_key)
        global_excludes = self._variaciones.get(macro, {}).get("global_exclude", []) if macro else []

        tags: List[str] = []
        excludes: List[str] = []
        for cluster in clusters:
            tags.extend(cluster.get("tags", []))
            excludes.extend(cluster.get("exclude", []))
        excludes.extend(global_excludes)

        pack = {
            "tags": tags,
            "exclude": excludes,
            "compiled_tags": self._compile_pattern(tags),
            "compiled_excludes": self._compile_pattern(excludes),
        }
        self._cached_category_packs[category_key] = pack
        return pack

    def matches_category(self, categoria: str, texto_producto: str) -> bool:
        """Verifica si el texto de un producto pertenece a una categoría dada.

        Args:
            categoria: Nombre de la categoría.
            texto_producto: Descripción a evaluar.

        Returns:
            True si coincide con los tags y no con las exclusiones.
        """
        if not categoria:
            return True

        pack = self._get_category_pack(categoria)
        if not pack["tags"] and not pack["exclude"]:
            return True

        texto_norm = normalizar_texto(texto_producto or "")
        if not texto_norm:
            return False

        compiled_excludes = pack.get("compiled_excludes")
        if compiled_excludes is not None and compiled_excludes.search(texto_norm):
            return False

        compiled_tags = pack.get("compiled_tags")
        if compiled_tags is not None and compiled_tags.search(texto_norm):
            return True

        if compiled_tags is None:
                return False

        return False

    def is_known_product(self, product_name: str) -> bool:
        """Determina si un producto es conocido en la taxonomía.

        Args:
            product_name: Nombre a consultar.

        Returns:
            True si existe un tag similar.
        """
        prod_norm = normalizar_texto(product_name or "")
        if not prod_norm:
            return False

        for variation in self._all_variations():
            var_norm = normalizar_texto(variation)
            if prod_norm in var_norm or var_norm in prod_norm:
                return True
        return False

    def _all_variations(self) -> List[str]:
        if self._cached_all_variations is not None:
            return self._cached_all_variations

        flat_list = []
        for subcategorias in self._variaciones.values():
            for clusters in subcategorias.get("subcategorias", {}).values():
                for cluster in clusters:
                    flat_list.extend(cluster.get("tags", []))
        self._cached_all_variations = flat_list
        return flat_list