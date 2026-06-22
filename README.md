# 🚀 Sistema Inteligente de Optimización de Inventarios (Reinforcement Learning)

¡Bienvenido al repositorio oficial del **Sistema Inteligente de Abastecimiento de Inventarios**! Este proyecto de noveno ciclo combina la potencia de la **Ingeniería de Datos**, el **Aprendizaje por Refuerzo** y el despliegue moderno de microservicios para resolver uno de los problemas logísticos más complejos del sector minorista (*Retail*): el equilibrio perfecto del stock de café.

---

## 📌 1. Planteamiento del Problema
Las organizaciones se enfrentan constantemente a un dilema logístico bidireccional:
* **📦 Exceso de Stock (Sobrealmacenamiento):** Capital inmovilizado, altos costos de mantenimiento y riesgo de merma.
* **⚠️ Quiebre de Stock (Desabastecimiento):** Pérdida inmediata de ventas e insatisfacción del cliente.

**Nuestra Solución:** Un agente autónomo que aprende del histórico transaccional real para decidir con precisión milimétrica la cantidad exacta de unidades a solicitar según el stock remanente y la temporalidad (día de la semana).

---

## 🛠️ 2. Arquitectura y Herramientas Utilizadas
El proyecto está construido bajo una infraestructura robusta y desacoplada:

* **🧠 Core de IA:** Algoritmo **Q-Learning** (Aprendizaje por Refuerzo) basado en la **Ecuación de Bellman** y una estrategia de exploración $\epsilon$-Greedy decreciente.
* **⚡ Backend API:** **FastAPI + Uvicorn** para exponer el conocimiento del agente mediante endpoints REST síncronos/asíncronos de alta velocidad.
* **💾 Capa de Datos:** **MySQL Workbench** encargado del almacenamiento transaccional y la auditoría de políticas.
* **📊 Pipeline ETL:** **Pandas + Openpyxl** para la ingesta, limpieza masiva y agregación temporal de un dataset real de **Kaggle** (*Coffee Shop Sales*).

---

## ⚙️ 3. Estructura del Proyecto
El código se organiza de manera modular siguiendo las mejores prácticas de la industria:

```text
├── BD/
│   └── proyectoclase.sql        # Diseño físico de la base de datos relacional
├── Coffee Shop Sales.xlsx       # Dataset real de Kaggle con el histórico transaccional
├── entorno_inventario.py        # Modelo dinámico de simulación (Estados, Acciones, Recompensas)
├── agente_bellman.py           # Script de entrenamiento y convergencia del agente de IA
├── main.py                      # Servidor FastAPI y lógica de inferencia en Producción
├── migrar_kaggle.py             # Pipeline ETL para inyección masiva de datos a MySQL
├── q_table.json                 # El "cerebro" entrenado del agente (Matriz de conocimiento)
└── .gitignore                   # Exclusión de archivos temporales y entorno virtual (venv)
