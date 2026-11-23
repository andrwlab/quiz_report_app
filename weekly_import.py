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
        if not given or not surname:
            raise ValidationError('An official student name cannot be indexed.')
        first, family = given.split()[0], surname.split()[0]
        keys.update(name_key(key) for key in [given+' '+surname, given, first, surname, family, first+' '+family[0], first+' '+family])
        for key in keys:
            index[grade_key(student['Group']), key].add(number)
    return index


def label_parts(cell):
    """Only documented separators and score annotations; no fuzzy correction."""
    for token in re.split(r'[,;\n]+|\s+(?:and|y)\s+', str(cell), flags=re.IGNORECASE):
        token = re.sub(r'\(\s*\d*(?:\.\d+)?\s*%?\s*\)', '', token)
        token = re.sub(r'\s+incomplete\s*$', '', token, flags=re.IGNORECASE)
        token = re.sub(r'\s+\d+(?:\.\d+)?\s*%?\s*$', '', token).strip()
        if token:
            yield token


def review_weekly_workbook(content, roster, aliases=()):
    review = WorkbookReview()
    by_number = {s['Student Number']: s for s in roster if s['Student Number']}
    if len(by_number) != sum(bool(s['Student Number']) for s in roster):
        raise ValidationError('Official Student Numbers must be unique.')
    index = student_index(roster)
    overrides = {}
    for row in aliases:
        if not any(str(v).strip() for v in row.values()):
            continue
        grade, subject, label, number = [str(row.get(k, '')).strip() for k in ['Grade', 'Subject', 'Report Name', 'Student Number']]
        key = (grade_key(grade), name_key(subject), name_key(label))
        if not key[0] or not label or number not in by_number or grade_key(by_number[number]['Group']) != key[0] or key in overrides:
            raise ValidationError('An alias is invalid, duplicated or belongs to a different grade.')
        overrides[key] = number
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
                    for label in label_parts(cell):
                        candidate = overrides.get((grade, name_key(subject), name_key(label))) or overrides.get((grade, '', name_key(label)))
                        candidates = {candidate} if candidate else index.get((grade, name_key(label)), set())
                        if len(candidates) != 1:
                            issue(label, 'Ambiguous student name' if candidates else 'No exact student identity', candidates)
                            continue
                        number = next(iter(candidates))
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
