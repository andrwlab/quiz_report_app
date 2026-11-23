import hashlib
import tempfile
import unittest
from unittest.mock import patch
from weekly_import import review_weekly_workbook
from sheets_storage import GoogleSheetsStore, publication_metadata, SheetsConnectionError, source_snapshot
from presentation import header, render_student
from test_weekly_import import workbook, ROSTER
from test_drive_source import TABLES, PROPS
from drive_source import DriveWorkbookStore

STAMP='2026-11-23T15:00:00-05:00'


class PartialReviewTests(unittest.TestCase):
    def test_valid_names_publish_while_unknown_names_are_reviewed(self):
        review=review_weekly_workbook(workbook('Unknown, Demo','Other'),ROSTER)
        self.assertEqual(len(review.publication_records()),2)
        self.assertEqual(review.review_scope(ROSTER),dict(review_count=1,review_students=['001','002'],review_all=False))

    def test_conflicting_statuses_never_choose_a_winner(self):
        review=review_weekly_workbook(workbook('Demo, Other','Demo'),ROSTER)
        self.assertEqual([r['number'] for r in review.publication_records()],['002'])
        self.assertEqual(review.review_scope(ROSTER)['review_students'],['001'])

    def test_ambiguous_names_and_confirmed_omissions_keep_candidate_scope(self):
        roster=ROSTER+[{'Student Number':'003','Student Name':'Gamma, Demo','Group':'G7A'}]
        review=review_weekly_workbook(workbook('Demo','Other'),roster)
        self.assertEqual([r['number'] for r in review.publication_records()],['002'])
        self.assertEqual(review.review_scope(roster)['review_students'],['001','003'])
        correction={'Term':'T1','Week':'Week 12','Subject':'Math','Grade':'G7','Quiz Code':'2627-Exact - Code','Status':'Pending','Source Text':'Demo, Other','Student Numbers':'002','Action':'Map students with review'}
        review=review_weekly_workbook(workbook('Demo, Other',None),roster,corrections=[correction],source_term='T1')
        self.assertEqual([r['number'] for r in review.publication_records()],['002'])
        self.assertEqual(review.review_scope(roster)['review_students'],['001','003'])

    def test_partial_import_writes_records_and_review_metadata_together(self):
        content=workbook('Unknown, Demo','Other')
        source={'id':'source-file','name':'Report-T1.xlsx','size':str(len(content)),'md5Checksum':hashlib.md5(content).hexdigest()}
        props={**PROPS,'Import Review':{'sheetId':5,'gridProperties':{'rowCount':100,'columnCount':10}}}
        with tempfile.TemporaryDirectory() as directory:
            store=DriveWorkbookStore('sheet-id','folder-id',directory)
            with patch.object(store,'_single_file',return_value=source),patch.object(store,'_tables',return_value=(props,TABLES,ROSTER,[],{},[])),patch.object(store,'_request') as request:
                request.return_value.content=content
                records,_=store._fetch()
                self.assertEqual(len(records),2)
                posts=[c for c in request.call_args_list if c.args[0]=='POST']
                self.assertEqual(len(posts),1)
                writes=[r['updateCells'] for r in posts[0].kwargs['json']['requests'] if 'updateCells' in r]
                self.assertEqual(len(writes),4)
                publication=next(r for r in writes if r['range']['sheetId']==PROPS['Publication']['sheetId'])
                values=[[v['userEnteredValue']['stringValue'] for v in row['values']] for row in publication['rows']]
                self.assertIn(['Review count','1'],values)
                self.assertEqual(store._publication_meta['review_students'],['001','002'])

    def test_header_indicator_is_conditional_and_below_update_date(self):
        with patch('presentation.st.markdown') as markdown:
            header({'updated_at':STAMP,'review_count':1})
            html=''.join(call.args[0] for call in markdown.call_args_list)
            self.assertIn('role="status">Pending review',html)
            self.assertLess(html.index('Data last updated'),html.index('role="status">Pending review'))
            self.assertIn('color:#ED6D83',html)
        with patch('presentation.st.markdown') as markdown:
            header({'updated_at':STAMP,'review_count':0})
            self.assertNotIn('role="status">Pending review',''.join(call.args[0] for call in markdown.call_args_list))

    def test_review_student_cannot_appear_up_to_date_or_have_zero_badges(self):
        with patch('presentation.st.html') as html:
            render_student(ROSTER[0],[],STAMP,all_records=[],pending_review=True)
            markup=html.call_args.args[0]
            self.assertIn('Data pending review',markup)
            self.assertNotIn('This student is up to date',markup)
            self.assertNotIn('aria-label="Totals across all subjects"',markup)
        with patch('presentation.st.html') as html:
            render_student(ROSTER[0],[],STAMP,all_records=[])
            self.assertIn('This student is up to date',html.call_args.args[0])

    def test_review_metadata_survives_failure_restart_and_clears_when_resolved(self):
        metadata=publication_metadata([['Key','Value'],['Status','Published'],['Updated At',STAMP],['Review count','2'],['Review students','["001"]'],['Review all','false']])
        records,roster=source_snapshot(TABLES['Students'],TABLES['Quizzes'])
        with tempfile.TemporaryDirectory() as directory:
            store=GoogleSheetsStore('sheet-id',directory,ttl=0)
            def fetch():
                store._publication_meta=metadata
                return records,roster
            with patch.object(store,'_fetch',side_effect=fetch):
                self.assertEqual(store.read()['review_count'],2)
            restarted=GoogleSheetsStore('sheet-id',directory,ttl=0)
            with patch.object(restarted,'_fetch',side_effect=SheetsConnectionError('Unavailable')):
                self.assertEqual(restarted.read()['review_students'],['001'])
            metadata.update(review_count=0,review_students=[],review_all=False)
            with patch.object(store,'_fetch',side_effect=fetch):
                self.assertEqual(store.read()['review_count'],0)
