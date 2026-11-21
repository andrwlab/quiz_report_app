# SABIS Quiz Status

Primera versión Streamlit con consulta pública por Student Number, consulta protegida para profesores y administración en procesos separados. No se ha desplegado. No hay datos publicados incluidos en el repositorio.

## Ejecutar localmente

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

En terminales separadas, configurar contraseñas propias mediante variables de entorno (sin guardarlas en Git) y ejecutar:

```sh
streamlit run teacher.py --server.port 8502
streamlit run admin.py --server.port 8503
```

`SABIS_TEACHER_PASSWORD` y `SABIS_ADMIN_PASSWORD` protegen cada entrada. Sin estas variables el acceso se cierra. Son contraseñas compartidas para esta primera versión; no equivalen a cuentas individuales. Para uso institucional se recomienda autenticar con el proveedor de identidad institucional. No existe selector público que permita acceder a un grupo. No colocar los archivos en una carpeta `pages/`.

`SABIS_DATA_DIR` permite elegir el directorio privado persistente compartido por los tres procesos; por defecto `private_data/` relativo al directorio de ejecución. Ejecutar los procesos desde el mismo directorio o usar una ruta absoluta. El servidor debe poder escribir allí. El almacenamiento local implementa publicación atómica, con la última escritura exitosa como versión vigente. Usar un volumen persistente y copias de seguridad para conservar datos entre reinicios; un filesystem efímero no es almacenamiento de producción. Los snapshots contienen datos personales y no deben exponerse como archivos estáticos.

## Cargar y publicar

En administración, cargar una lista oficial y un Excel de quizzes. Se valida antes de habilitar “Publish validated version”. Se reemplaza la publicación completa; no se mezclan actualizaciones parciales. Si la validación o escritura falla se conserva la versión anterior y su fecha. La lectura del Excel se cachea en servidor por hasta diez minutos, con dos entradas como máximo.

Lista oficial admitida:

- CSV UTF-8 con columnas `Student Number,Student Name,Group`; números tratados como texto para preservar ceros iniciales.
- Excel con el formato de `AY2627-HS Class Lists`: grupos en primera fila, bloques horizontales encabezados `ID#`, `Student Name` en segunda fila, datos desde tercera fila. No se usa la columna de género.

La lista aportada fue inspeccionada sin copiarla al repositorio: contiene 157 estudiantes, con los dos IDs de G10 ya completados en Google Sheets (el Excel de origen sigue sin esos números). El conteo inicial incluía 21 filas de totales/notas; ahora se excluyen por sus etiquetas exactas y únicamente si no tienen ID. Por autorización del usuario, administración permite publicar los estudiantes con identidad completa, advierte si un archivo de origen aún contiene IDs pendientes y excluye esos quizzes hasta completar sus números. No se inventan IDs. Los nombres deben coincidir exactamente, ignorando mayúsculas y espacios redundantes; no hay coincidencia aproximada. Los grupos se conservan como aparecen en la lista, por ejemplo `G7A`.

### Formatos de quizzes

1. **Pestañas semanales** `Week 12`, `Week 13`, etc.: cada pestaña debe tener encabezados `Student Name`, `Group`, `Subject`, `Quiz Code`, `Status`. `Student Number` es opcional y se contrasta si está presente. Estados exactos: `Pending`, `Low Score`, `Completed`. La semana se toma del nombre de la pestaña. Se publican solo Pending y Low Score. Este formato requiere estados explícitos; no se infieren ausencias de filas omitidas.
2. **Exportación histórica SABIS**, una hoja por quiz con encabezados `Student Name`, `Final Score` en fila 17: agregar una hoja `Quiz Metadata` con columnas `Sheet`, `Quiz Code`, `Subject`, `Week`, `Group`. Una fila por hoja detalla la materia, semana y grupo sin adivinarlos a partir del código. La semana debe ser `Week N`. El código se conserva literalmente. Se infieren pendientes a partir de los ausentes en la lista oficial de ese grupo; Low Score es menor que 75, coherente con el TXT histórico. Una hoja representa un grupo; para hojas combinadas se necesita adaptar el importador con evidencia del Excel de origen.

