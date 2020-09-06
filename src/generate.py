import streamlit as st
import re
from pathlib import Path
from io import open
from time import sleep

def main():
    st.set_option("deprecation.showfileUploaderEncoding", False)

    st.title("File Generator")      

    path_generate = Path(__file__).parent.parent / "pipelines"
    path_generate.mkdir(exist_ok=True)    

    select_mode = st.sidebar.selectbox("Select mode", ["Clone file"])

    name_file = st.text_input("New file's name", "new.jsonl")
    overwrite = st.checkbox("Overwrite")    

    path_file = path_generate / name_file

    if path_file.exists() and not overwrite:
        st.error("If file exists, then confirm **Overwrite** Option")
        return

    if select_mode == "Clone file":
        clone_mode(path_file)


def clone_mode(path_file):

    original_file = st.file_uploader("Input original file")
    time_sleep = st.number_input("Set sleep time",min_value=1, value=3, step=1)

    if st.button("Clone") and original_file:        
        edit_file = open(str(path_file),"w")
        file_view = st.empty()

        for s in re.findall("\{.*\}",original_file.read()):
            text = s+"\n"
            edit_file.write(text)
            edit_file.flush()
            file_view.text_area("File",text, height=400)

            sleep(time_sleep)    
    

if __name__ == "__main__":
    main()