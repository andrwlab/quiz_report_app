import io
import unittest
from openpyxl import Workbook
from data_pipeline import ValidationError
from weekly_import import review_weekly_workbook

ROSTER = [{'Student Number':'001','Student Name':'Alpha, Demo','Group':'G7A'}, {'Student Number':'002','Student Name':'Beta, Other','Group':'G7A'}]


def workbook(pending='Demo', low='Other', code='2627-Exact - Code'):
    book=Workbook();sheet=book.active;sheet.title='Week 12'
    sheet.append(['Weekly report'])
    sheet.append(['Math',None,None,None,None,None,None,'Teacher Follow-Up'])
    sheet.append(['Teacher','Grade','Quiz #','# of students','# completed','completion','average score','No Attempts','Low Scores'])
    sheet.append(['Demo Teacher','G7',code,2,1,.5,80,pending,low])
    scratch=book.create_sheet('Hoja1');scratch.append(['Ignored non-weekly data'])
    out=io.BytesIO();book.save(out);return out.getvalue()


class WeeklyImportTests(unittest.TestCase):
    def test_exact_identity_scores_and_code(self):
        review=review_weekly_workbook(workbook('Demo (0%)','Other 64%','  2627-Literal-Code  '),ROSTER)
        self.assertFalse(review.issues)
        self.assertEqual([(r['number'],r['status']) for r in review.records],[('001','Pending'),('002','Low Score')])
        self.assertEqual(review.records[0]['code'],'  2627-Literal-Code  ')
        self.assertEqual(review.records[0]['week'],'Week 12')
        self.assertEqual(review.ignored_sheets,['Hoja1'])

    def test_ambiguity_requires_explicit_alias(self):
        roster=ROSTER+[{'Student Number':'003','Student Name':'Gamma, Demo','Group':'G7A'}]
        review=review_weekly_workbook(workbook(),roster)
        with self.assertRaises(ValidationError):review.require_valid()
        aliases=[{'Grade':'G7','Subject':'Math','Report Name':'Demo','Student Number':'003'}]
        review=review_weekly_workbook(workbook(),roster,aliases)
        self.assertFalse(review.issues)
        self.assertEqual(review.records[0]['number'],'003')

    def test_missing_identity_conflicts_formulas_and_empty_import(self):
        for content in [workbook('Unknown'),workbook('Demo','Demo'),workbook('=A1'),workbook('Demo',None,None)]:
            with self.assertRaises(ValidationError):review_weekly_workbook(content,ROSTER).require_valid()

    def test_all_current_requires_actual_quizzes(self):
        review=review_weekly_workbook(workbook(None,None),ROSTER)
        self.assertEqual(review.require_valid(),[])
        self.assertEqual(review.quiz_rows,1)

    def test_bad_alias_cannot_assign_another_grade(self):
        alias=[{'Grade':'G8','Subject':'','Report Name':'Unknown','Student Number':'001'}]
        with self.assertRaises(ValidationError):review_weekly_workbook(workbook('Unknown'),ROSTER,alias)


if __name__=='__main__':unittest.main()
