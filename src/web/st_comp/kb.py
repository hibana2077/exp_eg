import streamlit as st
import requests
import os

# Minio
from minio import Minio

# Self-defined imports
from utils.size_cal import size_cal

MINIO_SERVER = os.getenv("MINIO_SERVER", "minio:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "root")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "password")

@st.dialog("View Knowledge Base")
def view_kb_dialog(kb_name:str):
    # Add view KB API
    tab1, tab2, tab3, tab4 = st.tabs(["Upload","Database","Retrieval testing","Configuration"])
    with tab1:
        st.write(f"Viewing KB: {kb_name}")
        st.write("This is a dummy content")
        uploaded_files = st.file_uploader(
            "Upload files", accept_multiple_files=True
        )
        for uploaded_file in uploaded_files:
            st.markdown(f"- filename: {uploaded_file.name}, type: {uploaded_file.type}, size: {size_cal(uploaded_file.size)}")
        if len(uploaded_files) > 0:
            if st.button("Upload"):
                client = Minio(
                    MINIO_SERVER,
                    access_key=MINIO_USER,
                    secret_key=MINIO_PASSWORD,
                    secure=False,
                )
                found = client.bucket_exists(kb_name.lower())
                if not found:client.make_bucket(kb_name.lower())
                # save file to local temp
                for uploaded_file in uploaded_files:
                    with open(uploaded_file.name, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    # Upload to Minio
                    client.fput_object(
                        kb_name.lower(), uploaded_file.name, uploaded_file.name,
                    )
                    os.remove(uploaded_file.name)
                    
                uploaded_files = []
                st.success("Upload successful!")
                st.balloons()

    with tab2:
        st.write("Database")
        client = Minio(
                    MINIO_SERVER,
                    access_key=MINIO_USER,
                    secret_key=MINIO_PASSWORD,
                    secure=False,
                )
        objects = client.list_objects(kb_name.lower())
        st.write(objects)
        # for obj in objects:
        #     st.markdown(f"- filename: {obj.object_name}, size: {size_cal(obj.size)}")


    with tab3:
        st.write("Retrieval testing")
        st.write("This is a dummy content")

    with tab4:
        st.write("Configuration")
        st.write("This is a dummy content")