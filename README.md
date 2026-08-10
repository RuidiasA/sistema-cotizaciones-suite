# Sistema Cotizaciones Suite (COMPIPRO / COMPINA S.A.C.)

Suite de automatización, analítica de datos y auditoría comercial desarrollada para optimizar el flujo de cotizaciones corporativas, reduciendo el tiempo de análisis de **3-4 horas manuales** a ejecuciones vectorizadas de alta velocidad en segundos. Este monorepo recopila el trabajo de ingeniería realizado durante las prácticas preprofesionales en **COMPINA S.A.C. / COMPIPRO**.

---

## Contexto del Problema y Fases Técnicas

La empresa manejaba un histórico de más de **900+ archivos Excel** de cotizaciones pasadas. Cada libro contenía múltiples hojas con estructuras altamente irregulares: celdas combinadas de forma aleatoria, columnas desplazadas en filas intermedias y descripciones escritas manualmente con variaciones tipográficas.

Para resolver este cuello de botella, el sistema se estructuró en **4 fases técnicas consecutivas** (Módulos 01 al 03 en producción, Módulo 04 en desarrollo):

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
[ 04-cotizador-expres (En Desarrollo) ]
      └─► GUI comercial de consulta en tiempo real O(1) y generación de propuestas.
```

---

## Módulos de la Suite

### 1. Módulo 01 — Escaneo Masivo y Benchmarking (`01-escaneo-masivo-cotizaciones`)

Script defensivo y concurrente en Python/Pandas capaz de superar celdas combinadas y desplazamientos de columnas para extraer y normalizar atributos (`Descripcion / Articulo`).

* **Capacidades:** Escaneo paralelo (`ThreadPoolExecutor`), renderizado por lotes (`after()`), cancelación en caliente e interfaz gráfica en CustomTkinter.
* **Artefactos:** Data Lake `debug_scan_raw.xlsx` y mapa de 1,220 productos únicos.

### 2. Módulo 02 — Automatización de Márgenes (`02-automatizacion-margenes`)

Pipeline estadístico que clasifica el dataset histórico en 30 subcategorías comerciales (con colador especial por costo de proveedor) y tramos de volumen ($10, 25, 50, \dots, 100k$ unidades).

* **Capacidades:** Control de *outliers* por Rango Intercuartílico (IQR), suavizado monótono decreciente de dos vías e inyección automática en el Módulo 03.
* **Artefactos:** Matriz optimizada `matriz_margenes.json` e inyección en `tarifario_diseno.xlsx`.

### 3. Módulo 03 — Motor de Ajustes Dinámicos (`03-motor-ajustes-dinamicos`)

Compilador multicapa de reglas de negocio y motor de auditoría comercial desacoplado.

* **Capacidades:** Compilación de 5 hojas de reglas Excel en artefactos JSON, cálculo de precios por algoritmo de *Piso Comercial / Escalón Duro* y evaluación de tolerancia ($\pm 2.00$ PEN) con $70.49\%$ de efectividad corporativa.
* **Artefactos:** `matrices_margen.json`, `ajustes_margen.json` y `auditoria_global.xlsx`.

### 4. Módulo 04 — Cotizador Exprès (`04-cotizador-expres`) *(Próximo Despliegue)*

Aplicación de escritorio final que consumirá los JSONs compilados del Módulo 03 para resolver consultas de cotización en tiempo real con exportación automática de propuestas comerciales.

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
├── 04-cotizador-expres/                   # Módulo 04: Interfaz de cotización rápida (En desarrollo)
├── .gitignore                             # Reglas de exclusión de Git unificadas
├── .venv/                                 # Entorno virtual unificado del monorepo
├── requirements.txt                       # Dependencias globales del proyecto
└── README.md                              # Documentación central de la suite
```

---

## Contratos de Integración entre Módulos

1. **Módulo 01 ➔ Módulo 02:** El escáner masivo genera `debug_scan_raw.xlsx`, el cual alimenta como Data Lake histórico el análisis estadístico del Módulo 02.
2. **Módulo 02 ➔ Módulo 03:** El analizador del Módulo 02 inyecta automáticamente los márgenes base calculados en la Hoja 1 (`Margenes_Base`) del tarifario maestro `03-motor-ajustes-dinamicos/config/tarifario_diseno.xlsx`.
3. **Módulo 02 ➔ Auditoría del Módulo 03:** `src/audit.py` (Módulo 03) importa dinámicamente la función `clasificar_producto_estricto` del Módulo 02 (`src/limpiador.py`) para asegurar una taxonomía unificada sin duplicar código.

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


---

## Métricas de Rendimiento Global

* **Velocidad de Escaneo (Móduo 01):** 908+ archivos procesados concurrentemente en la ingesta.
* **Tiempo de Análisis Estadístico (Móduo 02):** $\sim 1.47$ segundos en memoria RAM.
* **Tiempo de Compilación y Auditoría (Móduo 03):** $\sim 1.12$ segundos para 1,808 cotizaciones y 446 reglas.
* **Precisión Comercial Corporativa ($\ge 50$ u):** $70.49\%$ de efectividad dentro del rango de tolerancia ($\pm 2.00$ PEN).
