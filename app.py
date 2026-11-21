"""Public student entrypoint. No administration or group access."""
import streamlit as st
from public_view import run

st.set_page_config(page_title='SABIS Quiz Status', page_icon='📖', layout='centered')
run()
