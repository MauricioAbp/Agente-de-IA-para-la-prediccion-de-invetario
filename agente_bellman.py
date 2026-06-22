import json
import numpy as np
import random
import os
import logging
from entorno_inventario import EntornoInventario

# Configuración de Logs estilo producción industrial
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] -> %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AgenteBellman")

class AgenteQlearning:
    def __init__(self, acciones_posibles, alpha=0.1, gamma=0.9, epsilon=1.0, min_epsilon=0.01, decay_rate=0.005):
        self.acciones = acciones_posibles
        self.num_acciones = len(acciones_posibles)
        
        # Parámetros matemáticos de Bellman y RL
        self.alpha = alpha        
        self.gamma = gamma        
        self.epsilon = epsilon    
        self.min_epsilon = min_epsilon
        self.decay_rate = decay_rate
        self.q_table = {}

    def obtener_valores_q(self, estado):
        """Inicializa estados desconocidos garantizando aprendizaje desde cero"""
        if estado not in self.q_table:
            self.q_table[estado] = np.zeros(self.num_acciones)
        return self.q_table[estado]

    def elegir_accion(self, estado):
        """Estrategia Epsilon-Greedy (Exploración vs Explotación)"""
        valores_q = self.obtener_valores_q(estado)
        if random.uniform(0, 1) < self.epsilon:
            return random.randint(0, self.num_acciones - 1)
        else:
            return np.argmax(valores_q)

    def actualizar_bellman(self, estado, accion_idx, recompensa, siguiente_estado):
        """
        APLICACIÓN DE LA ECUACIÓN DE BELLMAN:
        Q(s,a) = Q(s,a) + alpha * [R + gamma * max(Q(s',a')) - Q(s,a)]
        """
        valores_q_actuales = self.obtener_valores_q(estado)
        valores_q_siguiente = self.obtener_valores_q(siguiente_estado)
        
        max_q_futuro = np.max(valores_q_siguiente)
        valores_q_actuales[accion_idx] += self.alpha * (recompensa + self.gamma * max_q_futuro - valores_q_actuales[accion_idx])

    def reducir_exploracion(self):
        if self.epsilon > self.min_epsilon:
            self.epsilon -= self.decay_rate
    
    def guardar_q_table(self, ruta_archivo="q_table.json"):
        q_table_serializable = {f"{k[0]},{k[1]}": v.tolist() for k, v in self.q_table.items()}
        with open(ruta_archivo, "w") as f:
            json.dump(q_table_serializable, f, indent=4)
        logger.info(f"Cerebro matemático exportado con éxito a: '{ruta_archivo}'")

if __name__ == "__main__":
    entorno = EntornoInventario()
    agente = AgenteQlearning(acciones_posibles=entorno.acciones_posibles)
    
    num_episodios = 500
    logger.info(f"Iniciando convergencia basada en la Ecuación de Bellman ({num_episodios} episodios desde cero)...")
    
    registros_auditoria = []
    
    for episodio in range(num_episodios):
        estado = entorno.reset()
        terminado = False
        recompensa_acumulada = 0
        
        while not terminado:
            stock_inicial = estado[0]
            fecha_actual = entorno.df_ventas.iloc[entorno.dia_actual_idx]['fecha']
            
            accion_idx = agente.elegir_accion(estado)
            siguiente_estado, recompensa, terminado, unidades_compradas = entorno.step(accion_idx)
            agente.actualizar_bellman(estado, accion_idx, recompensa, siguiente_estado)
            
            recompensa_acumulada += recompensa
            
            if episodio == (num_episodios - 1):
                registros_auditoria.append((
                    int(entorno.producto_id), str(fecha_actual), int(stock_inicial), int(unidades_compradas), float(recompensa)
                ))
            
            estado = siguiente_estado
        agente.reducir_exploracion()
        
        # Mostrar progreso cada 50 episodios para validar convergencia ante la profesora
        if (episodio + 1) % 50 == 0 or episodio == 0:
            logger.info(f"Episodio {episodio+1:03d}/{num_episodios} | Épsilon (Exploración): {agente.epsilon:.4f} | Política del Agente: Aprendiendo...")

    logger.info("¡Entrenamiento del agente e inferencia completados!")
    agente.guardar_q_table()
    
    if registros_auditoria:
        logger.info("Estabilizando políticas operativas. Conectando a MySQL...")
        cursor = entorno.conexion.cursor()
        sql = """INSERT INTO registro_acciones_agente 
                 (producto_id, fecha, estado_stock_inicial, accion_compra, recompensa_obtenida) 
                 VALUES (%s, %s, %s, %s, %s)"""
        
        cursor.executemany(sql, registros_auditoria)
        entorno.conexion.commit()
        logger.info(f"Auditoría inyectada: {cursor.rowcount} registros guardados vía (executemany) en tabla 'registro_acciones_agente'.")
        cursor.close()
    
    entorno.conexion.close()