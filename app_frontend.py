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
# CSS Personalizado
# -----------------------------

st.markdown("""
<style>

.main{
    background:linear-gradient(135deg,#eef4ff,#f7fbff);
}

.block-container{
    padding-top:2rem;
}

.titulo{
    text-align:center;
    color:#0f172a;
    font-size:40px;
    font-weight:700;
}

.subtitulo{
    text-align:center;
    color:#64748b;
    margin-bottom:35px;
}

.card{

    background:white;
    border-radius:18px;
    padding:20px;
    box-shadow:0 10px 25px rgba(0,0,0,.08);

}

.estado{
    font-size:18px;
    font-weight:bold;
    margin-top:20px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# Encabezado
# -----------------------------

st.markdown(
    "<div class='titulo'>🤖 Sistema Inteligente de Inventarios</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitulo'>Aprendizaje por Refuerzo • Q-Learning • Bellman</div>",
    unsafe_allow_html=True
)

# -----------------------------
# Columnas
# -----------------------------

col1,col2=st.columns([1,1.4])

# =====================================================
# COLUMNA IZQUIERDA
# =====================================================

with col1:

    st.subheader("📥 Parámetros")

    stock=st.number_input(
        "Stock actual",
        min_value=0,
        value=30
    )

    dia=st.selectbox(

        "Día de la semana",

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

    analizar=st.button(
        "🚀 Analizar Inventario",
        use_container_width=True
    )

# =====================================================
# COLUMNA DERECHA
# =====================================================

with col2:

    st.subheader("📊 Resultados")

    if analizar:

        with st.spinner("Analizando con el agente inteligente..."):

            try:

                respuesta=requests.post(

                    "http://127.0.0.1:8000/prediccion",

                    json={

                        "stock_actual":stock,
                        "dia_semana":dia

                    }

                )

                if respuesta.status_code==200:

                    datos=respuesta.json()

                    unidades=datos["decision_abastecimiento"]["unidades_a_solicitar"]

                    valor_q=float(
                        datos["metadatos"]["valor_q_maximo"]
                    )

                    impacto=datos["decision_abastecimiento"]["impacto_esperado"]

                    c1,c2=st.columns(2)

                    with c1:

                        st.metric(

                            "📦 Unidades recomendadas",

                            unidades

                        )

                    with c2:

                        st.metric(

                            "📈 Valor Q",

                            f"{valor_q:.4f}"

                        )

                    st.divider()

                    porcentaje=min(stock/100,1.0)

                    st.write("### Nivel de stock")

                    st.progress(porcentaje)

                    if stock>=60:

                        st.success("🟢 Stock alto")

                    elif stock>=25:

                        st.warning("🟡 Stock normal")

                    elif stock>0:

                        st.error("🔴 Stock bajo")

                    else:

                        st.error("🚨 Sin stock")

                    st.divider()

                    st.info(impacto)

                else:

                    st.error("La API devolvió un error.")

            except Exception as e:

                st.error(f"No fue posible conectar con la API.\n\n{e}")

st.divider()

st.caption(
    "Sistema desarrollado con FastAPI + Streamlit + Q-Learning + Bellman"
)