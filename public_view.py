import logging
import streamlit as st
from storage_config import get_store
from presentation import header, render_student


def run(teacher=False):
    try:
        snapshot = get_store().read()
    except (ValueError, OSError) as error:
        logging.getLogger(__name__).error('SABIS_CONNECTION_ERROR: %s', error)
        st.error('Published data is temporarily unavailable. The administrator must check the Google Sheets connection.')
        return
    header(snapshot)
    if snapshot and snapshot.get('source_warning'):
        st.caption('Showing the last successful update. New data is temporarily unavailable.')
    if not snapshot:
        st.info('No validated data has been published yet.')
        return
    if teacher:
        st.caption('Teacher view · Search within a selected group')
        group = st.selectbox('Group', ['Choose a group'] + sorted({s['Group'] for s in snapshot['roster']}))
        query = st.text_input('Name or Student Number', placeholder='Search this group').strip()
        candidates = [s for s in snapshot['roster'] if s['Group'] == group and (not query or query.casefold() in s['Student Name'].casefold() or query == s['Student Number'])]
    else:
        with st.form('student_search'):
            search_field, search_action = st.columns([5, 1], gap='small')
            with search_field:
                query = st.text_input('Student Number', placeholder='Enter your Student Number', autocomplete='off', label_visibility='collapsed').strip()
            with search_action:
                submitted = st.form_submit_button('Search', type='primary', use_container_width=True)
        if submitted:
            st.session_state['student_query'] = query
        active_query = st.session_state.get('student_query', '')
        # Exact identity lookup only; no roster or name suggestions in the student client.
        candidates = [s for s in snapshot['roster'] if s['Student Number'] == active_query] if active_query else []
        if not active_query:
            return
        if not candidates:
            st.info('No matching student. Check your Student Number.')
            return
    numbers = {s['Student Number'] for s in candidates}
    relevant = [r for r in snapshot['records'] if r['number'] in numbers]
    columns = st.columns(2)
    subject = columns[0].selectbox('Subject', ['All'] + sorted({r['subject'] for r in relevant}))
    status = columns[1].selectbox('Status', ['All', 'Pending', 'Low Score'])
    filtered = [r for r in relevant if (subject == 'All' or r['subject'] == subject) and (status == 'All' or r['status'] == status)]
    shown = 0
    for student in sorted(candidates, key=lambda s: s['Student Name'].casefold()):
        records = [r for r in filtered if r['number'] == student['Student Number']]
        if teacher and not records:
            continue
        all_records = [r for r in relevant if r['number'] == student['Student Number']]
        render_student(student, records, snapshot['updated_at'], all_records=all_records)
        shown += 1
    if teacher and not shown:
        st.info('No matching quizzes. Select a group or change the filters.')
