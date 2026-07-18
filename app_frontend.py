import streamlit as st
import requests

# -----------------------------
# Configuración de la página
# -----------------------------

st.set_page_config(
    page_title="Sistema Inteligente de Inventarios",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# CSS e Iconos Material Design 3
# -----------------------------

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap" rel="stylesheet">

<style>
/* Reset and General Font Style */
html, body, [class*="css"], .stApp {
    font-family: 'Roboto', sans-serif !important;
    background-color: #F8F9FA;
}

/* Custom Header with Material Look */
.md-header {
    background: linear-gradient(135deg, #6750A4 0%, #513B8C 100%);
    color: white;
    padding: 32px;
    border-radius: 20px;
    margin-bottom: 30px;
    box-shadow: 0 4px 15px rgba(103, 80, 164, 0.2);
    display: flex;
    align-items: center;
    gap: 20px;
}

.md-header-icon {
    font-size: 48px !important;
    color: #EADDFF;
}

.md-header-title-container {
    display: flex;
    flex-direction: column;
}

.md-header-title {
    font-size: 28px !important;
    font-weight: 700 !important;
    margin: 0 !important;
    line-height: 1.2;
}

.md-header-subtitle {
    font-size: 13px !important;
    color: #EADDFF;
    margin-top: 4px !important;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-weight: 500;
}

/* Material Container Cards */
.md-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
    border: 1px solid #E7E0EC;
    margin-bottom: 20px;
}

.md-card-title {
    font-size: 18px;
    font-weight: 500;
    color: #1D1B20;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.md-card-title span.icon {
    font-size: 24px !important;
    color: #6750A4;
}

/* Custom Metrics Cards (M3 style) */
.md-metric-container {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
}

.md-metric-card {
    flex: 1;
    background: #F3EDF7;
    border-radius: 12px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    border: 1px solid #E8DEF8;
}

.md-metric-icon-box {
    background: #EADDFF;
    color: #21005D;
    border-radius: 10px;
    padding: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.md-metric-icon-box span {
    font-size: 28px !important;
}

.md-metric-content {
    display: flex;
    flex-direction: column;
}

.md-metric-value {
    font-size: 24px;
    font-weight: 700;
    color: #21005D;
    line-height: 1.1;
}

.md-metric-label {
    font-size: 11px;
    color: #49454F;
    text-transform: uppercase;
    font-weight: 500;
    letter-spacing: 0.5px;
    margin-top: 2px;
}

/* Custom Chips for Status */
.md-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 500;
    margin-top: 8px;
}

.md-chip span.icon {
    font-size: 16px !important;
}

.md-chip-green {
    background-color: #E8F5E9;
    color: #2E7D32;
    border: 1px solid #C8E6C9;
}

.md-chip-yellow {
    background-color: #FFFDE7;
    color: #F57F17;
    border: 1px solid #FFF9C4;
}

.md-chip-red {
    background-color: #FFEBEE;
    color: #C62828;
    border: 1px solid #FFCDD2;
}

.md-chip-darkred {
    background-color: #FFEBEE;
    color: #C62828;
    border: 2px solid #D32F2F;
    animation: pulse 1.8s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); box-shadow: 0 0 8px rgba(211, 47, 47, 0.2); }
    100% { transform: scale(1); }
}

/* MD Info box for AI Explanation */
.md-info-box {
    background: #ECE6F0;
    color: #1D1B20;
    padding: 16px;
    border-radius: 12px;
    border-left: 5px solid #6750A4;
    font-size: 13.5px;
    line-height: 1.5;
    margin-top: 15px;
}

.md-info-box-title {
    font-weight: 700;
    color: #21005D;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.md-info-box-title span {
    font-size: 18px !important;
}

