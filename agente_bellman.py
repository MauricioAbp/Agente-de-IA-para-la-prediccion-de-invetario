import json
import numpy as np
import random
import os
import logging
import shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] -> %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AgenteBellman")

RUTA_Q_TABLE = os.getenv("RUTA_Q_TABLE", "q_table.json")
BACKUP_DIR   = "q_table_backups"


class AgenteQlearning:
    def __init__(self, acciones_posibles,
                 alpha=None, gamma=None, epsilon=None,
                 min_epsilon=None, decay_rate=None):
        self.acciones      = acciones_posibles
        self.num_acciones  = len(acciones_posibles)
        self.alpha         = float(os.getenv("ALPHA",       alpha       or 0.1))
        self.gamma         = float(os.getenv("GAMMA",       gamma       or 0.9))
        self.epsilon       = float(os.getenv("EPSILON",     epsilon     or 1.0))
        self.min_epsilon   = float(os.getenv("MIN_EPSILON", min_epsilon or 0.01))
        self.decay_rate    = float(os.getenv("DECAY_RATE",  decay_rate  or 0.005))
        self.q_table       = {}

    def obtener_valores_q(self, estado):
        if estado not in self.q_table:
            self.q_table[estado] = np.zeros(self.num_acciones)
        return self.q_table[estado]

    def elegir_accion(self, estado):
        valores_q = self.obtener_valores_q(estado)
        if random.uniform(0, 1) < self.epsilon:
            return random.randint(0, self.num_acciones - 1)
        return int(np.argmax(valores_q))

    def actualizar_bellman(self, estado, accion_idx, recompensa, siguiente_estado):
        vq  = self.obtener_valores_q(estado)
        vqs = self.obtener_valores_q(siguiente_estado)
        vq[accion_idx] += self.alpha * (recompensa + self.gamma * np.max(vqs) - vq[accion_idx])

    def reducir_exploracion(self):
        if self.epsilon > self.min_epsilon:
            self.epsilon -= self.decay_rate

    def guardar_q_table(self, ruta_archivo=None):
        ruta_archivo = ruta_archivo or RUTA_Q_TABLE
        serializable = {f"{k[0]},{k[1]}": v.tolist() for k, v in self.q_table.items()}

        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefijo_hoy  = datetime.now().strftime("%Y%m%d")
        versiones    = [f for f in os.listdir(BACKUP_DIR)
                        if f.startswith(f"q_table_{prefijo_hoy}") and f.endswith(".json")]
        version      = len(versiones) + 1
        ruta_backup  = os.path.join(BACKUP_DIR, f"q_table_{timestamp}_v{version}.json")

        with open(ruta_backup, "w") as f:
            json.dump(serializable, f, indent=4)
        logger.info(f"Backup: '{ruta_backup}'")

        with open(ruta_archivo, "w") as f:
            json.dump(serializable, f, indent=4)
        logger.info(f"Q-Table principal: '{ruta_archivo}'")


if __name__ == "__main__":
    # Importación tardía: solo cuando se ejecuta como script
    from entorno_inventario import EntornoInventario

    entorno = EntornoInventario()
    agente  = AgenteQlearning(acciones_posibles=entorno.acciones_posibles)

    num_episodios = int(os.getenv("NUM_EPISODIOS", 500))
    logger.info(f"Iniciando entrenamiento ({num_episodios} episodios)...")

    registros_auditoria = []

    for episodio in range(num_episodios):
        estado    = entorno.reset()
        terminado = False
        recompensa_acumulada = 0

        while not terminado:
            stock_inicial = estado[0]
            fecha_actual  = entorno.df_ventas.iloc[entorno.dia_actual_idx]['fecha']
            accion_idx    = agente.elegir_accion(estado)
            siguiente_estado, recompensa, terminado, unidades_compradas = entorno.step(accion_idx)
            agente.actualizar_bellman(estado, accion_idx, recompensa, siguiente_estado)
            recompensa_acumulada += recompensa

            if episodio == (num_episodios - 1):
                registros_auditoria.append((
                    int(entorno.producto_id), str(fecha_actual),
                    int(stock_inicial), int(unidades_compradas), float(recompensa)
                ))
            estado = siguiente_estado

        agente.reducir_exploracion()

        if (episodio + 1) % 50 == 0 or episodio == 0:
            logger.info(
                f"Episodio {episodio+1:03d}/{num_episodios} | "
                f"Épsilon: {agente.epsilon:.4f} | "
                f"Recompensa acumulada: {recompensa_acumulada:.2f}"
            )

    logger.info("¡Entrenamiento completado!")
    agente.guardar_q_table()

    if registros_auditoria:
        cursor = entorno.conexion.cursor()
        sql = """INSERT INTO registro_acciones_agente
                 (producto_id, fecha, estado_stock_inicial, accion_compra, recompensa_obtenida)
                 VALUES (%s, %s, %s, %s, %s)"""
        cursor.executemany(sql, registros_auditoria)
        entorno.conexion.commit()
        logger.info(f"{cursor.rowcount} registros en 'registro_acciones_agente'.")
        cursor.close()

    entorno.conexion.close()