import mysql.connector
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

class EntornoInventario:
    def __init__(self):
        self.conexion = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        acciones_raw = os.getenv("ACCIONES_POSIBLES", "0,10,20,30,50")
        self.acciones_posibles = [int(x) for x in acciones_raw.split(",")]
        self.penalizacion_factor = float(os.getenv("PENALIZACION_QUIEBRE_FACTOR", "1.5"))

        cursor = self.conexion.cursor()
        cursor.execute("SELECT id FROM productos LIMIT 1")
        resultado = cursor.fetchone()
        self.producto_id = resultado[0] if resultado else int(os.getenv("PRODUCTO_ID_DEFAULT", "1"))
        cursor.close()

        self.cargar_datos_negocio()
        self.cargar_historial_ventas()
        self.reset()

    def cargar_datos_negocio(self):
        cursor = self.conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT stock_actual, costo_almacenamiento_diario, precio_venta FROM productos WHERE id = %s",
            (self.producto_id,)
        )
        prod = cursor.fetchone()
        self.costo_almacenamiento = float(prod['costo_almacenamiento_diario'])
        self.precio_venta = float(prod['precio_venta'])
        self.stock_inicial_real = prod['stock_actual']
        cursor.close()

    def cargar_historial_ventas(self):
        query = f"SELECT fecha, cantidad_vendida FROM historial_ventas WHERE producto_id = {self.producto_id} ORDER BY fecha"
        self.df_ventas = pd.read_sql(query, self.conexion)
        self.total_dias = len(self.df_ventas)

    def reset(self):
        self.dia_actual_idx = 0
        self.stock_simulado = self.stock_inicial_real
        fecha_inicial = pd.to_datetime(self.df_ventas.iloc[0]['fecha'])
        return (self.stock_simulado, fecha_inicial.weekday())

    def step(self, accion_idx):
        unidades_compradas = self.acciones_posibles[accion_idx]
        self.stock_simulado += unidades_compradas
        stock_antes_de_vender = self.stock_simulado

        demanda_real = self.df_ventas.iloc[self.dia_actual_idx]['cantidad_vendida']
        fecha_actual = pd.to_datetime(self.df_ventas.iloc[self.dia_actual_idx]['fecha'])

        ventas_efectivas = min(stock_antes_de_vender, demanda_real)
        quiebre_stock = max(0, demanda_real - stock_antes_de_vender)
        self.stock_simulado = max(0, stock_antes_de_vender - ventas_efectivas)

        ingresos = ventas_efectivas * self.precio_venta
        costo_guardar = self.stock_simulado * self.costo_almacenamiento
        penalizacion_quiebre = quiebre_stock * (self.precio_venta * self.penalizacion_factor)
        recompensa = ingresos - costo_guardar - penalizacion_quiebre

        self.dia_actual_idx += 1
        terminado = self.dia_actual_idx >= self.total_dias

        if not terminado:
            siguiente_fecha = pd.to_datetime(self.df_ventas.iloc[self.dia_actual_idx]['fecha'])
            siguiente_estado = (self.stock_simulado, siguiente_fecha.weekday())
        else:
            siguiente_estado = (0, 0)

        return siguiente_estado, recompensa, terminado, unidades_compradas


if __name__ == "__main__":
    env = EntornoInventario()
    estado = env.reset()
    print(f"-> Conexión exitosa. Estado Inicial Simulado (Stock, Día de la semana): {estado}")