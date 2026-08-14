# Sistema Cotizaciones Suite (COMPIPRO / COMPINA S.A.C.)

Suite integral de automatización, analítica de datos y auditoría comercial desarrollada para optimizar el flujo operativo de cotizaciones corporativas, reduciendo el tiempo de análisis de **3-4 horas manuales** a ejecuciones vectorizadas en memoria RAM en cuestión de segundos. Este monorepo consolida la arquitectura de ingeniería de software implementada para **COMPINA S.A.C. / COMPIPRO**.

---

## Contexto del Problema y Fases Técnicas

La empresa administraba un repositorio histórico de más de **900+ archivos Excel** de cotizaciones pasadas. Cada libro contenía múltiples hojas con estructuras no uniformes: celdas combinadas arbitrarias, columnas desplazadas en filas intermedias y descripciones de taller escritas manualmente con variaciones tipográficas.

Para resolver este cuello de botella, el sistema se estructuró en **4 fases técnicas desacopladas e integradas**:

```text
[ 01-escaneo-masivo-cotizaciones ]
   │  └─► Genera Data Lake histórico (debug_scan_raw.xlsx) con 14k+ filas.
   ▼
[ 02-automatizacion-margenes ]
   │  ├─► Filtrado IQR + Suavizado monótono de curvas (matriz_margenes.json).
   │  └─► Inyección automática a Hoja 'Margenes_Base' en Módulo 03.
   ▼
[ 03-motor-ajustes-dinamicos ]
   │  ├─► Compilación de reglas multicapa (matrices_margen.json, ajustes_margen.json).
   │  └─► Auditoría global de tolerancia comercial (± 2.00 PEN).
   ▼
[ 04-cotizador-expres ]
      └─► GUI comercial multiproducto, búsqueda jerárquica y exportación maquetada.
```

---

## Módulos de la Suite

### 1. Módulo 01 — Escaneo Masivo y Benchmarking (`01-escaneo-masivo-cotizaciones`)

Script defensivo y concurrente en Python/Pandas capaz de superar celdas combinadas y desplazamientos de columnas para extraer y normalizar atributos (`Descripcion / Articulo`).

* **Capacidades:** Escaneo paralelo (`ThreadPoolExecutor`), renderizado por lotes (`after()`), cancelación en caliente e interfaz gráfica en CustomTkinter con modo oscuro nativo.
* **Artefactos:** Data Lake `debug_scan_raw.xlsx` y catálogo de 1,220 productos únicos.

### 2. Módulo 02 — Automatización de Márgenes (`02-automatizacion-margenes`)

Pipeline estadístico que clasifica el dataset histórico en 30 subcategorías comerciales (con discriminador especial por costo de proveedor) y tramos de volumen ($10, 25, 50, \dots, 100k$ unidades).

* **Capacidades:** Control de *outliers* por Rango Intercuartílico (IQR), suavizado monótono decreciente de dos vías e inyección directa en caliente en el Módulo 03.
* **Artefactos:** Matriz optimizada `matriz_margenes.json` e inyección en `tarifario_diseno.xlsx`.

### 3. Módulo 03 — Motor de Ajustes Dinámicos (`03-motor-ajustes-dinamicos`)

Compilador multicapa de reglas de negocio y motor de auditoría comercial desacoplado.

* **Capacidades:** Compilación de 5 hojas de reglas Excel en artefactos JSON optimizados, cálculo de precios por algoritmo de *Piso Comercial / Escalón Duro* y evaluación de tolerancia ($\pm 2.00$ PEN) con $70.49\%$ de efectividad corporativa.
* **Artefactos:** `matrices_margen.json`, `ajustes_margen.json` y `auditoria_global.xlsx`.

### 4. Módulo 04 — Cotizador Exprés Multiproducto (`04-cotizador-expres`)

Aplicación de escritorio final bajo arquitectura MVC para la cotización simultánea de requerimientos comerciales (1 a 7 productos).

* **Capacidades:** Búsqueda jerárquica en cascada (`debug_scan_raw_recent.xlsx` ➔ `debug_scan_raw.xlsx`), filtrado por bracket de volumen, selección de costo base más cercano y consolidación multilínea de proveedores con celdas de auditoría histórica.
* **Artefactos:** Propuestas comerciales maquetadas en Excel (`.xlsx`) con cabeceras amarillas de cliente y columnas grises de control interno.

---

## Estructura del Monorepo

