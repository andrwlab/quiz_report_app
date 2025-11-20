# processor.py — versión integrada para la web app
# Lee el Excel desde bytes (sin rutas), ejecuta tu lógica y devuelve:
#   1) report_df  (para mostrar/descargar report.tsv)
#   2) pending_text (para mostrar/descargar all_pending_low.txt)

import io
import pandas as pd

# ====== TUS LISTAS MAESTRAS ======
master_students_7A = [
    "Andrea Rodriguez Acevedo","Arantza Navarro Flores","Brandon Chock Kong","Crystal Hou Qiu",
    "Daniel Puga Mora","Diego Pimentel Woodley","Douglas Deweese Alonzo","Dylan Dely Flaautt",
    "Eduardo Gudiño Valdez","Ethan De Leon Raven","Franklin Sanchez Avecilla","Ian Chong Serrano",
    "Iann Arauz","Inna Diaz Agudo","Joyce Wei Zhang","Kaidy Chong Zhu","Kelly Qiu Luo","Kelly Xu Deng",
    "Kisbeth Chong Qiu","Luzarianis Prado Martinez","Melanie Villalaz Olivardia","Mia Atencio Giron",
    "Nicolas Perez Brown","Sebastian Villasmil Carosi","Siwen Zhang","Sofia Guevara","Sofia Zhu Wu",
    "Vicky Zhu Zhang","Vivian Wen Hou","William Qiu Hou","Zhuoying Qiu"
]

master_students_8G = [
    "Alexis Xu Wu","Andy Zhang Qiu","Antonella Jaen Lombardo","Anyoli Melo Cordoba","Christopher Wen Wen",
    "Dhruvin Ahir Ahir","Dominique Kreuzwirth Linares","Ellis He Cai","Heiley Qiu How","Hector Chen Wu",
    "Hilary Hou Qiu","Ian Navarro Garcia","Iria Luo Zhong","Ivery Wong Wang","Johan Ching Bernal",
    "John Li Hou","Jorge Hou Zhang","Jose Rodriguez Vega","Juan De Leon Caceres","Judith He Luo",
    "Kevin Liu Wu","Lady Ruiz Gonzalez","Maria Lourdes Sugasti Ledezma","Mario Zhong Huang",
    "Matias De Leon Caceres","Mateo Montero Cano","Meidy Sem Cheng","Rian Ahir Ahir","Ryan Melendez Smith",
    "Samantha Valero Bracamonte","Sara Morales Aguilera","Sarah Aguilar Espinosa","Sophia Rodriguez Valenzuela",
    "Steven Lai Zhong","Victoria Pérez Garcia","Williams Luo Qiu","Williams Luo Yang","Ximena Ramos Wilches",
    "Yesenia Li Qiu", "Zahid Amor Ladron De Guevara"
]

master_students_9A = [
    "Adrian Fernandez","Allison Chock Kong","Analia Gomez","Angela Li Fang","Andres Lan Lan",
    "Antonio Zhu Zhang","Brian Chen Wen","Carlos Luo Luo","David Li Hou","Dylan Rodriguez Delgado",
    "Dylan Sanjur Navarro","Gabriel Sanchez Serrano","Guohong Xu","Ian Espino Almanza",
    "Isabella Cordero Solano","Ivanna Acosta Aguilar","Jose Bertorelli Fernandez","Jorge He Luo",
    "Juan Bonilla Llanos","Justyn Wei Zhang","Karina Luo Luo","Kenny Qiu Zhu","Kevin Wen Zhang",
    "Kristal Cordoba Gooden","Leah Navarro","Luciana Ruiz Riveros","Paola Teng Arauz","Ray Cheung Luo",
    "Winston Chen Zhu","Yoselin Shen Chen","Zhiye Chen Li"
]

master_students_10A = [
    "Alexandra Aizpurua Culiolis","Angui Zhang Qiu","Anyi Zhang Zhong","Camila Gonzalez Lopez",
    "Danny Tang Zhong","Edwuar Qiu Wu","Gabriel Chen De Leon","Heidi Sem Cheng","Helen Fu Chen",
    "Jason Wen Hou","Jassek Cajar Muñoz","Jeniffer He Wen","Joanny Hou Zhang","Kelly Nie Nie",
    "Lauren Tapia Frias","Lucas Wu Luo","Mariangel Castro Ortega","Marcos Luo Zhong",
    "Miguel Concepcion Morales","Nishtha Ahir","Patricia Fu Chen","Sofia Ferrer Parra",
    "Yazmin Shen Chen","Zuwei Guo"
]

def extraer_nombre(nombre):
    if pd.isna(nombre):
        return ""
    partes = str(nombre).split()

    # Casos especiales
    if str(nombre).strip() == "Dylan Rodriguez Delgado":
        return "Dylan R"
    if str(nombre).strip() == "Dylan Sanjur Navarro":
        return "Dylan S"
    if str(nombre).strip() == "Kelly Qiu Luo":
        return "Kelly Qiu"
    if str(nombre).strip() == "Kelly Xu Deng":
        return "Kelly Xu"
    if str(nombre).strip() == "Sofia Guevara":
        return "Sofia G"
    if str(nombre).strip() == "Sofia Zhu Wu":
        return "Sofia Z"
    if str(nombre).strip() == "Zhiye Chen Li":
        return "Jimmy"
    if str(nombre).strip() == "Guohong Xu":
        return "Victor"

    if partes[0] == "Williams" and len(partes) >= 3:
        iniciales = partes[1][0] + partes[2][0]
        return f"Williams {iniciales}"

    if partes[0] == "William":
        return "William"

    return partes[0]


