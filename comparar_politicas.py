"""
Comparación: Agente Q-Learning vs Política Simple (comprar siempre 30)
Ejecutar: python comparar_politicas.py
"""
import json
import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# ── Configuración ──────────────────────────────────────────────────────────────
RUTA_Q_TABLE      = os.getenv("RUTA_Q_TABLE", "q_table.json")
ACCIONES_POSIBLES = [int(x) for x in os.getenv("ACCIONES_POSIBLES", "0,5,10,15,20,25,30,40,50,70,100").split(",")]
PRECIO_VENTA      = 5.0    # ajusta si sabes el valor real
COSTO_ALMACEN     = 0.1    # costo por unidad almacenada por día
PENALIZACION      = float(os.getenv("PENALIZACION_QUIEBRE_FACTOR", "3.0"))

# Escenarios de prueba: (stock_inicial, demanda_simulada, dia_idx)
ESCENARIOS = [
    {"nombre": "Stock crítico – Lunes",    "stock": 0,   "demanda": 45, "dia": 0},
    {"nombre": "Stock bajo – Martes",      "stock": 5,   "demanda": 38, "dia": 1},
    {"nombre": "Stock bajo – Miércoles",   "stock": 10,  "demanda": 42, "dia": 2},
    {"nombre": "Stock normal – Jueves",    "stock": 35,  "demanda": 40, "dia": 3},
    {"nombre": "Stock normal – Viernes",   "stock": 50,  "demanda": 55, "dia": 4},
    {"nombre": "Stock alto – Sábado",      "stock": 80,  "demanda": 30, "dia": 5},
    {"nombre": "Stock alto – Domingo",     "stock": 100, "demanda": 20, "dia": 6},
    {"nombre": "Stock cero – Viernes",     "stock": 0,   "demanda": 60, "dia": 4},
    {"nombre": "Stock bajo – Domingo",     "stock": 8,   "demanda": 18, "dia": 6},
    {"nombre": "Stock normal – Lunes",     "stock": 40,  "demanda": 50, "dia": 0},
]


def calcular_recompensa(stock_inicial, unidades_compradas, demanda):
    stock = stock_inicial + unidades_compradas
    ventas = min(stock, demanda)
    quiebre = max(0, demanda - stock)
    stock_final = max(0, stock - ventas)

    ingresos   = ventas * PRECIO_VENTA
    costo_alma = stock_final * COSTO_ALMACEN
    penalizacion = quiebre * (PRECIO_VENTA * PENALIZACION)
    return ingresos - costo_alma - penalizacion, ventas, quiebre, stock_final


def decision_agente(q_table, stock, dia):
    llave = f"{stock},{dia}"
    if llave in q_table:
        valores_q = q_table[llave]
        idx = int(np.argmax(valores_q))
        return ACCIONES_POSIBLES[idx], "Q-Table"
    # Contingencia inteligente
    if stock <= 10:
        return 70, "Contingencia"
    elif stock <= 30:
        return 30, "Contingencia"
    else:
        return 10, "Contingencia"


def decision_simple(stock, dia):
    return 30  # política fija


def main():
    if not os.path.exists(RUTA_Q_TABLE):
        print("❌ No se encontró q_table.json. Entrena el agente primero.")
        return

    with open(RUTA_Q_TABLE) as f:
        q_table = json.load(f)

    print("\n" + "═" * 85)
    print(f"{'COMPARACIÓN: AGENTE Q-LEARNING vs POLÍTICA SIMPLE (comprar siempre 30)':^85}")
    print("═" * 85)
    print(f"{'Escenario':<30} {'Compra':>6} {'Simple':>6} {'Recomp.Agente':>14} {'Recomp.Simple':>14} {'Ganador':>10}")
    print("─" * 85)

    total_agente = 0
    total_simple = 0
    victorias_agente = 0
    victorias_simple = 0

    for e in ESCENARIOS:
        compra_agente, origen = decision_agente(q_table, e["stock"], e["dia"])
        compra_simple         = decision_simple(e["stock"], e["dia"])

        r_agente, v_a, q_a, sf_a = calcular_recompensa(e["stock"], compra_agente, e["demanda"])
        r_simple, v_s, q_s, sf_s = calcular_recompensa(e["stock"], compra_simple, e["demanda"])

        total_agente += r_agente
        total_simple += r_simple

        if r_agente > r_simple:
            ganador = "🤖 Agente"
            victorias_agente += 1
        elif r_simple > r_agente:
            ganador = "📏 Simple"
            victorias_simple += 1
        else:
            ganador = "  Empate"

        print(f"{e['nombre']:<30} {compra_agente:>6} {compra_simple:>6} {r_agente:>14.2f} {r_simple:>14.2f} {ganador:>10}")

    print("─" * 85)
    print(f"{'TOTAL':.<30} {'':>6} {'':>6} {total_agente:>14.2f} {total_simple:>14.2f}")
    print("═" * 85)

    diferencia = total_agente - total_simple
    print(f"\n📊 RESULTADO FINAL")
    print(f"   Victorias Agente Q-Learning : {victorias_agente}/{len(ESCENARIOS)}")
    print(f"   Victorias Política Simple   : {victorias_simple}/{len(ESCENARIOS)}")
    print(f"   Diferencia de recompensa    : {diferencia:+.2f}")

    if diferencia > 0:
        mejora = (diferencia / abs(total_simple)) * 100
        print(f"   ✅ El agente supera a la política simple en {mejora:.1f}%")
    elif diferencia < 0:
        print(f"   ⚠️  La política simple supera al agente. Considera más episodios de entrenamiento.")
    else:
        print(f"   ⚖️  Empate exacto.")

    print("\n📋 DETALLE POR ESCENARIO")
    print("─" * 85)
    for e in ESCENARIOS:
        compra_agente, origen = decision_agente(q_table, e["stock"], e["dia"])
        compra_simple         = decision_simple(e["stock"], e["dia"])
        r_agente, v_a, q_a, sf_a = calcular_recompensa(e["stock"], compra_agente, e["demanda"])
        r_simple, v_s, q_s, sf_s = calcular_recompensa(e["stock"], compra_simple, e["demanda"])

        print(f"\n  {e['nombre']} | Stock: {e['stock']} | Demanda real: {e['demanda']}")
        print(f"  Agente ({origen}): compra {compra_agente} → vendió {v_a}, quiebre {q_a}, stock final {sf_a} → recompensa {r_agente:.2f}")
        print(f"  Simple          : compra {compra_simple} → vendió {v_s}, quiebre {q_s}, stock final {sf_s} → recompensa {r_simple:.2f}")

    print("\n" + "═" * 85)


if __name__ == "__main__":
    main()