Se rechazan hojas inesperadas, metadatos ausentes, identidades desconocidas, números incompatibles, duplicados y notas fuera de 0–100. Todavía falta contrastar el importador con un Excel semanal real de quizzes; el archivo recibido es la lista oficial, no contiene estados ni quizzes.

## Reportes y presentación

`app.py` solo permite buscar un número exacto. `teacher.py` requiere contraseña, grupo y permite buscar nombre o número; lista alfabéticamente los estudiantes con resultados. Ambos aplican filtros de materia y estado. Las materias se pliegan individualmente y la numeración reinicia por materia y estado. `presentation.py` centraliza el fucsia pendiente en `PENDING_COLOR` y los colores de materias.

Los resultados usan HTML nativo y el desplazamiento normal de la página. `mobile_actions.py` monta los botones ↑ y + en la página mediante Components v2, con márgenes para las zonas seguras del teléfono. Ambos aparecen también antes de buscar; el menú explica que hace falta consultar un estudiante para compartir o descargar su reporte. Compartir/copiar depende de permisos del navegador y contexto seguro. El campo de búsqueda vuelve transparente tanto el input como sus contenedores y neutraliza el estilo de autofill de Safari.

La página configura `theme-color`, `color-scheme`, fondo oscuro y `viewport-fit=cover`. Se aplica también al documento contenedor si es accesible. Las barras nativas de Safari, los controles del sistema y contenedores de otro origen conservan su propia política de color; no se puede garantizar su apariencia desde una página web. Estas interacciones y el tinte de Safari todavía requieren verificación en un iPhone real.

`reportlab` se agrega para generar PDF con texto seleccionable, salto de línea y paginación en páginas de 360 × 640 puntos, legibles en teléfonos; no usa capturas. Los reportes individuales contienen los resultados de los filtros activos y la hora de la publicación en `America/Panama`.

La opción **Legacy report builder** de administración conserva el procesador original `processor.py`, las descargas por archivo y acumuladas `report.tsv` y `all_pending_low.txt`, y las herramientas de copia. El antiguo cálculo TSV usa <70; el TXT usa <75. Estos umbrales históricos no se modificaron. Se evita volver a acumular el mismo archivo en cada rerun.

## Google Sheets: fuente activa

La integración está implementada en `sheets_storage.py`. `settings.json` selecciona Google Sheets. El ID de la hoja se configura únicamente en `settings.local.json` (ignorado por Git), en `SABIS_SPREADSHEET_ID` o en Streamlit Secrets. `SABIS_STORAGE=local` permite volver al modo local; `SABIS_SPREADSHEET_ID` permite cambiar la hoja sin editar código.

### Activación única

1. Crear o seleccionar un proyecto de Google Cloud y habilitar **Google Sheets API**.
2. En **IAM y administración → Cuentas de servicio**, crear una cuenta para la app. No necesita roles de proyecto para leer la hoja compartida. En esa cuenta, **Claves → Agregar clave → Crear clave nueva → JSON**. Guardar el archivo fuera del repositorio.
3. Compartir la hoja privada con el correo `client_email` de esa cuenta como **Lector**. No habilitar acceso público.
4. Configurar la ruta y ejecutar desde el mismo terminal:

```sh
cd /Users/andrewhall/Dev/quiz_report_app
source .venv/bin/activate
python -m pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS="/ruta/real/al/archivo.json"
python check_sheets.py
python -m streamlit run app.py
```

La ruta del ejemplo debe sustituirse por la ruta real. No pegar claves en el chat ni guardarlas en Git. La variable debe configurarse también en el servidor si se aloja la app. En esta computadora se guardó solo la ruta de la clave en `settings.local.json`, ignorado por Git; no hace falta exportar la variable en cada terminal. `GOOGLE_APPLICATION_CREDENTIALS` tiene prioridad sobre esa ruta. La clave permanece fuera del repositorio. Se admiten Application Default Credentials de Google; no se reutiliza la conexión de Google de ChatGPT como credencial de Streamlit.

