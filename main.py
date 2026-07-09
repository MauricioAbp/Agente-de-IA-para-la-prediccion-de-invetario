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


@app.get("/")
def inicio():
    return {
        "mensaje": "API del Sistema Inteligente de Inventarios",
        "estado": "Activa",
        "documentacion": "/docs"
    }


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