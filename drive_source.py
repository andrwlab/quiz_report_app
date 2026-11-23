"""Opt-in Drive Excel ingestion. Only validated data replaces the durable Sheet."""
import hashlib
import json
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from data_pipeline import ValidationError, read_roster
from sheets_storage import GoogleSheetsStore, SheetsConnectionError, source_snapshot
from weekly_import import review_weekly_workbook
import pandas as pd

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
QUIZ_HEADERS = ['Student Number','Student Name','Group','Subject','Quiz Code','Week','Status']


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


class DriveWorkbookStore(GoogleSheetsStore):
    # Reading uploads requires folder access; publishing requires Editor on the Sheet.
    OAUTH_SCOPES = ('https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.readonly')

    def __init__(self, spreadsheet_id, folder_id, directory=None, session=None, ttl=60, credentials_path=None):
        super().__init__(spreadsheet_id,directory,session,ttl,credentials_path)
        if not re.fullmatch(r'[A-Za-z0-9_-]+', folder_id or ''):
            raise SheetsConnectionError('Configure QUIZ_SOURCE_FOLDER_ID in server Secrets.')
        self.folder_id = folder_id
        self.publication_time = None

    def _request(self, method, url, **kwargs):
        try:
            response = self._session().request(method,url,timeout=30,**kwargs)
            if response.status_code != 200:
                raise SheetsConnectionError(f'Source service returned HTTP {response.status_code}. Check Drive API, folder Reader and spreadsheet Editor access.')
            return response
        except SheetsConnectionError:
            raise
        except Exception:
            raise SheetsConnectionError('Could not access the update source. Published data was kept.') from None

    def _single_file(self):
        response = self._request('GET','https://www.googleapis.com/drive/v3/files',params={
            'q': f"'{self.folder_id}' in parents and trashed = false",
            'fields':'nextPageToken,files(id,name,mimeType,size,md5Checksum)',
            'pageSize':100,'supportsAllDrives':'true','includeItemsFromAllDrives':'true'})
        data = response.json()
        files = [f for f in data.get('files',[]) if f.get('mimeType') == XLSX]
        if data.get('nextPageToken') or len(files) != 1:
            raise ValidationError('The update folder must contain exactly one XLSX file. Published data was kept.')
        file = files[0]
        if not file.get('md5Checksum') or int(file.get('size',0)) > 20*1024*1024:
            raise ValidationError('The source file is incomplete or exceeds 20 MB.')
        return file

    def _tables(self):
        base=f'https://sheets.googleapis.com/v4/spreadsheets/{self.spreadsheet_id}'
        metadata=self._request('GET',base,params={'fields':'sheets(properties(sheetId,title,gridProperties))'}).json()
        properties={s['properties']['title']:s['properties'] for s in metadata.get('sheets',[])}
        names=['Students','Aliases','Quizzes','Publication']
        if not all(name in properties for name in names):
            raise ValidationError('The data Sheet requires Students, Aliases, Quizzes and Publication tabs.')
        ranges=["'Students'!A1:C20000","'Aliases'!A1:D20000","'Quizzes'!A1:G100000","'Publication'!A1:B20"]
        for title, bounds in [('Roster Import','A1:C20000'),('Cell Corrections','A1:I20000')]:
            if title in properties:
                names.append(title)
                ranges.append(f"'{title}'!{bounds}")
        params=[('ranges',r) for r in ranges]+[('valueRenderOption','FORMATTED_VALUE')]
        result=self._request('GET',base+'/values:batchGet',params=params).json()
        values=result.get('valueRanges',[])
        if len(values)!=len(names):
            raise ValidationError('The data Sheet could not be read completely.')
        tables={name:value.get('values',[]) for name,value in zip(names,values)}
        if tables['Aliases'][:1] != [['Grade','Subject','Report Name','Student Number']]:
            raise ValidationError('Aliases requires Grade, Subject, Report Name, Student Number.')
        roster_rows=tables.get('Roster Import') or tables['Students']
        if roster_rows[:1] != [['Student Number','Student Name','Group']]:
            raise ValidationError('Unexpected official roster headers.')
        padded=[row+['']*(3-len(row)) for row in roster_rows[1:] if any(row)]
        roster=read_roster(pd.DataFrame(padded,columns=roster_rows[0]).to_csv(index=False).encode())
        aliases=[dict(zip(tables['Aliases'][0], row+['']*(4-len(row)))) for row in tables['Aliases'][1:] if any(row)]
        publication={row[0]:row[1] if len(row)>1 else '' for row in tables['Publication'][1:] if row}
        corrections=[]
        if 'Cell Corrections' in tables:
            correction_headers=['Term','Week','Subject','Grade','Quiz Code','Status','Source Text','Student Numbers','Action']
            if tables['Cell Corrections'][:1] != [correction_headers]:
                raise ValidationError('Unexpected Cell Corrections headers.')
            corrections=[dict(zip(correction_headers,row+['']*(9-len(row)))) for row in tables['Cell Corrections'][1:] if any(row)]
        return properties, tables, roster, aliases, publication, corrections

    def _published(self, tables, roster, publication):
        self.publication_time=publication.get('Updated At') or None
        if tables['Quizzes']==[QUIZ_HEADERS] and publication.get('Status')=='Published' and publication.get('Source fingerprint'):
            active_rows=tables['Students']
            active_roster=read_roster(pd.DataFrame([row+['']*(3-len(row)) for row in active_rows[1:] if any(row)],columns=active_rows[0]).to_csv(index=False).encode())
            return [],active_roster
        return source_snapshot(tables['Students'],tables['Quizzes'])

    def _fetch(self):
        # Complete source validation occurs before any write.
        file=self._single_file()
        properties,tables,roster,aliases,publication,corrections=self._tables()
        fingerprint=digest([file['id'],file['md5Checksum'],roster,aliases,corrections])
        if publication.get('Source fingerprint')==fingerprint:
            return self._published(tables,roster,publication)
        content=self._request('GET',f"https://www.googleapis.com/drive/v3/files/{file['id']}",params={'alt':'media','supportsAllDrives':'true'}).content
        if hashlib.md5(content).hexdigest()!=file['md5Checksum']:
            raise ValidationError('The upload changed during download. Waiting for a complete source.')
        term_match=re.search(r'(?:^|[-_ ])(T\d+)(?:\.|$)',file['name'],re.IGNORECASE)
        source_term=term_match.group(1).upper() if term_match else None
        review=review_weekly_workbook(content,roster,aliases,corrections,source_term=source_term)
        records=review.require_valid()
        # Protect against a teacher replacing the file or roster during validation.
        latest=self._single_file()
        _,_,latest_roster,latest_aliases,_,latest_corrections=self._tables()
        if digest([latest['id'],latest['md5Checksum'],latest_roster,latest_aliases,latest_corrections])!=fingerprint:
            raise ValidationError('Source identities or file changed during import. Waiting for a stable version.')
        updated_at=datetime.now(ZoneInfo('America/Panama')).isoformat()
        quiz_rows=[QUIZ_HEADERS]+[[r['number'],r['name'],r['group'],r['subject'],r['code'],r['week'],r['status']] for r in records]
        publication_rows=[['Key','Value'],['Status','Published'],['Updated At',updated_at],['Time Zone','America/Panama'],['Source fingerprint',fingerprint],['Source File',file['name']],['Source quiz rows',str(review.quiz_rows)]]
        requests=[]
        roster_rows=[['Student Number','Student Name','Group']]+[[s['Student Number'],s['Student Name'],s['Group']] for s in roster]
        for title,rows in [('Students',roster_rows),('Quizzes',quiz_rows),('Publication',publication_rows)]:
            prop=properties[title];grid=prop['gridProperties'];width=len(rows[0]);height=max(grid['rowCount'],len(rows))
            if height>grid['rowCount']:
                requests.append({'updateSheetProperties':{'properties':{'sheetId':prop['sheetId'],'gridProperties':{'rowCount':height}},'fields':'gridProperties.rowCount'}})
            requests.append({'repeatCell':{'range':{'sheetId':prop['sheetId'],'startRowIndex':0,'endRowIndex':height,'startColumnIndex':0,'endColumnIndex':width},'cell':{},'fields':'userEnteredValue'}})
            requests.append({'updateCells':{'range':{'sheetId':prop['sheetId'],'startRowIndex':0,'endRowIndex':len(rows),'startColumnIndex':0,'endColumnIndex':width},'rows':[{'values':[{'userEnteredValue':{'stringValue':str(v)}} for v in row]} for row in rows],'fields':'userEnteredValue'}})
        # One atomic Sheets batch: an error keeps the previous published version intact.
        self._request('POST',f'https://sheets.googleapis.com/v4/spreadsheets/{self.spreadsheet_id}:batchUpdate',json={'requests':requests})
        self.publication_time=updated_at
        return records,roster

    def read(self):
        try:
            snapshot=super().read()
        except SheetsConnectionError:
            # After a cloud restart the durable Sheet still contains the last valid version.
            _,tables,roster,_,publication,_=self._tables()
            records,roster=self._published(tables,roster,publication)
            snapshot={**self.local.publish(records,roster),'source_warning':True}
            self._cached=snapshot
            self._checked_at=time.monotonic()
        if self.publication_time:
            try:
                datetime.fromisoformat(self.publication_time)
            except ValueError:
                raise ValidationError('Publication timestamp is invalid.') from None
            return {**snapshot,'updated_at':self.publication_time}
        return snapshot
