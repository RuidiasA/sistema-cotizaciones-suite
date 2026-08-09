"""Módulo de Entidades de Dominio del Sistema de Cotizaciones.

Contiene las clases de transferencia de datos (DTOs) y las estructuras del
dominio comercial para filas escaneadas, métricas de precios, reportes de
archivos y la matriz de benchmarking por arquetipos.

Principios aplicados:
    - Single Responsibility (SRP): Cada entidad maneja exclusivamente su estado.
    - Encapsulamiento: Operaciones sobre métricas y selecciones de margen dentro de la entidad.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ScanRow:
    """Representa una fila individual extraída o descartada del escaneo.

    Attributes:
        fila_id: Índice o número de fila en la hoja de Excel.
        articulo: Descripción completa o detalle del producto.
        cantidad: Unidades del pedido.
        precio_prov: Costo unitario de proveedor (S/.).
        precio_cli: Precio unitario de venta al cliente (S/.).
        margen: Porcentaje de margen comercial generado.
        motivo: Causa de descarte si la fila falló las validaciones.
        arquetipo: Identificador normalizado de la variante de producto.
        margen_fila: Copia del margen para sincronización interna.
    """

    fila_id: int
    articulo: str
    cantidad: int
    precio_prov: float
    precio_cli: float
    margen: float
    motivo: Optional[str] = None
    arquetipo: str = ""
    margen_fila: float = 0.0


@dataclass
class PriceStats:
    """Acumulador estadístico de márgenes agrupado por tramos de volumen (Tiers).

    Attributes:
        acum_gt_1000: Acumulado de márgenes para pedidos >= 1000 unidades.
        count_gt_1000: Total de casos en el tier >= 1000.
        acum_gt_500: Acumulado de márgenes para pedidos >= 500 y < 1000 unidades.
        count_gt_500: Total de casos en el tier >= 500.
        acum_rest: Acumulado de márgenes para pedidos < 500 unidades.
        count_rest: Total de casos en el tier resto.
    """

    acum_gt_1000: float = 0.0
    count_gt_1000: int = 0
    acum_gt_500: float = 0.0
    count_gt_500: int = 0
    acum_rest: float = 0.0
    count_rest: int = 0

    def add_margin(self, cantidad: int, margen: float) -> None:
        """Suma un margen al acumulador según el tier de cantidad.

        Args:
            cantidad: Unidades cotizadas.
            margen: Porcentaje de margen calculado.
        """
        if cantidad >= 1000:
            self.acum_gt_1000 += margen
            self.count_gt_1000 += 1
        elif cantidad >= 500:
            self.acum_gt_500 += margen
            self.count_gt_500 += 1
        else:
            self.acum_rest += margen
            self.count_rest += 1

    def promedio_para_cantidad(self, cantidad: int, margen_defecto: float = 35.0) -> float:
        """Calcula el margen promedio ponderado para el tier asociado a la cantidad.

        Args:
            cantidad: Volumen a consultar.
            margen_defecto: Margen por defecto si no existen casos.

        Returns:
            Porcentaje de margen promedio redondeado a 2 decimales.
        """
        if cantidad >= 1000:
            acum, count = self.acum_gt_1000, self.count_gt_1000
        elif cantidad >= 500:
            acum, count = self.acum_gt_500, self.count_gt_500
        else:
            acum, count = self.acum_rest, self.count_rest

        if count > 0:
            return round(acum / count, 2)

        return margen_defecto

    def merge(self, other: Optional["PriceStats"]) -> None:
        """Fusiona los acumulados de otra instancia de forma segura.

        Args:
            other: Instancia a combinar.
        """
        if other is None:
            return

        self.acum_gt_1000 += other.acum_gt_1000
        self.count_gt_1000 += other.count_gt_1000
        self.acum_gt_500 += other.acum_gt_500
        self.count_gt_500 += other.count_gt_500
        self.acum_rest += other.acum_rest
        self.count_rest += other.count_rest


@dataclass
class FileScanReport:
    """Reporte del procesamiento individual de un archivo Excel.

    Attributes:
        file_name: Nombre del libro de Excel.
        sheet_name: Nombre o lista de pestañas escaneadas.
        matched_rows: Registros válidos procesados.
        failed_rows: Registros descartados con motivo de fallo.
        stats: Métricas de márgenes extraídas del archivo.
        error_message: Detalle de excepción en caso de error crítico de lectura.
    """

    file_name: str
    sheet_name: Optional[str] = None
    matched_rows: List[ScanRow] = field(default_factory=list)
    failed_rows: List[ScanRow] = field(default_factory=list)
    stats: PriceStats = field(default_factory=PriceStats)
    error_message: Optional[str] = None


@dataclass
class ArchetypeData:
    """Representa las métricas comerciales agregadas de un arquetipo por tiers.

    Attributes:
        nombre_arquetipo: Nombre del grupo (ej: "CASACA TASLAN CORPORATIVO").
        categoria: Categoría asignada.
        margen_tier_100: Margen para volumen < 500.
        casos_tier_100: Número de casos en tier 100.
        costo_avg_100: Costo promedio del proveedor en tier 100.
        precio_avg_100: Precio promedio al cliente en tier 100.
        margen_tier_500: Margen para volumen >= 500 y < 1000.
        casos_tier_500: Número de casos en tier 500.
        costo_avg_500: Costo promedio del proveedor en tier 500.
        precio_avg_500: Precio promedio al cliente en tier 500.
        margen_tier_1000: Margen para volumen >= 1000.
        casos_tier_1000: Número de casos en tier 1000.
        costo_avg_1000: Costo promedio del proveedor en tier 1000.
        precio_avg_1000: Precio promedio al cliente en tier 1000.
        actualizado_en: Fecha y hora de generación ISO.
        confianza_general: Porcentaje de confianza estadística (0-100%).
    """

    nombre_arquetipo: str
    categoria: str
    margen_tier_100: float = 0.0
    casos_tier_100: int = 0
    costo_avg_100: float = 0.0
    precio_avg_100: float = 0.0
    margen_tier_500: float = 0.0
    casos_tier_500: int = 0
    costo_avg_500: float = 0.0
    precio_avg_500: float = 0.0
    margen_tier_1000: float = 0.0
    casos_tier_1000: int = 0
    costo_avg_1000: float = 0.0
    precio_avg_1000: float = 0.0
    actualizado_en: str = ""
    confianza_general: float = 0.0


@dataclass
class BenchmarkingMatrix:
    """Matriz consolidada de inteligencia comercial para una categoría.

    Attributes:
        categoria: Nombre de la categoría o subcategoría.
        arquetipos: Lista de arquetipos generados.
        fecha_generacion: Marca de tiempo de procesamiento.
        total_registros_procesados: Total de filas evaluadas de entrada.
    """

    categoria: str
    arquetipos: List[ArchetypeData] = field(default_factory=list)
    fecha_generacion: str = ""
    total_registros_procesados: int = 0

    def get_arquetipo_por_nombre(self, nombre: str) -> Optional[ArchetypeData]:
        """Busca un arquetipo por su nombre ignorando diferencias de formato.

        Args:
            nombre: Cadena del arquetipo a buscar.

        Returns:
            Instancia de ArchetypeData o None si no se encuentra.
        """
        nombre_norm = str(nombre or "").strip().lower()
        if not nombre_norm:
            return None

        for arquetipo in self.arquetipos:
            if arquetipo.nombre_arquetipo.strip().lower() == nombre_norm:
                return arquetipo
        return None

    def get_margen_para_cantidad(self, nombre_arquetipo: str, cantidad: int) -> float:
        """Obtiene el margen correspondiente para una cantidad dada.

        Args:
            nombre_arquetipo: Nombre del arquetipo.
            cantidad: Volumen a consultar.

        Returns:
            Porcentaje de margen asignado al tier o 35.0% si no existe.
        """
        arquetipo = self.get_arquetipo_por_nombre(nombre_arquetipo)
        if arquetipo is None:
            return 35.0

        if cantidad >= 1000:
            return arquetipo.margen_tier_1000
        if cantidad >= 500:
            return arquetipo.margen_tier_500
        return arquetipo.margen_tier_100