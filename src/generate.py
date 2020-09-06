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

    name_file = st.text_input("New file's name", "new.jsonl")
    overwrite = st.checkbox("Overwrite")

    original_file = st.file_uploader("Input original file")
    time_sleep = st.number_input("Set sleep time",min_value=1, value=3, step=1)

    edit_file = None

    if st.button("Clone") and original_file:
        if (path_generate / name_file).exists() and not overwrite:
            st.error("If file exists, then confirm **Overwrite** Option")
            return
        edit_file = open(str(path_generate / name_file),"w")        

        for s in re.findall("\{.*\}",original_file.read()):
            edit_file.writelines(s + "\n")
            edit_file.flush()
            st.write(s)
            sleep(time_sleep)
    

if __name__ == "__main__":
    main()