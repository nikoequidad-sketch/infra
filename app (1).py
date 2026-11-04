import streamlit as st
import networkx as nx
import pandas as pd
import streamlit.components.v1 as components

from pyvis.network import Network
import streamlit.components.v1 as components


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
    g = nx.Graph()

    for _, r in df.iterrows():
        if (
            r["Disponible"]
            and r["Retardo (ms)"] > 0
            and r["Capacidad (Mbps)"] > 0
        ):
            u, v = r["Enlace"].split("-")

            g.add_edge(
                u,
                v,
                retardo=float(r["Retardo (ms)"]),
                banda=float(r["Capacidad (Mbps)"])
            )

    return g


def evaluar_camino(path, G_net):
    saltos = len(path) - 1
    retardo_total = 0
    banda_minima = float("inf")

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]

        if G_net.has_edge(u, v):
            d_val = G_net[u][v]["retardo"]
            b_val = G_net[u][v]["banda"]

            retardo_total += d_val
            banda_minima = min(banda_minima, b_val)

        else:
            return None

    return saltos, retardo_total, banda_minima


def mostrar_grafo_interactivo(
    G,
    posiciones,
    aristas_resaltadas=None,
    aristas_sink=None,
    dirigido=False,
    clave="grafo"
):
    """
    Genera una red interactiva con nodos arrastrables.
    """

    aristas_resaltadas = aristas_resaltadas or set()
    aristas_sink = aristas_sink or []

    net = Network(
        height="500px",
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
            color={
                "background": color,
                "border": "#ffffff",
                "highlight": {
                    "background": color,
                    "border": "#222222"
                }
            },
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
                color="#3498db" if es_optima else "#7f8c8d",
                width=5 if es_optima else 2,
                smooth=False
            )

    # INTERACCIÓN
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
        height=520,
        scrolling=False
    )


# =========================================================
# TÍTULO
# =========================================================

st.title("Laboratorio: Optimalidad y Sink Tree")

st.markdown(
    "Basado en Johal (2008) · Origen H, destino B · "
    "Datos en ms y Mbps de ejemplo"
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
    "Criterio",
    MODOS
)

st.sidebar.subheader("Pesos (multicriterio)")

alpha = st.sidebar.slider(
    "α (saltos)",
    0.0, 1.0, 0.50
)

beta = st.sidebar.slider(
    "β (retardo)",
    0.0, 1.0, 0.35
)

gamma = st.sidebar.slider(
    "γ (baja capacidad)",
    0.0, 1.0, 0.15
)


# =========================================================
# TABLA DE ENLACES
# =========================================================

df = st.session_state.df_enlaces

G = construir_grafo(df)

st.subheader("1. Tabla de enlaces")

df_editado = st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    key="editor_enlaces"
)

if not df_editado.equals(df):
    st.session_state.df_enlaces = df_editado
    st.rerun()

G = construir_grafo(st.session_state.df_enlaces)


# =========================================================
# RUTAS ESTÁTICAS
# =========================================================

st.subheader("2. Ruta estática vs. ruta óptima")

st.markdown(
    r"""
    $$G = (V,E), \quad H(P) = \sum_{(i,j)\in P} h_{ij}$$

    $$D(P) = \sum d_{ij}, \quad B(P) = \min b_{ij}$$

    $$C(P) = \sum \left[
    \alpha \frac{d_{ij}}{d_{ref}} +
    \gamma \frac{b_{ref}}{b_{ij}}
    \right]$$
    """
)

resultados_estaticos = []

for nombre_ruta, path in RUTAS.items():

    res = evaluar_camino(path, G)

    if res:

        s, r, b = res

        if criterio == "Johal: mínimo de saltos":
            costo = s

        elif criterio == "Mínimo retardo":
            costo = r

        else:
            costo = (
                alpha * (s / 3)
                + beta * (r / 30)
                + gamma * (100 / b)
            )

        resultados_estaticos.append(
            {
                "Ruta": nombre_ruta,
                "Camino": "-".join(path),
                "Disponible": True,
                "Saltos H(P)": s,
                "Retardo D(P) ms": r,
                "Banda B(P) Mbps": b,
                "Costo C(P)": round(costo, 3)
            }
        )

df_rutas = pd.DataFrame(resultados_estaticos)

camino_optimo_nodos = []

if not df_rutas.empty:

    st.dataframe(
        df_rutas,
        use_container_width=True,
        hide_index=True
    )

    best_idx = df_rutas["Costo C(P)"].idxmin()

    optima_str = df_rutas.loc[best_idx]["Camino"]

    camino_optimo_nodos = optima_str.split("-")

    st.success(f"Óptimo recalculado: {optima_str}")

else:
    st.warning("No hay rutas disponibles entre H y B.")


# =========================================================
# VISUALIZACIÓN INTERACTIVA
# =========================================================

st.subheader("3. Visualización interactiva de la red")

st.info(
    "Arrastra los nodos con el mouse para cambiar sus posiciones. "
    "Puedes acercar, alejar y desplazar la visualización."
)

pares_optimos = {
    frozenset((u, v))
    for u, v in zip(
        camino_optimo_nodos[:-1],
        camino_optimo_nodos[1:]
    )
}

mostrar_grafo_interactivo(
    G,
    POS,
    aristas_resaltadas=pares_optimos,
    clave="red_principal"
)


# =========================================================
# SINK TREE
# =========================================================

st.subheader(f"4. Sink Tree hacia {DESTINO}")

sink_data = []
sink_edges = []

if nx.has_path(G, ORIGEN, DESTINO):

    for node in G.nodes():

        if node != DESTINO and nx.has_path(G, node, DESTINO):

            path = nx.shortest_path(
                G,
                source=node,
                target=DESTINO,
                weight="retardo"
            )

            siguiente = path[1]

            costo_ac = len(path) - 1

            sink_data.append(
                {
                    "Router": node,
                    "Siguiente salto hacia B": siguiente,
                    "Costo acumulado": costo_ac
                }
            )

            sink_edges.append((node, siguiente))

    st.info(
        "Sink Tree interactivo: puedes arrastrar cada router "
        "y sus conexiones seguirán al nodo."
    )

    mostrar_grafo_interactivo(
        G,
        POS,
        aristas_sink=sink_edges,
        dirigido=True,
        clave="sink_tree"
    )

else:
    st.warning(
        "No existe conexión entre el origen H y el destino B."
    )


# =========================================================
# TABLA SINK TREE
# =========================================================

if sink_data:

    st.subheader("Tabla de siguientes saltos")

    st.dataframe(
        pd.DataFrame(sink_data),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# LEYENDA
# =========================================================

st.divider()

st.markdown("### Leyenda de la red")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🟢 **H:** Nodo origen")

with col2:
    st.markdown("🟠 **B:** Nodo destino")

with col3:
    st.markdown("🔵 **Routers intermedios**")

st.caption(
    "Laboratorio de optimalidad y Sink Tree · "
    "Modelo basado en Johal (2008)"
