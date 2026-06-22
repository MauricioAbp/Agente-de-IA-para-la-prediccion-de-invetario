# Optimización de Inventarios mediante Aprendizaje por Refuerzo

Este proyecto implementa un agente autónomo para la toma de decisiones secuenciales en la gestión de abastecimiento. A través del algoritmo Q-Learning y un entorno de simulación dinámico, el sistema procesa datos transaccionales históricos para mitigar los problemas de quiebre de stock y sobrealmacenamiento en entornos minoristas.

---

## 📌 1. Problema de Negocio
La gestión de inventarios tradicional basada en heurísticas manuales o modelos estáticos (como el EOQ) suele fallar ante la variabilidad de la demanda diaria. Este desarrollo aborda el problema automatizando la decisión de compra en base a dos variables de estado:
* **Nivel de Stock Remanente:** Monitoreo diario para evitar detener las ventas.
* **Temporalidad Operativa:** El comportamiento de la demanda indexado por el día de la semana.

---

## 🛠️ 2. Arquitectura del Sistema
La solución se estructura mediante componentes desacoplados:

* **Core de Inteligencia Artificial:** Agente entrenado desde cero con el algoritmo **Q-Learning** (Ecuación de Bellman) y una estrategia de exploración-explotación $\epsilon$-Greedy decreciente.
* **Capa de Datos:** **MySQL Workbench** como base de datos relacional para la persistencia transaccional e histórico de auditoría de acciones.
* **Pipeline ETL:** Procesamiento con **Pandas** y **Openpyxl** para la ingesta, limpieza e indexación por jornadas de un dataset transaccional masivo de Kaggle (*Coffee Shop Sales*).
* **Capa de Inferencia (Despliegue):** Microservicio web desarrollado en **FastAPI + Uvicorn** que expone el conocimiento del agente mediante endpoints síncronos/asíncronos.

---

## ⚙️ 3. Estructura del Repositorio

```text
├── BD/
│   └── proyectoclase.sql        # Definición del esquema y tablas en MySQL
├── Coffee Shop Sales.xlsx       # Dataset histórico crudo (Kaggle)
├── entorno_inventario.py        # Simulación matemática de estados y recompensas
├── agente_bellman.py           # Bucle de entrenamiento y convergencia del agente
├── main.py                      # Definición de la API REST para inferencias en producción
├── migrar_kaggle.py             # Pipeline ETL para la carga masiva de datos a MySQL
├── q_table.json                 # Matriz de conocimiento serializada
└── .gitignore                   # Exclusión de archivos del entorno virtual y caché

## 🔬 4. Modelo Matemático

La actualización de la política óptima de abastecimiento se realiza mediante **Aprendizaje por Refuerzo**, utilizando la ecuación fundamental de diferencias temporales basada en la ecuación de Bellman. Esta expresión permite que el agente aprenda progresivamente a maximizar la recompensa esperada a partir de la experiencia obtenida durante las simulaciones.

$$
Q(s, a) \leftarrow Q(s, a) + \alpha \left[ R(s, a) + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]
$$

### 📌 Espacio de Estados ($s$)

El estado del entorno está definido por una tupla conformada por:

* 📦 **stock_actual**
* 📅 **dia_semana**

Esta representación permite al agente considerar tanto el nivel actual de inventario como la variación de la demanda según el día.

### 🎯 Espacio de Acciones ($a$)

Las acciones disponibles corresponden a los posibles lotes de unidades a solicitar:

```python
[0, 10, 20, 30, 50]
```

Cada acción representa una decisión discreta de abastecimiento tomada por el agente.

### 💰 Función de Recompensa ($R$)

La función de recompensa fue diseñada con el objetivo de maximizar el beneficio neto de la operación, equilibrando ingresos y costos asociados al inventario.

$$
R = \text{Ingresos} - \text{Costos Almacenamiento} - \text{Penalización por Desabastecimiento}
$$

De esta forma, el agente aprende a mantener niveles adecuados de stock, evitando tanto el exceso de inventario como la falta de productos.

---

# 🚀 5. Pipeline de Ejecución

El flujo de ejecución del sistema se divide en tres etapas principales, que abarcan desde la preparación de los datos hasta el despliegue del servicio para realizar inferencias en tiempo real.

## 📋 Prerrequisitos

Antes de ejecutar el proyecto, es necesario activar el entorno virtual local de Python:

```bash
.\venv\Scripts\activate
```

---

## 📂 Paso 1: Migración y Transformación de Datos

En esta etapa se consolidan los datos históricos obtenidos desde Kaggle y se almacenan en la base de datos relacional utilizada por el sistema.

```bash
python migrar_kaggle.py
```

---

## 🧠 Paso 2: Simulación y Entrenamiento del Agente

Se ejecuta el proceso de entrenamiento compuesto por 500 episodios, permitiendo que el agente aprenda la política óptima de abastecimiento y almacene el conocimiento adquirido en la tabla Q.

```bash
python agente_bellman.py
```

El resultado del entrenamiento se guarda en el archivo:

```text
q_table.json
```

---

## ⚙️ Paso 3: Despliegue del Microservicio

Finalmente, se inicia el servidor local encargado de exponer el modelo entrenado mediante una API, permitiendo realizar consultas e inferencias en tiempo real.

```bash
uvicorn main:app --reload
```

---

# 🐳 6. Interfaz de Pruebas

La API incorpora documentación interactiva generada automáticamente mediante el estándar **OpenAPI (Swagger UI)**, lo que facilita la prueba y validación de las respuestas del modelo sin necesidad de herramientas externas.

### 🔗 Swagger UI Local

```
http://127.0.0.1:8000/docs
```

Desde esta interfaz es posible explorar los endpoints disponibles, enviar solicitudes y visualizar las respuestas generadas por el sistema de manera sencilla e interactiva.
