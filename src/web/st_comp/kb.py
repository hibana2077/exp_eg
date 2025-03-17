import streamlit as st
import requests
import os

# Minio
from minio import Minio

# Self-defined imports
from utils.size_cal import size_cal

CORE_SERVER = os.getenv("CORE_SERVER", "http://localhost:14514")
BACKEND_SERVER = os.getenv("BACKEND_SERVER", "http://localhost:8081")
MINIO_SERVER = os.getenv("MINIO_SERVER", "minio:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "root")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "password")

@st.dialog("View Knowledge Base")
def view_kb_dialog(kb_name:str):
    # Add view KB API
    tab1, tab2, tab3, tab4 = st.tabs(["Upload","Database","Retrieval testing","Configuration"])
    with tab1:
        st.write(f"Viewing KB: {kb_name}")
        st.write("Please Upload your files")
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
        objects_list = []
        # Create table headers
        table_content = "| Filename | Size | Type |\n|----------|------|------|\n"

        # Add each object as a row in the table
        for obj in objects:
            table_content += f"| {obj.object_name} | {size_cal(obj.size)} | {obj.content_type} |\n"
            objects_list.append(obj.object_name)

        # Display the complete table
        st.markdown(table_content)

        # Form to process selected objects
        with st.form(key='process_form'):
            selected_objects = st.multiselect("Select objects to process", objects_list)
            submit_button = st.form_submit_button(label='Process Selected Objects')

            if submit_button:
                if len(selected_objects) > 0:
                    # Send request to core /process_file
                    payload = {
                        "kb_name": kb_name,
                        "task_queue": []
                    }
                    for obj in selected_objects:
                        payload["task_queue"].append({
                            "kb_name": kb_name,
                            "file_name": obj
                        })
                    # Send request to core
                    res = requests.post(f"{CORE_SERVER}/process_file", json=payload)
                    if res.status_code == 200 and res.json()["status"] == "success":
                        st.success("Processing success!")
                        st.balloons()
                    else:
                        st.error(f"Error: {res.json().get('message', 'Unknown error')}")
                else:
                    st.warning("Please select at least one object to process.")

    with tab3:
        st.write("Retrieval testing")
        # @app.get("/list_tables/{kb_name}")
        # async def list_tables(kb_name:str):
        res = requests.get(f"{CORE_SERVER}/list_tables/{kb_name}")
        if res.json()['status'] != "success":
            st.error(res.json()['message'])
            st.stop()

        if len(res.json()['tables']['files']) == 0:
            st.warning("No tables found.")
            st.stop()

        tables_list = res.json()['tables']['files'] # key: file_name, status, texts_table_name
        # Create table headers
        table_content = "| Filename | Texts Table Name | Status |\n|----------|--------|------------------|\n"
        # Add each object as a row in the table
        for obj in tables_list:
            table_content += f"| {obj['file_name']} | {obj['texts_table_name']} | {obj['status']} |\n"
        # Display the complete table
        st.markdown(table_content)

        # Form to Retrieval testing
        with st.form(key='retrieval_form'):
            selected_tables = st.multiselect("Select tables to test", [obj['texts_table_name'] for obj in tables_list])
            query_text = st.text_input("Query text")
            submit_button = st.form_submit_button(label='Retrieval Testing')

    with tab4:
        st.write("Configuration")
        st.write("This is a dummy content")