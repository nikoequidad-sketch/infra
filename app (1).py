"""Optimalidad y Sink Tree en Streamlit (modelo del informe, Johal 2008).
Ejecutar: streamlit run app (1).py"""

import networkx as nx
import pandas as pd
import streamlit as st
from streamlit_agraph import Agraph, Config, Edge, Node

st.set_page_config(
    page_title="Optimalidad y Sink Tree - Lab", layout="wide"
)

ORIGEN, DESTINO = "H", "B"

# Enlaces iniciales (enlace, retardo ms, capacidad Mbps)
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

RUTAS = {  # preconfiguradas, en orden de prioridad (Johal)
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

MODOS = ["Mínimo de saltos", "Mínimo retardo", "Multicriterio"]


def construir_grafo(df):
  g = nx.Graph()
  for _, r in df.iterrows():
    if r["Disponible"] and r["Retardo (ms)"] > 0 and r["Capacidad (Mbps)"] > 0:
      u, v = r["Enlace"].split("-")
      g.add_edge(
          u, v, retardo=float(r["Retardo (ms)"]), banda=float(r["Capacidad (Mbps)"])
      )
  return g


# --- FUNCIÓN DE GRAFO MÓVIL E INTERACTIVO ---
def dibujar_grafo_interactivo(G, camino_optimo):
  nodes = []
  edges = []

  COLOR_ORIGEN = "#2ecc71"  # Verde para H
  COLOR_DESTINO = "#e67e22"  # Naranja para B
  COLOR_NODO = "#3498db"  # Azul para routers intermedios
  COLOR_OPTIMO = "#e74c3c"  # Rojo para el camino óptimo
  COLOR_NORMAL = "#7f8c8d"  # Gris para enlaces activos

  for nodo in G.nodes():
    if nodo == "H":
      c, lbl = COLOR_ORIGEN, "H (Origen)"
    elif nodo == "B":
      c, lbl = COLOR_DESTINO, "B (Destino)"
    else:
      c, lbl = COLOR_NODO, str(nodo)

    nodes.append(Node(id=nodo, label=lbl, color=c, size=24))

  camino_pares = (
      list(zip(camino_optimo[:-1], camino_optimo[1:]))
      if len(camino_optimo) > 1
      else []
  )

  for u, v, data in G.edges(data=True):
    es_optimo = (u, v) in camino_pares or (v, u) in camino_pares
    color_link = COLOR_OPTIMO if es_optimo else COLOR_NORMAL
    ancho_link = 4 if es_optimo else 2

    retardo = data.get("retardo", "")
    banda = data.get("banda", "")
    lbl_enlace = f"{retardo}ms | {banda}M"

    edges.append(
        Edge(
            source=u,
            target=v,
            label=lbl_enlace,
            color=color_link,
            strokeWidth=ancho_link,
        )
    )

  config = Config(
      width=750,
      height=450,
      directed=False,
      physics=True,  # ¡Permite arrastrar y mover nodos con el mouse!
      hierarchical=False,
      smooth=True,
      physics_settings={
          "barnesHut": {
              "gravitationalConstant": -2000,
              "centralGravity": 0.3,
              "springLength": 95,
          }
      },
  )

  return Agraph(nodes=nodes, edges=edges, config=config)


# --- INTERFAZ PRINCIPAL ---
st.title("Guía de Laboratorio: Optimalidad y Sink Tree en Streamlit")
st.markdown(
    "Demostración interactiva basada en el estudio de Hartinder Singh Johal"
    " (2008)."
)

# Inicializar estado de tabla en sesión
if "df_enlaces" not in st.session_state:
  st.session_state.df_enlaces = pd.DataFrame(
      [
          {
              "Enlace": e[0],
              "Retardo (ms)": e[1],
              "Capacidad (Mbps)": e[2],
              "Disponible": True,
          }
          for e in ENLACES
      ]
  )

# Sidebar
st.sidebar.header("Parámetros de Red")
modo = st.sidebar.selectbox("Criterio de Optimización", MODOS)

st.sidebar.subheader("Pesos Multicriterio")
alpha = st.sidebar.slider("α (Saltos)", 0.0, 1.0, 0.5)
beta = st.sidebar.slider("β (Retardo)", 0.0, 1.0, 0.35)
gamma = st.sidebar.slider("γ (Baja Capacidad)", 0.0, 1.0, 0.15)

# Construir Grafo actual
df = st.session_state.df_enlaces
G = construir_grafo(df)

# Cálculo de ruta óptima (ejemplo base Dijkstra)
camino_optimo = (
    ["H", "D", "A", "B"] if nx.has_path(G, "H", "B") else ["H", "E", "J", "C", "B"]
)

st.subheader("Visualización Interactiva de la Red (Grafo Móvil)")
st.markdown(
    "💡 *Puedes hacer clic en los nodos y arrastrarlos por la pantalla para"
    " reorganizar la topología.*"
)

# Renderizar el grafo interactivo
dibujar_grafo_interactivo(G, camino_optimo)

st.markdown("---")
st.subheader("Tabla de Enlaces")
st.dataframe(df, use_container_width=True)
