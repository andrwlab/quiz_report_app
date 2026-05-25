import streamlit as st
import pandas as pd

# --- Page config
st.set_page_config(page_title="SABIS Quiz Report Builder", page_icon="🧮", layout="wide")

st.title("🧮 SABIS Quiz Report Builder")
st.caption("Arrastra uno o varios archivos *QuizResultsByStudent-QuizDetails…* (.xls/.xlsx). El procesamiento corre automáticamente.")

# --- Session state
if "combined_report" not in st.session_state:
    st.session_state.combined_report = pd.DataFrame(columns=[
        "quiz_id", "total", "submitted", "avg_total_%", "avg_submitted_%", "pending_names", "low_names"
    ])
if "combined_pending_low" not in st.session_state:
    st.session_state.combined_pending_low = []
if "runs" not in st.session_state:
    st.session_state.runs = 0

# --- Sidebar controls
with st.sidebar:
    st.header("Opciones")
    append_mode = st.toggle(
        "Acumular resultados entre archivos",
        value=True,
        help="Si está activo, los resultados de cada archivo se agregan a un resumen maestro en esta sesión.",
    )
    if st.button("🧹 Limpiar sesión"):
        st.session_state.combined_report = st.session_state.combined_report.iloc[0:0]
        st.session_state.combined_pending_low = []
        st.session_state.runs = 0
        st.rerun()

st.divider()


def render_copy_to_clipboard_block(tsv_text: str, *, title: str, block_id: str, height: int = 220) -> None:
    """Render a client-side copy-to-clipboard block for touch devices."""
    safe_text = tsv_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    st.markdown(f"**{title}**")
    st.components.v1.html(
        f"""
        <div style="display:flex; gap:8px; align-items:center; margin-bottom:8px;">
          <button
            onclick="copyTSV_{block_id}()"
            style="padding:6px 12px; border-radius:6px; border:1px solid #D1D5DB; background:#F3F4F6; cursor:pointer;">
            📋 Copiar al portapapeles
          </button>
          <span id="status_{block_id}" style="font-size:12px; color:#6B7280;"></span>
        </div>
        <textarea
          id="tsv_{block_id}"
          readonly
          style="width:100%; height:{height}px; padding:8px; border:1px solid #D1D5DB; border-radius:6px; font-family:monospace; font-size:12px; white-space:pre;"
        >{safe_text}</textarea>
        <script>
          async function copyTSV_{block_id}() {{
            const el = document.getElementById("tsv_{block_id}");
            const status = document.getElementById("status_{block_id}");
            try {{
              await navigator.clipboard.writeText(el.value);
              status.textContent = "✅ Copiado. Ya puedes pegar en Excel.";
            }} catch (e) {{
              el.focus();
              el.select();
              status.textContent = "⚠️ No se pudo copiar automático. Usa selección manual.";
            }}
          }}
        </script>
        """,
        height=height + 70,
        scrolling=False,
    )


def render_touch_copy_table(df: pd.DataFrame, *, title: str) -> None:
    """Render a touch-friendly HTML table so users can long-press and copy values on tablets."""
    st.markdown(f"**{title}**")
    if df is None or df.empty:
        st.info("No hay datos para copiar.")
        return

    safe_df = df.fillna("").astype(str)
    html_table = safe_df.to_html(index=False, escape=True)

    st.components.v1.html(
        f"""
        <style>
            .copy-wrap {{
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                max-height: 280px;
                overflow: auto;
                -webkit-overflow-scrolling: touch;
                background: white;
            }}
            .copy-wrap table {{
                border-collapse: collapse;
                width: 100%;
                font-size: 14px;
            }}
            .copy-wrap th, .copy-wrap td {{
                border: 1px solid #E5E7EB;
                padding: 8px;
                white-space: nowrap;
                user-select: text;
                -webkit-user-select: text;
                -webkit-touch-callout: default;
            }}
            .copy-wrap th {{
                position: sticky;
                top: 0;
                background: #F9FAFB;
                z-index: 1;
            }}
        </style>
        <div class="copy-wrap">{html_table}</div>
        <p style="margin-top:8px; color:#6B7280; font-size:12px;">
          En tablet/touchscreen: mantén presionada una celda para seleccionar y copiar texto a Excel.
        </p>
        """,
        height=360,
        scrolling=True,
    )


