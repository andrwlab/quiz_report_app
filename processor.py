import io
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional, Set, Tuple

import pandas as pd

# ====== TUS LISTAS MAESTRAS ======
master_students_2A = ["Ayaan Ahir","Jean Paolo Atencio Mejias","Sophie Marie Bernal Ruiz","Idelfonso Bracho","Gia Broce","Maria Valentina Cardenas","Alanna Gibell Castillo Jean-Louis","Gian Felipe Chapman Rodríguez","Rosmira Chavez","Axl Chirinos","Daniel Espinoza Rueda","Arianna Ferrer","Isabella Flaautt","Dana Gomez","Kemuel Guardia","Sofía He Liu","Olivia Law Shiu","Sara Luo","Ana Victoria Marquez Onodera","Luis Mendoza","Louis Rubin","Alexander Solis Salomon","Lakdar Terreros Acuña","Eren Devin Yau Su","Daniela Zhang Fan","Erick Zhong Hou"]
master_students_2B = ["Yaksh Ahir","Bayazid Amor","Brianna Arauz","Angel Chacon","Chloe Cheng Cham","Dereck David Chu Zhong","Alida Duarte Castro","Hilary Feng Zhong","Keyden Gonzalez","Axl Lin","Tiffany Liu","Javier Zaid Ortiz","Emily Osorio Gonzalez","Isaac Pinillo","Felicia Qiu Huang","Luca Rafael Romero Puig","Alana Solis Salomon","Jeremy Thoubourne","Marcelo Vergara","Dereck Vigil Aguilar","Myka Weets","Sofia Wei Zhang","Sebástian Wong Cheung","Eiji Yoshioka","Chloe Zhang Chung","Alberto Zhang Fan","Javier Zheng"]
master_students_3A = ["Humberto Amores","Victoria Campos","Kevin Joel Chen Liu","Daniel Chen Wong","Guillermo Chen","Jay Jackson Cheung","Hamet Perez Christie","Tania Isabel He Chen","Carlos Hou Zhang Xu Xuan","Daniel Lambis Burgos","Angeline Alejandra Lizondro Bello","Jennifer Ainhoa Lopez Silva","Jennyfer Luo Luo","Ana Sofia Luo Zhang","Tom Luo","Paulina Moreno","Eugene Abdel Pinto Navarro","Mateo Ricord","Diago Rodríguez Delgado","Axel Javier Sinisterra Quintero","Aiden Wen Luo","Terry Wong","Kaylie Wu Liu","Kenji Yoshioka","Kevin Zhang Luo","Angela Zhang Zhong","Evanys Zheng"]
master_students_3B = ["Vihanna Tushar Ahir Ahir","Mia Alvarado","Andreh Arana Cano","Noah Nelson Ardines Ortega","David Atencio","Jasbir Batista","Kerem Jearim Campo De Gracia","Daniel Cepeda Shiu","Thiago Ching","Daniela Alejandra Espinoza Rueda","Alejandro Gael Garza Fu","Mia Victoria Gonzalez Zurita","Christian Guerra Lezcano","Lucia Gutierrez Monroy","Eythan Hernandez Arrocha","John Local Solís","Jennifer Ivonne Loo Yau","Amelie Lucia Luo Lo","Alejandro Marin","Farah Ponton","Arturo Velarde Herrera","Samantha Velasquez Cordoba","Christopher Visuetty Singh","Azaid Antonio Wang"]
master_students_4A = ["Vishva Ahir Ahir","Alessandro Benitez","Pandora Betancourt","Ilhan Ernesto Calvo González","Zhen (Joe) Chen","Jose Cheng Chong","Aimee Ching","Kurt Chong","Amelia Córdoba Montezuma","Matthew Andrés De León Raven","Sadith Domínguez","Monica Feng Zhong","Emmanuel Gao","Miah Valentina Gomez","Lyanne Christine Guo Yau","Emily Luo Luo","Valeria Isabella Marulanda","Hellen Montenegro","Damon Ng","Priscila Olivardia Valdes","Willy Bryant Qiu Jiang","Alejandro Fabian Sanchez Rodriguez","Cecilia Tang","Victoria Teran","Mía Wong Cheung"]
master_students_4B = ["Noelia Raquel Ardines Ortega","Valentina Benites","Geovanna Castillero Castro","Ricardo Isaac Chapman Rodríguez","Juan David Chavez Prado","Alex Cheung","Athan Chichaco","Luna Ching","Kenneth Chong","Iris Chung Li","Sofia Alejandra Cortez Del Cid","Leonor Domínguez","Daniel Gibbs","Jade He","Analia Herrera","Vivian Stephanie Ho Zeng","Alessa Braja Jaén","Eduardo Jiménez Manoleskos","Melody Liu Wu","Ricardo Lin Luo Qiu Luo","Daryelis Rodriguez","Mia Valeria Romero Puig","Dubraska Sarmiento Suárez","Fabian Torres Reyna","Kamila Nazareth Vergara","Sofía Cindy Zhang Fan"]
master_students_5A = ["Nahikary Amor","Samuel Roberto Ayala Macias","Paul Andrés Castillero Delgado","Thiago Castro","Emily Catherine Chen He","Kenneth Fu Chen","Francisco Gurdián","Nicole He Gan","Jimmy Hummer He","Kimi He","Gian Luca Laniado Vega","Alicia Luo Luo","Valeria Montenegro Soto","Valentina Sofía Muñoz Díaz","Felipe Olivardia","Emma Oro","Hannah Peralta","Valentina Marie Rivera Celis","Andres Rodriguez","Hazel Rodriguez","Sebastian Ruiz","Lyan Alexander Sánchez Del Río","Isabella Nicole Schloss Herrera","Roberto Tan","Sofia Visuetty Singh","Eleine Michelle Yau Su","Lucas Young Obando","Daniel Zhang Fan","Steven Zhang Luo","William Antonio Zhong Huang"]
master_students_6A = ["Akari Carrera Barber","Angeline Victoria Cepeda Shiu","Valeria Sophia Chen De Leon","Hiram Antony Chen He","Edwin Chen","Gabriela Marie Guerra Lezcano","Daisy Jiang Wen","Maribel Pei Lin Lai Zhong","Jimmie Liu Wu","Jia Ying Luo","Allison Nicole Plicet De Gracia","Ashley Qiu Jiang","Camila Qiu","Lia Roxette Robinson Arias","Adriam Jose Rodriguez Luna","Valentina Isabella Velarde Herrera","Evelyn Yang","Juke He"]
master_students_6B = ["Henrique Arenas","Daniel Jesus De Leon Caceres","Alexia Isabel Diaz Herrera","Hector Fu Chen","Josahir Darshan Garcia Cubilla","Jaime Javier Gibbs Guerra","Andrew David Guo Yau","Alessandra Daniela Lambis Burgos","Khloe Isabelle Lau Rodriguez","Carolina Hiriam Luo Luo","Paola Luo Qiu","Kaleeth Montalvo","Maria Jose Pardo Caceres","Penelope Perez Arauz","Jose Felix Pimentel Woodley","Angelie Sophia Wu Liu","Elizabeth Xu","Lucia Zhang Zhong"]
master_students_7A = ["Andrea Rodriguez Acevedo","Arantza Navarro Flores","Brandon Chock Kong","Crystal Hou Qiu","Daniel Puga Mora","Diego Pimentel Woodley","Douglas Deweese Alonzo","Dylan Dely Flaautt","Eduardo Gudiño Valdez","Ethan De Leon Raven","Franklin Sanchez Avecilla","Ian Chong Serrano","Iann Arauz","Inna Diaz Agudo","Joyce Wei Zhang","Kaidy Chong Zhu","Kelly Qiu Luo","Kelly Xu Deng","Kevin Luo Zhang","Kisbeth Chong Qiu","Luzarianis Prado Martinez","Melanie Villalaz Olivardia","Mia Atencio Giron","Nicolas Perez Brown","Sebastian Villasmil Carosi","Siwen Zhang","Sofia Guevara","Sofia Zhu Wu","Vicky Zhu Zhang","Vivian Wen Hou","William Qiu Hou","Zhuoying Qiu","Junke He"]
master_students_8G = ["Alexis Xu Wu","Andy Zhang Qiu","Antonella Jaen Lombardo","Anyoli Melo Cordoba","Christopher Wen Wen","Dhruvin Ahir Ahir","Dominique Kreuzwirth Linares","Ellis He Cai","Heiley Qiu How","Hector Chen Wu","Hilary Hou Qiu","Ian Navarro Garcia","Iria Luo Zhong","Ivery Wong Wang","Johan Ching Bernal","John Li Hou","Jorge Hou Zhang","Jose Rodriguez Vega","Juan De Leon Caceres","Judith He Luo","Kevin Liu Wu","Lady Ruiz Gonzalez","Maria Lourdes Sugasti Ledezma","Mario Zhong Huang","Matias De Leon Caceres","Mateo Montero Cano","Meidy Sem Cheng","Rian Ahir Ahir","Ryan Melendez Smith","Samantha Valero Bracamonte","Sara Morales Aguilera","Sarah Aguilar Espinosa","Sophia Rodriguez Valenzuela","Steven Lai Zhong","Victoria Pérez Garcia","Williams Luo Qiu","Williams Luo Yang","Ximena Ramos Wilches","Yesenia Li Qiu", "Zahid Amor Ladron De Guevara"]
master_students_9A = ["Adrian Fernandez","Allison Chock Kong","Analia Gomez","Angela Li Fang","Andres Lan Lan","Antonio Zhu Zhang","Brian Chen Wen","Carlos Luo Luo","David Li Hou","Dylan Rodriguez Delgado","Dylan Sanjur Navarro","Gabriel Sanchez Serrano","Guohong Xu","Ian Espino Almanza","Isabella Cordero Solano","Jose Bertorelli Fernandez","Jorge He Luo","Juan Bonilla Llanos","Justyn Wei Zhang","Karina Luo Luo","Kenny Qiu Zhu","Kevin Wen Zhang","Kristal Cordoba Gooden","Leah Navarro","Luciana Ruiz Riveros","Paola Teng Arauz","Ray Cheung Luo","Winston Chen Zhu","Yoselin Shen Chen","Zhiye Chen Li"]
master_students_10A = ["Angui Zhang Qiu","Anyi Zhang Zhong","Camila Gonzalez Lopez","Danny Tang Zhong","Edwuar Qiu Wu","Gabriel Chen De Leon","Heidi Sem Cheng","Helen Fu Chen","Jason Wen Hou","Jassek Cajar Muñoz","Jeniffer He Wen","Joanny Hou Zhang","Kelly Nie Nie","Lauren Tapia Frias","Lucas Wu Luo","Mariangel Castro Ortega","Marcos Luo Zhong","Miguel Concepcion Morales","Nishtha Ahir","Patricia Fu Chen","Sofia Ferrer Parra","Yazmin Shen Chen","Zuwei Guo"]
master_students_11A = ["Wilson Chen Zhu","Rocco Lokee Solis","James De Gracia Vega","Lyannie Chen Liu","Mavielis Castillero Delgado","Jackson Zhu Wu","Ashly Li Hou","Joel Perez Botello","Wilken Wong Wang","Michell Qiu Luo","Rafael Romero Burgos","Anny Deng Liu","Sofia Liang Wu"]
MASTER_GROUPS = {"2A": master_students_2A,"2B": master_students_2B,"3A": master_students_3A,"3B": master_students_3B,"4A": master_students_4A,"4B": master_students_4B,"5A": master_students_5A,"6A": master_students_6A,"6B": master_students_6B,"7A": master_students_7A,"8G": master_students_8G,"9A": master_students_9A,"10A": master_students_10A,"11A": master_students_11A}

