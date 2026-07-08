import streamlit as st
import requests

st.set_page_config(
    page_title="Optimización de Inventario",
    page_icon="📦",
    layout="centered"
)

st.title("📦 Sistema de Optimización de Inventarios")
st.subheader("Selector de Acciones mediante Aprendizaje por Refuerzo (Bellman)")
st.write("Introduce el estado actual del almacén para consultar la política óptima del agente.")

# Formulario de entrada
with st.form("formulario_inventario"):
    stock_actual = st.number_input(
        "Stock Actual en Almacén:",
        min_value=0,
        max_value=200,
        value=30,
        step=1
    )

    dia_semana = st.selectbox(
        "Día de la Semana:",
        [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo"
        ]
    )

    boton_consultar = st.form_submit_button("Consultar Agente Inteligente")

# Procesar la petición
if boton_consultar:

    # Normalizar el día de la semana
    dia_normalizado = (
        dia_semana.lower()
        .replace("miércoles", "miercoles")
        .replace("sábado", "sabado")
    )

    payload = {
        "stock_actual": int(stock_actual),
        "dia_semana": dia_normalizado
    }

    try:
        respuesta = requests.post(
            "http://127.0.0.1:8000/prediccion",
            json=payload
        )

        if respuesta.status_code == 200:

            resultado = respuesta.json()

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Recomendación de Compra",
                    f"{resultado['decision_abastecimiento']['unidades_a_solicitar']} unidades"
                )

            with col2:
                st.metric(
                    "Valor Q Estimado (Convergencia)",
                    resultado["metadatos"]["valor_q_maximo"]
                )

            st.info(
                f"💡 **Nota del Agente:** {resultado['decision_abastecimiento']['impacto_esperado']}"
            )

        else:
            st.error(
                f"Error en la API: {respuesta.status_code} - "
                f"{respuesta.json().get('detail', 'Desconocido')}"
            )

    except requests.exceptions.ConnectionError:
        st.error(
            "❌ No se pudo conectar con la API de FastAPI. "
            "Asegúrate de que el servidor uvicorn esté corriendo en el puerto 8000."
        )