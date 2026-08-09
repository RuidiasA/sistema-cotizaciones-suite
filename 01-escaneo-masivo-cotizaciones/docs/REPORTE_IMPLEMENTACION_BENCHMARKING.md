# REPORTE TÉCNICO: Implementación de Benchmarking en Compipro 2.0

**Fecha:** May 14, 2026  
**Versión del Spec:** benchmarking_specs.md  
**Análisis Scope:** models/, services/, controllers/  

---

## RESUMEN EJECUTIVO

El spec demanda un motor de **Benchmarking por Arquetipos** que agrupe productos históricos por su identidad comercial (base + material + segmento de calidad), calcule márgenes por tiers de cantidad (100, 500, 1000) y exporte reportes en Excel.

**Estado Actual:** Sistema capaz de escanear y cotizar; falta completamente la **lógica de agrupación semántica y la matriz de benchmarking**.

**Impacto en MVC:** Requiere **2 nuevas clases en models**, **1 nuevo servicio**, y **refactorización del controlador** sin romper el patrón MVC.

---

## 1. ANÁLISIS DE BRECHAS

### 1.1 Modelo de Datos (src/models/)

#### ✅ LO QUE EXISTE
| Clase | Responsabilidad | Estado |
|-------|-----------------|--------|
| `ScanRow` | Fila individual con precio y margen | Completo |
| `PriceStats` | Agregador de márgenes por 3 tiers (100, 500, 1000) | Completo |
| `FileScanReport` | Contenedor de filas escaneadas + errores | Completo |

#### ❌ LO QUE FALTA
| Clase | Responsabilidad | Prioridad | Razón |
|-------|-----------------|-----------|-------|
| `ArchetypeData` | Representación de un arquetipo único con sus tiers | CRÍTICA | La columna 1 del spec (Producto Arquetipo) sin esta clase no tiene contenedor |
| `BenchmarkingMatrix` | Matriz completa de arquetipos por categoría + tiers | CRÍTICA | La exportación a Excel necesita un formato estructurado |

#### Propuesta de Entidades

**`ArchetypeData`** (Dataclass)
```python
@dataclass
class ArchetypeData:
    """Representa un arquetipo único (base + material + segmento de calidad)"""
    nombre_arquetipo: str              # Ej: "GORRO DRILL PUBLICITARIO"
    categoria: str                      # Ej: "prendas de cabeza"
    
    # Tier 100 (< 500 unidades)
    margen_tier_100: float             # Promedio de márgenes
    casos_tier_100: int                # Nro. de registros históricos
    
    # Tier 500 (>= 500 y < 1000)
    margen_tier_500: float
    casos_tier_500: int
    
    # Tier 1000 (>= 1000)
    margen_tier_1000: float
    casos_tier_1000: int
    
    # Metadatos
    actualizado_en: str                # Timestamp del último escaneo
    confianza_general: float           # Porcentaje: (casos_totales / umbral_minimo) * 100
```

**`BenchmarkingMatrix`** (Dataclass)
```python
@dataclass
class BenchmarkingMatrix:
    """Matriz completa de benchmarking por categoría"""
    categoria: str
    arquetipos: List[ArchetypeData]    # Lista de arquetipos únicos
    fecha_generacion: str
    total_registros_procesados: int
    
    def get_arquetipo_por_nombre(self, nombre: str) -> Optional[ArchetypeData]:
        """Búsqueda rápida por nombre"""
        ...
    
    def get_margen_para_cantidad(self, nombre_arquetipo: str, cantidad: int) -> float:
        """Retorna margen sugerido para cantidad y arquetipo dados"""
        ...
```

---

### 1.2 Servicios (src/services/)

#### ✅ LO QUE EXISTE
| Servicio | Métodos | Estado |
|----------|---------|--------|
| `VariationService` | `get_categories()`, `get_variations()`, `is_known_product()` | Completo |
| `ExcelScanService` | `scan_folder()`, `scan_file()`, `_process_rows()` | Completo |
| `QuoteService` | `create_quote()` | Completo |

#### ❌ LO QUE FALTA

**`BenchmarkingService`** (NUEVO - archivo: src/services/benchmarking_service.py)

