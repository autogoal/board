import streamlit as st
import json
import black
import altair as alt
import re
import pandas as pd
from pathlib import Path


st.beta_set_page_config(
    page_title="AutoGOAL Board",
    page_icon=str(Path(__file__).parent.parent / "img" / "autogoal-logo-embedded.png"),
    layout="centered",
    initial_sidebar_state="expanded",
)


def main():
    st.set_option("deprecation.showfileUploaderEncoding", False)

    st.image(
        (Path(__file__).parent.parent / "img" / "autogoal-banner.png").read_bytes(),
        # width=600,
        use_column_width=True,
    )

    input_mode = st.sidebar.selectbox("Input mode", ["Upload file", "Enter path"])

    fp = None

    if input_mode == "Enter path":
        path = st.sidebar.text_input("Input path")
        if path:
            fp = open(path, "r")

    elif input_mode == "Upload file":
        fp = st.sidebar.file_uploader("Input file")

    if fp is None:
        return

    number_features = st.sidebar.number_input("Pipeline features", 0, None, 1)
    features = []

    for i in range(number_features):
        features.append(st.sidebar.text_input("Feature %i" % i, key="feature_%i" % i, value="\w+=[a-zA-Z_]+"))

    process(fp, features)


def describe(pipeline):
    try:
        return black.format_str(pipeline, mode=black.FileMode())
    except black.InvalidInput:
        return pipeline


def extract_features(pipeline, features):
    results = []

    for f in features:
        if not f:
            continue

        for m in re.findall(f, pipeline):
            results.append((f, m))

    return results


def process(fp, features):
    lines = st.sidebar.empty()

    ignore_zero = st.sidebar.checkbox("Ignore fitness=0")

    max_fitness = st.empty()
    chart = st.altair_chart(
        alt.Chart(data=None)
        .mark_bar()
        .encode(
            x=alt.X("pipeline:O", title="Pipelines"),
            y="fitness:Q",
            tooltip="fitness:Q",
        )
        + alt.Chart(data=None)
        .mark_line(color="green")
        .encode(x="pipeline:O", y="max_fit:Q",)
        + alt.Chart(data=None)
        .mark_rule(color="red")
        .encode(y=alt.Y("mean(fitness):Q", title="Fitness")),
        use_container_width=True,
    )

    features_chart = st.altair_chart(
        alt.Chart(data=None)
        .mark_circle(opacity=1)
        .encode(
            y=alt.Y("feature_name:N", title="Feature"),
            x=alt.X("feature_value:O", title="Fitness"),
            size=alt.X("count()", title="Count"),
            color=alt.Color("feature_type:N", title=None),
        ),
        use_container_width=True,
    )

    show_features_table = st.sidebar.checkbox("Show features as table")
    features_table = st.empty()
    all_features = []

    st.markdown("### Best pipeline")
    best_text = st.empty()

    pipeline = 0
    max_fit = 0.0
    avg_fit = []

    for i, line in enumerate(fp):
        lines.info(f"Loading line: {i}")
        data = json.loads(line)

        if "evaluating_pipeline" in data:
            fitness = data["evaluating_pipeline"].get("fitness", 0.0)
            pipeline_str = describe(data["evaluating_pipeline"]["pipeline"])

            for f, m in extract_features(
                data["evaluating_pipeline"]["pipeline"], features
            ):
                features_chart.add_rows(
                    [dict(feature_name=m, feature_value=fitness, feature_type=f,)]
                )

                all_features.append(
                    dict(feature_name=m, feature_value=fitness, feature_type=f)
                )

            if show_features_table:
                features_table.table(
                    pd.DataFrame(all_features)
                    .groupby(["feature_type", "feature_name"])
                    .agg(
                        mean_fitness=("feature_value", "mean"),
                        std_fitness=("feature_value", "std"),
                        records=("feature_value", "count"),
                    )
                )

            if fitness >= max_fit:
                max_fit = fitness
                best_text.code(pipeline_str)

            max_fitness.info(
                f"- **Max Fitness:** `{max_fit}` \n - **Average Fitness:** `{sum(avg_fit) / len(avg_fit) if avg_fit else 0.0:0.3}`"
            )

            if fitness > 0 or not ignore_zero:
                pipeline += 1
                avg_fit.append(fitness)

                chart.add_rows(
                    [
                        dict(
                            pipeline=pipeline,
                            fitness=fitness,
                            description=pipeline_str,
                            max_fit=max_fit,
                        )
                    ]
                )

    lines.success("File loaded succesfully")


if __name__ == "__main__":
    main()
