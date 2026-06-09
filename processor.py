# processor.py — versión integrada para la web app
# Lee el Excel desde bytes (sin rutas), ejecuta tu lógica y devuelve:
#   1) report_df  (para mostrar/descargar report.tsv)
#   2) pending_text (para mostrar/descargar all_pending_low.txt)

import io
import pandas as pd

# ====== TUS LISTAS MAESTRAS ======

master_students_2A = [
    "Ayaan Ahir","Jean Paolo Atencio Mejias","Sophie Marie Bernal Ruiz","Idelfonso Bracho","Gia Broce",
    "Maria Valentina Cardenas","Alanna Gibell Castillo Jean-Louis","Gian Felipe Chapman Rodríguez","Rosmira Chavez",
    "Axl Chirinos","Daniel Espinoza Rueda","Arianna Ferrer","Isabella Flaautt","Dana Gomez","Kemuel Guardia",
    "Sofía He Liu","Olivia Law Shiu","Sara Luo","Ana Victoria Marquez Onodera","Luis Mendoza","Louis Rubin",
    "Alexander Solis Salomon","Lakdar Terreros Acuña","Eren Devin Yau Su","Daniela Zhang Fan","Erick Zhong Hou"
]

master_students_2B = [
    "Yaksh Ahir","Bayazid Amor","Brianna Arauz","Angel Chacon","Chloe Cheng Cham","Dereck David Chu Zhong",
    "Alida Duarte Castro","Hilary Feng Zhong","Keyden Gonzalez","Axl Lin","Tiffany Liu","Javier Zaid Ortiz",
    "Emily Osorio Gonzalez","Isaac Pinillo","Felicia Qiu Huang","Luca Rafael Romero Puig","Alana Solis Salomon",
    "Jeremy Thoubourne","Marcelo Vergara","Dereck Vigil Aguilar","Myka Weets","Sofia Wei Zhang",
    "Sebástian Wong Cheung","Eiji Yoshioka","Chloe Zhang Chung","Alberto Zhang Fan","Javier Zheng"
]

master_students_3A = [
    "Humberto Amores","Victoria Campos","Kevin Joel Chen Liu","Daniel Chen Wong","Guillermo Chen",
    "Jay Jackson Cheung","Hamet Perez Christie","Tania Isabel He Chen","Carlos Hou Zhang Xu Xuan",
    "Daniel Lambis Burgos","Angeline Alejandra Lizondro Bello","Jennifer Ainhoa Lopez Silva","Jennyfer Luo Luo",
    "Ana Sofia Luo Zhang","Tom Luo","Paulina Moreno","Eugene Abdel Pinto Navarro","Mateo Ricord",
    "Diago Rodríguez Delgado","Axel Javier Sinisterra Quintero","Aiden Wen Luo","Terry Wong","Kaylie Wu Liu",
    "Kenji Yoshioka","Kevin Zhang Luo","Angela Zhang Zhong","Evanys Zheng"
]

master_students_3B = [
    "Vihanna Tushar Ahir Ahir","Mia Alvarado","Andreh Arana Cano","Noah Nelson Ardines Ortega","David Atencio",
    "Jasbir Batista","Kerem Jearim Campo De Gracia","Daniel Cepeda Shiu","Thiago Ching",
    "Daniela Alejandra Espinoza Rueda","Alejandro Gael Garza Fu","Mia Victoria Gonzalez Zurita",
    "Christian Guerra Lezcano","Lucia Gutierrez Monroy","Eythan Hernandez Arrocha","John Local Solís",
    "Jennifer Ivonne Loo Yau","Amelie Lucia Luo Lo","Alejandro Marin","Farah Ponton","Arturo Velarde Herrera",
    "Samantha Velasquez Cordoba","Christopher Visuetty Singh","Azaid Antonio Wang"
]

master_students_4A = [
    "Vishva Ahir Ahir","Alessandro Benitez","Pandora Betancourt","Ilhan Ernesto Calvo González","Zhen (Joe) Chen",
    "Jose Cheng Chong","Aimee Ching","Kurt Chong","Amelia Córdoba Montezuma","Matthew Andrés De León Raven",
    "Sadith Domínguez","Monica Feng Zhong","Emmanuel Gao","Miah Valentina Gomez","Lyanne Christine Guo Yau",
    "Emily Luo Luo","Valeria Isabella Marulanda","Hellen Montenegro","Damon Ng","Priscila Olivardia Valdes",
    "Willy Bryant Qiu Jiang","Alejandro Fabian Sanchez Rodriguez","Cecilia Tang","Victoria Teran","Mía Wong Cheung"
]

master_students_4B = [
    "Noelia Raquel Ardines Ortega","Valentina Benites","Geovanna Castillero Castro","Ricardo Isaac Chapman Rodríguez",
    "Juan David Chavez Prado","Alex Cheung","Athan Chichaco","Luna Ching","Kenneth Chong","Iris Chung Li",
    "Sofia Alejandra Cortez Del Cid","Leonor Domínguez","Daniel Gibbs","Jade He","Analia Herrera",
    "Vivian Stephanie Ho Zeng","Alessa Braja Jaén","Eduardo Jiménez Manoleskos","Melody Liu Wu",
    "Ricardo Lin Luo Qiu Luo","Daryelis Rodriguez","Mia Valeria Romero Puig","Dubraska Sarmiento Suárez",
    "Fabian Torres Reyna","Kamila Nazareth Vergara","Sofía Cindy Zhang Fan"
]