Responsabilidades:
1. **Extracción de Arquetipos:** Limpieza y segmentación de `ScanRow.articulo` en componentes
2. **Agrupación por Tier:** Clasificación en 100/500/1000 y agregación de márgenes
3. **Filtrado de Servicios:** Exclusión de palabras clave (MOVILIDAD, ENVÍO, EMBALAJE, etc.)
4. **Construcción de la Matriz:** Generación de `BenchmarkingMatrix` lista para exportar

Métodos Propuestos:
```python
class BenchmarkingService:
    def __init__(self):
        pass
    
    def extraer_arquetipo(self, fila_detalle: str) -> Optional[str]:
        """
        Transforma "GORRO DRILL PUBLICITARIO TALLA L" -> "GORRO DRILL PUBLICITARIO"
        Lógica:
        - Extrae base + material + segmento de calidad
        - Elimina talla, color, dimensión, etc.
        """
        ...
    
    def es_servicio_excluido(self, articulo: str) -> bool:
        """
        Retorna True si contiene MOVILIDAD, ENVÍO, EMBALAJE, ROTULADO, FLETE
        """
        ...
    
    def generar_benchmarking(
        self, 
        scan_rows: List[ScanRow],
        categoria: str
    ) -> BenchmarkingMatrix:
        """
        Agrupa filas por arquetipo, calcula tiers y márgenes
        Retorna BenchmarkingMatrix lista para exportar
        """
        ...
    
    def calcular_confianza(self, casos_totales: int) -> float:
        """
        Confianza = (casos_totales / umbral_minimo) * 100
        Umbral mínimo = 3 casos por tier
        """
        ...
```

---

### 1.3 Controlador (src/controllers/app_controller.py)

#### ✅ LO QUE EXISTE
| Método | Responsabilidad |
|--------|-----------------|
| `__init__()` | Inicialización de servicios y vista |
| `run()` | Lanzamiento de la app |
| `handle_scan()` | Dispara escaneo en background |
| `handle_cancel()` | Cancela escaneo activo |
| `_on_scan_done()` | Callback para renderizar resultados |
| `handle_quote()` | Genera cotización rápida |

#### ❌ LO QUE FALTA

**Nueva Inyección de Dependencia:**
```python
def __init__(self) -> None:
    # ... código existente ...
    self._benchmarking_service = BenchmarkingService()  # NUEVA
```

**Nuevos Métodos:**
```python
def handle_benchmarking(self, categoria: str = "") -> None:
    """
    Orquesta la generación de matriz de benchmarking a partir de datos ya escaneados.
    Flujo:
    1. Validar que self._matched_total > 0 (hay datos del escaneo)
    2. Lanzar en ThreadPoolExecutor a self._benchmarking_service.generar_benchmarking()
    3. Callback -> actualizar UI con matriz
    """
    ...

def _on_benchmarking_done(self, future) -> None:
    """
    Callback después de generar benchmarking.
    Actualiza la vista y prepara para exportar.
    """
    ...

def handle_export_benchmarking(self, categoria: str, output_path: str) -> None:
    """
    Exporta la matriz de benchmarking a Excel.
    Nombre de archivo: Benchmarking_[Categoria].xlsx
    """
    ...
```

---

### 1.4 Utilidades (src/services/text_utils.py)

#### ✅ LO QUE EXISTE
```python
limpiar_y_entero()     # Extrae números
limpiar_precio()       # Limpia formato de precio
normalizar_texto()     # Normaliza con Regex y Unicodedata
recortar_detalle()     # Trunca con ellipsis
```

#### ❌ LO QUE FALTA

**Funciones de Arquetipos:**
```python
def extraer_material(texto: str) -> Optional[str]:
    """
    Identifica material de la descripción.
    Ej: "GORRO NOTEX PUBLICITARIO" -> "NOTEX"
    Materiales conocidos: NOTEX, TASLAN, NYLON, SOFTSHELL, JERSEY, LINO, DRILL, etc.
    """
    ...

def extraer_segmento_calidad(texto: str) -> Optional[str]:
    """
    Identifica si es PUBLICITARIO o CORPORATIVO (los únicos términos protegidos por spec).
    Ej: "GORRO DRILL PUBLICITARIO" -> "PUBLICITARIO"
    """
    ...

def remover_ruido_de_especificacion(texto: str) -> str:
    """
    Elimina talla, color, tipo, modelo, fabricación nacional, etc.
    Ej: "GORRO DRILL PUBLICITARIO TALLA L COLOR ROJO" -> "GORRO DRILL PUBLICITARIO"
    """
    ...

def es_servicio_o_logistica(texto: str) -> bool:
    """
    Detecta si la fila es un servicio (MOVILIDAD, ENVÍO, EMBALAJE, ROTULADO, FLETE).
    Retorna True si debe excluirse.
    """
    ...
```

