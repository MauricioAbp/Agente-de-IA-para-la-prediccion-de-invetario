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
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Sistema Inteligente de Inventarios</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>

*{
margin:0;
padding:0;
box-sizing:border-box;
font-family:'Poppins',sans-serif;
}

body{

background:linear-gradient(135deg,#0f172a,#1d4ed8,#38bdf8);

min-height:100vh;

display:flex;

justify-content:center;

align-items:center;

padding:30px;

}

.container{

width:100%;
max-width:1100px;

display:grid;

grid-template-columns:420px 1fr;

gap:30px;

}

.card{

background:rgba(255,255,255,.13);

backdrop-filter:blur(20px);

border:1px solid rgba(255,255,255,.15);

border-radius:22px;

padding:30px;

box-shadow:0 20px 45px rgba(0,0,0,.25);

color:white;

}
select{
    position: relative;
    z-index: 1000;
}
.form-group{
    position: relative;
    z-index: 1000;
}

.logo{

font-size:55px;

text-align:center;

margin-bottom:10px;

}

h1{

font-size:28px;

text-align:center;

font-weight:700;

}

.subtitle{

text-align:center;

margin-top:10px;

opacity:.8;

font-size:14px;

margin-bottom:35px;

}

.form-group{

margin-bottom:22px;

}

label{

display:block;

margin-bottom:8px;

font-weight:600;

}

input,select{

width:100%;

padding:14px;

border:none;

outline:none;

border-radius:12px;

font-size:15px;

background:white;

}

button{

width:100%;

padding:15px;

border:none;

border-radius:14px;

cursor:pointer;

font-size:17px;

font-weight:600;

background:linear-gradient(90deg,#06b6d4,#22c55e);

color:white;

transition:.3s;

}

button:hover{

transform:translateY(-2px);

box-shadow:0 10px 20px rgba(0,0,0,.2);

}

.dashboard{

display:flex;

flex-direction:column;

gap:20px;

}

.cards{

display:grid;

grid-template-columns:repeat(2,1fr);

gap:20px;

}

.info{

background:white;

color:#111827;

border-radius:18px;

padding:25px;

text-align:center;

box-shadow:0 8px 25px rgba(0,0,0,.12);

transition:.25s;

}

.info:hover{

transform:translateY(-5px);

}

.icon{

font-size:35px;

margin-bottom:10px;

}

.title{

font-size:14px;

color:#6b7280;

margin-bottom:10px;

}

.value{

font-size:30px;

font-weight:700;

color:#2563eb;

}

.result{

background:white;

border-radius:18px;

padding:25px;

display:none;

animation:fade .5s;

}

@keyframes fade{

from{

opacity:0;

transform:translateY(15px);

}

to{

opacity:1;

transform:translateY(0);

}

}

.result h2{

color:#111827;

margin-bottom:20px;

}

.status{

display:flex;

align-items:center;

gap:15px;

margin-top:20px;

}

.circle{

width:18px;

height:18px;

border-radius:50%;

background:#22c55e;

box-shadow:0 0 12px #22c55e;

}

.progress{

height:14px;

background:#e5e7eb;

border-radius:30px;

overflow:hidden;

margin-top:15px;

}

.progress{

    height:14px;
    background:#e5e7eb;
    border-radius:30px;
    overflow:hidden;
    margin-top:15px;

}

#barra-q{

    height:100%;
    width:0%;
    transition:width .6s ease, background .4s ease;
    background:linear-gradient(90deg,#06b6d4,#22c55e);

}

.note{

margin-top:18px;

line-height:1.7;

color:#374151;

}

.footer{

margin-top:30px;

font-size:13px;

color:#94a3b8;

text-align:center;

}

.loading{

display:none;

text-align:center;

color:white;

margin-top:20px;

font-weight:600;

}

</style>

</head>

<body>

<div class="container">

<div class="card">

<div class="logo">🤖</div>

<h1>Sistema Inteligente de Inventarios</h1>

<div class="subtitle">
Aprendizaje por Refuerzo • Q-Learning • Bellman
</div>

<div class="form-group">

<label>📦 Stock actual</label>

<input
type="number"
id="stock"
value="30">

</div>

<div class="form-group">

<label>📅 Día de la semana</label>

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

<button onclick="consultarAgente()">

Analizar Inventario

</button>

<div class="loading" id="loading">

⏳ Analizando con el agente inteligente...

</div>

<div class="footer">

FastAPI • HTML5 • Reinforcement Learning

</div>

</div>

<div class="dashboard">

<div class="cards">

<div class="info">

<div class="icon">📦</div>

<div class="title">

Unidades recomendadas

</div>

<div
class="value"
id="res-unidades">

--

</div>

</div>

<div class="info">

<div class="icon">📈</div>

<div class="title">

Valor Q

</div>

<div
class="value"
id="res-q">

--

</div>

</div>

</div>

<div
class="result"
id="resultado">

<h2>

🤖 Evaluación del Agente Inteligente

</h2>

<p style="color:#6b7280; font-size:13px; margin-bottom:6px;">📊 Nivel de stock actual</p>
<div class="progress">
    <div id="barra-q"></div>
</div>
<p id="label-stock" style="font-size:12px; color:#6b7280; margin-top:5px; text-align:right;"></p>

<div class="status">

<div class="circle"></div>

<strong>

Estado óptimo encontrado

</strong>

</div>

<div
class="note"
id="res-nota">

</div>

</div>

</div>

</div>

<script>

async function consultarAgente(){

document.getElementById("loading").style.display="block";

document.getElementById("resultado").style.display="none";

const stock=parseInt(document.getElementById("stock").value);

const dia=document.getElementById("dia").value;

try{

const res=await fetch('/prediccion',{

method:'POST',

headers:{'Content-Type':'application/json'},

body:JSON.stringify({

stock_actual:stock,

dia_semana:dia

})

});

if(res.ok){

const data = await res.json();

const q = Number(data.metadatos.valor_q_maximo);

document.getElementById("res-unidades").innerText =
data.decision_abastecimiento.unidades_a_solicitar;

document.getElementById("res-q").innerText =
q.toFixed(4);

const barra = document.getElementById("barra-q");
const STOCK_MAX = 100;
const porcentaje = Math.min(100, Math.round((stock / STOCK_MAX) * 100));
barra.style.width = porcentaje + "%";

if(porcentaje >= 60){
    barra.style.background = "#22c55e";
    document.getElementById("label-stock").innerText = "Stock alto ✅";
}else if(porcentaje >= 25){
    barra.style.background = "#f59e0b";
    document.getElementById("label-stock").innerText = "Stock normal ⚠️";
}else if(porcentaje > 0){
    barra.style.background = "#ef4444";
    document.getElementById("label-stock").innerText = "Stock bajo 🔴";
}else{
    barra.style.background = "#ef4444";
    barra.style.width = "3%";
    document.getElementById("label-stock").innerText = "Sin stock 🚨";
}

document.getElementById("res-nota").innerHTML =
"<strong>Impacto esperado:</strong><br>" +
data.decision_abastecimiento.impacto_esperado;

document.getElementById("resultado").style.display = "block";

}else{

alert("Error al consultar el agente.");

}

}catch{

alert("No fue posible conectar con la API.");

}

document.getElementById("loading").style.display="none";

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