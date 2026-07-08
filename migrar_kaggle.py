import pandas as pd
import mysql.connector
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] -> %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("MigradorKaggle")


def migrar_datos():
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = conexion.cursor()
    except Exception as e:
        logger.error(f"Error de conexión a MySQL: {e}")
        return

    nombre_archivo = os.getenv("EXCEL_FILENAME", "Coffee Shop Sales.xlsx")
    carpeta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_excel     = os.path.join(carpeta_actual, nombre_archivo)

    if not os.path.exists(ruta_excel):
        logger.error(f"Archivo no encontrado: '{ruta_excel}'")
        logger.info(f"Archivos en carpeta: {os.listdir(carpeta_actual)}")
        cursor.close()
        conexion.close()
        return

    try:
        logger.info(f"Leyendo: {ruta_excel}")
        df = pd.read_excel(ruta_excel)
        df.columns = [col.lower().strip() for col in df.columns]
        logger.info(f"Columnas: {list(df.columns)}")

        col_fecha    = 'transaction_date' if 'transaction_date' in df.columns else [c for c in df.columns if 'date' in c][0]
        col_cantidad = 'transaction_qty'  if 'transaction_qty'  in df.columns else [c for c in df.columns if 'qty' in c or 'quant' in c][0]

        logger.info(f"Fecha: '{col_fecha}' | Cantidad: '{col_cantidad}'")

        df['fecha_limpia'] = pd.to_datetime(df[col_fecha]).dt.strftime('%Y-%m-%d')
        df_diario = df.groupby('fecha_limpia')[col_cantidad].sum().reset_index()
        df_diario.sort_values('fecha_limpia', inplace=True)
        logger.info(f"{len(df_diario)} días consolidados.")

    except Exception as e:
        logger.error(f"Error procesando Excel: {e}")
        cursor.close()
        conexion.close()
        return

    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE historial_ventas;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conexion.commit()
    except Exception as e:
        logger.error(f"Error limpiando tabla: {e}")
        cursor.close()
        conexion.close()
        return

    producto_id = int(os.getenv("PRODUCTO_ID_DEFAULT", "1"))
    sql = "INSERT INTO historial_ventas (producto_id, fecha, cantidad_vendida) VALUES (%s, %s, %s)"
    registros = [(producto_id, row['fecha_limpia'], int(row[col_cantidad])) for _, row in df_diario.iterrows()]

    try:
        cursor.executemany(sql, registros)
        conexion.commit()
        logger.info(f"{cursor.rowcount} días migrados a 'historial_ventas'.")
    except Exception as e:
        conexion.rollback()
        logger.error(f"Error en inserción masiva: {e}")
    finally:
        cursor.close()
        conexion.close()


if __name__ == "__main__":
    migrar_datos()