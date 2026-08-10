"""Servicio de Inteligencia Comercial y Benchmarking por Arquetipos.

Agrupa registros escaneados en arquetipos de productos mediante la concatenación
de raíz canónica, material y segmento. Ejecuta algoritmos de inferencia y
restricciones de monotonía comercial por tiers de cantidad (100, 500, 1000).

Principios applied:
    - Single Responsibility (SRP): Exclusivamente dedicado al cálculo e inferencia de benchmarking.
    - Information Expert: Mantiene las constantes y lógica de estimación de márgenes.
"""

from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd

from ..models.entities import ArchetypeData, BenchmarkingMatrix, ScanRow
from .text_utils import (
    es_servicio_o_logistica,
    extraer_material,
    extraer_producto_base,
    extraer_segmento_calidad,
    normalizar_texto,
    remover_ruido_de_especificacion,
)


class BenchmarkingService:
    """Calculador de matrices de benchmarking e inferencia de márgenes comerciales."""

    MARGEN_BASE = 35.0
    PESO_VIRTUAL = 3

    def __init__(self, umbral_confianza: int = 3) -> None:
        """Inicializa el servicio.

        Args:
            umbral_confianza: Muestra mínima de registros para 100% de confianza.
        """
        self._umbral_confianza = max(1, int(umbral_confianza))

    def extraer_arquetipo(self, fila_detalle: str, keyword: str = "") -> Optional[str]:
        """Construye la firma del arquetipo (Base + Material + Segmento).

        Args:
            fila_detalle: Descripción original.
            keyword: Palabra clave opcional.

        Returns:
            Nombre del arquetipo en mayúsculas o None.
        """
        if es_servicio_o_logistica(fila_detalle):
            return None

        limpio = remover_ruido_de_especificacion(fila_detalle)
        limpio_norm = normalizar_texto(limpio)
        if not limpio_norm:
            return None

        material = extraer_material(limpio)
        segmento = extraer_segmento_calidad(limpio)
        base = extraer_producto_base(limpio)

        if not base:
            return None

        partes = [base]
        if material and material not in partes:
            partes.append(material)
        if segmento and segmento not in partes:
            partes.append(segmento)

        return " ".join(partes).strip()

    def es_servicio_excluido(self, articulo: str) -> bool:
        """Verifica si un artículo debe ser omitido por ser un servicio."""
        return es_servicio_o_logistica(articulo)

    def generar_benchmarking(self, scan_rows: List[ScanRow], categoria: str, keyword: str = "") -> BenchmarkingMatrix:
        """Genera la matriz analítica de benchmarking.

        Args:
            scan_rows: Colección de filas válidas procesadas.
            categoria: Categoría seleccionada.
            keyword: Término de búsqueda opcional.

        Returns:
            BenchmarkingMatrix consolidada.
        """
        fecha = datetime.now().isoformat(timespec="seconds")
        records: List[Dict[str, object]] = []

        for row in scan_rows:
            if row.cantidad <= 0:
                logging.warning("Benchmarking: descartado por cantidad<=0 -> %s | cantidad=%s", row.articulo, row.cantidad)
                continue
            if row.margen <= 0:
                logging.warning("Benchmarking: descartado por margen<=0 -> %s | margen=%s", row.articulo, row.margen)
                continue

            arquetipo = self.extraer_arquetipo(row.articulo, keyword)
            if not arquetipo:
                logging.warning("Benchmarking: descartado por arquetipo vacío -> %s", row.articulo)
                continue

            raiz = arquetipo.split()[0] if arquetipo else ""
            records.append(
                {
                    "arquetipo": arquetipo,
                    "raiz_producto": raiz,
                    "tier": self._tier_para_cantidad(row.cantidad),
                    "costo_prov": float(row.precio_prov),
                    "precio_cli": float(row.precio_cli),
                    "margen": float(row.margen),
                }
            )

        if not records:
            return BenchmarkingMatrix(categoria=categoria, arquetipos=[], fecha_generacion=fecha, total_registros_procesados=0)

        df_raw = pd.DataFrame(records)

        # Filtro de relevancia dinámico (Top 3 variantes)
        ranking = (
            df_raw.groupby(["raiz_producto", "arquetipo"], as_index=False)
            .size()
            .rename(columns={"size": "conteo"})
            .sort_values(["raiz_producto", "conteo", "arquetipo"], ascending=[True, False, True])
        )
        arquetipos_validos = set(ranking.groupby("raiz_producto", sort=False).head(3)["arquetipo"])

        df = df_raw[df_raw["arquetipo"].isin(arquetipos_validos)].copy()

        grouped = (
            df.groupby(["arquetipo", "tier"], as_index=False)
            .agg(
                margen_promedio=("margen", "mean"),
                costo_promedio=("costo_prov", "mean"),
                precio_promedio=("precio_cli", "mean"),
                casos=("precio_cli", "count"),
            )
            .sort_values(["arquetipo", "tier"])
        )

        bucket: Dict[str, Dict[str, Dict[str, float]]] = {}
        for row in grouped.itertuples(index=False):
            arquetipo = str(row.arquetipo)
            tier = str(row.tier)
            bucket.setdefault(arquetipo, {})[tier] = {
                "margen": round(float(row.margen_promedio), 2),
                "costo": round(float(row.costo_promedio), 2),
                "precio": round(float(row.precio_promedio), 2),
                "casos": int(row.casos),
            }

        arquetipos: List[ArchetypeData] = []
        for nombre, tiers in sorted(bucket.items()):
            t100 = tiers.get("100", {"margen": 0.0, "costo": 0.0, "precio": 0.0, "casos": 0})
            t500 = tiers.get("500", {"margen": 0.0, "costo": 0.0, "precio": 0.0, "casos": 0})
            t1000 = tiers.get("1000", {"margen": 0.0, "costo": 0.0, "precio": 0.0, "casos": 0})

            c100, c500, c1000 = int(t100["casos"]), int(t500["casos"]), int(t1000["casos"])
            m100_obs = float(t100["margen"]) if c100 > 0 else None
            m500_obs = float(t500["margen"]) if c500 > 0 else None
            m1000_obs = float(t1000["margen"]) if c1000 > 0 else None

            margen_100, margen_500, margen_1000, c100, c500, c1000 = self._inferir_margenes(
                m100_obs, m500_obs, m1000_obs, c100, c500, c1000
            )

            casos_totales = c100 + c500 + c1000
            arquetipos.append(
                ArchetypeData(
                    nombre_arquetipo=nombre,
                    categoria=categoria,
                    margen_tier_100=round(margen_100, 2),
                    casos_tier_100=c100,
                    costo_avg_100=float(t100["costo"]),
                    precio_avg_100=float(t100["precio"]),
                    margen_tier_500=round(margen_500, 2),
                    casos_tier_500=c500,
                    costo_avg_500=float(t500["costo"]),
                    precio_avg_500=float(t500["precio"]),
                    margen_tier_1000=round(margen_1000, 2),
                    casos_tier_1000=c1000,
                    costo_avg_1000=float(t1000["costo"]),
                    precio_avg_1000=float(t1000["precio"]),
                    actualizado_en=fecha,
                    confianza_general=self.calcular_confianza(casos_totales),
                )
            )

        return BenchmarkingMatrix(
            categoria=categoria, arquetipos=arquetipos, fecha_generacion=fecha, total_registros_procesados=len(records)
        )

    def _weighted_avg(self, valor_a: float, peso_a: int, valor_b: float, peso_b: int) -> float:
        total_peso = max(1, peso_a + peso_b)
        return round(((valor_a * peso_a) + (valor_b * peso_b)) / total_peso, 2)

    def _inferir_margenes(
        self,
        margen_100_obs: Optional[float],
        margen_500_obs: Optional[float],
        margen_1000_obs: Optional[float],
        c100: int,
        c500: int,
        c1000: int,
    ) -> Tuple[float, float, float, int, int, int]:
        m100, m500, m1000 = margen_100_obs, margen_500_obs, margen_1000_obs

        # Escenarios de inferencia
        if m100 is None and m500 is None and m1000 is None:
            m100 = m500 = m1000 = self.MARGEN_BASE
        elif m100 is not None and m500 is None and m1000 is None:
            m1000 = self._weighted_avg(m100, c100, self.MARGEN_BASE, self.PESO_VIRTUAL)
            m500 = self._weighted_avg(m100, c100, m1000, self.PESO_VIRTUAL)
        elif m1000 is not None and m100 is None and m500 is None:
            piso = max(self.MARGEN_BASE, m1000)
            m100 = m500 = piso
        elif m500 is not None and m100 is None and m1000 is None:
            m100 = max(self.MARGEN_BASE, m500)
            m1000 = self._weighted_avg(m500, c500, self.MARGEN_BASE, self.PESO_VIRTUAL)
        elif m100 is not None and m1000 is not None and m500 is None:
            m500 = self._weighted_avg(m100, c100, m1000, c1000)

        m100 = m100 if m100 is not None else self.MARGEN_BASE
        m1000 = m1000 if m1000 is not None else self.MARGEN_BASE
        m500 = m500 if m500 is not None else self._weighted_avg(m100, c100, m1000, c1000)

        # Restricción de monotonía comercial
        m100_ant, m500_ant, m1000_ant = m100, m500, m1000

        if m500_ant < m1000_ant:
            m500 = m1000_ant
        if m500_ant > m100_ant:
            m500 = m100_ant
        if m100_ant < m500:
            m100 = m500
        if m1000_ant > m500:
            m1000 = m500

        return round(m100, 2), round(m500, 2), round(m1000, 2), c100, c500, c1000

    def calcular_confianza(self, casos_totales: int) -> float:
        confianza = (float(casos_totales) / float(self._umbral_confianza)) * 100.0
        return round(min(100.0, max(0.0, confianza)), 2)

    def _tier_para_cantidad(self, cantidad: int) -> str:
        if cantidad >= 1000:
            return "1000"
        if cantidad >= 500:
            return "500"
        return "100"