master_students_5A = [
    "Nahikary Amor","Samuel Roberto Ayala Macias","Paul Andrés Castillero Delgado","Thiago Castro",
    "Emily Catherine Chen He","Kenneth Fu Chen","Francisco Gurdián","Nicole He Gan","Jimmy Hummer He","Kimi He",
    "Gian Luca Laniado Vega","Alicia Luo Luo","Valeria Montenegro Soto","Valentina Sofía Muñoz Díaz",
    "Felipe Olivardia","Emma Oro","Hannah Peralta","Valentina Marie Rivera Celis","Andres Rodriguez","Hazel Rodriguez",
    "Sebastian Ruiz","Lyan Alexander Sánchez Del Río","Isabella Nicole Schloss Herrera","Roberto Tan",
    "Sofia Visuetty Singh","Eleine Michelle Yau Su","Lucas Young Obando","Daniel Zhang Fan","Steven Zhang Luo",
    "William Antonio Zhong Huang"
]

master_students_6A = [
    "Akari Carrera Barber","Angeline Victoria Cepeda Shiu","Valeria Sophia Chen De Leon","Hiram Antony Chen He",
    "Edwin Chen","Gabriela Marie Guerra Lezcano","Daisy Jiang Wen","Maribel Pei Lin Lai Zhong","Jimmie Liu Wu",
    "Jia Ying Luo","Allison Nicole Plicet De Gracia","Ashley Qiu Jiang","Camila Qiu","Lia Roxette Robinson Arias",
    "Adriam Jose Rodriguez Luna","Valentina Isabella Velarde Herrera","Evelyn Yang","Juke He"
]

master_students_6B = [
    "Henrique Arenas","Daniel Jesus De Leon Caceres","Alexia Isabel Diaz Herrera","Hector Fu Chen",
    "Josahir Darshan Garcia Cubilla","Jaime Javier Gibbs Guerra","Andrew David Guo Yau",
    "Alessandra Daniela Lambis Burgos","Khloe Isabelle Lau Rodriguez","Carolina Hiriam Luo Luo","Paola Luo Qiu",
    "Kaleeth Montalvo","Maria Jose Pardo Caceres","Penelope Perez Arauz","Jose Felix Pimentel Woodley",
    "Angelie Sophia Wu Liu","Elizabeth Xu","Lucia Zhang Zhong"
]

master_students_7A = [
    "Andrea Rodriguez Acevedo","Arantza Navarro Flores","Brandon Chock Kong","Crystal Hou Qiu",
    "Daniel Puga Mora","Diego Pimentel Woodley","Douglas Deweese Alonzo","Dylan Dely Flaautt",
    "Eduardo Gudiño Valdez","Ethan De Leon Raven","Franklin Sanchez Avecilla","Ian Chong Serrano",
    "Iann Arauz","Inna Diaz Agudo","Joyce Wei Zhang","Kaidy Chong Zhu","Kelly Qiu Luo","Kelly Xu Deng","Kevin Luo Zhang",
    "Kisbeth Chong Qiu","Luzarianis Prado Martinez","Melanie Villalaz Olivardia","Mia Atencio Giron",
    "Nicolas Perez Brown","Sebastian Villasmil Carosi","Siwen Zhang","Sofia Guevara","Sofia Zhu Wu",
    "Vicky Zhu Zhang","Vivian Wen Hou","William Qiu Hou","Zhuoying Qiu","Junke He"
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
    "Isabella Cordero Solano","Jose Bertorelli Fernandez","Jorge He Luo",
    "Juan Bonilla Llanos","Justyn Wei Zhang","Karina Luo Luo","Kenny Qiu Zhu","Kevin Wen Zhang",
    "Kristal Cordoba Gooden","Leah Navarro","Luciana Ruiz Riveros","Paola Teng Arauz","Ray Cheung Luo",
    "Winston Chen Zhu","Yoselin Shen Chen","Zhiye Chen Li"
]

master_students_10A = [
    "Angui Zhang Qiu","Anyi Zhang Zhong","Camila Gonzalez Lopez",
    "Danny Tang Zhong","Edwuar Qiu Wu","Gabriel Chen De Leon","Heidi Sem Cheng","Helen Fu Chen",
    "Jason Wen Hou","Jassek Cajar Muñoz","Jeniffer He Wen","Joanny Hou Zhang","Kelly Nie Nie",
    "Lauren Tapia Frias","Lucas Wu Luo","Mariangel Castro Ortega","Marcos Luo Zhong",
    "Miguel Concepcion Morales","Nishtha Ahir","Patricia Fu Chen","Sofia Ferrer Parra",
    "Yazmin Shen Chen","Zuwei Guo"
]

