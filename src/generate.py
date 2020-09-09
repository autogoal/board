import streamlit as st
import re
from pathlib import Path
import os
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
        st.error("If you want to overwrite the file, please confirm first")
        return

    if select_mode == "Clone file":
        clone_mode(path_file)


def clone_mode(path_file):

    input_mode = st.selectbox("Input mode", ["Upload file","Local file"])

    original_file = None

    if input_mode == "Upload file":
        original_file = st.file_uploader("Upload original file")

    elif input_mode == "Local file":
        local_path = Path(__file__).parent.parent / "pipelines"
        files = list(map(lambda f: f.name,
                        filter(lambda path : path.is_file(),
                        local_path.iterdir()
                    )   )
        )               
        select_box = st.selectbox("Select file",list(files))
        if select_box and select_box != path_file.name:
            original_file = open(local_path / select_box, "r")
    
    time_sleep = st.number_input("Set sleep time",min_value=1, value=3, step=1)

    if st.button("Clone") and original_file:        
        edit_file = open(str(path_file),"w")
        file_view = st.empty()

        for s in re.findall("\{.*\}",original_file.read()):
            text = s+"\n"
            edit_file.write(text)
            edit_file.flush()
            os.fsync(edit_file.fileno())
            file_view.text_area("Line",text, height=400)

            sleep(time_sleep)    
    

if __name__ == "__main__":
    main()