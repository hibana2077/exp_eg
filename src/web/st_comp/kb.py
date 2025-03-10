import streamlit as st
import requests
import os

# Minio
from minio import Minio

# Self-defined imports
from utils.size_cal import size_cal

MINIO_SERVER = os.getenv("MINIO_SERVER", "minio:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "root")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "password")

@st.dialog("View Knowledge Base")
def view_kb_dialog(name:str):
    # Add view KB API
    tab1, tab2, tab3 = st.tabs(["Dataset","Retrieval testing","Configuration"])
    with tab1:
        st.write(f"Viewing KB: {name}")
        st.write("This is a dummy content")
        uploaded_files = st.file_uploader(
            "Upload files", accept_multiple_files=True
        )
        for uploaded_file in uploaded_files:
            # bytes_data = uploaded_file.read()
            # st.write("filename:", uploaded_file.name)
            st.markdown(f"- filename: {uploaded_file.name}, type: {uploaded_file.type}, size: {size_cal(uploaded_file.size)}")
            # st.write(bytes_data)
        if len(uploaded_files) > 0:
            if st.button("Upload"):
                pass

    with tab2:
        st.write("Retrieval testing")
        st.write("This is a dummy content")

    with tab3:
        st.write("Configuration")
        st.write("This is a dummy content")