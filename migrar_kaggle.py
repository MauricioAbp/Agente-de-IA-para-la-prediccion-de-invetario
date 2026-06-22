import pandas as pd
import mysql.connector
import logging
import os

# Configuración de logs profesionales
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] -> %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("MigradorKaggle")

def migrar_datos():
    # 1. Conexión a la Base de Datos MySQL
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="77016141",
            database="sistema_inventario_ml"
        )
        cursor = conexion.cursor()
    except Exception as e:
        logger.error(f"Error de conexión a MySQL: {e}")
        return

    # 2. Localizar el archivo Excel de forma robusta usando rutas absolutas
    nombre_archivo = "Coffee Shop Sales.xlsx"
    carpeta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_excel = os.path.join(carpeta_actual, nombre_archivo)
    
    if not os.path.exists(ruta_excel):
        logger.error(f"No se encontró el archivo en la ruta esperada: '{ruta_excel}'")
        logger.info("Archivos detectados actualmente en esta carpeta por Python:")
        logger.info(os.listdir(carpeta_actual))
        cursor.close()
        conexion.close()
        return
    
    try:
        logger.info(f"Leyendo dataset de Kaggle desde Excel: {ruta_excel}...")
        # Leemos el archivo .xlsx usando pandas
        df = pd.read_excel(ruta_excel)
        
        # Normalizar los nombres de las columnas a minúsculas y sin espacios marginales
        df.columns = [col.lower().strip() for col in df.columns]
        logger.info(f"Columnas normalizadas en el archivo: {list(df.columns)}")
        
        # Mapeo dinámico de columnas por palabras clave
        col_fecha = 'transaction_date' if 'transaction_date' in df.columns else 'date'
        col_cantidad = 'transaction_qty' if 'transaction_qty' in df.columns else 'quantity'
        
        # Si fallan los nombres exactos, buscamos aproximaciones
        if col_fecha not in df.columns:
            col_fecha = [c for c in df.columns if 'date' in c][0]
        if col_cantidad not in df.columns:
            col_cantidad = [c for c in df.columns if 'qty' in c or 'quant' in c][0]

        logger.info(f"Columnas seleccionadas para el mapeo -> Fecha: '{col_fecha}', Cantidad: '{col_cantidad}'")

        # Convertir y estandarizar la columna de fechas a formato ISO (YYYY-MM-DD)
        df['fecha_limpia'] = pd.to_datetime(df[col_fecha]).dt.strftime('%Y-%m-%d')
        
        # Consolidamos la demanda sumando las cantidades por día (Agrupación de transacciones)
        df_diario = df.groupby('fecha_limpia')[col_cantidad].sum().reset_index()
        df_diario.sort_values('fecha_limpia', inplace=True)
        
        logger.info(f"Procesamiento finalizado. Se consolidaron {len(df_diario)} días de demanda real.")
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento y limpieza del Excel: {e}")
        cursor.close()
        conexion.close()
        return

    # 3. Limpieza segura de la tabla para evitar duplicar registros
    try:
        logger.info("Vaciando registros anteriores de 'historial_ventas' mediante TRUNCATE...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE historial_ventas;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conexion.commit()
    except Exception as e:
        logger.error(f"Error al limpiar la tabla de la base de datos: {e}")
        cursor.close()
        conexion.close()
        return

    # 4. Inserción Masiva Optimizada (Bulk Insert con executemany)
    sql = "INSERT INTO historial_ventas (producto_id, fecha, cantidad_vendida) VALUES (%s, %s, %s)"
    
    # Asignamos de manera fija el producto_id = 1 (Café Premium de tu catálogo)
    registros = [(1, row['fecha_limpia'], int(row[col_cantidad])) for _, row in df_diario.iterrows()]
    
    try:
        logger.info("Inyectando el nuevo dataset de Kaggle a MySQL Workbench...")
        cursor.executemany(sql, registros)
        conexion.commit()
        logger.info(f"¡Éxito absoluto! {cursor.rowcount} días transaccionales migrados a la tabla 'historial_ventas'.")
    except Exception as e:
        conexion.rollback()
        logger.error(f"Error crítico durante la inserción masiva en BD: {e}")
    finally:
        cursor.close()
        conexion.close()

if __name__ == "__main__":
    migrar_datos()