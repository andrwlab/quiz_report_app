# processor.py — versión integrada para la web app
# Lee el Excel desde bytes (sin rutas), ejecuta tu lógica y devuelve:
#   1) report_df  (para mostrar/descargar report.tsv)
#   2) pending_text (para mostrar/descargar all_pending_low.txt)

import io
import unicodedata
import pandas as pd

# ====== LISTAS MAESTRAS ======

master_students_2A = [
    "Ethan Blake", "Mishva Ahir", "Liz Victoria Alonso", "Avyana Betancourt", "Jimena Crespo",
    "Diego Espinoza", "Sophia Gaspard", "Ziad Gaviria", "Alexa Jiang", "Lucas Lam", "Lia Laniado",
    "Edwin Lin", "Dominic Mcgee", "Caleb Ng", "Luna Nuñez", "Ilhem Ortiz", "Isis Rivera",
    "Nohellys Rodriguez", "Mia Sarmiento", "Emma Valdes", "Lucas Watler", "Danny Wen", "Dylan Zou"
]

master_students_2B = [
    "Alessandra Calvo", "Ian Cerrud", "Tiffany Chong", "Alejandro Contreras", "Ian Gonzalez",
    "Mei Gonzalez", "Analia Jimenez", "Nicolas Lasso", "Nicolas Latorraca", "Ical Nuñez",
    "Eliannah Peralta", "Amelia Quezada", "Gael Quintero", "Liam Rodriguez", "Isabella Sanchez",
    "Sebastian Sarmiento", "Ezra Schloss", "Kamila Sosa", "Scotty Villasanta", "Abby Wen",
    "Jennifer Zheng", "Arthur Zhong"
]

master_students_3A = [
    "Yaksh Ahir", "Idelfonso Bracho", "Gia Broce", "Maria Valentina Cardenas",
    "Alanna Gibell Castillo Jean-Louis", "Alida Duarte Castro", "Hilary Feng Zhong", "Danna Gomez",
    "Sofía He Liu", "Olivia Law Shiu", "Sara Luo", "Ana Victoria Marquez Onodera", "Luis Mendoza",
    "Luca Rafael Romero Puig", "Alexander Solis Salomon", "Jeremy Thobourne", "Sofia Wei Zhang",
    "Eren Devin Yau Su", "Eiji Yoshioka", "Alberto Zhang Fan", "Daniela Zhang Fan", "William Zhang",
    "Javier Zheng", "Erick Zhong Hou"
]

master_students_3B = [
    "Bayazid Amor", "Jean Paolo Atencio Mejias", "Sophie Marie Bernal Ruiz", "Angel Chacon",
    "Rosmira Chavez", "Chloe Cheng Cham", "Axl Chirinos", "Dereck David Chu Zhong",
    "Daniel Espinoza Rueda", "Arianna Ferrer", "Isabella Flaautt", "Axl Lin", "Tiffany Liu",
    "Javier Zaid Ortiz", "Emily Osorio Gonzalez", "Isaac Pinillo", "Felicia Qiu Huang", "Louis Rubin",
    "Alana Solis Salomon", "Marcelo Vergara", "Dereck Vigil Aguilar", "Myka Weets", "Chloe Zhang Chung"
]

master_students_4A = [
    "Humberto Amores", "Mia Alvarado", "Victoria Campos", "Kevin Joel Chen Liu", "Daniel Chen Wong",
    "Guillermo Chen", "Jay Cheung", "Tania Isabel He Chen", "Carlos Hou Zhang Xu Xuan",
    "Angeline Alejandra Lizondro Bello", "Jennifer Ainhoa Lopez Silva", "Jennyfer Luo Luo",
    "Ana Sofia Luo Zhang", "Tom Luo", "Hamet Perez Christie", "Eugene Abdel Pinto Navarro", "Mateo Ricord",
    "Diago Rodríguez Delgado", "Axel Javier Sinisterra Quintero", "Kaylie Wu Liu", "Kenji Yoshioka",
    "Kevin Zhang Luo", "Angela Zhang Zhong", "Evanys Zheng"
]

