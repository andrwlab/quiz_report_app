"""Run locally after configuring Google credentials. Prints no student identities."""
from storage_config import get_store, settings

if __name__ == '__main__':
    try:
        if settings()[0] != 'google_sheets':
            raise OSError('SABIS_STORAGE must be google_sheets to check this connection.')
        snapshot = get_store().read()
        if snapshot.get('source_warning'):
            raise OSError('Google Sheets could not be read or validated. The previous snapshot is still available.')
        print(f"Connected: {len(snapshot['roster'])} students; {len(snapshot['records'])} quizzes.")
        print('Last successful update:', snapshot['updated_at'])
    except (ValueError, OSError) as error:
        print(str(error))
        raise SystemExit(1)
