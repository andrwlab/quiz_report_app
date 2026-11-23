"""Private, read-only Sheets source; publish only fully validated local snapshots."""
import hashlib
import json
import re
import threading
import time
from pathlib import Path

import pandas as pd

from data_pipeline import ValidationError, normalized, read_roster
from storage import LocalStore


class SheetsConnectionError(OSError):
    pass


def source_snapshot(student_rows, quiz_rows, *, allow_empty=False):
    """Validate a complete source read. Numeric weeks become Week N, codes stay literal."""
    def table(rows, columns, title):
        if not rows or rows[0] != columns:
            raise ValidationError(f'{title}: unexpected column headers.')
        result = []
        for row in rows[1:]:
            if not any(str(value).strip() for value in row):
                continue
            if len(row) > len(columns):
                raise ValidationError(f'{title}: unexpected extra cells.')
            result.append(dict(zip(columns, [str(v).strip() for v in row] + [''] * (len(columns) - len(row)))))
        return result

    students = table(student_rows, ['Student Number', 'Student Name', 'Group'], 'Students')
    csv_bytes = pd.DataFrame(students, columns=['Student Number', 'Student Name', 'Group']).to_csv(index=False).encode()
    roster = read_roster(csv_bytes, allow_missing_numbers=True)
    quizzes = table(quiz_rows, ['Student Number', 'Student Name', 'Group', 'Subject', 'Quiz Code', 'Week', 'Status'], 'Quizzes')
    if not quizzes and not allow_empty:
        raise ValidationError('Quizzes is empty; refusing to replace published data with an unfinished import.')
    by_identity = {(normalized(s['Student Name']), normalized(s['Group'])): s for s in roster}
    records, seen, issues = [], set(), []
    for index, row in enumerate(quizzes, 2):
        student = by_identity.get((normalized(row['Student Name']), normalized(row['Group'])))
        if not student or (row['Student Number'] and row['Student Number'] != student['Student Number']):
            issues.append(f'Quizzes row {index}: student identity does not match Students.')
            continue
        week = row['Week']
        if week.isdigit():
            week = 'Week ' + week
        if not row['Subject'] or not row['Quiz Code'] or not re.fullmatch(r'Week\s+\d+', week):
            issues.append(f'Quizzes row {index}: missing/invalid subject, code or week.')
            continue
        if row['Status'] not in ('Pending', 'Low Score', 'Completed'):
            issues.append(f'Quizzes row {index}: invalid status.')
            continue
        key = (normalized(student['Student Name']), normalized(student['Group']), row['Subject'], row['Quiz Code'], week)
        if key in seen:
            issues.append(f'Quizzes row {index}: duplicate quiz for the same student.')
            continue
        seen.add(key)
        if student['Student Number'] and row['Status'] != 'Completed':
            records.append(dict(number=student['Student Number'], name=student['Student Name'], group=student['Group'], subject=row['Subject'], code=row['Quiz Code'], week=week, status=row['Status']))
    if issues:
        raise ValidationError('\n'.join(issues[:20]) + (f'\n{len(issues)} errors total.' if len(issues) > 20 else ''))
    return records, roster


def publication_metadata(rows):
    values = {r[0]:r[1] if len(r)>1 else '' for r in rows[1:] if r}
    if not values or values.get('Status') != 'Published':
        return {}
    try:
        count = int(values.get('Review count', '0'))
        students = json.loads(values.get('Review students', '[]'))
        if count < 0 or not isinstance(students,list) or any(not isinstance(n,str) for n in students):
            raise ValueError()
        result = dict(review_count=count, review_students=students, review_all=values.get('Review all')=='true')
        if values.get('Updated At'):
            from datetime import datetime
            datetime.fromisoformat(values['Updated At'])
            result['updated_at'] = values['Updated At']
        return result
    except (ValueError, TypeError):
        raise ValidationError('Publication review metadata is invalid.') from None


