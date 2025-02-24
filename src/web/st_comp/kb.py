import streamlit as st
import requests
import os

@st.dialog("View Knowledge Base")
def view_kb_dialog(name:str):
    # Add view KB API
    st.write(f"Viewing KB: {name}")
    st.write("This is a dummy content")