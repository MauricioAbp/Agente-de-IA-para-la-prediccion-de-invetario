from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import json
import os
import numpy as np
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API-Inventario")

RUTA_Q_TABLE    = os.getenv("RUTA_Q_TABLE", "q_table.json")
ACCIONES_POSIBLES = [int(x) for x in os.getenv("ACCIONES_POSIBLES", "0,10,20,30,50").split(",")]
DIAS_MAPEO = {
    "lunes": 0, "martes": 1, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6
}

q_table_cargada = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global q_table_cargada
    if not os.path.exists(RUTA_Q_TABLE):
        logger.warning(f"'{RUTA_Q_TABLE}' no encontrada. Ejecute el agente primero.")
        q_table_cargada = {}
    else:
        with open(RUTA_Q_TABLE, "r") as f:
            q_table_cargada = json.load(f)
        logger.info(f"Q-Table cargada: {len(q_table_cargada)} estados.")
    yield
    logger.info("Apagando microservicio.")


app = FastAPI(
    title="Sistema Inteligente de Optimización de Abastecimiento",
    description="API REST para toma de decisiones logísticas óptimas vía Q-Learning.",
    version="2.0.0",
    lifespan=lifespan
)


class PeticionInventario(BaseModel):
    stock_actual: int = Field(..., ge=0)
    dia_semana: str


@app.get("/", response_class=HTMLResponse)
def inicio():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API - Sistema Inteligente de Inventarios</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Material+Icons&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #6750A4;
                --primary-container: #EADDFF;
                --on-primary: #ffffff;
                --background: #F3F0F7;
                --surface: #ffffff;
                --outline: #79747E;
                --text-primary: #1C1B1F;
                --text-secondary: #49454F;
            }

            body {
                font-family: 'Roboto', sans-serif;
                background-color: var(--background);
                color: var(--text-primary);
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }

            /* Top App Bar */
            .app-bar {
                background-color: var(--primary);
                color: var(--on-primary);
                padding: 16px 24px;
                display: flex;
                align-items: center;
                gap: 16px;
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
            }

            .app-bar h1 {
                margin: 0;
                font-size: 20px;
                font-weight: 500;
            }

            .container {
                max-width: 800px;
                margin: 40px auto;
                padding: 0 16px;
                flex-grow: 1;
            }

            /* Hero Header */
            .hero {
                text-align: center;
                margin-bottom: 40px;
            }

            .hero h2 {
                font-size: 32px;
                font-weight: 700;
                margin: 0 0 8px 0;
                color: var(--primary);
            }

            .hero p {
                font-size: 16px;
                color: var(--text-secondary);
                margin: 0;
            }

            /* Material Card */
            .card {
                background-color: var(--surface);
                border-radius: 16px;
                padding: 24px;
                margin-bottom: 24px;
                box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.05);
                border: 1px solid #E7E0EC;
                transition: transform 0.2s, box-shadow 0.2s;
            }

            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            }

            .card-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 16px;
            }

            .card-header .icon {
                color: var(--primary);
                font-size: 28px;
            }

            .card-header h3 {
                margin: 0;
                font-size: 18px;
                font-weight: 500;
            }

            /* Badge/Chip */
            .badge {
                background-color: #E8F5E9;
                color: #2E7D32;
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }

            .badge .dot {
                width: 8px;
                height: 8px;
                background-color: #2E7D32;
                border-radius: 50%;
                display: inline-block;
                animation: pulse 1.5s infinite;
            }

            @keyframes pulse {
                0% { transform: scale(0.9); opacity: 0.6; }
                50% { transform: scale(1.2); opacity: 1; }
                100% { transform: scale(0.9); opacity: 0.6; }
            }

            /* Buttons */
            .btn {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background-color: var(--primary);
                color: var(--on-primary);
                padding: 12px 24px;
                border-radius: 100px;
                text-decoration: none;
                font-weight: 500;
                font-size: 14px;
                box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.15);
                transition: all 0.2s;
            }

            .btn:hover {
                background-color: #513B8C;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
                transform: translateY(-1px);
            }

            /* Tables/Lists */
            .info-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
            }

            .info-table td {
                padding: 8px 0;
                border-bottom: 1px solid #E7E0EC;
                font-size: 14px;
            }

            .info-table td.label {
                font-weight: 500;
                color: var(--text-secondary);
                width: 30%;
            }

            /* Footer */
            footer {
                background-color: #ECE6F0;
                padding: 24px;
                text-align: center;
                font-size: 12px;
                color: var(--text-secondary);
                border-top: 1px solid #E7E0EC;
            }
        </style>
    </head>
    <body>
        <div class="app-bar">
            <span class="material-icons">smart_toy</span>
            <h1>Sistema Inteligente de Inventarios</h1>
        </div>

        <div class="container">
            <div class="hero">
                <h2>Módulo de Inferencia REST</h2>
                <p>Motor de Aprendizaje por Refuerzo para Toma de Decisiones Secuenciales</p>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="material-icons icon">wifi_tethering</span>
                    <h3>Estado del Servidor</h3>
                </div>
                <div class="badge">
                    <span class="dot"></span>
                    API Activa y Operacional
                </div>
                <table class="info-table">
                    <tr>
                        <td class="label">Versión</td>
                        <td>2.0.0</td>
                    </tr>
                    <tr>
                        <td class="label">Plataforma</td>
                        <td>FastAPI + Uvicorn</td>
                    </tr>
                    <tr>
                        <td class="label">Algoritmo</td>
                        <td>Q-Learning (Ecuación de Bellman)</td>
                    </tr>
                </table>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="material-icons icon">api</span>
                    <h3>Documentación Interactiva</h3>
                </div>
                <p style="font-size: 14px; color: var(--text-secondary); margin-bottom: 20px;">
                    Explore y pruebe de forma interactiva los endpoints de inferencia del agente utilizando la interfaz automática Swagger UI de OpenAPI.
                </p>
                <a href="/docs" class="btn">
                    <span class="material-icons">rocket_launch</span>
                    Acceder a Swagger UI
                </a>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="material-icons icon">psychology</span>
                    <h3>Especificación del Agente</h3>
                </div>
                <table class="info-table">
                    <tr>
                        <td class="label">Estado (S)</td>
                        <td>Tupla: [Stock Actual, Día de la Semana]</td>
                    </tr>
                    <tr>
                        <td class="label">Acciones (A)</td>
                        <td>Lotes de reabastecimiento: [0, 10, 20, 30, 50] unidades</td>
                    </tr>
                    <tr>
                        <td class="label">Estrategia</td>
                        <td>&epsilon;-Greedy decreciente con actualización de Bellman</td>
                    </tr>
                </table>
            </div>
        </div>

        <footer>
            Microservicio de Abastecimiento Logístico Autónomo. Desarrollado con FastAPI, Python y Numpy.
        </footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/prediccion", status_code=status.HTTP_200_OK)
