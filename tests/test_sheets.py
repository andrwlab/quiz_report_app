import copy
import tempfile
import unittest
from unittest.mock import Mock, patch
from sheets_storage import GoogleSheetsStore, SheetsConnectionError, source_snapshot
from data_pipeline import ValidationError

STUDENTS = [['Student Number','Student Name','Group'],['001','Demo Alpha','G7'],['002','Demo Beta','G7']]
QUIZZES = [['Student Number','Student Name','Group','Subject','Quiz Code','Week','Status'],['001','Demo Alpha','G7','Math','Exact-Code','12','Pending']]


def response(students=STUDENTS, quizzes=QUIZZES):
    sheets = []
    for title, rows in [('Students', students), ('Quizzes', quizzes)]:
        sheets.append({'properties':{'title':title},'data':[{'rowData':[{'values':[{'userEnteredValue':{'stringValue':value}} for value in row]} for row in rows]}]})
    return {'sheets':sheets}


class SheetsTests(unittest.TestCase):
    def test_cloud_secrets_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            store = GoogleSheetsStore('demo-id', directory)
            info = {'type':'service_account', 'client_email':'demo@example.invalid', 'private_key':'fake-test-key'}
            with patch('streamlit.secrets', {'gcp_service_account':info}), patch('google.oauth2.service_account.Credentials.from_service_account_info') as load, patch('google.auth.transport.requests.AuthorizedSession') as session, patch('google.auth.default') as default:
                result = store._session()
                load.assert_called_once_with(info, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
                session.assert_called_once_with(load.return_value, refresh_timeout=15)
                default.assert_not_called()
                self.assertIs(result, session.return_value)

    def test_validation(self):
        records, roster = source_snapshot(STUDENTS, QUIZZES)
        self.assertEqual(records[0]['week'], 'Week 12')
        self.assertEqual(records[0]['code'], 'Exact-Code')
        self.assertEqual(len(roster), 2)
        for change in ['identity','duplicate','empty','status']:
            rows = copy.deepcopy(QUIZZES)
            if change == 'identity': rows[1][0] = '999'
            if change == 'duplicate': rows.append(rows[1][:])
            if change == 'empty': rows = rows[:1]
            if change == 'status': rows[1][-1] = 'Unknown'
            with self.assertRaises(ValidationError):
                source_snapshot(STUDENTS, rows)

    def test_read_cache_unchanged_and_last_good(self):
        session = Mock()
        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = response()
        with tempfile.TemporaryDirectory() as directory:
            store = GoogleSheetsStore('demo-id', directory, session, ttl=60)
            first = store.read()
            self.assertEqual(store.read(), first)
            self.assertEqual(session.get.call_count, 1)
            store.ttl = 0
            self.assertEqual(store.read()['updated_at'], first['updated_at'])
            session.get.return_value.status_code = 403
            fallback = store.read()
            self.assertTrue(fallback['source_warning'])
            self.assertEqual(fallback['records'], first['records'])
            self.assertEqual(fallback['updated_at'], first['updated_at'])
            session.get.return_value.status_code = 200
            rows = copy.deepcopy(QUIZZES)
            rows[1][-1] = 'Low Score'
            session.get.return_value.json.return_value = response(quizzes=rows)
            updated = store.read()
            self.assertNotIn('source_warning', updated)
            self.assertEqual(updated['records'][0]['status'], 'Low Score')

    def test_invalid_source_does_not_replace_snapshot(self):
        session = Mock()
        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = response()
        with tempfile.TemporaryDirectory() as directory:
            store = GoogleSheetsStore('demo-id', directory, session, ttl=0)
            first = store.read()
            session.get.return_value.json.return_value = response(quizzes=QUIZZES[:1])
            self.assertTrue(store.read()['source_warning'])
            self.assertEqual(store.local.read(), first)

    def test_connection_failure_without_previous(self):
        session = Mock()
        session.get.return_value.status_code = 403
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SheetsConnectionError):
                GoogleSheetsStore('demo-id', directory, session).read()

    def test_formula_source_rejected(self):
        payload = response()
        payload['sheets'][0]['data'][0]['rowData'][1]['values'][0] = {'userEnteredValue':{'formulaValue':'=1'}}
        session = Mock()
        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = payload
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SheetsConnectionError):
                GoogleSheetsStore('demo-id', directory, session).read()


if __name__ == '__main__':
    unittest.main()
