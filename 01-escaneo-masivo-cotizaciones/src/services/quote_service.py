"""Servicio de Cálculo Matemático para Cotizaciones Rápida.

Aplica fórmulas de markup comercial considerando estadísticas acumuladas 
de escaneo y niveles de margen de seguridad por defecto.

Principios aplicados:
    - Single Responsibility (SRP): Exclusivamente responsable del cálculo matemático de cotización.
"""

from typing import Dict

from ..models.entities import PriceStats


class QuoteService:
    """Calculador de precios de venta unitarios y totales para cotizaciones."""

    def create_quote(
        self,
        product_name: str,
        cantidad: int,
        precio_prov: float,
        stats: PriceStats,
        margen_defecto: float = 35.0,
    ) -> Dict[str, float]:
        """Calcula el margen, precio unitario y total para una solicitud.

        Args:
            product_name: Nombre del producto.
            cantidad: Unidades solicitadas (debe ser > 0).
            precio_prov: Costo unitario del proveedor (debe ser > 0).
            stats: Estadísticas históricas de precios.
            margen_defecto: Margen de respaldo en caso de falta de muestra.

        Returns:
            Diccionario con las claves 'margen', 'precio_unit' y 'total'.
        """
        cant_valid = max(1, int(cantidad))
        costo_valid = max(0.01, float(precio_prov))

        margen = stats.promedio_para_cantidad(cant_valid, margen_defecto)
        precio_unit = round(costo_valid * (1 + (margen / 100.0)), 2)
        total = round(precio_unit * cant_valid, 2)

        return {
            "margen": margen,
            "precio_unit": precio_unit,
            "total": total,
        }