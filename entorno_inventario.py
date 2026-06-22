import mysql.connector
import pandas as pd
import numpy as np

class EntornoInventario:
    def __init__(self):
        self.conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="77016141",
            database="sistema_inventario_ml"
        )
        # Buscar el primer ID válido directamente de la base de datos
        cursor = self.conexion.cursor()
        cursor.execute("SELECT id FROM productos LIMIT 1")
        resultado = cursor.fetchone()
        self.producto_id = resultado[0] if resultado else 1
        cursor.close()
        
        self.cargar_datos_negocio()
        self.cargar_historial_ventas()
        
        self.acciones_posibles = [0,10,20,30,50]
        self.reset()
    
    
    def cargar_datos_negocio(self):
        cursor = self.conexion.cursor(dictionary=True)
        cursor.execute("SELECT stock_actual, costo_almacenamiento_diario, precio_venta FROM productos WHERE id = %s",(self.producto_id,))
        prod = cursor.fetchone()
        self.costo_almacenamiento =float(prod['costo_almacenamiento_diario'])
        self.precio_venta = float(prod['precio_venta'])
        self.stock_inicial_real=prod['stock_actual']
        cursor.close()
    
    def cargar_historial_ventas(self):
        # Inyectamos el ID directamente en el string para evitar problemas de compatibilidad con pandas
        query = f"SELECT fecha, cantidad_vendida FROM historial_ventas WHERE producto_id = {self.producto_id} ORDER BY fecha"
        
        # Ignora el UserWarning que suelta pandas, no afecta en nada a la ejecución local
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
        penalizacion_quiebre = quiebre_stock * (self.precio_venta * 1.5) # Castigo fuerte por perder cliente
        
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
        