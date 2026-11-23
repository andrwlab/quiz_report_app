"""Read the teachers' weekly summary without guessing student identities."""
from collections import defaultdict
from dataclasses import dataclass, field
from io import BytesIO
import re
import unicodedata
from openpyxl import load_workbook

from data_pipeline import ValidationError


def name_key(value):
    value = ''.join(c for c in unicodedata.normalize('NFKD', str(value)) if not unicodedata.combining(c))
    return ' '.join(value.casefold().replace('.', '').split())


def grade_key(value):
    match = re.fullmatch(r'(G\d+)[A-Z]?', str(value).strip().upper())
    return match.group(1) if match else None


@dataclass
class WorkbookReview:
    records: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    ignored_sheets: list = field(default_factory=list)
    quiz_rows: int = 0

    def publication_records(self):
        # A damaged/unrecognizable workbook cannot replace a whole term.
        if not self.quiz_rows or any(i['Reason'] == 'Term in sheet title disagrees with the uploaded filename' for i in self.issues):
            self.require_valid()
        conflicting = {(i['Week'], i['Subject'], i['Quiz Code'], n.strip())
                       for i in self.issues if i['Reason'] == 'Conflicting states'
                       for n in i['Candidate Numbers'].split(',') if n.strip()}
        return [r for r in self.records if (r['week'],r['subject'],r['code'],r['number']) not in conflicting]

    def review_scope(self, roster):
        numbers, all_students = set(), False
        for issue in self.issues:
            candidates = {n.strip() for n in issue['Candidate Numbers'].split(',') if n.strip()}
            if candidates:
                numbers.update(candidates)
            elif grade_key(issue['Grade']):
                numbers.update(s['Student Number'] for s in roster if grade_key(s['Group']) == grade_key(issue['Grade']))
            else:
                all_students = True
        return dict(review_count=len(self.issues), review_students=sorted(numbers), review_all=all_students)

    def require_valid(self):
        if self.issues:
            locations = ', '.join(f"{issue['Week']} row {issue['Row']}" for issue in self.issues[:4])
            raise ValidationError(f'Weekly workbook has {len(self.issues)} issues requiring review ({locations}). Published data was kept.')
        return self.records


def student_index(roster):
    index = defaultdict(set)
    for student in roster:
        number, name = student['Student Number'], student['Student Name'].strip()
        if not grade_key(student['Group']):
            raise ValidationError('An official student group is invalid.')
        if not number:
            continue
        keys = {name_key(name)}
        if ',' in name:
            surname, given = (part.strip() for part in name.split(',', 1))
        else:
            parts = name.split()
            given, surname = parts[0], ' '.join(parts[1:])
        if ',' not in name and len(name.split()) >= 2:
            parts = name.split()
            last_given, alternate_family = parts[-1], parts[:-1]
            keys.update(name_key(key) for key in [last_given, last_given+' '+alternate_family[0][0], last_given+' '+''.join(part[0] for part in alternate_family)])
        if not given or not surname:
            raise ValidationError('An official student name cannot be indexed.')
        first, family = given.split()[0], surname.split()[0]
        keys.update(name_key(key) for key in [given+' '+surname, given, first, surname, family, first+' '+family[0], first+' '+family])
        keys.add(name_key(first+' '+''.join(token[0] for token in surname.split())))
        if len(given.split()) > 1:
            keys.add(name_key(first+' '+''.join(token[0] for token in given.split()[1:])))
        for key in keys:
            index[grade_key(student['Group']), key].add(number)
    return index


def label_parts(cell):
    """Scores terminate labels; they never become student identities."""
    text = re.sub(r'(?<=\d),(?=\d)', '.', str(cell))
    text = re.sub(r'\(\s*\d*(?:\.\d+)?\s*%?\s*\)', ';', text)
    text = re.sub(r'\d+(?:\.\d+)?\s*%', ';', text)
    for token in re.split(r'[,;\n]+|\s+(?:and|y)\s+', text, flags=re.IGNORECASE):
        token = re.sub(r'\s+incomplete\s*$', '', token, flags=re.IGNORECASE)
        token = re.sub(r'\s+\d+(?:\.\d+)?\s*$', '', token).strip()
        if token and not re.fullmatch(r'\d+(?:\.\d+)?', token):
            yield token


