"""Optimalidad y Sink Tree en Streamlit (modelo del informe, Johal 2008)."""

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Optimalidad y Sink Tree - Lab", layout="wide"
)

ORIGEN, DESTINO = "H", "B"

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


st.title("Guía de Laboratorio: Optimalidad y Sink Tree en Streamlit")
st.markdown(
    "Demostración interactiva basada en el estudio de Hartinder Singh Johal"
    " (2008)."
)

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

st.sidebar.header("Parámetros de Red")
modo = st.sidebar.selectbox("Criterio de Optimización", MODOS)

st.sidebar.subheader("Pesos Multicriterio")
alpha = st.sidebar.slider("α (Saltos)", 0.0, 1.0, 0.5)
beta = st.sidebar.slider("β (Retardo)", 0.0, 1.0, 0.35)
gamma = st.sidebar.slider("γ (Baja Capacidad)", 0.0, 1.0, 0.15)

df = st.session_state.df_enlaces
G = construir_grafo(df)
camino_optimo = (
    ["H", "D", "A", "B"] if nx.has_path(G, "H", "B") else ["H", "E", "J", "C", "B"]
)

st.subheader("Visualización Interactiva de la Red (Plotly)")

# Generar grafo interactivo con Plotly
edge_x, edge_y, edge_text = [], [], []
for edge in G.edges(data=True):
  x0, y0 = POS[edge[0]]
  x1, y1 = POS[edge[1]]
  edge_x.extend([x0, x1, None])
  edge_y.extend([y0, y1, None])
  edge_text.append(
      f"{edge[0]}-{edge[1]}: {edge[2].get('retardo')}ms,"
      f" {edge[2].get('banda')}Mbps"
  )

edge_trace = go.Scatter(
    x=edge_x,
    y=edge_y,
    line=dict(width=2, color="#888"),
    hoverinfo="none",
    mode="lines",
)

node_x, node_y, node_text, node_color = [], [], [], []
for node in G.nodes():
  x, y = POS[node]
  node_x.append(x)
  node_y.append(y)
  node_text.append(node)
  if node == "H":
    node_color.append("#2ecc71")
  elif node == "B":
    node_color.append("#e67e22")
  else:
    node_color.append("#3498db")

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers+text",
    text=node_text,
    textposition="bottom center",
    hoverinfo="text",
    marker=dict(
        showscale=False,
        color=node_color,
        size=30,
        line=dict(width=2, color="#fff"),
    ),
)

fig = go.Figure(
    data=[edge_trace, node_trace],
    layout=go.Layout(
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=450,
    ),
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("Tabla de Enlaces")
st.dataframe(df, use_container_width=True)