master_students_4B = [
    "Vihanna Tushar Ahir Ahir", "Andreh Arana Cano", "Noah Nelson Ardines Ortega", "David Atencio",
    "Jasbir Batista", "Keren Jearim Campo De Gracia", "Daniel Cepeda Shiu", "Thiago Ching",
    "Daniela Alejandra Espinoza Rueda", "Alejandro Gael Garza Fu", "Mia Victoria Gonzalez Zurita",
    "Christian Guerra Lezcano", "Lucia Gutierrez Monroy", "Eythan Hernandez Arrocha", "John Local Solís",
    "Jennifer Ivonne Loo Yau", "Amelie Lucia Luo Lo", "Paulina Moreno", "Farah Ponton",
    "Arturo Velarde Herrera", "Samantha Velasquez Cordoba", "Azaid Antonio Wang", "Aiden Wen Luo"
]

master_students_5A = [
    "Alessandro Benitez", "Pandora Betancourt", "Ilhan Ernesto Calvo González", "Zhen (Joe) Chen",
    "Jose Cheng Chong", "Alex Cheung", "Athan Chichaco", "Kurt Chong", "Iris Chung Li",
    "Amelia Córdoba Montezuma", "Matthew Andrés De León Raven", "Sadith Domínguez", "Monica Feng Zhong",
    "Emmanuel Gao", "Miah Valentina Gomez", "Sebastian Gomez", "Jade He", "Valeria Isabella Marulanda",
    "Hellen Montenegro", "Damon Ng", "Priscila Olivardia Valdes", "Alejandro Fabian Sanchez Rodriguez",
    "Victoria Teran", "Sofía Cindy Zhang Fan"
]

master_students_5B = [
    "Noelia Raquel Ardines Ortega", "Valentina Benites", "Geovanna Castillero Castro",
    "Juan David Chavez Prado", "Aimee Ching", "Luna Ching", "Kenneth Chong",
    "Sofia Alejandra Cortez Del Cid", "Leonor Domínguez", "Daniel Gibbs", "Lyanne Christine Guo Yau",
    "Analia Herrera", "Vivian Stephanie Ho Zeng", "Alessa Braja Jaén", "Eduardo Jiménez Manoleskos",
    "Melody Liu Wu", "Emily Luo Luo", "Daryelis Rodriguez", "Mia Valeria Romero Puig",
    "Dubraska Sarmiento Suárez", "Cecilia Tang", "Fabian Torres Reyna", "Kamila Nazareth Vergara"
]

master_students_6A = [
    "Samuel Roberto Ayala Macias", "Skylar Bailey", "Paul Andrés Castillero Delgado",
    "Emily Catherine Chen He", "Kenneth Fu Chen", "Francisco Gurdián", "Nicole He Gan",
    "Jimmy Hummer He", "Kimi He", "Mina He", "Gian Luca Laniado Vega", "Alicia Luo Luo",
    "Valeria Montenegro Soto", "Valentina Sofía Muñoz Díaz", "Felipe Olivardia", "Emma Oro",
    "Hannah Peralta", "Valentina Marie Rivera Celis", "Andres Rodriguez", "Hazel Rodriguez",
    "Sebastian Ruiz", "Lyan Alexander Sánchez Del Río", "Isabella Nicole Schloss Herrera", "Roberto Tan",
    "Eleine Michelle Yau Su", "Lucas Young Obando", "Daniel Zhang Fan", "Steven Zhang Luo",
    "William Antonio Zhong Huang"
]