master_students_11A = [
    "Wilson Chen Zhu","Rocco Lokee Solis","James De Gracia Vega",
    "Lyannie Chen Liu","Mavielis Castillero Delgado","Jackson Zhu Wu",
    "Ashly Li Hou","Joel Perez Botello","Wilken Wong Wang",
    "Michell Qiu Luo","Rafael Romero Burgos","Anny Deng Liu",
    "Sofia Liang Wu"
]

MASTER_GROUPS = {
    "2A": master_students_2A,
    "2B": master_students_2B,
    "3A": master_students_3A,
    "3B": master_students_3B,
    "4A": master_students_4A,
    "4B": master_students_4B,
    "5A": master_students_5A,
    "6A": master_students_6A,
    "6B": master_students_6B,
    "7A": master_students_7A,
    "8G": master_students_8G,
    "9A": master_students_9A,
    "10A": master_students_10A,
    "11A": master_students_11A,
}

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
        return "Kelly Q"
    if str(nombre).strip() == "Kelly Xu Deng":
        return "Kelly X"
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


def _pick_master_by_sheet_name(sheet_name: str):
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


def _normalize_name(name: str) -> str:
    return " ".join(str(name).split()).casefold()


def _build_name_keys(name: str):
    """
    Genera llaves de comparación para un nombre:
    - nombre completo normalizado
    - nombre corto (extraer_nombre) normalizado
    """
    if pd.isna(name) or not str(name).strip():
        return set()

    full_key = _normalize_name(name)
    short_key = _normalize_name(extraer_nombre(name))
    return {full_key, short_key}


def _find_present_master_students(master_list, student_names):
    """
    Empareja alumnos presentes en la tabla con la lista maestra, tolerando:
    - nombre completo vs nombre corto (ej. "Angeline" vs nombre completo)
    - variaciones de espacios/mayúsculas.
    """
    observed_keys = set()
    for student in student_names:
        observed_keys.update(_build_name_keys(student))

    present_master = []
    for master_student in master_list:
        if _build_name_keys(master_student) & observed_keys:
            present_master.append(master_student)
    return present_master


def _infer_master_from_students(student_names):
    """
    Si el nombre de la hoja no coincide con los patrones conocidos,
    infiere el grupo comparando los nombres del Excel contra las listas maestras.
    """
    observed_keys = set()
    for student in student_names:
        observed_keys.update(_build_name_keys(student))

    if not observed_keys:
        return []

    best_group = None
    best_overlap = 0
    best_ratio = 0.0

    for group_name, master_list in MASTER_GROUPS.items():
        normalized_master = set()
        for master_student in master_list:
            normalized_master.update(_build_name_keys(master_student))
        overlap = len(observed_keys & normalized_master)
        ratio = overlap / len(normalized_master) if normalized_master else 0.0

        if overlap > best_overlap or (overlap == best_overlap and ratio > best_ratio):
            best_group = group_name
            best_overlap = overlap
            best_ratio = ratio

    # Umbral conservador para evitar asignaciones por coincidencia accidental.
    if best_group and best_overlap >= 3:
        return MASTER_GROUPS[best_group]

    return []


def _sheet_sort_key(sheet_name: str):
    """Ordena hojas por grado y deja 10A al final."""
    if sheet_name.startswith("2526-07") or "MI" in sheet_name:
        return (0, sheet_name)
    if sheet_name.startswith("2526-08") or "MJ" in sheet_name:
        return (1, sheet_name)
    if sheet_name.startswith("2526-09") or "MK" in sheet_name:
        return (2, sheet_name)
    if sheet_name.startswith("2526-00") or "ML" in sheet_name:
        return (4, sheet_name)
    return (3, sheet_name)


def process_workbook(file_bytes: bytes):
    """
    Lee un archivo Excel desde bytes y devuelve:
      - report_df (DataFrame) con columnas esperadas por la app
      - pending_text (str) con el contenido para all_pending_low.txt
    """
    sheets_noheader = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)

    report_rows = []
    pending_blocks = []

    for sheet_name in sorted(sheets_noheader.keys(), key=_sheet_sort_key):
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

        if not table.empty and "Student Name" in table.columns:
            student_names = table["Student Name"].dropna().tolist()
        else:
            student_names = []

        # 1) Intentar por nombre de hoja conocido.
        # 2) Si no coincide, inferir por comparación de nombres de estudiantes.
        current_master = _pick_master_by_sheet_name(sheet_name)
        if not current_master:
            current_master = _infer_master_from_students(student_names)

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
            present_students = _find_present_master_students(
                current_master,
                table["Student Name"].dropna().unique().tolist()
            )
            missing_students = [st for st in current_master if st not in set(present_students)]
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
            block_lines = [f"Quiz: {sheet_name}\n"]
            # Pending
            block_lines.append("\nPending:\n")
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
                f"Quiz: {sheet_name}\n\nPending:\n\nLow Score (< 15.1%):\n\nLow Score (15.1% - 74.9%):\n\n{'_'*44}\n"
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
