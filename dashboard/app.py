import streamlit as st
import requests
import pandas as pd
import os

# Config del API local
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "supersecret_dba_key")

st.set_page_config(page_title="DBA-Sentinel Dashboard", page_icon="🛡️", layout="wide")
st.title("🛡️ DBA-Sentinel Analytics")

st.markdown("Plataforma autonóma de análisis de Seguridad y Rendimiento multi-motor.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Auditoría Bajo Demanda")
    engine_choice = st.selectbox("Motor Objetivo", ["postgres", "mysql"])
    if st.button("🚀 Lanzar Auditoría Ahora"):
        with st.spinner(f"Analizando {engine_choice} (Llamando LLMs y BDs)..."):
            headers = {"X-API-Key": API_KEY, "engine-type": engine_choice}
            try:
                response = requests.post(f"{API_URL}/api/v1/audit", headers=headers)
                if response.status_code == 200:
                    findings = response.json()
                    st.success(f"Completado: {len(findings)} hallazgos.")
                    
                    df = pd.DataFrame(findings)
                    if not df.empty:
                        st.dataframe(df, use_container_width=True)
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Error de conexión: {str(e)}")

with col2:
    st.subheader("Visualización Rápida")
    st.info("Para gráficos temporales conecte el Dashboard a la DB SQLite generada por FastAPI.")
    # Muestra un botón visual para descargar el último reporte generado por API
    st.markdown(f"[Descargar Último Reporte Oficial PDF]({API_URL}/api/v1/audit/report) (Necesario Plugin REST)")
