"""Strict import boundary: no fuzzy identity matching or invented quiz metadata."""
import io
import re
import unicodedata
import pandas as pd


class ValidationError(ValueError):
    pass


def normalized(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value)).casefold().split())


# These labels are class-list summaries/legend entries, not student identities.
ROSTER_ANNOTATIONS = {'boys', 'girls', 'total', 'new student', 'aac spanish', 'x english'}


def read_roster(content, *, allow_missing_numbers=False):
    if content[:2] == b'PK' or content[:4] == bytes.fromhex('D0CF11E0'):
        sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, header=None, dtype=str, keep_default_na=False)
        rows = []
        for sheet, raw in sheets.items():
            if sheet != 'Students Lists' and (sheet == 'ACC SP-X-Support' or re.fullmatch(r'Watch List-T\d+', sheet)):
                continue
            if len(raw) < 2:
                raise ValidationError(f'Unexpected official roster sheet: {sheet}')
            blocks = [c for c in range(len(raw.columns) - 1) if raw.iloc[1, c] == 'ID#' and raw.iloc[1, c + 1] == 'Student Name']
            if not blocks:
                raise ValidationError(f'Unrecognized class-list layout: {sheet}')
            for c in blocks:
                group = str(raw.iloc[0, c]).strip()
                if not re.fullmatch(r'G\d+[A-Z]?', group):
                    raise ValidationError(f'Invalid group heading: {group}')
                for _, row in raw.iloc[2:].iterrows():
                    number, name = str(row.iloc[c]).strip(), str(row.iloc[c + 1]).strip()
                    if not number and not name:
                        continue
                    rows.append({'Student Number': number, 'Student Name': name, 'Group': group})
        df = pd.DataFrame(rows)
    else:
        df = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
    required = ['Student Number', 'Student Name', 'Group']
    if not set(required) <= set(df.columns):
        raise ValidationError('Official roster requires: ' + ', '.join(required))
    df = df[required].apply(lambda col: col.str.strip())
    annotation = df.apply(lambda r: not r['Student Number'] and normalized(r['Student Name']) in ROSTER_ANNOTATIONS, axis=1)
    df = df[~annotation].copy()
    if df.empty:
        raise ValidationError('Official roster is empty.')
    required_values = required[1:] if allow_missing_numbers else required
    incomplete = df[(df[required_values] == '').any(axis=1)]
    if not incomplete.empty:
        counts = incomplete.groupby('Group').size().to_dict()
        raise ValidationError(f'Official roster has {len(incomplete)} incomplete identities (missing number/name/group). By group: {counts}. Correct the source file; no IDs are inferred.')
    if df.loc[df['Student Number'] != '', 'Student Number'].duplicated().any() or df.apply(lambda r: (normalized(r['Student Name']), normalized(r['Group'])), axis=1).duplicated().any():
        raise ValidationError('Duplicate identity in official roster.')
    return df.to_dict('records')


def parse_workbook(content, roster):
    """Weekly sheets with explicit statuses; legacy exports use a metadata sheet."""
    sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, header=None, dtype=str, keep_default_na=False)
    issues, records, seen = [], [], set()
    identities = {(normalized(s['Student Name']), normalized(s['Group'])): s for s in roster}
    by_number = {s['Student Number']: s for s in roster}
    metadata = None
    if 'Quiz Metadata' in sheets:
        metadata = pd.read_excel(io.BytesIO(content), sheet_name='Quiz Metadata', dtype=str, keep_default_na=False)
        if not {'Sheet', 'Quiz Code', 'Subject', 'Week', 'Group'} <= set(metadata.columns):
            raise ValidationError('Quiz Metadata requires Sheet, Quiz Code, Subject, Week, Group.')
        if metadata['Sheet'].duplicated().any():
            raise ValidationError('Duplicate metadata sheet mapping.')
        unknown = set(metadata['Sheet']) - (set(sheets) - {'Quiz Metadata'})
        if unknown:
            raise ValidationError('Metadata references nonexistent sheets.')

    def add(name, group, subject, code, week, status, number=''):
        student = identities.get((normalized(name), normalized(group)))
        if not student or (number and by_number.get(str(number)) != student):
            issues.append(f'Unidentified or mismatched student: {name} / {group}')
            return
        if not all(str(x).strip() for x in (subject, code, week)) or not re.fullmatch(r'Week\s+\d+', week):
            issues.append(f'Missing or invalid quiz metadata: {code}')
            return
        if status not in ('Pending', 'Low Score', 'Completed'):
            issues.append(f'Unexpected status: {status}')
            return
        key = (normalized(student['Student Name']), normalized(student['Group']), subject, code, week)
        if key in seen:
            issues.append(f'Duplicate quiz record: {code} / {name}')
            return
        seen.add(key)
        if status != 'Completed' and student['Student Number']:
            records.append(dict(number=student['Student Number'], name=student['Student Name'], group=student['Group'], subject=subject, code=code, week=week, status=status))

    for sheet, raw in sheets.items():
        if sheet == 'Quiz Metadata':
            continue
        if re.fullmatch(r'Week\s+\d+', sheet):
            table = pd.read_excel(io.BytesIO(content), sheet_name=sheet, dtype=str, keep_default_na=False)
            required = {'Student Name', 'Group', 'Subject', 'Quiz Code', 'Status'}
            if not required <= set(table.columns) or table.empty:
                issues.append(f'{sheet}: missing columns or empty sheet')
                continue
            for row in table.to_dict('records'):
                add(row['Student Name'], row['Group'], row['Subject'], row['Quiz Code'], sheet, row['Status'], row.get('Student Number', ''))
        elif metadata is not None and sheet in set(metadata['Sheet']):
            meta = metadata[metadata['Sheet'] == sheet].iloc[0]
            if len(raw) < 17 or not {'Student Name', 'Final Score'} <= set(raw.iloc[16]):
                issues.append(f'{sheet}: invalid SABIS detail header (row 17)')
                continue
            table = raw.iloc[17:].copy()
            table.columns = raw.iloc[16]
            present = set()
            for _, row in table.iterrows():
                name = row['Student Name']
                if not str(name).strip():
                    continue
                try:
                    score = float(str(row['Final Score']).rstrip('%'))
                    if not 0 <= score <= 100:
                        raise ValueError()
                except ValueError:
                    issues.append(f'{sheet}: invalid score for {name}')
                    continue
                present.add(normalized(name))
                add(name, meta['Group'], meta['Subject'], meta['Quiz Code'], meta['Week'], 'Low Score' if score < 75 else 'Completed')
            group_students = [s for s in roster if normalized(s['Group']) == normalized(meta['Group'])]
            if not group_students:
                issues.append(f'{sheet}: unknown group')
            for student in group_students:
                if normalized(student['Student Name']) not in present:
                    add(student['Student Name'], meta['Group'], meta['Subject'], meta['Quiz Code'], meta['Week'], 'Pending')
        else:
            issues.append(f'Unexpected sheet: {sheet}; explicit Quiz Metadata mapping required.')
    if not seen:
        issues.append('No valid quiz records.')
    if issues:
        raise ValidationError('\n'.join(issues))
    return records
