
# SABIS Quiz Report Builder (Streamlit)

Una app sencilla para arrastrar archivos de **QuizResultsByStudent-QuizDetails** (.xls/.xlsx),
ejecutar tu lógica de procesamiento en Python y descargar `report.tsv` y `all_pending_low.txt`.

## Cómo usar localmente
1. Crea un entorno (opcional) e instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta la app:
   ```bash
   streamlit run app.py
   ```
3. Abre el enlace que te muestra la terminal (por defecto: http://localhost:8501).

## Dónde pegar tu lógica
- Edita `processor.py` y reemplaza la función `process_workbook` por la que ya tienes en Colab.
- Punto clave: en lugar de leer por ruta, usa
  ```python
  pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)
  ```
  para cargar el Excel directamente desde los bytes subidos por el usuario.

## Despliegue rápido (Streamlit Community Cloud)
1. Sube estos archivos a un repo de GitHub.
2. Ve a https://share.streamlit.io, conecta el repo y selecciona `app.py` como entrypoint.
3. Eso es todo: podrás arrastrar archivos desde cualquier navegador.

## Tips
- Puedes subir varios archivos a la vez: la app acumula los resultados en esta sesión.
- Botones de descarga están disponibles tanto por archivo como en el **acumulado**.