def review_weekly_workbook(content, roster, aliases=(), corrections=(), source_term=None):
    review = WorkbookReview()
    by_number = {s['Student Number']: s for s in roster if s['Student Number']}
    if len(by_number) != sum(bool(s['Student Number']) for s in roster):
        raise ValidationError('Official Student Numbers must be unique.')
    index = student_index(roster)
    full_tokens = defaultdict(set)
    for student in roster:
        if student['Student Number']:
            tokens = tuple(sorted(name_key(student['Student Name'].replace(',', ' ')).split()))
            full_tokens[grade_key(student['Group']), tokens].add(student['Student Number'])
    overrides = {}
    for row in aliases:
        if not any(str(v).strip() for v in row.values()):
            continue
        grade, subject, label, number = [str(row.get(k, '')).strip() for k in ['Grade', 'Subject', 'Report Name', 'Student Number']]
        key = (grade_key(grade), name_key(subject), name_key(label))
        if not key[0] or not label or number not in by_number or grade_key(by_number[number]['Group']) != key[0] or key in overrides:
            raise ValidationError('An alias is invalid, duplicated or belongs to a different grade.')
        overrides[key] = number
    cell_corrections = {}
    for row in corrections:
        if not any(str(value).strip() for value in row.values()):
            continue
        term, week, subject, grade, code, status, text, numbers = [str(row.get(k, '')).strip() for k in ['Term','Week','Subject','Grade','Quiz Code','Status','Source Text','Student Numbers']]
        action = str(row.get('Action', 'Map students')).strip()
        ids = [value.strip() for value in numbers.split(',') if value.strip()]
        key = (term.upper(), week, name_key(subject), grade_key(grade), code, status, ' '.join(text.split()))
        if not key[3] or not re.fullmatch(r'T\d+', term.upper()) or not re.fullmatch(r'Week\s+\d+', week) or not subject or not code or status not in ('Pending','Low Score') or not text or action not in ('Map students','Map students with review','Ignore note') or (action.startswith('Map students') and not ids) or (action == 'Ignore note' and ids) or len(set(ids)) != len(ids) or key in cell_corrections:
            raise ValidationError('A cell correction is invalid or duplicated.')
        if any(number not in by_number or grade_key(by_number[number]['Group']) != key[3] for number in ids):
            raise ValidationError('A cell correction references an unknown student or another grade.')
        cell_corrections[key] = (ids, action)
    book = load_workbook(BytesIO(content), read_only=True, data_only=True)
    formulas = load_workbook(BytesIO(content), read_only=True, data_only=False)
    seen = {}
    try:
        for sheet in book:
            week = sheet.title
            if not re.fullmatch(r'Week\s+\d+', week):
                review.ignored_sheets.append(week)
                continue
            rows = list(sheet.values)
            term_match = re.search(r'\bT\d+\b', str(rows[0][0] or '') if rows else '', re.IGNORECASE)
            term = (source_term or (term_match.group() if term_match else '')).upper()
            if source_term and term_match and term_match.group().upper() != source_term.upper():
                review.issues.append({'Week':week,'Row':1,'Subject':'','Grade':'','Quiz Code':'','Report Name':'','Reason':'Term in sheet title disagrees with the uploaded filename','Candidate Numbers':''})
                continue
            formula_rows = list(formulas[week].values)
            subject, grade = None, None
            for index_row, raw in enumerate(rows):
                cells = list(raw) + [None] * 9
                a, b, c = [str(v).strip() if v is not None else '' for v in cells[:3]]
                row_number = index_row + 1
                code = str(cells[2]) if cells[2] is not None else ''
                def issue(label, reason, candidates=()):
                    review.issues.append({'Week':week, 'Row':row_number, 'Subject':subject or '', 'Grade':grade or '', 'Quiz Code':code, 'Report Name':label, 'Reason':reason, 'Candidate Numbers':', '.join(sorted(candidates))})
                if name_key(b) == 'grade' and name_key(c) == 'quiz #':
                    if name_key(cells[7] or '') not in ('no attempts', 'pending') or name_key(cells[8] or '') not in ('low scores', 'low score'):
                        issue('', 'Unexpected Pending/Low Score column headings')
                        subject, grade = None, None
                        continue
                    subject = str(rows[index_row-1][0] or '').strip() if index_row else ''
                    grade = None
                    if not subject:
                        issue('', 'Missing subject heading')
                    continue
                next_row = list(rows[index_row+1]) + [None]*3 if index_row+1 < len(rows) else [None]*3
                if not c and name_key(next_row[1] or '') == 'grade' and name_key(next_row[2] or '') == 'quiz #':
                    grade = None
                    continue
                if grade_key(b):
                    grade = grade_key(b)
                if not c or name_key(c) == 'quiz #':
                    if not c and any(cells[col] for col in [7,8]) and grade and subject:
                        # Empty grade placeholders are valid only when status cells are empty.
                        issue('', 'Student statuses exist without a quiz code')
                    continue
                if not re.search(r'\d', c) or '-' not in c or not subject or not grade:
                    issue('', 'Quiz code, subject or grade is invalid')
                    continue
                review.quiz_rows += 1
                # Formula caches can be missing/stale; only literal source status lists are accepted.
                source_row = list(formula_rows[index_row]) + [None]*9
                if any(isinstance(source_row[col], str) and source_row[col].startswith('=') for col in [2,7,8]):
                    issue('', 'Code/status cells must be literal values, not formulas')
                    continue
                for status, col in [('Pending',7), ('Low Score',8)]:
                    cell = cells[col]
                    if cell is None or not str(cell).strip():
                        continue
                    cell_key = (term, week, name_key(subject), grade, c, status, ' '.join(str(cell).strip().split()))
                    correction = cell_corrections.get(cell_key)
                    if correction is not None:
                        direct_numbers, action = correction
                        resolved = [(number, str(cell)) for number in direct_numbers]
                        if action == 'Map students with review':
                            ambiguous = [label for label in label_parts(cell) if len(index.get((grade,name_key(label)),set())) > 1]
                            candidates = set().union(*(index[(grade,name_key(label))] for label in ambiguous)) if ambiguous else set()
                            issue(', '.join(ambiguous), 'Source names omitted by administrator; pending review', candidates)
                    else:
                        labels = []
                        for raw_label in label_parts(cell):
                            parts = raw_label.split('. ')
                            if len(parts) > 1 and all(len(index.get((grade, name_key(part)), set())) == 1 for part in parts):
                                labels.extend(parts)
                            else:
                                labels.append(raw_label)
                        resolved = []
                        for label in labels:
                            candidate = overrides.get((grade, name_key(subject), name_key(label))) or overrides.get((grade, '', name_key(label)))
                            candidates = {candidate} if candidate else index.get((grade, name_key(label)), set())
                            if not candidates and len(label.split()) > 1:
                                candidates = full_tokens.get((grade, tuple(sorted(name_key(label).split()))), set())
                            if len(candidates) != 1:
                                issue(label, 'Ambiguous student name' if candidates else 'No exact student identity', candidates)
                                continue
                            resolved.append((next(iter(candidates)), label))
                    for number, label in resolved:
                        key = (number, subject, code, week)
                        if key in seen:
                            issue(label, 'Conflicting states' if seen[key] != status else 'Duplicate quiz entry', [number])
                            continue
                        seen[key] = status
                        student = by_number[number]
                        review.records.append(dict(number=number,name=student['Student Name'],group=student['Group'],subject=subject,code=code,week=week,status=status))
        if not review.quiz_rows:
            review.issues.append({'Week':'', 'Row':0, 'Subject':'', 'Grade':'', 'Quiz Code':'', 'Report Name':'', 'Reason':'No weekly quizzes found', 'Candidate Numbers':''})
        return review
    finally:
        book.close()
        formulas.close()