```text
sistema-cotizaciones-suite/
├── 01-escaneo-masivo-cotizaciones/        # Módulo 01: Ingesta, limpieza regex, benchmarking y UI
│   ├── data/                              # Datasets, checkpoints y logs de auditoría
│   ├── scripts/                           # Crawlers y tests de búsqueda por CLI
│   └── src/                               # Controladores, modelos y servicios del escáner
├── 02-automatizacion-margenes/            # Módulo 02: Control IQR, suavizado monótono y JSON
│   ├── data/                              # Dataset histórico y matriz JSON
│   └── src/                               # Analizador estadístico y limpiador por costo/tokens
├── 03-motor-ajustes-dinamicos/            # Módulo 03: Compilador de reglas y auditoría
│   ├── config/                            # Tarifario maestro (Excel) y JSONs compilados
│   ├── data/                              # Input de pruebas y reporte de auditoría global
│   ├── scripts/                           # ETL de saneamiento y diagnóstico corporativo
│   └── src/                               # Compilador multicapa y motor de auditoría
├── 04-cotizador-expres/                   # Módulo 04: Cotizador exprés GUI y exportador multilínea
│   ├── data/                              # Input de Data Lakes y output de propuestas generadas
│   └── src/                               # Controladores MVC, DataEngine y ExcelExporter
├── .gitignore                             # Reglas de exclusión de Git unificadas
├── .venv/                                 # Entorno virtual unificado del monorepo
├── requirements.txt                       # Dependencias globales del proyecto
└── README.md                              # Documentación central de la suite
```

---

## Contratos de Integración entre Módulos

```text
┌────────────────────────────────┐
│  01-escaneo-masivo             │
│  (Extracción & Consolidación)  │
└───────────────┬────────────────┘
                │
                │ 1. Data Lake histórico (debug_scan_raw.xlsx)
                ▼
┌────────────────────────────────┐
│  02-automatizacion-margenes    │
│  (Filtro IQR + Curvas Base)    │
└───────────────┬────────────────┘
                │
                │ 2. Inyección de márgenes base en tarifario_diseno.xlsx
                │ 3. Reglas taxonómicas compartidas (limpiador.py)
                ▼
┌────────────────────────────────┐
│  03-motor-ajustes-dinamicos    │
│  (Compilador de Reglas & Audit)│
└───────────────┬────────────────┘
                │
                │ 4. Artefactos compilados (matrices_margen.json / ajustes_margen.json)
                ▼
┌────────────────────────────────┐
│  04-cotizador-expres           │
│  (Cotizador Comercial UI)      │
└────────────────────────────────┘
```

1. **Módulo 01 ➔ Módulo 02:** El escáner masivo genera `debug_scan_raw.xlsx`, el cual alimenta como Data Lake histórico el análisis estadístico del Módulo 02.
2. **Módulo 02 ➔ Módulo 03:** El analizador del Módulo 02 inyecta automáticamente los márgenes base calculados en la Hoja 1 (`Margenes_Base`) del tarifario maestro `03-motor-ajustes-dinamicos/config/tarifario_diseno.xlsx`.
3. **Módulo 02 ➔ Auditoría del Módulo 03:** `src/audit.py` (Módulo 03) importa dinámicamente la función `clasificar_producto_estricto` del Módulo 02 (`src/limpiador.py`) para asegurar una taxonomía unificada sin duplicar código.
4. **Módulo 03 ➔ Módulo 04:** El Cotizador Exprés consume directamente los artefactos `matrices_margen.json` y `ajustes_margen.json` compilados por el Módulo 03 para resolver consultas en tiempo real.

---

## Configuración General y Ejecución

### 1. Clonar el repositorio y configurar el entorno:

```bash
git clone https://github.com/RuidiasA/sistema-cotizaciones-suite.git
cd sistema-cotizaciones-suite

python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
```

### 2. Ejecución independiente de los Módulos:

* **Módulo 01 (Interfaz Gráfica del Escáner):**
```bash
python 01-escaneo-masivo-cotizaciones/main.py
```

* **Módulo 02 (Pipeline Estadístico de Márgenes):**
```bash
python 02-automatizacion-margenes/main.py
```

* **Módulo 03 (Compilación de Reglas y Auditoría Global):**
```bash
python 03-motor-ajustes-dinamicos/main.py
```

* **Módulo 04 (Cotizador Exprés UI Desktop):**
```bash
python 04-cotizador-expres/main.py
```

---

## Métricas de Rendimiento Global

* **Velocidad de Escaneo (Módulo 01):** 908+ archivos procesados concurrentemente en la ingesta.
* **Tiempo de Análisis Estadístico (Módulo 02):** $\sim 1.47$ segundos en memoria RAM.
* **Tiempo de Compilación y Auditoría (Módulo 03):** $\sim 1.12$ segundos para 1,808 cotizaciones y 446 reglas.
* **Precisión Comercial Corporativa ($\ge 50$ u):** $70.49\%$ de efectividad dentro del rango de tolerancia ($\pm 2.00$ PEN).
* **Tiempo de Respuesta Comercial (Módulo 04):** Generación de propuestas multilínea maquetadas en $< 1.0$ segundo.
