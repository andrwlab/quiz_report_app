import io
import tempfile
import unittest
from openpyxl import Workbook
from data_pipeline import read_roster, ValidationError
from weekly_import import review_weekly_workbook
from drive_source import QUIZ_HEADERS, DriveWorkbookStore
from test_weekly_import import workbook, ROSTER
from test_drive_source import TABLES


class RosterRefreshTests(unittest.TestCase):
    def test_known_auxiliary_roster_tabs_only(self):
        book=Workbook();sheet=book.active;sheet.title='Students Lists'
        sheet.append(['G7A']);sheet.append(['ID#','Student Name']);sheet.append(['001','Alpha, Demo'])
        for title in ['ACC SP-X-Support','Watch List-T2']:book.create_sheet(title).append(['Notes'])
        out=io.BytesIO();book.save(out)
        self.assertEqual(len(read_roster(out.getvalue())),1)
        book.create_sheet('Unexpected').append(['Notes']);out=io.BytesIO();book.save(out)
        with self.assertRaises(ValidationError):read_roster(out.getvalue())

    def test_family_first_without_comma_still_requires_unique_given(self):
        roster=[{'Student Number':'001','Student Name':'Alpha Demo','Group':'G7A'}]
        self.assertEqual(review_weekly_workbook(workbook('Demo',None),roster).require_valid()[0]['number'],'001')
        roster.append({'Student Number':'002','Student Name':'Beta Demo','Group':'G7A'})
        with self.assertRaises(ValidationError):review_weekly_workbook(workbook('Demo',None),roster).require_valid()

    def test_note_and_partial_cell_corrections_are_exact_and_term_scoped(self):
        base={'Term':'T1','Week':'Week 12','Subject':'Math','Grade':'G7','Quiz Code':'2627-Exact - Code','Status':'Low Score','Source Text':'An explanatory note','Student Numbers':'','Action':'Ignore note'}
        content=workbook('Demo','An explanatory note')
        review=review_weekly_workbook(content,ROSTER,corrections=[base],source_term='T1')
        self.assertEqual([r['number'] for r in review.require_valid()],['001'])
        with self.assertRaises(ValidationError):review_weekly_workbook(content,ROSTER,corrections=[base],source_term='T2').require_valid()
        mapped={**base,'Source Text':'Invalid, Other','Student Numbers':'002','Action':'Map students'}
        review=review_weekly_workbook(workbook('Demo','Invalid, Other'),ROSTER,corrections=[mapped],source_term='T1')
        self.assertEqual([r['number'] for r in review.require_valid()],['001','002'])
        with self.assertRaises(ValidationError):review_weekly_workbook(content,ROSTER,corrections=[{**base,'Grade':'Unknown'}])
        with self.assertRaises(ValidationError):review_weekly_workbook(content,ROSTER,corrections=[{**mapped,'Student Numbers':'999'}])

    def test_restart_with_empty_published_quizzes_uses_active_roster(self):
        with tempfile.TemporaryDirectory() as directory:
            store=DriveWorkbookStore('sheet-id','folder-id',directory)
            staged=[{'Student Number':'002','Student Name':'Beta, Other','Group':'G7A'}]
            tables={**TABLES,'Quizzes':[QUIZ_HEADERS]}
            records,roster=store._published(tables,staged,{'Status':'Published','Source fingerprint':'valid'})
            self.assertEqual(records,[])
            self.assertEqual(roster[0]['Student Number'],'001')
