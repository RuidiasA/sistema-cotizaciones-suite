# 02 - Motor de Automatización y Suavizado de Márgenes

Módulo backend de la **SistemaCotizaciones Suite** encargado de procesar volúmenes masivos de datos históricos de cotización, aplicar filtrado estadístico de *outliers* por Rango Intercuartílico (IQR), realizar un suavizado monótono decreciente de curvas de margen y exportar los resultados tanto en formato JSON como inyectados directamente en el tarifario maestro del Módulo 03.

---

## Características Clave

1. **Taxonomía Comercial de 30 Subcategorías:** Clasificación precisa por tipo de prenda, material y colador especial por costo de proveedor (ej. discriminación en `limpiador.py` de Tomatodos económicamente comerciales `< S/ 8.00` PEN vs. insulados/premium).
2. **Filtro Estadístico IQR (Interquartile Range):** Depuración de registros históricos atípicos mediante el cálculo de cuantiles $Q_1$ (25%) y $Q_3$ (75%) por tramo de cantidad.
3. **Suavizado Monótono Decreciente:** Corrección de curvas financieras de dos vías (izquierda a derecha y derecha a izquierda) para evitar inconsistencias de margen al escalar volúmenes de pedido.
4. **Inyección Directa en Módulo 03:** Sincronización automática de la Hoja 1 (`Margenes_Base`) en `03-motor-ajustes-dinamicos/config/tarifario_diseno.xlsx`, eliminando la edición manual de tablas de Excel.

---

## Flujo de Procesamiento de Datos

```text
[ Excel Histórico debug_scan_raw.xlsx ]
          │
          ▼ (Fase 1: Extracción y Clasificación Estricta)
[ Limpiador y Colador de Costos ] ➔ (Mapeo a 30 subcategorías comerciales exactas en limpiador.py)
          │
          ▼ (Fase 2: Segmentación por Escala Comercial)
[ Agrupador por Volumen ] ➔ (Ajuste a escalas estándar: 10, 25, 50, 100, ..., 100k)
          │
          ▼ (Fase 3: Control Estadístico y Suavizado)
[ Filtro IQR + Mediana + Monotonía ] ➔ (Depuración de outliers y corrección de picos/valles)
          │
          ▼ (Fase 4: Exportación Multicapa)
[ matriz_margenes.json ] ➔ (Estructura optimizada para consulta O(1) en el Cotizador Exprès)
[ tarifario_diseno.xlsx ] ➔ (Inyección automática en Hoja 1 'Margenes_Base' del Módulo 03)
```

---

## Tecnologías y Dependencias

* **Python 3.12+**
* **Pandas & NumPy:** Procesamiento vectorial, cálculo de cuantiles IQR y suavizado de curvas.
* **Openpyxl:** Inyección y modificación de hojas en libros de Excel sin perder formatos existentes.

---

## Estructura del Módulo

```text
02-automatizacion-margenes/
├── data/
│   ├── debug_scan_raw.xlsx   # Dataset histórico de entrada (Sincronizado desde 01-escaneo-masivo-cotizaciones)
│   └── matriz_margenes.json  # Artefacto JSON de márgenes suavizados autogenerado
├── src/
│   ├── analizador.py         # Lógica matemática de IQR, medianas, suavizado e inyección a Excel
│   └── limpiador.py          # Diccionario de 30 subcategorías y clasificación estricta por costo/tokens
├── main.py                   # Orquestador global: Autodetecta el dataset en data/ y ejecuta el pipeline
└── README.md                 # Documentación técnica del módulo
```

---

## Ejecución del Pipeline

El orquestador `main.py` autodetecta dinámicamente el primer archivo `.xlsx` disponible en la carpeta `data/` y ejecuta en cascada la limpieza, el análisis estadístico, la exportación del JSON y la inyección en el Módulo 03.

Asegúrate de tener el entorno virtual del monorepo activo (`.venv` en la raíz) y ejecuta:
```bash
python 02-automatizacion-margenes/main.py
```

**Ejemplo de salida en consola:**

```text
==============================================
 MOTOR DE OPTIMIZACIÓN DE MÁRGENES (GLOBAL)   
==============================================
Archivo de entrada detectado: debug_scan_raw.xlsx
Iniciando la trituración de datos históricos con motor modular...
Clasificando arquetipos dinámicamente mediante el diccionario maestro...
Agrupando bloques y ejecutando control estadístico IQR por tramo...
Aplicando suavizado monótono e inyectando claves estructurales...
¡Matriz unificada exportada con éxito en: matriz_margenes.json!
¡Hoja 'Margenes_Base' inyectada y actualizada en: tarifario_diseno.xlsx!
==================================================
¡Pipeline de análisis masivo ejecutado con éxito!
Tiempo de procesamiento RAM: 1.47 segundos.
==================================================
```

---

## Métricas de Desempeño

* **Tiempo Promedio de Procesamiento RAM:** $\sim 1.47$ segundos.
* **Categorías Mapeadas:** 30 Arquetipos comerciales de la suite.
* **Formato de Exportación:** JSON estructurado para lectura inmediata + Excel XLSX inyectado en caliente.