def _pick_master(sheet_name: str):
    """Selecciona lista maestra según prefijo/código de hoja."""
    if sheet_name.startswith("2526-07") or "MI" in sheet_name:
        return master_students_7A
    if sheet_name.startswith("2526-08") or "MJ" in sheet_name:
        return master_students_8G
    if sheet_name.startswith("2526-09") or "MK" in sheet_name:
        return master_students_9A
    if sheet_name.startswith("2526-00") or "ML" in sheet_name:
        return master_students_10A
    return []


def process_workbook(file_bytes: bytes):
    """
    Lee un archivo Excel desde bytes y devuelve:
      - report_df (DataFrame) con columnas esperadas por la app
      - pending_text (str) con el contenido para all_pending_low.txt
    """
    sheets_noheader = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)

    report_rows = []
    pending_blocks = []

    for sheet_name in sorted(sheets_noheader.keys()):
        current_master = _pick_master(sheet_name)
        df_noheader = sheets_noheader[sheet_name]

        # D16 → "# completed" (índices base 0)
        try:
            num_intentos = int(df_noheader.iloc[15, 3])
        except Exception:
            num_intentos = 0

        # Construir la tabla real desde la fila 17 (índice 16) y usar esa fila como header
        try:
            table = df_noheader.iloc[16:].copy()
            table.columns = table.iloc[0]
            table = table.drop(table.index[0])
            table.columns = table.columns.astype(str).str.strip()
        except Exception:
            table = pd.DataFrame()

        if not table.empty and ("Student Name" in table.columns) and ("Final Score" in table.columns):
            # Final Score a float
            table["Final Score"] = (
                table["Final Score"].astype(str).str.rstrip("%").replace("", "0").astype(float)
            )

            # Promedio
            promedio = table["Final Score"].mean() if not table["Final Score"].empty else 0.0

            # < 70 para el reporte general (nombres “cortos”)
            low_score_general = table[table["Final Score"] < 70].copy()
            low_score_general.loc[:, "Display Name"] = low_score_general["Student Name"].apply(extraer_nombre)
            low_names_general = low_score_general["Display Name"].tolist()

            # Métricas de reporte
            quiz_code = sheet_name
            total_students = len(current_master)
            completed = int(num_intentos)
            completion_pct = (completed / total_students) * 100 if total_students else 0.0

            completion_str = f"{completion_pct:.1f}%"
            avg_score_str = f"{promedio:.1f}%"

            # Pending: en master pero no aparecen en la tabla
            present_students = [
                st for st in table["Student Name"].dropna().unique().tolist()
                if st in current_master
            ]
            missing_students = [st for st in current_master if st not in present_students]
            missing_display = [extraer_nombre(st) for st in missing_students]

            pending_str = ", ".join(missing_display) if missing_display else ""
            low_score_str = ", ".join(low_names_general) if low_names_general else ""

            # === Fila para el DataFrame que consume la app ===
            # Mapear: avg_total_%  <- % completado
            #         avg_submitted_% <- promedio de Final Score
            #         low_or_pending_names <- pending + low (corto)
            

            report_rows.append({
                "quiz_id": quiz_code,
                "total": str(total_students),
                "submitted": str(completed),
                "avg_total_%": completion_str,
                "avg_submitted_%": avg_score_str,
                "pending_names": pending_str,       # <--- SOLO pendientes
                "low_names": low_score_str          # <--- SOLO low scores (<70)
            })

            # === Bloque para all_pending_low.txt (nombres completos y con % cuando aplica) ===
            block_lines = []
            block_lines.append(f"Quiz: {quiz_code}\n")

            # Pending
            block_lines.append("Pending:\n")
            for st in missing_students:
                block_lines.append(f"{st}\n")

            # Low Score (< 15.1%)
            low_score_lt_15 = table[table["Final Score"] < 15.1]["Student Name"].tolist()
            block_lines.append("\nLow Score (< 15.1%):\n")
            for st in low_score_lt_15:
                block_lines.append(f"{st}\n")

            # Low Score (15.1% - 74.9%)
            mid_low_df = table[(table["Final Score"] >= 15.1) & (table["Final Score"] < 75)][["Student Name", "Final Score"]]
            block_lines.append("\nLow Score (15.1% - 74.9%):\n")
            for _, row in mid_low_df.iterrows():
                block_lines.append(f"{row['Student Name']} - {row['Final Score']:.1f}%\n")

            block_lines.append("\n" + "_" * 44 + "\n")
            pending_blocks.append("".join(block_lines))

        else:
            # Si una hoja no tiene columnas necesarias, aún devolvemos algo coherente
            report_rows.append({
                "quiz_id": sheet_name,
                "total": "0",
                "submitted": "0",
                "avg_total_%": "0.0%",
                "avg_submitted_%": "0.0%",
                "pending_names": "",   
                "low_names": ""        
            })
            pending_blocks.append(
                f"Quiz: {sheet_name}\nPending:\n\nLow Score (< 15.1%):\n\nLow Score (15.1% - 74.9%):\n\n{'_'*44}\n"
            )

        # --- construir DataFrame y ordenar columnas ---
    report_df = pd.DataFrame(report_rows)

    # garantizar que existan las columnas nuevas, aunque alguna rama no las haya puesto
    for col in ["pending_names", "low_names"]:
        if col not in report_df.columns:
            report_df[col] = ""

    cols = ["quiz_id","total","submitted","avg_total_%","avg_submitted_%","pending_names","low_names"]
    report_df = report_df.reindex(columns=cols)

    pending_text = "\n\n".join(pending_blocks)
    return report_df, pending_text

