from black import FileMode, format_str
import streamlit as st
import json
import time
import black
import altair as alt
from pathlib import Path


st.beta_set_page_config(
    page_title="AutoGOAL Board",
    page_icon=str(Path(__file__).parent.parent / "img" / "autogoal-logo-embedded.png"),
    layout="centered",
    initial_sidebar_state="expanded",
)


def main():
    st.set_option('deprecation.showfileUploaderEncoding', False)

    st.image(
        str(Path(__file__).parent.parent / "img" / "autogoal-banner.png"),
        # width=600,
        use_column_width=True,
    )

    input_mode = st.sidebar.selectbox("Input mode", ["Upload file", "Enter path"])

    fp = None

    if input_mode == 'Enter path':
        path = st.sidebar.text_input("Input path")
        if path:
            fp = open(path, "r")

    elif input_mode == 'Upload file':
        fp = st.sidebar.file_uploader("Input file")

    if fp is None:
        return

    process(fp)


def describe(pipeline):
    try:
        return black.format_str(pipeline, mode=black.FileMode())
    except black.InvalidInput:
        return pipeline


def process(fp):
    lines = st.sidebar.empty()

    ignore_zero = st.sidebar.checkbox("Ignore fitness=0")

    max_fitness = st.empty()
    chart = st.altair_chart(alt.Chart(data=None).mark_bar().encode(
        x=alt.X("pipeline:O", title="Pipelines"),
        y="fitness:Q",
        tooltip="fitness:Q",
    ) + alt.Chart(data=None).mark_line(color='green').encode(
        x="pipeline:O",
        y="max_fit:Q",
    ) + alt.Chart(data=None).mark_rule(color='red').encode(
        y=alt.Y("mean(fitness):Q", title="Fitness")
    ), use_container_width=True)

    st.markdown("### Best pipeline")
    best_text = st.empty()

    pipeline = 0
    max_fit =  0.0
    avg_fit = []

    for i, line in enumerate(fp):
        lines.info(f"Loading line: {i}")
        data = json.loads(line)

        if 'evaluating_pipeline' in data:
            fitness = data['evaluating_pipeline'].get('fitness', 0.0)
            pipeline_str = describe(data['evaluating_pipeline']['pipeline'])

            if fitness > max_fit:
                max_fit = fitness
                best_text.code(pipeline_str)

            max_fitness.info(f"- **Max Fitness:** `{max_fit}` \n - **Average Fitness:** `{sum(avg_fit) / len(avg_fit) if avg_fit else 0.0:0.3}`")

            if fitness > 0 or not ignore_zero:
                pipeline += 1
                avg_fit.append(fitness)

                chart.add_rows([dict(
                    pipeline=pipeline,
                    fitness=fitness,
                    description=pipeline_str,
                    max_fit=max_fit,
                )])
                
    lines.success("File loaded succesfully")


if __name__ == "__main__":
    main()