SECONDARY_GRADES = {"7A", "8G", "9A", "10A", "11A"}


def _norm(s: str) -> str:
    text = " ".join(str(s or "").split()).strip().casefold()
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def parse_pending_low_text(text: str) -> List[dict]:
    quizzes = []
    blocks = re.split(r"_{8,}", text or "")
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        q = re.search(r"Quiz:\s*(.+)", b)
        if not q:
            continue
        quiz_id = q.group(1).strip()
        pending = re.search(r"Pending:\s*(.*?)\n\s*Low Score \(< 15\.1%\):", b, re.S)
        low15 = re.search(r"Low Score \(< 15\.1%\):\s*(.*?)\n\s*Low Score \(15\.1% - 74\.9%\):", b, re.S)
        pending_names = [ln.strip() for ln in (pending.group(1).splitlines() if pending else []) if ln.strip()]
        low15_names = [ln.strip() for ln in (low15.group(1).splitlines() if low15 else []) if ln.strip()]
        quizzes.append({"quiz_id": quiz_id, "pending": pending_names, "low_lt_15": low15_names})
    return quizzes


def map_students_to_master(quizzes: List[dict], master_groups: Dict[str, List[str]] = MASTER_GROUPS):
    norm_ix = {}
    for grade, students in master_groups.items():
        for order, name in enumerate(students):
            norm_ix[_norm(name)] = (grade, name, order)

    mapped = []
    unmatched: Set[str] = set()
    for q in quizzes:
        students = set(q["pending"] + q["low_lt_15"])
        matched = []
        for s in students:
            info = norm_ix.get(_norm(s))
            if not info:
                unmatched.add(s)
                continue
            grade, canonical, order = info
            matched.append({"grade": grade, "name": canonical, "order": order})
        mapped.append({"quiz_id": q["quiz_id"], "students": matched})
    return mapped, sorted(unmatched)


