"""
pytest tests/test_agente.py
"""
import json
import os
import sys
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_agente(acciones=None):
    """Importa AgenteQlearning sin cargar .env del disco."""
    from agente_bellman import AgenteQlearning
    return AgenteQlearning(acciones_posibles=acciones or [0, 10, 20, 30, 50])


# ── AgenteQlearning ────────────────────────────────────────────────────────────

class TestAgenteQlearning:
    def test_inicializa_q_table_vacia(self):
        agente = make_agente()
        assert agente.q_table == {}

    def test_obtener_valores_q_crea_estado_nuevo(self):
        agente = make_agente()
        estado = (30, 0)
        valores = agente.obtener_valores_q(estado)
        assert len(valores) == 5
        assert all(v == 0.0 for v in valores)

    def test_elegir_accion_explotacion(self):
        """Con epsilon=0 siempre elige el índice de mayor Q."""
        agente = make_agente()
        agente.epsilon = 0.0
        estado = (30, 0)
        agente.q_table[estado] = np.array([0.0, 0.0, 9.9, 0.0, 0.0])
        assert agente.elegir_accion(estado) == 2

    def test_elegir_accion_exploracion(self):
        """Con epsilon=1 la acción es aleatoria (puede ser cualquier índice)."""
        agente = make_agente()
        agente.epsilon = 1.0
        estado = (30, 0)
        accion = agente.elegir_accion(estado)
        assert 0 <= accion < 5

    def test_actualizar_bellman_cambia_q(self):
        agente = make_agente()
        agente.epsilon = 0.0
        estado = (30, 0)
        siguiente = (20, 1)
        agente.q_table[estado]    = np.zeros(5)
        agente.q_table[siguiente] = np.array([0, 5, 0, 0, 0])

        agente.actualizar_bellman(estado, 1, recompensa=10.0, siguiente_estado=siguiente)
        # Q(s,a) debe subir desde 0
        assert agente.q_table[estado][1] > 0.0

    def test_reducir_exploracion(self):
        agente = make_agente()
        agente.epsilon    = 0.5
        agente.decay_rate = 0.1
        agente.min_epsilon = 0.01
        agente.reducir_exploracion()
        assert abs(agente.epsilon - 0.4) < 1e-9

    def test_epsilon_no_baja_de_min(self):
        agente = make_agente()
        agente.epsilon     = 0.01
        agente.decay_rate  = 1.0
        agente.min_epsilon = 0.01
        agente.reducir_exploracion()
        assert agente.epsilon == 0.01

    def test_guardar_q_table_crea_archivos(self, tmp_path):
        agente = make_agente()
        agente.q_table = {(10, 0): np.array([1.0, 2.0, 3.0, 4.0, 5.0])}

        ruta_principal = str(tmp_path / "q_table.json")
        backup_dir_orig = __import__("agente_bellman").BACKUP_DIR

        # Redirigir el directorio de backups al tmp_path
        import agente_bellman
        agente_bellman.BACKUP_DIR = str(tmp_path / "backups")

        agente.guardar_q_table(ruta_archivo=ruta_principal)

        agente_bellman.BACKUP_DIR = backup_dir_orig  # restaurar

        assert os.path.exists(ruta_principal)
        backups = list((tmp_path / "backups").glob("q_table_*.json"))
        assert len(backups) == 1

    def test_guardar_q_table_contenido_correcto(self, tmp_path):
        agente = make_agente()
        agente.q_table = {(5, 2): np.array([0.1, 0.2, 0.3, 0.4, 0.5])}

        import agente_bellman
        old_backup = agente_bellman.BACKUP_DIR
        agente_bellman.BACKUP_DIR = str(tmp_path / "backups")

        ruta = str(tmp_path / "q_table.json")
        agente.guardar_q_table(ruta_archivo=ruta)
        agente_bellman.BACKUP_DIR = old_backup

        with open(ruta) as f:
            data = json.load(f)

        assert "5,2" in data
        assert len(data["5,2"]) == 5


# ── API FastAPI ─────────────────────────────────────────────────────────────────

