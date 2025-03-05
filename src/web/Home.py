import streamlit as st
import os
import requests
from minio import Minio
from st_comp.new_kb import new_kb_dialog
from st_comp.kb import view_kb_dialog

if 'login' not in st.session_state:
    st.session_state.login = False

demo_kb = [
    {'name':'KB1','description':'This is KB1','icon':'📚'},
    {'name':'KB2','description':'This is KB2','icon':'📚'},
    {'name':'KB3','description':'This is KB3','icon':'📚'},
    {'name':'KB4','description':'This is KB4','icon':'📚'},
    {'name':'KB5','description':'This is KB5','icon':'📚'},
    {'name':'KB6','description':'This is KB6','icon':'📚'},
]

if not st.session_state.login:
    # login form
    with st.form(key='login_form'):
        st.title('Login')
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submit_button = st.form_submit_button(label='Login')
        if submit_button:
            if username == 'admin' and password == 'admin':
                st.session_state.login = True
                st.session_state.username = username
                st.success('Login success')
                st.rerun()
            else:
                st.write('Invalid username or password')
else:
    # page content
    st.title("💾Knowledge Base")
    st.divider()
    
    col_l, col_r = st.columns([3, 1])
    
    with col_l:
        st.write('Your knowledge base:')
    with col_r:
        new_kb = st.button('New KB')
        if new_kb:new_kb_dialog()
    
    kb_left, kb_mid, kb_right = st.columns(3)
    for it, kb in enumerate(demo_kb):
        where = kb_left if it%3==0 else kb_mid if it%3==1 else kb_right
        new_container = where.container(key=f'kb_{it}', border=True)
        with new_container:
            st.markdown(f"## {kb['icon']} {kb['name']}")
            st.write(kb['description'])
            if st.button('Open', key=f'open_kb_{it}'):
                view_kb_dialog(kb['name'])