def build_infraction_emails(mapped_quizzes: List[dict], *, context_label="Periodic Quizzes", subject_subject="Math", intro_text: Optional[str]=None):
    grade_data: Dict[str, dict] = {}
    for q in mapped_quizzes:
        per_grade_seen = set()
        for st in q["students"]:
            gd = grade_data.setdefault(st["grade"], {"quiz_ids": set(), "freq": {}, "order": {}})
            gd["quiz_ids"].add(q["quiz_id"])
            gd["freq"][st["name"]] = gd["freq"].get(st["name"], 0) + 1
            gd["order"][st["name"]] = st["order"]
            per_grade_seen.add(st["grade"])

    sections = []
    for grade, d in sorted(grade_data.items(), key=lambda x: (int(re.match(r"(\d+)", x[0]).group(1)), x[0])):
        quiz_count = len(d["quiz_ids"])
        names = sorted(d["freq"].keys(), key=lambda n: d["order"][n])
        students = [{"name": n, **({"frequency": d["freq"][n]} if quiz_count > 1 else {})} for n in names]
        if not students:
            continue
        if quiz_count == 1:
            reason = f"they had 1 {context_label} assigned but didn’t complete it before the due date."
        else:
            reason = f"they had {quiz_count} periodic quizzes assigned but didn’t complete them before the due date."
        sections.append({"grade": grade, "students": students, "quizCount": quiz_count, "reason": reason})

    primary = [s for s in sections if s["grade"] not in SECONDARY_GRADES]
    secondary = [s for s in sections if s["grade"] in SECONDARY_GRADES]

    def mk_email(recipient: Literal["Mr. Ortega", "Ms. López"], group_sections: List[dict]):
        if not group_sections:
            return None
        intro = intro_text or "At the bottom there is a list of students who didn’t finish their assignments for the periodic quizzes and will get an infraction."
        body_parts = [f"Dear {recipient},", "", "Hope this finds you well.", "", intro, ""]
        for sec in group_sections:
            body_parts.append("Student name:")
            for st in sec["students"]:
                line = st["name"] + (f" - {st['frequency']}" if "frequency" in st else "")
                body_parts.append(line)
            body_parts.extend(["", f"Grade: {sec['grade']}", f"Subject: {subject_subject}", f"Reason for infraction: {sec['reason']}", ""])
        body_parts.extend(["Regards,", "Mr. Hall"])
        return {"recipientName": recipient, "subject": f"Infractions - {subject_subject} {context_label} - 7th to 10th", "body": "\n".join(body_parts), "sections": group_sections}

    emails = []
    if primary:
        emails.append(mk_email("Ms. López", primary))
    if secondary:
        emails.append(mk_email("Mr. Ortega", secondary))
    return {"emails": [e for e in emails if e], "sections": sections}


