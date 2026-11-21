import io
import os
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from streamlit.testing.v1 import AppTest
from data_pipeline import read_roster, parse_workbook, ValidationError
from storage import LocalStore
from reports import report_text, report_pdf

ROSTER = b'Student Number,Student Name,Group\n001,Demo Alpha,G7\n002,Demo Beta,G7\n003,Demo Gamma,G8\n'


def workbook(rows=None, name='Week 12'):
    rows = rows if rows is not None else [dict(**{'Student Name': 'Demo Alpha', 'Group': 'G7', 'Subject': 'Mathematics', 'Quiz Code': '2627-DEMO-M-Periodic', 'Status': 'Pending'})]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name=name, index=False)
    return output.getvalue()


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.roster = read_roster(ROSTER)

    def test_exact_identity_and_code(self):
        records = parse_workbook(workbook(), self.roster)
        self.assertEqual(records[0]['number'], '001')
        self.assertEqual(records[0]['code'], '2627-DEMO-M-Periodic')
        self.assertEqual(records[0]['week'], 'Week 12')

    def test_reject_unexpected_unknown_duplicate(self):
        for content in [workbook(name='Unexpected'), workbook([{'Student Name':'Unknown','Group':'G7','Subject':'Math','Quiz Code':'X','Status':'Pending'}]), workbook([{'Student Name':'Demo Alpha','Group':'G7','Subject':'Math','Quiz Code':'X','Status':'Pending'}]*2)]:
            with self.assertRaises(ValidationError):
                parse_workbook(content, self.roster)
        with self.assertRaises(ValidationError):
            read_roster(ROSTER + b'001,Other Demo,G8\n')

    def test_class_list_excel(self):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame([['G7A',''],['ID#','Student Name'],['001','Demo Alpha']]).to_excel(writer, sheet_name='Students Lists', header=False, index=False)
        self.assertEqual(read_roster(output.getvalue())[0]['Student Number'], '001')
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame([['G7A',''],['ID#','Student Name'],['','Demo Alpha']]).to_excel(writer, sheet_name='Students Lists', header=False, index=False)
        with self.assertRaisesRegex(ValidationError, 'incomplete identities'):
            read_roster(output.getvalue())

    def test_authorized_missing_numbers(self):
        roster = read_roster(ROSTER + b',Demo Delta,G7\n,Demo Epsilon,G7\n,Boys,G7\n,Total,G7\n', allow_missing_numbers=True)
        self.assertEqual(len(roster), 5)
        rows = [
            {'Student Name':'Demo Alpha','Group':'G7','Subject':'Math','Quiz Code':'X','Status':'Pending'},
            {'Student Name':'Demo Delta','Group':'G7','Subject':'Math','Quiz Code':'X','Status':'Pending'},
            {'Student Name':'Demo Epsilon','Group':'G7','Subject':'Math','Quiz Code':'X','Status':'Low Score'}]
        records = parse_workbook(workbook(rows), roster)
        self.assertEqual([r['number'] for r in records], ['001'])
        with self.assertRaises(ValidationError):
            read_roster(ROSTER + b'001,Demo Delta,G7\n', allow_missing_numbers=True)

    def test_snapshot_atomic_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LocalStore(directory)
            initial = store.publish(parse_workbook(workbook(), self.roster), self.roster)
            with patch('storage.os.replace', side_effect=OSError('disk error')):
                with self.assertRaises(OSError):
                    store.publish([], self.roster)
            self.assertEqual(store.read(), initial)

    def test_legacy_adapter(self):
        output = io.BytesIO()
        rows = [['']*2 for _ in range(17)]
        rows[16] = ['Student Name', 'Final Score']
        rows.append(['Demo Alpha', '60'])
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(rows).to_excel(writer, sheet_name='quiz', index=False, header=False)
            pd.DataFrame([dict(Sheet='quiz', **{'Quiz Code':'Exact-Code','Subject':'Math','Week':'Week 12','Group':'G7'})]).to_excel(writer, sheet_name='Quiz Metadata', index=False)
        records = parse_workbook(output.getvalue(), self.roster)
        self.assertEqual([(r['number'], r['status']) for r in records], [('001','Low Score'),('002','Pending')])

    def test_pdf_and_text(self):
        records = parse_workbook(workbook(), self.roster)
        text = report_text(self.roster[0], records, '2026-11-20T19:35:00-05:00')
        self.assertIn('Week 12', text)
        self.assertIn('America/Panama', text)
        self.assertTrue(report_pdf(self.roster[0], records, '2026-11-20T19:35:00-05:00').startswith(b'%PDF'))

    def test_public_and_protected_entries(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'SABIS_DATA_DIR':directory, 'SABIS_STORAGE':'local'}):
            LocalStore().publish(parse_workbook(workbook(), self.roster), self.roster)
            app = AppTest.from_string('from public_view import run\nrun()').run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.file_uploader) if hasattr(app, 'file_uploader') else len(app.get('file_uploader')), 0)
            self.assertNotIn('Demo Alpha', str(app))
            app.text_input[0].set_value('001')
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertNotIn('Demo Beta', str(app))
            self.assertEqual([x.label for x in app.selectbox], ['Subject','Status'])
            app.selectbox[1].select('Low Score').run()
            self.assertFalse(app.exception)
            for entry in ['admin.py', 'teacher.py', 'legacy_builder.py']:
                protected = AppTest.from_file(entry).run()
                self.assertFalse(protected.exception)
                self.assertEqual(len(protected.get('file_uploader')), 0)


if __name__ == '__main__':
    unittest.main()
