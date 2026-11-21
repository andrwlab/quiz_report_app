import hmac
import os
import streamlit as st


def require_access(role):
    """Separate process entrypoints; fail closed without configured server secret."""
    expected = os.environ.get(f'SABIS_{role.upper()}_PASSWORD', '')
    if not expected:
        st.info(f'{role.title()} access is not configured.')
        st.stop()
    key = f'{role}_authenticated'
    if not st.session_state.get(key):
        with st.form(f'{role}_login'):
            password = st.text_input(f'{role.title()} password', type='password')
            submitted = st.form_submit_button('Sign in')
        if submitted:
            if hmac.compare_digest(password.encode(), expected.encode()):
                st.session_state[key] = True
                st.rerun()
            st.error('Invalid credentials.')
        st.stop()
    if st.button('Sign out'):
        st.session_state.clear()
        st.rerun()
