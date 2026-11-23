import hashlib
import tempfile
import unittest
from unittest.mock import Mock,patch
from drive_source import DriveWorkbookStore,digest
from data_pipeline import ValidationError
from sheets_storage import SheetsConnectionError

ROSTER=[{'Student Number':'001','Student Name':'Alpha, Demo','Group':'G7A'}]
FILE={'id':'file-id','name':'source.xlsx','mimeType':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','size':'4','md5Checksum':hashlib.md5(b'demo').hexdigest()}
PROPS={name:{'sheetId':i,'gridProperties':{'rowCount':100,'columnCount':7}} for i,name in enumerate(['Students','Quizzes','Publication'])}
TABLES={'Students':[['Student Number','Student Name','Group'],['001','Alpha, Demo','G7A']],'Quizzes':[['Student Number','Student Name','Group','Subject','Quiz Code','Week','Status'],['001','Alpha, Demo','G7A','Math','DEMO','Week 12','Pending']]}


class DriveSourceTests(unittest.TestCase):
    def store(self,directory):return DriveWorkbookStore('sheet-id','folder-id',directory,session=Mock(),ttl=0)

    def test_empty_or_ambiguous_folder_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.store(directory)
            for files in [[],[FILE,FILE]]:
                with patch.object(store,'_request') as req:
                    req.return_value.json.return_value={'files':files}
                    with self.assertRaises(ValidationError):store._single_file()

    def test_invalid_import_cannot_write_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.store(directory)
            with patch.object(store,'_single_file',return_value=FILE),patch.object(store,'_tables',return_value=(PROPS,TABLES,ROSTER,[],{},[])),patch.object(store,'_request') as request,patch('drive_source.review_weekly_workbook') as review:
                request.return_value.content=b'demo';review.return_value.require_valid.side_effect=ValidationError('Needs identity review')
                with self.assertRaises(ValidationError):store._fetch()
                self.assertEqual(request.call_count,1)
                self.assertEqual(request.call_args.args[0],'GET')

    def test_verified_import_publishes_in_one_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.store(directory)
            with patch.object(store,'_single_file',return_value=FILE),patch.object(store,'_tables',return_value=(PROPS,TABLES,ROSTER,[],{},[])),patch.object(store,'_request') as request,patch('drive_source.review_weekly_workbook') as review:
                request.return_value.content=b'demo';review.return_value.require_valid.return_value=[];review.return_value.quiz_rows=1
                records,roster=store._fetch()
                self.assertEqual(records,[])
                posts=[call for call in request.call_args_list if call.args[0]=='POST']
                self.assertEqual(len(posts),1)
                batch=posts[0].kwargs['json']['requests']
                self.assertEqual(len(batch),6)
                writes=[r['updateCells'] for r in batch if 'updateCells' in r]
                self.assertEqual({r['range']['sheetId'] for r in writes},{p['sheetId'] for p in PROPS.values()})
                student_write=next(r for r in writes if r['range']['sheetId']==PROPS['Students']['sheetId'])
                self.assertEqual(student_write['rows'][1]['values'][0]['userEnteredValue']['stringValue'],'001')
                self.assertTrue(store.publication_time)

    def test_file_changed_during_import_prevents_write(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.store(directory)
            with patch.object(store,'_single_file',side_effect=[FILE,{**FILE,'id':'new-file'}]),patch.object(store,'_tables',return_value=(PROPS,TABLES,ROSTER,[],{},[])),patch.object(store,'_request') as request,patch('drive_source.review_weekly_workbook') as review:
                request.return_value.content=b'demo';review.return_value.require_valid.return_value=[]
                with self.assertRaises(ValidationError):store._fetch()
                self.assertEqual(request.call_count,1)

    def test_restart_falls_back_to_durable_published_sheet(self):
        with tempfile.TemporaryDirectory() as directory:
            store=self.store(directory)
            with patch.object(store,'_single_file',side_effect=SheetsConnectionError('No file')),patch.object(store,'_tables',return_value=(PROPS,TABLES,ROSTER,[],{},[])):
                snapshot=store.read()
                self.assertTrue(snapshot['source_warning'])
                self.assertEqual(snapshot['records'][0]['number'],'001')


if __name__=='__main__':unittest.main()
