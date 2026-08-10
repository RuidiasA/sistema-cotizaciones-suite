# 02 - Motor de Automatización y Suavizado de Márgenes

Módulo backend de la **Sistema Cotizaciones Suite** encargado de procesar volúmenes masivos de datos históricos de cotización, aplicar filtrado estadístico de *outliers* por rango intercuartílico (IQR) y generar matrices de margen suavizadas y unificadas en formato JSON para toda la taxonomía comercial.

---

## Flujo de Procesamiento de Datos

```text
[ Excel Histórico 14k+ ]
          │
          ▼ (Fase 1: Extracción y Limpieza)
[ Filtro Regex & Tokenización ] ➔ (Clasificación por arquetipos dinámicos desde Módulo 01)
          │
          ▼ (Fase 2: Segmentación por Escala)
[ Agrupador por Volumen ] ➔ (Mapeo a escalas comerciales 10, 25, 50... 100k)
          │
          ▼ (Fase 3: Control Estadístico)
[ Filtro IQR + Mediana ] ➔ (Depuración de precios anómalos / outliers)
          │
          ▼ (Fase 4: Exportación)
[ JSON Autogenerado ] ➔ (Estructura lista para consulta O(1) en Compipro)
```

---

## Tecnologías y Dependencias

* **Python 3.12+**
* **Pandas & NumPy:** Procesamiento vectorial, cálculo de cuantiles IQR y regresión logarítmica para el suavizado de curvas.
* **Openpyxl:** Extracción de datos desde hojas de cálculo Excel.

---

## Estructura del Módulo

```text
02-automatizacion-margenes/
├── data/                            # Datasets de entrada (.xlsx) y salida (.json)
│   ├── debug_scan_raw.xlsx
│   └── matriz_margenes.json
├── src/
│   ├── analizador.py                # Lógica matemática de IQR, medianas y suavizado
│   └── limpiador.py                 # Carga dinámica de taxonomía y clasificación de arquetipos
├── main.py                          # Punto de entrada y orquestador de pipeline
└── README.md                        # Documentación técnica del módulo
```

---

## Ejecución

Asegúrate de tener el entorno virtual del monorepo activo (`.venv` en la raíz), entra a este módulo y ejecuta el orquestador:

```bash
cd 02-automatizacion-margenes
python main.py
```
