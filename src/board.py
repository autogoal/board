import streamlit as st
import json
import black
import altair as alt
import re
import pandas as pd
from pathlib import Path

#Se inicializa la pagina poniendole titulo, un icono, y estableciendo el estado de la disposicion y la barra lateral
st.beta_set_page_config(
    page_title="AutoGOAL Board",
    page_icon=str(Path(__file__).parent.parent / "img" / "autogoal-logo-embedded.png"),
    layout="centered",
    initial_sidebar_state="expanded",
)


def main():
    #Se restablece la configuracion de la opcion showfileUploaderEncoding para evitar una advertencia indeseada
    st.set_option("deprecation.showfileUploaderEncoding", False)
    
    #Se carga la imagen de la página
    st.image(
        str(Path(__file__).parent.parent / "img" / "autogoal-banner.png"),
        # width=600,
        use_column_width=True,
    )
    #Se da a escoger como se quiere cargar el archivo mediante una selectbox
    input_mode = st.sidebar.selectbox("Input mode", ["Upload file", "Enter path"])
    #Se crea la variable "fp" donde se guardara el archivo en cuestion
    fp = None
    #Segun la opcion escogida se le asigna a la variable fb el valor que debe tener
    if input_mode == "Enter path":
        path = st.sidebar.text_input("Input path")
        if path:
            fp = open(path, "r")

    elif input_mode == "Upload file":
        fp = st.sidebar.file_uploader("Input file")

    if fp is None:
        return
    #Se muestra en la barra lateral un widget donde se puede aumentar o disminuir las "Pipeline features" y se almacena este numero en una variable
    number_features = st.sidebar.number_input("Pipeline features", 0, None, 1)
    #Se crea una lista "features" para almacenar expresiones regulares
    features = []
    #Se añaden los elementos a features
    for i in range(number_features):
        features.append(st.sidebar.text_input("Feature %i" % i, key="feature_%i" % i, value="\w+=[a-zA-Z_]+"))

    process(fp, features)

#Trata de castear el pipeline a string y si no lo consigue lo devuelve igual que entró
def describe(pipeline):
    try:
        return black.format_str(pipeline, mode=black.FileMode())
    except black.InvalidInput:
        return pipeline


def extract_features(pipeline, features):
    results = []

    for f in features:
        #(no entiendo por que se usa el not f, si f es un str, no un valor booleano)
        if not f:
            continue
       #Se comprueba cuales strs coinciden con la expresion regular definida, y se añaden a ¨results¨
        for m in re.findall(f, pipeline):
            results.append((f, m))

    return results


def process(fp, features):
    #Se crea la variable "lines" y se abre un espacio para esta en la barra lateral
    lines = st.sidebar.empty()
    #Muestra un checkbox en la barra lateral que permite decidir si Ignore fitness = 0
    ignore_zero = st.sidebar.checkbox("Ignore fitness=0")
    #Se crea la variable "max_fitness" donde se almacenara al maximo valor que alcance "fitness" en la grafica, y se abre un espacio para esta en la pagina
    max_fitness = st.empty()
    #Se crea el grafico que se muestra en la pagina (me causan dudas las especificidades de COMO se crea el grafico)
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
    #Se crea un checkbox en la barra lateral que permite decidir si se desean mostrar los features como tabla
    show_features_table = st.sidebar.checkbox("Show features as table")
    features_table = st.empty()
    all_features = []
   
    st.markdown("### Best pipeline")
    best_text = st.empty()

    pipeline = 0
    max_fit = 0.0
    avg_fit = []

    for i, line in enumerate(fp):
        #Muestra que linea del archivo se esta cargando
        lines.info(f"Loading line: {i}")
        #se guarda en la variable "data" el contenido linea por linea del archivo
        data = json.loads(line)
   #(esto me confunde, creo que aqui se realiza como tal el procesamiento especifico de los datos de cada linea del archivo que se cargó, pero no se bien que hace)   
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
            #Se actualiza, de ser necesario, el valor maximo de fitness
            if fitness >= max_fit:
                max_fit = fitness
                #Se muestra en la pagina el codigo del pipeline
                best_text.code(pipeline_str)
        #Muestra en la pagina un label con el maximo valor alcanzado por fitness y la media de los valores de fitness
            max_fitness.info(
                f"- **Max Fitness:** `{max_fit}` \n - **Average Fitness:** `{sum(avg_fit) / len(avg_fit) if avg_fit else 0.0:0.3}`"
            )

            #(no se por que o para que este pedazo)
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
    #Muestra un mensaje cuando se hayan cargado todas las lineas del archivo
    lines.success("File loaded succesfully")

#(no entiendo que variable es "_name_", ni por que se hace esta condicional antes de llamar al main)
if __name__ == "__main__":
    main()
