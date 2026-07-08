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


@app.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def interfaz_grafica():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Optimización</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background:#f4f6f9; margin:40px; }
            .card { background:white; padding:30px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05); max-width:500px; margin:auto; }
            h2 { color:#2c3e50; text-align:center; }
            .form-group { margin-bottom:20px; }
            label { display:block; margin-bottom:8px; font-weight:bold; color:#34495e; }
            input, select { width:100%; padding:10px; border:1px solid #ccd1d9; border-radius:6px; box-sizing:border-box; }
            button { width:100%; padding:12px; background:#2ecc71; color:white; border:none; border-radius:6px; font-size:16px; cursor:pointer; font-weight:bold; }
            button:hover { background:#27ae60; }
            .result-box { margin-top:25px; padding:15px; border-radius:6px; display:none; background:#d4edda; color:#155724; border:1px solid #c3e6cb; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>📦 Dashboard de Inventarios (RL)</h2>
            <div class="form-group">
                <label>Stock Actual:</label>
                <input type="number" id="stock" value="30">
            </div>
            <div class="form-group">
                <label>Día de la Semana:</label>
                <select id="dia">
                    <option value="lunes">Lunes</option>
                    <option value="martes">Martes</option>
                    <option value="miercoles">Miércoles</option>
                    <option value="jueves">Jueves</option>
                    <option value="viernes">Viernes</option>
                    <option value="sabado">Sábado</option>
                    <option value="domingo">Domingo</option>
                </select>
            </div>
            <button onclick="consultarAgente()">Consultar Decisión Óptima</button>
            <div id="resultado" class="result-box">
                <p><strong>Unidades a comprar:</strong> <span id="res-unidades"></span></p>
                <p><strong>Valor Q (Bellman):</strong> <span id="res-q"></span></p>
                <small id="res-nota" style="display:block;margin-top:10px;font-weight:500;"></small>
            </div>
        </div>
        <script>
            async function consultarAgente() {
                const stock = parseInt(document.getElementById('stock').value);
                const dia   = document.getElementById('dia').value;
                const res   = await fetch('/prediccion', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({stock_actual: stock, dia_semana: dia})
                });
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('res-unidades').innerText = data.decision_abastecimiento.unidades_a_solicitar;
                    document.getElementById('res-q').innerText        = data.metadatos.valor_q_maximo;
                    document.getElementById('res-nota').innerText     = data.decision_abastecimiento.impacto_esperado;
                    document.getElementById('resultado').style.display = 'block';
                } else {
                    alert('Error al consultar al agente.');
                }
            }
        </script>
    </body>
    </html>
    """


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
        confianza_pct      = min(100, round(abs(diferencia_q) / (abs(valores_q[accion_optima_idx]) + 1) * 100, 1))
        explicacion = (
            f"Con stock {nivel_stock} ({datos.stock_actual} unidades) un {NOMBRES_DIAS[dia_idx]}, "
            f"el agente recomienda {NOMBRES_ACCIONES[cantidad_a_comprar]}. "
            f"La segunda mejor opción era {segunda_mejor_cant} unidades (diferencia Q: {diferencia_q}). "
            f"Nivel de confianza en la decisión: {confianza_pct}%."
        )
    else:
        cantidad_a_comprar = 10
        confianza_bellman  = 0.0
        origen_politica    = "Política de Contingencia (Estado Desconocido)"
        explicacion        = "Estado no visto durante el entrenamiento. Se aplica política de contingencia: comprar 10 unidades."

    return {
        "status": "success",
        "metadatos": {
            "estrategia_aplicada": origen_politica,
            "valor_q_maximo": round(confianza_bellman, 4)
        },
        "decision_abastecimiento": {
            "unidades_a_solicitar": cantidad_a_comprar,
            "unidad_medida": "Unidades",
            "impacto_esperado": explicacion
        }
    }