import streamlit as st
from auth import require_access
from data_pipeline import read_roster, parse_workbook, ValidationError
from storage_config import get_store, settings

st.set_page_config(page_title='Quiz Administration', page_icon='📖')
require_access('admin')
st.title('Quiz · Administration')
mode = st.radio('Workspace', ['Publish quiz status', 'Legacy report builder'])
if mode == 'Legacy report builder':
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).with_name('legacy_builder.py')), init_globals={'LEGACY_EMBEDDED': True})
    st.stop()
if settings()[0] in ('google_sheets', 'google_drive_folder'):
    st.info('The configured online source is active. Updates are validated before replacing the published data.')
    if st.button('Check source connection'):
        try:
            snapshot = get_store().read()
            if snapshot.get('source_warning'):
                st.warning('The new source could not be validated. The last successful version is still available.')
            else:
                st.success(f"Connected: {len(snapshot['roster'])} students; {len(snapshot['records'])} pending / low score quizzes.")
        except (ValueError, OSError) as error:
            st.error(str(error))
    st.stop()
st.caption('Publish a complete replacement. Validation failure keeps the last successful publication.')
roster_file = st.file_uploader('Official roster CSV or HS Class Lists Excel', type=['csv', 'xlsx'])
workbook = st.file_uploader('Quiz workbook', type=['xlsx', 'xls'])

@st.cache_data(show_spinner=False, max_entries=2, ttl=600)
def validate(workbook_bytes, roster_bytes):
    roster = read_roster(roster_bytes, allow_missing_numbers=True)
    return parse_workbook(workbook_bytes, roster), roster

if workbook and roster_file:
    try:
        records, roster = validate(workbook.getvalue(), roster_file.getvalue())
        st.success(f'Validation passed: {len(roster)} students; {len(records)} pending / low score records.')
        unresolved = [s for s in roster if not s['Student Number']]
        if unresolved:
            st.warning(f'{len(unresolved)} students are waiting for Student Numbers. Their quizzes will not be published until their IDs are supplied.')
        if st.button('Publish validated version', type='primary'):
            get_store().publish(records, roster)
            st.success('Published successfully.')
    except (ValidationError, ValueError, OSError) as error:
        st.error(str(error))