master_students_7A = [
    "Henrique Arenas", "Angeline Victoria Cepeda Shiu", "Edwin Chen", "Hiram Antony Chen He",
    "Valeria Sophia Chen De Leon", "Daniel Jesus De Leon Caceres", "Alexia Isabel Diaz Herrera",
    "Hector Fu Chen", "Josahir Darshan Garcia Cubilla", "Jaime Javier Gibbs Guerra",
    "Gabriela Marie Guerra Lezcano", "Andrew David Guo Yau", "Junke He", "Daisy Jiang Wen",
    "Maribel Pei Lin Lai Zhong", "Khloe Isabelle Lau Rodriguez", "Emily Li", "Jimmie Liu Wu",
    "Paola Luo Qiu", "Carolina Hiriam Luo Luo", "Jia Ying Luo", "Kaleth Montalvo",
    "Maria Jose Pardo Caceres", "Penelope Perez Arauz", "Jose Felix Pimentel Woodley",
    "Allison Nicole Plicet De Gracia", "Camila Qiu", "Lia Roxette Robinson Arias",
    "Adriam Jose Rodriguez Luna", "Valentina Isabella Velarde Herrera", "Angelie Sophia Wu Liu",
    "Evelyn Yang", "Lucia Zhang Zhong", "Lucas Spencer Duran"
]

master_students_8G = [
    "Iann Arauz", "Mia Atencio Giron", "Brandon Chock Kong", "Kaidy Chong Zhu",
    "Ian Chong Serrano", "Kisbeth Chong Qiu", "Ethan De Leon Raven", "Dylan Dely Flaautt",
    "Douglas Deweese Alonzo", "Inna Diaz Agudo", "Eduardo Gudiño Valdez", "Sofia Guevara",
    "Crystal Hou Qiu", "Kevin Luo Zhang", "Arantza Navarro Flores", "Nicolas Perez Brown",
    "Diego Pimentel Woodley", "Luzarianis Prado Martinez", "Daniel Puga Mora", "William Qiu Hou",
    "Kelly Qiu Luo", "Andrea Rodriguez Acevedo", "Franklin Sanchez Avecilla",
    "Melanie Villalaz Olivardia", "Sebastian Villasmil Carosi", "Joyce Wei Zhang",
    "Vivian Wen Hou", "Siwen Zhang", "Sofia Zhu Wu", "Vicky Zhu Zhang"
]

master_students_9A = [
    "Sarah Aguilar Espinosa", "Dhruvin Ahir Ahir", "Hector Chen Wu", "Matias De Leon Caceres",
    "Judith He Luo", "Jorge Hou Zhang", "Antonella Jaen Lombardo", "Dominique Kreuzwirth Linares",
    "John Li Hou", "Ryan Melendez Smith", "Anyoli Melo Cordoba", "Sara Morales Aguilera",
    "Ximena Ramos Wilches", "Jose Rodriguez Vega", "Lady Ruiz Gonzalez", "Heiley Qiu How",
    "Meidy Sem Cheng", "Maria Lourdes Sugasti Ledezma", "Alexis Xu Wu", "Rian Ahir Ahir",
    "Johan Ching Bernal", "Juan De Leon Caceres", "Ellis He Cai", "Hilary Hou Qiu",
    "Steven Lai Zhong", "Yesenia Li Qiu", "Kevin Liu Wu", "Williams Luo Qiu", "Williams Luo Yang",
    "Iria Luo Zhong", "Mateo Montero Cano", "Victoria Pérez Garcia", "Sophia Rodriguez Valenzuela",
    "Samantha Valero Bracamonte", "Christopher Wen Wen", "Ivery Wong Wang", "Mario Zhong Huang"
]

master_students_10A = [
    "Jose Bertorelli Fernandez", "Juan Bonilla Llanos", "Kenneth Chan", "Brian Chen Wen",
    "Winston Chen Zhu", "Zhiye Chen Li", "Ray Cheung Luo", "Allison Chock Kong",
    "Isabella Cordero Solano", "Kristal Cordoba Gooden", "Ian Espino Almanza", "Adrian Fernandez",
    "Jorge He Luo", "Andres Lan Lan", "Angela Li Fang", "David Li Hou", "Carlos Luo Luo",
    "Karina Luo Luo", "Leah Navarro", "Kenny Qiu Zhu", "Dylan Rodriguez Delgado",
    "Luciana Ruiz Riveros", "Dylan Sanjur Navarro", "Yoselin Shen Chen", "Paola Teng Arauz",
    "Justyn Wei Zhang", "Johnny Yang", "Antonio Zhu Zhang"
]

