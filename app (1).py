import streamlit as st
import networkx as nx
import pandas as pd
import streamlit.components.v1 as components
from pyvis.network import Network

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Optimalidad y Sink Tree - Lab",
    layout="wide"
)

ORIGEN = "H"
DESTINO = "B"

ENLACES = [
    ("H-D", 8, 100),
    ("D-A", 9, 100),
    ("A-B", 7, 100),
    ("H-E", 5, 50),
    ("E-J", 10, 50),
    ("J-C", 8, 100),
    ("C-B", 6, 100),
    ("H-O", 7, 50),
    ("O-N", 9, 50),
    ("N-J", 9, 50),
]

RUTAS = {
    "PSRC": ["H", "D", "A", "B"],
    "SSRC": ["H", "E", "J", "C", "B"],
    "TSRC": ["H", "O", "N", "J", "C", "B"],
}

POS = {
    "H": (0, 1),
    "D": (1.2, 2.2),
    "A": (3.2, 2.2),
    "B": (5, 1),
    "E": (1.2, 1),
    "J": (2.6, 1),
    "C": (3.8, 1),
    "O": (1.2, -0.2),
    "N": (2.6, -0.2),
}

MODOS = [
    "Johal: mínimo de saltos",
    "Mínimo retardo",
    "Multicriterio ponderado",
]

# =========================================================
# FUNCIONES
# =========================================================

def construir_grafo(df):

    G = nx.Graph()

    for _, r in df.iterrows():

        if (
            r["Disponible"]
            and r["Retardo (ms)"] > 0
            and r["Capacidad (Mbps)"] > 0
        ):

            u, v = r["Enlace"].split("-")

            G.add_edge(
                u,
                v,
                retardo=float(r["Retardo (ms)"]),
                banda=float(r["Capacidad (Mbps)"])
            )

    return G


def evaluar_camino(path, G):

    saltos = len(path) - 1
    retardo = 0
    banda = float("inf")

    for u, v in zip(path[:-1], path[1:]):

        if not G.has_edge(u, v):
            return None

        retardo += G[u][v]["retardo"]

        banda = min(
            banda,
            G[u][v]["banda"]
        )

    return saltos, retardo, banda


def calcular_costo(path, G, criterio, alpha, beta, gamma):

    resultado = evaluar_camino(path, G)

    if resultado is None:
        return None

    saltos, retardo, banda = resultado

    if criterio == "Johal: mínimo de saltos":

        return float(saltos)

    elif criterio == "Mínimo retardo":

        return float(retardo)

    else:

        return (
            alpha * (saltos / 5)
            + beta * (retardo / 50)
            + gamma * (100 / banda)
        )


def mostrar_grafo_interactivo(
    G,
    posiciones,
    aristas_resaltadas=None,
    aristas_sink=None,
    dirigido=False
):

    aristas_resaltadas = aristas_resaltadas or set()
    aristas_sink = aristas_sink or []

    net = Network(
        height="520px",
        width="100%",
        directed=dirigido,
        bgcolor="#ffffff",
        font_color="#263238",
        cdn_resources="in_line"
    )

    # NODOS

    for nodo in G.nodes():

        x, y = posiciones.get(nodo, (0, 0))

        if nodo == ORIGEN:
            color = "#2ecc71"

        elif nodo == DESTINO:
            color = "#e67e22"

        else:
            color = "#3498db"

        net.add_node(
            nodo,
            label=nodo,
            x=x * 150,
            y=-y * 150,
            physics=False,
            fixed=False,
            color=color,
            size=28,
            borderWidth=2,
            font={
                "size": 20,
                "color": "#263238",
                "face": "Arial"
            }
        )

    # ARISTAS

    if dirigido:

        for u, v in aristas_sink:

            net.add_edge(
                u,
                v,
                color="#2ecc71",
                width=4,
                arrows="to",
                smooth=False
            )

    else:

        for u, v in G.edges():

            es_optima = frozenset((u, v)) in aristas_resaltadas

            net.add_edge(
                u,
                v,
                color="#e74c3c" if es_optima else "#7f8c8d",
                width=5 if es_optima else 2,
                smooth=False
            )

    net.set_options("""
    {
        "physics": {
            "enabled": false
        },
        "interaction": {
            "dragNodes": true,
            "dragView": true,
            "zoomView": true,
            "hover": true,
            "navigationButtons": true
        },
        "nodes": {
            "borderWidth": 2,
            "shadow": true
        },
        "edges": {
            "smooth": false,
            "hoverWidth": 2
        }
    }
    """)

    html = net.generate_html()

    components.html(
        html,
        height=540,
        scrolling=False
    )


# =========================================================
# TÍTULO
# =========================================================

st.title("Laboratorio: Optimalidad y Sink Tree")

st.markdown(
    "Basado en Johal (2008) | Origen H | Destino B"
)

# =========================================================
# DATOS INICIALES
# =========================================================

if "df_enlaces" not in st.session_state:

    st.session_state.df_enlaces = pd.DataFrame(
        [
            {
                "Enlace": e[0],
                "Retardo (ms)": e[1],
                "Capacidad (Mbps)": e[2],
                "Disponible": True
            }
            for e in ENLACES
        ]
    )

# =========================================================
# PANEL LATERAL
# =========================================================

st.sidebar.header("Función objetivo")

