"""One storage choice shared by student, teacher and admin processes."""
import json
import os
from pathlib import Path
from functools import lru_cache
from storage import LocalStore


def _cloud_setting(name, default=None):
    import streamlit as st
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, KeyError):
        return default


def settings():
    path = Path(__file__).with_name('settings.json')
    config = json.loads(path.read_text()) if path.exists() else {}
    local_path = Path(__file__).with_name('settings.local.json')
    if local_path.exists():
        config.update(json.loads(local_path.read_text()))
    if os.environ.get('SABIS_STORAGE') == 'local':
        return ('local', '', os.environ.get('SABIS_DATA_DIR', str(Path(__file__).parent / 'private_data')), None)
    return ((os.environ.get('SABIS_STORAGE') or _cloud_setting('SABIS_STORAGE', config.get('storage', 'local'))),
            (os.environ.get('SABIS_SPREADSHEET_ID') or _cloud_setting('SABIS_SPREADSHEET_ID', config.get('spreadsheet_id', ''))),
            os.environ.get('SABIS_DATA_DIR', str(Path(__file__).parent / 'private_data')),
            os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', config.get('credentials_path')),
            (os.environ.get('QUIZ_SOURCE_FOLDER_ID') or _cloud_setting('QUIZ_SOURCE_FOLDER_ID', config.get('source_folder_id', ''))))


@lru_cache(maxsize=4)
def _store(backend, spreadsheet_id, directory, credentials_path=None, source_folder_id=None):
    if backend == 'local':
        return LocalStore(directory)
    if backend == 'google_sheets':
        from sheets_storage import GoogleSheetsStore
        return GoogleSheetsStore(spreadsheet_id, directory, credentials_path=credentials_path)
    if backend == 'google_drive_folder':
        from drive_source import DriveWorkbookStore
        return DriveWorkbookStore(spreadsheet_id, source_folder_id, directory, credentials_path=credentials_path)
    raise OSError('Unsupported SABIS_STORAGE backend.')


def get_store():
    return _store(*settings())