# --- Uploader
uploaded = st.file_uploader(
    "Arrastra aquí tus archivos .xls / .xlsx",
    type=["xls", "xlsx"],
    accept_multiple_files=True,
)

if uploaded:
    import processor  # Tu lógica vive aquí

    for up in uploaded:
        with st.spinner(f"Procesando: {up.name}"):
            file_bytes = up.read()
            try:
                report_df, pending_text = processor.process_workbook(file_bytes)
            except Exception as e:
                st.error(f"Ocurrió un error procesando {up.name}: {e}")
                continue

            with st.expander(f"📄 Resultado de: {up.name}", expanded=False):
                if isinstance(report_df, pd.DataFrame) and not report_df.empty:
                    st.dataframe(report_df, use_container_width=True, height=240)
                    tsv_text = report_df.to_csv(sep="\t", index=False, header=False)
                    block_id = f"file_{st.session_state.runs}_{abs(hash(up.name))}"
                    render_copy_to_clipboard_block(
                        tsv_text,
                        title="📋 Copiar todo para Excel (TSV)",
                        block_id=block_id,
                        height=180,
                    )
                    tsv_bytes = tsv_text.encode("utf-8")
                    st.download_button(
                        "⬇️ Descargar report.tsv",
                        data=tsv_bytes,
                        file_name=f"report_{up.name}.tsv",
                        mime="text/tab-separated-values",
                    )
                else:
                    st.info("No se generó contenido para **report.tsv**")

                if pending_text and pending_text.strip():
                    st.text_area("all_pending_low.txt", pending_text, height=220)
                    st.download_button(
                        "⬇️ Descargar all_pending_low.txt",
                        data=pending_text.encode("utf-8"),
                        file_name=f"all_pending_low_{up.name}.txt",
                        mime="text/plain",
                    )
                else:
                    st.info("No se generó contenido para **all_pending_low.txt**")

            if append_mode:
                if isinstance(report_df, pd.DataFrame) and not report_df.empty:
                    st.session_state.combined_report = pd.concat(
                        [st.session_state.combined_report, report_df],
                        ignore_index=True,
                    )
                if pending_text and pending_text.strip():
                    st.session_state.combined_pending_low.append(pending_text)

            st.session_state.runs += 1

    st.success("Listo ✅")

# --- Bloque de acumulados (si los hay)
if st.session_state.runs > 0:
    st.divider()
    st.subheader("📊 Resumen acumulado de la sesión")

    if not st.session_state.combined_report.empty:
        st.dataframe(st.session_state.combined_report, use_container_width=True, height=260)
        combined_tsv_text = st.session_state.combined_report.to_csv(sep="\t", index=False, header=False)
        render_copy_to_clipboard_block(
            combined_tsv_text,
            title="📋 Copiar acumulado para Excel (TSV)",
            block_id="combined",
            height=220,
        )
        tsv_bytes = combined_tsv_text.encode("utf-8")
        st.download_button(
            "⬇️ Descargar report.tsv (acumulado)",
            tsv_bytes,
            file_name="report.tsv",
            mime="text/tab-separated-values",
        )
    else:
        st.info("Aún no hay filas en el **report.tsv** acumulado.")

    if st.session_state.combined_pending_low:
        all_text = "\n\n".join(st.session_state.combined_pending_low)
        st.text_area("all_pending_low.txt (acumulado)", all_text, height=260)
        st.download_button(
            "⬇️ Descargar all_pending_low.txt (acumulado)",
            data=all_text.encode("utf-8"),
            file_name="all_pending_low.txt",
            mime="text/plain",
        )
    else:
        st.info("Aún no hay contenido en **all_pending_low.txt** acumulado.")

st.divider()
with st.expander("ℹ️ Cómo adaptar tu lógica existente", expanded=False):
    st.markdown("""
    - La app llama a `processor.process_workbook(file_bytes)` para cada archivo subido.
    - Dentro de `processor.py` puedes **pegar tu lógica** del Colab (la que calcula `report.tsv` y `all_pending_low.txt`).
    - No necesitas rutas: usa `pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)`.
    - Regresa dos cosas:
        1) un `pandas.DataFrame` con columnas de salida para el reporte, y
        2) un `str` con el contenido de `all_pending_low.txt`.
    - La app se encarga de previsualizar y ofrecer los botones de descarga (individuales y acumulados).
    """)