class TestAPI:
    @pytest.fixture(autouse=True)
    def setup_client(self, tmp_path):
        """Arranca la app con una q_table de prueba."""
        import main as api_module
        from fastapi.testclient import TestClient

        # Inyectar q_table de prueba directamente
        api_module.q_table_cargada = {
            "30,0": [0.0, 1.0, 5.0, 2.0, 0.5],   # mejor acción: índice 2 → 20 unidades
            "0,3":  [0.0, 0.0, 0.0, 0.0, 0.0],
        }
        self.client = TestClient(api_module.app)

    def test_prediccion_estado_conocido(self):
        res = self.client.post("/prediccion", json={"stock_actual": 30, "dia_semana": "lunes"})
        assert res.status_code == 200
        data = res.json()
        assert data["decision_abastecimiento"]["unidades_a_solicitar"] == 20

    def test_prediccion_estado_desconocido_devuelve_contingencia(self):
        res = self.client.post("/prediccion", json={"stock_actual": 999, "dia_semana": "martes"})
        assert res.status_code == 200
        data = res.json()
        assert data["decision_abastecimiento"]["unidades_a_solicitar"] == 10
        assert "Contingencia" in data["metadatos"]["estrategia_aplicada"]

    def test_prediccion_dia_invalido(self):
        res = self.client.post("/prediccion", json={"stock_actual": 10, "dia_semana": "ayer"})
        assert res.status_code == 400

    def test_prediccion_stock_negativo_rechazado(self):
        res = self.client.post("/prediccion", json={"stock_actual": -1, "dia_semana": "lunes"})
        assert res.status_code == 422  # Pydantic validation error

    def test_prediccion_dia_en_mayusculas(self):
        """El endpoint debe tolerar mayúsculas."""
        res = self.client.post("/prediccion", json={"stock_actual": 30, "dia_semana": "Lunes"})
        assert res.status_code == 200

    def test_interfaz_grafica_devuelve_html(self):
        res = self.client.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]


# ── Entorno (unitario, sin BD) ──────────────────────────────────────────────────

class TestEntornoInventario:
    @pytest.fixture
    def entorno_mock(self):
        """Entorno con dependencias de MySQL y pandas mockeadas."""
        import sys
        import types
        import pandas as pd

        # Inyectar mysql.connector falso antes de importar el módulo
        mysql_mock = types.ModuleType("mysql")
        connector_mock = types.ModuleType("mysql.connector")
        connector_mock.connect = MagicMock()
        mysql_mock.connector = connector_mock
        sys.modules.setdefault("mysql", mysql_mock)
        sys.modules.setdefault("mysql.connector", connector_mock)

        import entorno_inventario as env_module

        fechas = pd.date_range("2024-01-01", periods=5, freq="D")
        df_ventas = pd.DataFrame({
            "fecha": fechas,
            "cantidad_vendida": [10, 20, 15, 25, 5]
        })

        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        with patch("entorno_inventario.mysql.connector.connect", return_value=mock_conn), \
             patch("entorno_inventario.pd.read_sql", return_value=df_ventas), \
             patch.object(env_module.EntornoInventario, "cargar_datos_negocio",
                          lambda self: setattr(self, "costo_almacenamiento", 0.5) or
                                       setattr(self, "precio_venta", 10.0) or
                                       setattr(self, "stock_inicial_real", 50)):
            entorno = env_module.EntornoInventario()

        entorno.df_ventas = df_ventas
        entorno.total_dias = len(df_ventas)
        return entorno

    def test_reset_devuelve_estado_correcto(self, entorno_mock):
        estado = entorno_mock.reset()
        assert isinstance(estado, tuple)
        assert len(estado) == 2
        assert estado[0] == 50  # stock_inicial_real

    def test_step_avanza_dia(self, entorno_mock):
        entorno_mock.reset()
        _, _, _, _ = entorno_mock.step(0)  # acción 0 = comprar 0
        assert entorno_mock.dia_actual_idx == 1

    def test_step_detecta_terminado(self, entorno_mock):
        entorno_mock.reset()
        terminado = False
        for _ in range(5):
            _, _, terminado, _ = entorno_mock.step(0)
        assert terminado is True

    def test_step_recompensa_es_float(self, entorno_mock):
        entorno_mock.reset()
        _, recompensa, _, _ = entorno_mock.step(1)
        assert isinstance(recompensa, float)