/* Override Streamlit UI Buttons */
div.stButton > button {
    background: #6750A4 !important;
    color: white !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    letter-spacing: 0.5px !important;
    border-radius: 100px !important;
    padding: 12px 24px !important;
    border: none !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

div.stButton > button:hover {
    background: #513B8C !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    transform: translateY(-1px) !important;
}

div.stButton > button:active {
    transform: translateY(1px) !important;
}

/* Style the text and inputs slightly */
label {
    font-weight: 500 !important;
    color: #49454F !important;
    font-size: 13px !important;
}

.stCaption {
    color: #79747E !important;
    text-align: center;
    font-size: 11.5px !important;
    margin-top: 30px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# Encabezado Material Design 3
# -----------------------------

st.markdown("""
<div class="md-header">
    <span class="material-symbols-outlined md-header-icon">smart_toy</span>
    <div class="md-header-title-container">
        <h1 class="md-header-title">Sistema Inteligente de Inventarios</h1>
        <span class="md-header-subtitle">Aprendizaje por Refuerzo • Q-Learning • Bellman</span>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Columnas principales
# -----------------------------

col1, col2 = st.columns([1, 1.4], gap="large")

# =====================================================
# COLUMNA IZQUIERDA: Parámetros
# =====================================================

with col1:
    st.markdown("""
    <div class="md-card">
        <div class="md-card-title">
            <span class="material-symbols-outlined icon">tune</span>
            Parámetros del Entorno
        </div>
    </div>
    """, unsafe_allow_html=True)

    # El contenedor de arriba es puramente visual, colocamos los inputs debajo.
    # Usaremos contenedores estilizados o los controles nativos.
    stock = st.number_input(
        "Stock actual en bodega",
        min_value=0,
        value=30
    )

    dia = st.selectbox(
        "Día de la semana operativa",
        [
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
            "sabado",
            "domingo"
        ]
    )

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    analizar = st.button("🚀 Analizar Inventario")

# =====================================================
# COLUMNA DERECHA: Resultados
# =====================================================

with col2:
    st.markdown("""
    <div class="md-card">
        <div class="md-card-title">
            <span class="material-symbols-outlined icon">analytics</span>
            Recomendación del Agente
        </div>
    </div>
    """, unsafe_allow_html=True)

    if analizar:
        with st.spinner("El agente inteligente está analizando el estado óptimo..."):
            try:
                respuesta = requests.post(
                    "http://127.0.0.1:8000/prediccion",
                    json={
                        "stock_actual": stock,
                        "dia_semana": dia
                    }
                )

                if respuesta.status_code == 200:
                    datos = respuesta.json()

                    unidades = datos["decision_abastecimiento"]["unidades_a_solicitar"]
                    valor_q = float(datos["metadatos"]["valor_q_maximo"])
                    impacto = datos["decision_abastecimiento"]["impacto_esperado"]
                    estrategia = datos["metadatos"]["estrategia_aplicada"]
                    confianza_pct = datos["metadatos"].get("confianza_pct", 0)

                    # Custom metrics display using M3 styling
                    st.markdown(f"""
                    <div class="md-metric-container">
                        <div class="md-metric-card">
                            <div class="md-metric-icon-box">
                                <span class="material-symbols-outlined">inventory_2</span>
                            </div>
                            <div class="md-metric-content">
                                <span class="md-metric-value">{unidades}</span>
                                <span class="md-metric-label">Unidades a Solicitar</span>
                            </div>
                        </div>
                        <div class="md-metric-card">
                            <div class="md-metric-icon-box">
                                <span class="material-symbols-outlined">query_stats</span>
                            </div>
                            <div class="md-metric-content">
                                <span class="md-metric-value">{valor_q:.4f}</span>
                                <span class="md-metric-label">Valor Q Máximo</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("### Nivel de Stock y Diagnóstico")
                    porcentaje = min(stock / 100, 1.0)
                    st.progress(porcentaje)

                    # State calculations and styled chips
                    if stock >= 60:
                        st.markdown("""
                        <div class="md-chip md-chip-green">
                            <span class="material-symbols-outlined icon">check_circle</span>
                            🟢 Stock Alto y Seguro
                        </div>
                        """, unsafe_allow_html=True)
                    elif stock >= 25:
                        st.markdown("""
                        <div class="md-chip md-chip-yellow">
                            <span class="material-symbols-outlined icon">warning</span>
                            🟡 Stock Normal
                        </div>
                        """, unsafe_allow_html=True)
                    elif stock > 0:
                        st.markdown("""
                        <div class="md-chip md-chip-red">
                            <span class="material-symbols-outlined icon">error</span>
                            🔴 Stock Bajo (Crítico)
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="md-chip md-chip-darkred">
                            <span class="material-symbols-outlined icon">emergency_home</span>
                            🚨 Sin Stock (Quiebre)
                        </div>
                        """, unsafe_allow_html=True)

                    # Strategy Info
                    st.markdown(f"""
                    <div style="margin-top: 15px; font-size: 13px; color: #49454F;">
                        <strong>Estrategia aplicada:</strong> {estrategia}
                        {f'| <strong>Confianza:</strong> {confianza_pct}%' if 'Inferencia' in estrategia else ''}
                    </div>
                    """, unsafe_allow_html=True)

                    # AI Impact Explanation card
                    st.markdown(f"""
                    <div class="md-info-box">
                        <div class="md-info-box-title">
                            <span class="material-symbols-outlined">lightbulb</span>
                            Análisis del Agente IA (Bellman)
                        </div>
                        {impacto}
                    </div>
                    """, unsafe_allow_html=True)

                else:
                    st.error("Error: La API devolvió una respuesta inesperada o con código de error.")

            except Exception as e:
                st.error(f"No fue posible conectar con el microservicio API. Asegúrate de iniciar uvicorn primero.\n\nDetalle: {e}")
    else:
        # Default placeholder when no analysis is running
        st.markdown("""
        <div style="text-align: center; color: #79747E; padding: 40px 20px;">
            <span class="material-symbols-outlined" style="font-size: 48px; color: #938F99;">ads_click</span>
            <p style="margin-top: 12px; font-size: 14px;">Ingresa los parámetros a la izquierda y presiona <b>Analizar Inventario</b> para ver el diagnóstico del agente de IA.</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div class="stCaption">
    Sistema de Abastecimiento Inteligente • Arquitectura de Microservicios • FastAPI + Streamlit • Q-Learning (Ecuación de Bellman)
</div>
""", unsafe_allow_html=True)