---

## 2. MATRIZ DE CAMBIOS POR PRIORIDAD

### Prioridad CRÍTICA (Bloquean la feature)

| Archivo | Acción | Líneas | Riesgo |
|---------|--------|--------|--------|
| `models/entities.py` | CREAR `ArchetypeData` | ~20 | Bajo (solo dataclass) |
| `models/entities.py` | CREAR `BenchmarkingMatrix` | ~25 | Bajo (solo dataclass) |
| `services/benchmarking_service.py` | CREAR nuevo servicio | ~150 | Medio (lógica de agrupación) |
| `services/text_utils.py` | AGREGAR funciones de extracción | ~80 | Bajo (funciones puras) |
| `controllers/app_controller.py` | INYECTAR `BenchmarkingService` | 1 línea | Bajo |
| `controllers/app_controller.py` | AGREGAR `handle_benchmarking()` | ~30 | Medio |

### Prioridad MEDIA (Mejoras de UX)

| Archivo | Acción | Líneas | Razón |
|---------|--------|--------|-------|
| `views/results_view.py` | CREAR vista de matriz benchmarking | ~100 | Mostrar datos en tabla de arquetipos |
| `controllers/app_controller.py` | AGREGAR `handle_export_benchmarking()` | ~50 | Exportar a Excel |

### Prioridad BAJA (Documentación)

| Archivo | Acción | Razón |
|---------|--------|-------|
| `docs/` | Actualizar flujo completo | Documentar la cadena escaneo -> benchmarking -> exportación |

---

## 3. IMPACTO EN PATRÓN MVC

### 3.1 ¿Se rompe el MVC?
**NO.** El diseño propuesto **mantiene la separación de responsabilidades:**

| Capa | Cambios |
|------|---------|
| **Modelos** | +2 nuevas dataclasses (sin lógica) |
| **Servicios** | +1 servicio (lógica pura, sin dependencia de UI) |
| **Controlador** | +2 métodos de orquestación (coordinación de servicios + UI) |
| **Vistas** | +1 nueva vista para matriz (opcional) |

### 3.2 Flujo de Control (Sin Cambios al Existente)

```
usuario presiona "INICIAR ESCANEO"
    ↓
AppController.handle_scan()  (EXISTENTE)
    ↓
ExcelScanService.scan_folder()  (EXISTENTE)
    ↓
AppController._on_scan_done()  (EXISTENTE, EXTENDIDO)
    ↓
(NUEVO) usuario presiona "GENERAR BENCHMARKING"
    ↓
(NUEVO) AppController.handle_benchmarking()
    ↓
(NUEVO) BenchmarkingService.generar_benchmarking()
    ↓
(NUEVO) AppController._on_benchmarking_done()
    ↓
(NUEVO) Mostrar matriz en ResultsView
    ↓
(NUEVO) usuario presiona "EXPORTAR A EXCEL"
    ↓
(NUEVO) AppController.handle_export_benchmarking()
```

---

## 4. RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Severidad | Mitigación |
|--------|--------------|-----------|-----------|
| Extracción deficiente de arquetipos | MEDIA | ALTA | Unit tests con nombres reales de productos |
| Rendimiento en dataset grande | BAJA | MEDIA | Usar GroupBy de Pandas + memoización |
| Conflicto de threads en BenchmarkingService | BAJA | ALTA | Asegurar que el servicio es thread-safe (no state compartido) |
| Exportación a Excel falla | BAJA | BAJA | Usar openpyxl + manejo de excepciones |

---

## 5. CHECKLIST DE IMPLEMENTACIÓN