criterio = st.sidebar.selectbox(
    "Selecciona el criterio",
    MODOS
)

st.sidebar.subheader("Pesos multicriterio")

alpha = st.sidebar.slider(
    "α (saltos)", 0.0, 1.0, 0.50
)

beta = st.sidebar.slider(
    "β (retardo)", 0.0, 1.0, 0.35
)

gamma = st.sidebar.slider(
    "γ (capacidad)", 0.0, 1.0, 0.15
)

if criterio == "Multicriterio ponderado":

    st.sidebar.caption(
        f"Suma de pesos: {alpha + beta + gamma:.2f}"
    )

# =========================================================
# TABLA DE ENLACES
# =========================================================

st.subheader("1. Tabla de enlaces")

df_editado = st.data_editor(
    st.session_state.df_enlaces,
    use_container_width=True,
    hide_index=True,
    key="editor_enlaces",
    column_config={
        "Disponible": st.column_config.CheckboxColumn(
            "Disponible",
            default=True
        ),
        "Retardo (ms)": st.column_config.NumberColumn(
            "Retardo (ms)",
            min_value=0.1
        ),
        "Capacidad (Mbps)": st.column_config.NumberColumn(
            "Capacidad (Mbps)",
            min_value=0.1
        )
    }
)

st.session_state.df_enlaces = df_editado.copy()

G = construir_grafo(st.session_state.df_enlaces)

# =========================================================
# RUTAS ESTÁTICAS Y ÓPTIMAS
# =========================================================

st.subheader("2. Comparación de rutas")

st.markdown(
    r"""
    **Funciones de evaluación**

    $$H(P)=\sum_{(i,j)\in P}1$$

    $$D(P)=\sum_{(i,j)\in P}d_{ij}$$

    $$B(P)=\min_{(i,j)\in P}b_{ij}$$

    $$C(P)=\alpha\frac{H(P)}{5}
    +\beta\frac{D(P)}{50}
    +\gamma\frac{100}{B(P)}$$
    """
)

resultados = []

for nombre, path in RUTAS.items():

    res = evaluar_camino(path, G)

    if res is not None:

        saltos, retardo, banda = res

        costo = calcular_costo(
            path,
            G,
            criterio,
            alpha,
            beta,
            gamma
        )

        resultados.append({
            "Ruta": nombre,
            "Camino": " - ".join(path),
            "Saltos": saltos,
            "Retardo (ms)": retardo,
            "Capacidad (Mbps)": banda,
            "Costo": round(costo, 3)
        })

df_rutas = pd.DataFrame(resultados)

camino_optimo = []

if not df_rutas.empty:

    st.dataframe(
        df_rutas,
        use_container_width=True,
        hide_index=True
    )

    idx = df_rutas["Costo"].idxmin()

    camino_optimo = RUTAS[
        df_rutas.loc[idx, "Ruta"]
    ]

    st.success(
        f"Ruta óptima: {' - '.join(camino_optimo)}"
    )

else:

    st.warning(
        "No hay rutas disponibles entre H y B."
    )

# =========================================================
# VISUALIZACIÓN PRINCIPAL
# =========================================================

st.subheader("3. Visualización interactiva de la red")

st.info(
    "Puedes arrastrar los nodos, acercar, alejar "
    "y desplazar el grafo."
)

pares_optimos = {
    frozenset((u, v))
    for u, v in zip(
        camino_optimo[:-1],
        camino_optimo[1:]
    )
}

mostrar_grafo_interactivo(
    G,
    POS,
    aristas_resaltadas=pares_optimos
)

# =========================================================
# SINK TREE
# =========================================================

st.subheader("4. Sink Tree hacia B")

sink_data = []
sink_edges = []

if DESTINO in G and ORIGEN in G and nx.has_path(G, ORIGEN, DESTINO):

    for node in G.nodes():

        if node == DESTINO:
            continue

        if nx.has_path(G, node, DESTINO):

            path = nx.shortest_path(
                G,
                source=node,
                target=DESTINO,
                weight="retardo"
            )

            siguiente = path[1]

            costo_retardo = nx.shortest_path_length(
                G,
                source=node,
                target=DESTINO,
                weight="retardo"
            )

            saltos = len(path) - 1

            sink_data.append({
                "Router": node,
                "Siguiente salto hacia B": siguiente,
                "Saltos acumulados": saltos,
                "Retardo acumulado (ms)": costo_retardo
            })

            sink_edges.append((node, siguiente))

    st.info(
        "Árbol de encaminamiento dirigido hacia el destino B."
    )

    mostrar_grafo_interactivo(
        G,
        POS,
        aristas_sink=sink_edges,
        dirigido=True
    )

else:

    st.warning(
        "No existe conexión entre H y B."
    )

# =========================================================
# TABLA SINK TREE
# =========================================================

if sink_data:

    st.subheader("5. Tabla de siguientes saltos")

    df_sink = pd.DataFrame(sink_data)

    st.dataframe(
        df_sink,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# LEYENDA
# =========================================================

st.divider()

st.subheader("6. Leyenda")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🟢 **H:** Nodo origen")

with col2:
    st.markdown("🟠 **B:** Nodo destino")

with col3:
    st.markdown("🔵 **Routers intermedios**")

st.caption(
    "Laboratorio de redes | Optimalidad y Sink Tree"
)

