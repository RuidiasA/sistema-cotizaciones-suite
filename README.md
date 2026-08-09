# 🏢 Sistema Cotizaciones Suite (COMPIPRO / COMPINA)

Suite de automatización y procesamiento masivo de cotizaciones desarrollada para optimizar el flujo comercial, reduciendo el tiempo de generación de cotizaciones de **3-4 horas manuales** a procesos automatizados de alta velocidad. Este monorepo recopila el trabajo de ingeniería realizado durante las prácticas preprofesionales en **COMPINA / COMPIPRO**.

---

## 🚀 Contexto del Problema y Fases del Proyecto
La empresa manejaba un histórico masivo de más de **800+ / 900+ archivos Excel** de cotizaciones (desde antes de 2010 hasta 2025), con estructuras irregulares, celdas combinadas y descripciones inconsistentes. El reto consistió en estructurar este conocimiento histórico en 4 fases técnicas:

1. **Fase Inicial y Análisis:** Estandarización de más de 20,000 productos de proveedores nacionales e internacionales, agrupándolos en categorías con un margen de ganancia mínimo del 30% y un rango de error tolerado de $\pm 2$ soles.
2. **Proyecto 1 (Escaneo Masivo y Limpieza):** Motor de extracción, limpieza de texto y vectorización sobre miles de archivos Excel históricos para generar una base de conocimiento limpia de más de **14,000+ filas de productos**.
3. **Proyecto 2 (Automatización de Márgenes):** Generación matricial de márgenes base por categorías y rangos de volúmenes de cantidades.
4. **Proyecto 3 (Motor de Ajustes Dinámicos):** Sistema de reglas condicionales por ID, variantes de materiales y modificadores de puntos o márgenes fijos.
5. **Proyecto 4 (Interfaz de Cotización Rápida):** Aplicación de escritorio final basada en componentes para cotizar dinámicamente en segundos.

---

## 📁 Estructura del Monorepo

```text
sistema-cotizaciones-suite/
├── 01-escaneo-masivo-cotizaciones/    # Módulo Core: Motor de lectura, regex y UI de resultados
├── 02-... (Próximamente)              # Módulos de márgenes, ajustes y cotizador final
└── README.md                          # Documentación central de la suite
```

---

## 📦 Módulos Disponibles

### 01 - Motor de Escaneo Masivo y Benchmarking

Módulo encargado de la ingesta masiva de excels históricos.

* **Rendimiento:** Validado con más de 900 archivos y 14k+ filas sin bloqueos de interfaz gracias a *UI Chunking* en CustomTkinter.
* **Tecnologías:** Python 3.12+, Pandas, Openpyxl, xlrd, CustomTkinter.

---

## ⚙️ Configuración General del Repositorio

1. **Clonar el repositorio:**
```bash
git clone https://github.com/RuidiasA/sistema-cotizaciones-suite.git
cd sistema-cotizaciones-suite
```

2. **Acceder a los módulos individuales:** Cada submódulo cuenta con su propio entorno y dependencias independientes documentadas en su respectivo directorio.
