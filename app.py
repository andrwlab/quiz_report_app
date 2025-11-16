
import io
import streamlit as st
import pandas as pd
from datetime import datetime

# --- Page config
st.set_page_config(page_title="SABIS Quiz Report Builder", page_icon="🧮", layout="wide")

st.title("🧮 SABIS Quiz Report Builder")
st.caption("Arrastra uno o varios archivos *QuizResultsByStudent-QuizDetails…* (.xls/.xlsx). El procesamiento corre automáticamente.")

# --- Session state
if "combined_report" not in st.session_state:
    st.session_state.combined_report = pd.DataFrame(columns=[
        "quiz_id","total","submitted","avg_total_%","avg_submitted_%","pending_names","low_names"
    ])
if "combined_pending_low" not in st.session_state:
    st.session_state.combined_pending_low = []
if "runs" not in st.session_state:
    st.session_state.runs = 0

# --- Sidebar controls
with st.sidebar:
    st.header("Opciones")
    append_mode = st.toggle("Acumular resultados entre archivos", value=True,
                            help="Si está activo, los resultados de cada archivo se agregan a un resumen maestro en esta sesión.")
    if st.button("🧹 Limpiar sesión"):
        st.session_state.combined_report = st.session_state.combined_report.iloc[0:0]
        st.session_state.combined_pending_low = []
        st.session_state.runs = 0
        st.experimental_rerun()

st.divider()

# --- Uploader
uploaded = st.file_uploader("Arrastra aquí tus archivos .xls / .xlsx", type=["xls", "xlsx"], accept_multiple_files=True)

if uploaded:
    import processor  # Tu lógica vive aquí

    for up in uploaded:
        with st.spinner(f"Procesando: {up.name}"):
            # Lee bytes y pásalos al procesador (no se necesita path)
            file_bytes = up.read()
            try:
                report_df, pending_text = processor.process_workbook(file_bytes)
            except Exception as e:
                st.error(f"Ocurrió un error procesando {up.name}: {e}")
                continue

            # Previews por archivo
            with st.expander(f"📄 Resultado de: {up.name}", expanded=False):
                if isinstance(report_df, pd.DataFrame) and not report_df.empty:
                    st.dataframe(report_df, use_container_width=True, height=240)
                    tsv_bytes = report_df.to_csv(sep="\t", index=False).encode("utf-8")
                    st.download_button(
                        "⬇️ Descargar report.tsv",
                        data=tsv_bytes,
                        file_name=f"report_{up.name}.tsv",
                        mime="text/tab-separated-values"
                    )
                else:
                    st.info("No se generó contenido para **report.tsv**")

                if pending_text and pending_text.strip():
                    st.text_area("all_pending_low.txt", pending_text, height=220)
                    st.download_button(
                        "⬇️ Descargar all_pending_low.txt",
                        data=pending_text.encode("utf-8"),
                        file_name=f"all_pending_low_{up.name}.txt",
                        mime="text/plain"
                    )
                else:
                    st.info("No se generó contenido para **all_pending_low.txt**")

            # Acumulados
            if append_mode:
                if isinstance(report_df, pd.DataFrame) and not report_df.empty:
                    st.session_state.combined_report = pd.concat(
                        [st.session_state.combined_report, report_df], ignore_index=True
                    )
                if pending_text and pending_text.strip():
                    st.session_state.combined_pending_low.append(pending_text)

            st.session_state.runs += 1

    st.success("Listo ✅")

# --- Bloque de acumulados (si los hay)
if st.session_state.runs > 0:
    st.divider()
    st.subheader("📊 Resumen acumulado de la sesión")

    # Tabla acumulada
    if not st.session_state.combined_report.empty:
        st.dataframe(st.session_state.combined_report, use_container_width=True, height=260)
        tes = st.session_state.combined_report.to_csv(sep="\t", index=False).encode("utf-8")
        st.download_button("⬇️ Descargar report.tsv (acumulado)", tsv_bytes, file_name="report.tsv", mime="text/tab-separated-values")
    else:
        st.info("Aún no hay filas en el **report.tsv** acumulado.")

    # Texto acumulado
    if st.session_state.combined_pending_low:
        all_text = "\n\n".join(st.session_state.combined_pending_low)
        st.text_area("all_pending_low.txt (acumulado)", all_text, height=260)
        st.download_button("⬇️ Descargar all_pending_low.txt (acumulado)",
                           data=all_text.encode("utf-8"),
                           file_name="all_pending_low.txt",
                           mime="text/plain")
    else:
        st.info("Aún no hay contenido en **all_pending_low.txt** acumulado.")

st.divider()
with st.expander("ℹ️ Cómo adaptar tu lógica existente", expanded=False):
    st.markdown("""
    - La app llama a `processor.process_workbook(file_bytes)` para cada archivo subido.
    - Dentro de `processor.py` puedes **pegar tu lógica** del Colab (la que calcula `report.tsv` y `all_pending_low.txt`).
    - No necesitas rutas: usa `pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)`.
    - Regresa dos cosas: 
        1) un `pandas.DataFrame` con las columnas `['quiz_id','total','submitted','avg_total_%','avg_submitted_%','low_or_pending_names']`, y 
        2) un `str` con el contenido de `all_pending_low.txt`.
    - La app se encarga de previsualizar y ofrecer los botones de descarga (individuales y acumulados).
    """)
