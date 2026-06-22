from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import json
import os
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API-Inventario")

RUTA_Q_TABLE = "q_table.json"
DIAS_MAPEO = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}
ACCIONES_POSIBLES = [0, 10, 20, 30, 50]

# Memoria global en caché de la API
q_table_cargada = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Protocolo Lifespan para pre-cargar la Q-Table antes de escuchar tráfico de red"""
    global q_table_cargada
    logger.info("Verificando existencia del conocimiento del agente de RL...")
    if not os.path.exists(RUTA_Q_TABLE):
        logger.warning(f"Matriz '{RUTA_Q_TABLE}' ausente. Se inicializa en cero. Ejecute el agente para optimizar.")
        q_table_cargada = {}
    else:
        with open(RUTA_Q_TABLE, "r") as f:
            q_table_cargada = json.load(f)
        logger.info(f"Cerebro del agente montado con éxito. {len(q_table_cargada)} combinaciones de estados listas.")
    yield
    logger.info("Liberando recursos y apagando el microservicio.")

app = FastAPI(
    title="Sistema Inteligente de Optimización de Abastecimiento",
    description="API REST corporativa orientada a la toma de decisiones logísticas óptimas vía Q-Learning.",
    version="2.0.0",
    lifespan=lifespan
)

class PeticionInventario(BaseModel):
    # Validaciones robustas con Pydantic para blindar la entrada ante errores de usuario
    stock_actual: int = Field(..., ge=0, description="Nivel físico actual en almacén (no puede ser negativo)")
    dia_semana: str = Field(..., description="Día operativo actual (ej: Lunes, Martes)")

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "sistema": "Optimización Secuencial de Inventarios",
        "motor_matematico": "Ecuación de Bellman (Diferencia Temporal)",
        "estados_en_memoria": len(q_table_cargada),
        "documentacion_interactiva": "/docs"
    }

@app.post("/prediccion", status_code=status.HTTP_200_OK)
async def obtener_recomendacion(datos: PeticionInventario):
    dia_normalizado = datos.dia_semana.lower().strip()
    if dia_normalizado not in DIAS_MAPEO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Día inválido. Valores aceptados: {list(DIAS_MAPEO.keys())}"
        )
    
    dia_idx = DIAS_MAPEO[dia_normalizado]
    llave_estado = f"{datos.stock_actual},{dia_idx}"
    
    # Inferencia del Agente Inteligente
    if llave_estado in q_table_cargada:
        valores_q = q_table_cargada[llave_estado]
        accion_optima_idx = int(np.argmax(valores_q))
        cantidad_a_comprar = ACCIONES_POSIBLES[accion_optima_idx]
        confianza_bellman = valores_q[accion_optima_idx]
        origen_politica = "Inferencia Óptima (Q-Table Evaluada)"
    else:
        # Política de mitigación segura en caso de un escenario nunca antes visto en el dataset
        cantidad_a_comprar = 10
        confianza_bellman = 0.0
        origen_politica = "Política de Contingencia (Estado Desconocido)"
        
    return {
        "status": "success",
        "metadatos": {
            "estrategia_aplicada": origen_politica,
            "valor_q_maximo": round(confianza_bellman, 4)
        },
        "decision_abastecimiento": {
            "unidades_a_solicitar": cantidad_a_comprar,
            "unidad_medida": "Unidades",
            "impacto_esperado": "Maximización de utilidad operativa mitigando costos de quiebre de stock y bodegaje."
        }
    }