def process_workbook(file_bytes: bytes):
    sheets_noheader = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)
    report_rows, pending_blocks = [], []
    for sheet_name, df_noheader in sheets_noheader.items():
        try:
            num_intentos = int(df_noheader.iloc[15, 3])
        except Exception:
            num_intentos = 0
        try:
            table = df_noheader.iloc[16:].copy(); table.columns = table.iloc[0]; table = table.drop(table.index[0]); table.columns = table.columns.astype(str).str.strip()
        except Exception:
            table = pd.DataFrame()
        current_master = MASTER_GROUPS.get("7A", [])
        if not table.empty and {"Student Name", "Final Score"}.issubset(table.columns):
            table["Final Score"] = table["Final Score"].astype(str).str.rstrip("%").replace("", "0").astype(float)
            promedio = table["Final Score"].mean() if not table["Final Score"].empty else 0.0
            total_students = len(current_master); completed = int(num_intentos); completion_pct = (completed / total_students) * 100 if total_students else 0.0
            present = [st for st in table["Student Name"].dropna().unique().tolist() if st in current_master]
            missing_students = [st for st in current_master if st not in present]
            low_names = table[table["Final Score"] < 70]["Student Name"].tolist()
            report_rows.append({"quiz_id": sheet_name,"total": str(total_students),"submitted": str(completed),"avg_total_%": f"{completion_pct:.1f}%","avg_submitted_%": f"{promedio:.1f}%","pending_names": ", ".join(missing_students),"low_names": ", ".join(low_names)})
            low_score_lt_15 = table[table["Final Score"] < 15.1]["Student Name"].tolist()
            mid_low_df = table[(table["Final Score"] >= 15.1) & (table["Final Score"] < 75)][["Student Name", "Final Score"]]
            lines = [f"Quiz: {sheet_name}\n", "Pending:\n", *[f"{s}\n" for s in missing_students], "\nLow Score (< 15.1%):\n", *[f"{s}\n" for s in low_score_lt_15], "\nLow Score (15.1% - 74.9%):\n", *[f"{r['Student Name']} - {r['Final Score']:.1f}%\n" for _, r in mid_low_df.iterrows()], "\n" + "_" * 44 + "\n"]
            pending_blocks.append("".join(lines))
    report_df = pd.DataFrame(report_rows).reindex(columns=["quiz_id","total","submitted","avg_total_%","avg_submitted_%","pending_names","low_names"])
    return report_df, "\n\n".join(pending_blocks)
