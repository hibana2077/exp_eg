import streamlit as st
import os
import requests

@st.dialog("New Knowledge Base")
def new_kb_dialog():
    name = st.text_input("New KB Name")
    desc = st.text_input("Description")
    icon = st.selectbox("Icon",['📚','📖','📕','📗','📘','📙','📔','📒','📚','📓','📃','📜','📄','📰','🗞️','📑','🔖','🏷️','📎','🖇️','📌','📍','📏','📐','🗂️','📁','📂','🗃️','🗄️','🗑️','🔒','🔓','🔏','🔐','🔑','🗝️','🔨','⛏️','🛠️','🗡️','🔫','🏹','🛡️','🔧','🔩','🗜️','🔗','⛓️','🧰','🧲','🔬','🔭','📡','💉','💊','🚪','🛏️','🛋️','🚽','🚿','🛁','🪒','🧴','🧷','🧹','🧺','🧻','🧼','🧽','🧯','🛒','🚬','🗿','🏧','🚮','🚰','🚹','🚺','🚻','🚼','🚾','🛂','🛃','🛄','🛅','🚸','⛔','🚫','🚳','🚭','🚯','🚱','🚷','📵','🔞'])
    if st.button("Create",key="new_kb_btn"):
        # Need name validation
        # Add create new KB API
        st.rerun()