master_students_11A = [
    "Jassek Cajar Muñoz", "Mariangel Castro Ortega", "Gabriel Chen De Leon",
    "Miguel Concepcion Morales", "Sofia Ferrer Parra", "Helena Fu Chen", "Patricia Fu Chen",
    "Camila Gonzalez Lopez", "Zuwei Guo", "Jennifer He Wen", "Joanny Hou Zhang", "Lucas Wu Luo",
    "Kelly Nie Nie", "Edwuar Qiu Wu", "Heidi Sem Cheng", "Yazmin Shen Chen", "Danny Tang Zhong",
    "Lauren Tapia Frias", "Jason Wen Hou", "Anyi Zhang Zhong"
]

master_students_12A = [
    "Mavielis Castillero Delgado", "Lyannie Chen Liu", "Wilson Chen Zhu", "James De Gracia Vega",
    "Anny Deng Liu", "Ashley Li Hou", "Sofia Liang Wu", "Rocco Lokee Solis", "Joel Perez Botello",
    "Michelle Qiu Luo", "Rafael Romero Burgos", "Wilken Wong Wang", "Jackson Zhu Wu"
]

MASTER_GROUPS = {
    "2A": master_students_2A,
    "2B": master_students_2B,
    "3A": master_students_3A,
    "3B": master_students_3B,
    "4A": master_students_4A,
    "4B": master_students_4B,
    "5A": master_students_5A,
    "5B": master_students_5B,
    "6A": master_students_6A,
    # Las listas combinadas permiten reconocer reportes que incluyen ambas
    # secciones; si el reporte contiene solo una, la razón de coincidencia
    # favorece automáticamente a la sección individual.
    "2": master_students_2A + master_students_2B,
    "3": master_students_3A + master_students_3B,
    "4": master_students_4A + master_students_4B,
    "5": master_students_5A + master_students_5B,
    "7A": master_students_7A,
    "8G": master_students_8G,
    "9A": master_students_9A,
    "10A": master_students_10A,
    "11A": master_students_11A,
    "12A": master_students_12A,
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
    """Selecciona la lista maestra AY2627 según grado o código de clase."""
    masters_by_grade = {
        "07": master_students_7A,
        "08": master_students_8G,
        "09": master_students_9A,
        "10": master_students_10A,
        "11": master_students_11A,
        "12": master_students_12A,
    }
    class_codes = {
        "MI": master_students_7A,
        "MJ": master_students_8G,
        "MK": master_students_9A,
        "ML": master_students_10A,
        "MM": master_students_11A,
        "MN": master_students_12A,
    }

    normalized_name = str(sheet_name).upper()
    # Algunos reportes de décimo han usado "00" en vez de "10".
    if normalized_name.startswith("2627-00"):
        return master_students_10A
    for grade, master in masters_by_grade.items():
        if normalized_name.startswith(f"2627-{grade}"):
            return master
    for code, master in class_codes.items():
        if code in normalized_name:
            return master
    return []


def _normalize_name(name: str) -> str:
    normalized = " ".join(str(name).split()).casefold()
    return "".join(
        char for char in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(char)
    )


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
    """Ordena las hojas AY2627 de séptimo a duodécimo grado."""
    normalized_name = str(sheet_name).upper()
    grade_markers = [
        (("2627-07", "MI"), 0),
        (("2627-08", "MJ"), 1),
        (("2627-09", "MK"), 2),
        (("2627-10", "2627-00", "ML"), 3),
        (("2627-11", "MM"), 4),
        (("2627-12", "MN"), 5),
    ]
    for markers, order in grade_markers:
        if any(marker in normalized_name for marker in markers):
            return (order, normalized_name)
    return (6, normalized_name)


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