Guías oficiales: https://docs.cloud.google.com/iam/docs/keys-create-delete y https://developers.google.com/workspace/sheets/api/quickstart/python (habilitar la API; el método de autenticación aquí es cuenta de servicio).

### Actualizar desde ChatGPT

Editar **Students** y **Quizzes** en la hoja conectada. Los encabezados deben conservarse. La app hace una lectura conjunta privada, valida todas las identidades, códigos, estados y semanas y adopta la nueva versión solo si pasa la validación completa. Las semanas pueden ser `12` o `Week 12`; en pantalla y PDF se muestran como `Week 12`. Los códigos no se reinterpretan. Los cambios de una carga deben escribirse en un único batch atómico de Sheets para evitar que una carga parcial pero válida se adopte antes de terminar.

La app consulta como máximo una vez por minuto, cuando se vuelve a ejecutar la interfaz (por ejemplo al buscar, cambiar un filtro o recargar). No hace polling automático de una pantalla inactiva. La fecha muestra la hora de la primera importación exitosa de cada versión a la app, en `America/Panama`; no cambia si los datos son idénticos. `Publication` es una pestaña informativa; no controla el acceso ni es el registro de sincronización. El estado efectivo y la fecha se guardan en el snapshot privado de la app.

Los snapshots se guardan en `SABIS_DATA_DIR/google_sheets/<spreadsheet-id>/`. Si falla Google o una validación, se conserva la última versión exitosa y se muestra un aviso. Sin ninguna versión válida ni credenciales, no se muestran datos. Es necesario conservar ese directorio en un volumen persistente. El alcance OAuth es solo lectura; la app no cambia el Google Sheets. La administración permite comprobar la conexión; la carga histórica sigue disponible en **Legacy report builder**. La publicación por Excel queda disponible al seleccionar `SABIS_STORAGE=local`.

Se verificó la fuente actual desde el conector de ChatGPT: **157 estudiantes con número y 1.159 registros de quizzes**. Esta validación no demuestra acceso de Streamlit: falta crear las credenciales, compartir la hoja y ejecutar `python check_sheets.py`. No se ha desplegado nada ni se ha creado una publicación local de los datos reales.

## Archivos y verificación

`data_pipeline.py`: lectura y validación. `storage.py`: snapshots. `storage_config.py` y `sheets_storage.py`: selección y lectura privada de Google Sheets. `check_sheets.py`: diagnóstico sin mostrar identidades. `auth.py`: acceso. `public_view.py` y `presentation.py`: búsqueda y diseño. `reports.py`: texto/PDF. `admin.py`, `teacher.py`, `app.py`: entradas. `legacy_builder.py`: interfaz anterior protegida. `processor.py`: lógica histórica sin cambios.

```sh
python -m unittest discover -s tests -v
```

Las pruebas usan solo datos ficticios y cubren importación, identidades, errores, almacenamiento atómico, PDF, consulta pública y cierre del acceso sin secretos. La UI se verifica con Streamlit AppTest; no sustituye la revisión visual e interacción de móvil.

## Streamlit Community Cloud

Configurar el despliegue con repositorio `andrwlab/quiz_report_app`, rama `main`, archivo `app.py` y Python 3.11 (la versión usada en las pruebas). En **App settings → Secrets** pegar las claves de nivel superior `SABIS_STORAGE = "google_sheets"` y `SABIS_SPREADSHEET_ID` (con el ID real de la hoja), más la sección `[gcp_service_account]` con las propiedades del JSON de la cuenta de servicio. La app carga esas credenciales en memoria; no requiere la ruta local del Mac. La clave nunca se sube a GitHub. La cuenta ya tiene acceso de Lector a la hoja.

En esta computadora se preparó `.streamlit/secrets.toml` para copiar a ese panel. Está excluido de Git y contiene información privada. No compartir su contenido por chat. La hoja de Google es persistente; el snapshot local de Community Cloud es solo una copia temporal que puede perderse al reiniciar y se reconstruye desde la hoja si la conexión funciona.

La app pública se despliega con `app.py`. `admin.py` y `teacher.py` solo se activan si se crean despliegues separados con contraseñas configuradas; no se exponen mediante páginas públicas.