async def obtener_recomendacion(datos: PeticionInventario):
    dia_normalizado = datos.dia_semana.lower().strip()
    if dia_normalizado not in DIAS_MAPEO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Día inválido. Valores aceptados: {list(DIAS_MAPEO.keys())}"
        )

    dia_idx      = DIAS_MAPEO[dia_normalizado]
    llave_estado = f"{datos.stock_actual},{dia_idx}"

    NOMBRES_ACCIONES = {a: f"comprar {a} unidades" for a in ACCIONES_POSIBLES}
    NOMBRES_DIAS = {0: "lunes", 1: "martes", 2: "miércoles", 3: "jueves",
                    4: "viernes", 5: "sábado", 6: "domingo"}

    if llave_estado in q_table_cargada:
        valores_q         = q_table_cargada[llave_estado]
        accion_optima_idx = int(np.argmax(valores_q))
        cantidad_a_comprar = ACCIONES_POSIBLES[accion_optima_idx]
        confianza_bellman  = valores_q[accion_optima_idx]
        origen_politica    = "Inferencia Óptima (Q-Table)"

        segunda_mejor_idx  = sorted(range(len(valores_q)), key=lambda i: valores_q[i], reverse=True)[1]
        segunda_mejor_cant = ACCIONES_POSIBLES[segunda_mejor_idx]
        diferencia_q       = round(valores_q[accion_optima_idx] - valores_q[segunda_mejor_idx], 2)
        nivel_stock        = "crítico" if datos.stock_actual == 0 else "bajo" if datos.stock_actual < 20 else "normal" if datos.stock_actual < 60 else "alto"
       # Normaliza la diferencia relativa entre la mejor y segunda mejor acción
        todos_q = sorted(valores_q, reverse=True)
        rango = abs(todos_q[0] - todos_q[-1])
        confianza_pct = min(100, round((abs(diferencia_q) / (rango + 1)) * 100, 1)) if rango > 0 else 0
        explicacion = (
            f"Con stock {nivel_stock} ({datos.stock_actual} unidades) un {NOMBRES_DIAS[dia_idx]}, "
            f"el agente recomienda {NOMBRES_ACCIONES[cantidad_a_comprar]}. "
            f"La segunda mejor opción era {segunda_mejor_cant} unidades (diferencia Q: {diferencia_q}). "
            f"Nivel de confianza en la decisión: {confianza_pct}%."
        )
    else:
        if datos.stock_actual <= 10:
            cantidad_a_comprar = 70
        elif datos.stock_actual <= 30:
            cantidad_a_comprar = 30
        else:
            cantidad_a_comprar = 10
        confianza_bellman  = 0.0
        origen_politica    = "Política de Contingencia (Estado Desconocido)"
        nivel_stock        = "crítico" if datos.stock_actual == 0 else "bajo" if datos.stock_actual < 20 else "normal" if datos.stock_actual < 60 else "alto"
        explicacion        = (
            f"Estado no visto en entrenamiento. Stock {nivel_stock} ({datos.stock_actual} unidades) "
            f"un {NOMBRES_DIAS[dia_idx]}: se aplica regla de contingencia, comprar {cantidad_a_comprar} unidades."
        )

    return {
        "status": "success",
        "metadatos": {
            "estrategia_aplicada": origen_politica,
            "valor_q_maximo": round(confianza_bellman, 4),
            "confianza_pct": confianza_pct if llave_estado in q_table_cargada else 0
        },
        "decision_abastecimiento": {
            "unidades_a_solicitar": cantidad_a_comprar,
            "unidad_medida": "Unidades",
            "impacto_esperado": explicacion
        }
    }