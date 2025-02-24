import streamlit as st
import requests
import os

@st.dialog("View Knowledge Base")
def view_kb_dialog(name:str):
    # Add view KB API
    tab1, tab2, tab3 = st.tabs(["Dataset","Retrieval testing","Configuration"])
    with tab1:
        st.write(f"Viewing KB: {name}")
        st.write("This is a dummy content")

    with tab2:
        st.write("Retrieval testing")
        st.write("This is a dummy content")

    with tab3:
        st.write("Configuration")
        st.write("This is a dummy content")