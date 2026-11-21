import streamlit as st
from auth import require_access
from public_view import run

st.set_page_config(page_title='Quiz Status · Teacher', page_icon='📖')
require_access('teacher')
run(teacher=True)