### FASE 1: Modelos (Estimado: 0.5 hrs)
- [ ] Crear `ArchetypeData` en `entities.py`
- [ ] Crear `BenchmarkingMatrix` en `entities.py`
- [ ] Validar compilación (sin errores sintácticos)

### FASE 2: Utilidades (Estimado: 1.5 hrs)
- [ ] Crear `extraer_material()` en `text_utils.py`
- [ ] Crear `extraer_segmento_calidad()` en `text_utils.py`
- [ ] Crear `remover_ruido_de_especificacion()` en `text_utils.py`
- [ ] Crear `es_servicio_o_logistica()` en `text_utils.py`
- [ ] Unit tests para cada función

### FASE 3: Servicio de Benchmarking (Estimado: 3 hrs)
- [ ] Crear `benchmarking_service.py`
- [ ] Implementar `extraer_arquetipo()`
- [ ] Implementar `es_servicio_excluido()`
- [ ] Implementar `generar_benchmarking()`
- [ ] Implementar `calcular_confianza()`
- [ ] Unit tests para agrupación

### FASE 4: Controlador (Estimado: 1 hr)
- [ ] Inyectar `BenchmarkingService` en `__init__`
- [ ] Crear `handle_benchmarking()`
- [ ] Crear `_on_benchmarking_done()`
- [ ] Crear `handle_export_benchmarking()`
- [ ] Validar integración con threading

### FASE 5: Vistas (Estimado: 2 hrs)
- [ ] Crear vista de matriz benchmarking (o tabla en `results_view.py`)
- [ ] Botón "Generar Benchmarking" en `ScanControls`
- [ ] Botón "Exportar a Excel" en interfaz

### FASE 6: Testing Integrado (Estimado: 1.5 hrs)
- [ ] Scan -> Benchmarking -> Excel (full pipeline)
- [ ] Validar filtros de exclusión
- [ ] Validar cálculos de márgenes por tier

---

## 6. ARCHIVOS A CREAR / MODIFICAR

### CREAR
```
src/services/benchmarking_service.py       (NUEVA)
```

### MODIFICAR
```
src/models/entities.py                     (+45 líneas)
src/services/text_utils.py                 (+80 líneas)
src/controllers/app_controller.py          (+100 líneas)
src/views/results_view.py                  (+50 líneas, OPCIONAL)
```

### NO TOCAR
```
src/services/excel_scan_service.py         (SIN CAMBIOS)
src/services/quote_service.py              (SIN CAMBIOS)
src/services/variation_service.py          (SIN CAMBIOS)
src/views/main_view.py                     (SIN CAMBIOS)
src/views/quote_view.py                    (SIN CAMBIOS)
src/views/scan_controls.py                 (Agregar botón, MÍNIMO)
```

---

## 7. DEPENDENCIAS EXTERNAS

| Paquete | Versión | Uso | Estado |
|---------|---------|-----|--------|
| pandas | Actual | GroupBy, agg en benchmarking | ✅ Instalado |
| openpyxl | Requerido | Exportación a Excel | ⚠️ VERIFICAR si está en requirements.txt |

**Acción:** Validar `requirements.txt` e incluir `openpyxl>=3.0` si falta.

---

## 8. RESUMEN TÉCNICO

| Métrica | Valor |
|---------|-------|
| Clases nuevas | 2 (en models) |
| Servicios nuevos | 1 (benchmarking_service.py) |
| Métodos nuevos en controller | 3 (handle_benchmarking, _on_benchmarking_done, handle_export_benchmarking) |
| Funciones nuevas en text_utils | 4 |
| Líneas de código nueva (approx) | 350-400 |
| Riesgo de regresión | BAJO (cambios aislados) |
| Tiempo estimado total | 9-10 horas (con testing) |

---

## 9. CONCLUSIÓN

El spec de benchmarking es **técnicamente viable** sin romper el patrón MVC. Requiere:
1. ✅ Extensión limpia de modelos (2 dataclasses)
2. ✅ 1 nuevo servicio auto-contenido
3. ✅ 3 nuevos métodos en controlador (orquestación)
4. ✅ Funciones de utilidad para limpieza y extracción

**Recomendación:** Proceder con la implementación en las 4 fases críticas (1-4). Fases 5-6 pueden ser incrementales.