class GoogleSheetsStore:
    OAUTH_SCOPES = ('https://www.googleapis.com/auth/spreadsheets.readonly',)

    def __init__(self, spreadsheet_id, directory=None, session=None, ttl=60, credentials_path=None):
        if not re.fullmatch(r'[A-Za-z0-9_-]+', spreadsheet_id):
            raise SheetsConnectionError('Invalid spreadsheet ID.')
        self.spreadsheet_id = spreadsheet_id
        self.local = LocalStore(Path(directory or 'private_data') / 'google_sheets' / spreadsheet_id)
        self.credentials_path = credentials_path
        self.session = session
        self.ttl = ttl
        self._checked_at = None
        self._cached = None
        self._lock = threading.Lock()
        self._publication_meta = {}

    def _session(self):
        if self.session is None:
            try:
                import google.auth
                from google.auth.transport.requests import AuthorizedSession
                scopes = list(self.OAUTH_SCOPES)
                if self.credentials_path:
                    from google.oauth2.service_account import Credentials
                    credentials = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
                else:
                    # Community Cloud stores the service account in its Secrets settings.
                    import streamlit as st
                    try:
                        account_info = dict(st.secrets['gcp_service_account'])
                    except (FileNotFoundError, KeyError):
                        account_info = None
                    if account_info:
                        from google.oauth2.service_account import Credentials
                        credentials = Credentials.from_service_account_info(account_info, scopes=scopes)
                    else:
                        credentials, _ = google.auth.default(scopes=scopes)
                self.session = AuthorizedSession(credentials, refresh_timeout=15)
            except Exception:
                raise SheetsConnectionError('Google credentials are missing or invalid. Configure gcp_service_account in Streamlit Secrets or GOOGLE_APPLICATION_CREDENTIALS on the server.') from None
        return self.session

    def _fetch(self):
        # One spreadsheets.get response for both tabs avoids mixing two separate reads.
        fields = 'sheets(properties(title),data(rowData(values(userEnteredValue))))'
        try:
            response = self._session().get(
                f'https://sheets.googleapis.com/v4/spreadsheets/{self.spreadsheet_id}',
                params=[('ranges', "'Students'!A1:C20000"), ('ranges', "'Quizzes'!A1:G100000"), ('ranges', "'Publication'!A1:B20"), ('includeGridData', 'true'), ('fields', fields)],
                timeout=20)
            if response.status_code != 200:
                raise SheetsConnectionError(f'Google Sheets returned HTTP {response.status_code}. Check Sheets API and file sharing permissions.')
            payload = response.json()
        except SheetsConnectionError:
            raise
        except Exception:
            raise SheetsConnectionError('Could not read Google Sheets. Check the server connection and credentials.') from None
        result = {}
        for sheet in payload.get('sheets', []):
            rows = []
            for block in sheet.get('data', []):
                for row in block.get('rowData', []):
                    values = []
                    for cell in row.get('values', []):
                        value = cell.get('userEnteredValue', {})
                        if 'formulaValue' in value:
                            raise ValidationError('Students and Quizzes must contain source values, not formulas.')
                        values.append(str(value.get('stringValue', value.get('numberValue', ''))))
                    rows.append(values)
            # Ignore empty trailing cells when Google returns a shorter header.
            result[sheet['properties']['title']] = rows
        self._publication_meta = publication_metadata(result.get('Publication', []))
        return source_snapshot(result.get('Students', []), result.get('Quizzes', []), allow_empty=bool(self._publication_meta))

    def read(self):
        with self._lock:
            now = time.monotonic()
            if self._checked_at is not None and now - self._checked_at < self.ttl:
                return self._cached
            previous = self.local.read()
            try:
                records, roster = self._fetch()
                metadata = self._publication_meta
                fingerprint = hashlib.sha256(json.dumps([records, roster, metadata], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                previous_fingerprint = None
                if previous:
                    previous_fingerprint = hashlib.sha256(json.dumps([previous['records'], previous['roster'], {k:previous[k] for k in metadata if k in previous}], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                snapshot = previous if fingerprint == previous_fingerprint else self.local.publish(records, roster, **metadata)
            except (SheetsConnectionError, ValidationError, OSError) as error:
                if not previous:
                    raise SheetsConnectionError(str(error)) from None
                snapshot = {**previous, 'source_warning': True}
            self._cached = snapshot
            self._checked_at = now
            return snapshot

    def publish(self, records, roster):
        raise SheetsConnectionError('This source is read-only. Update Students and Quizzes through ChatGPT or Google Sheets.')
