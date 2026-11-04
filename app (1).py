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

MODOS = [
    "Johal: mínimo de saltos",
    "Mínimo retardo",
    "Multicriterio ponderado",
]


def construir_grafo(df):
  g = nx.Graph()
  for _, r in df.iterrows():
    if r["Disponible"] and r["Retardo (ms)"] > 0 and r["Capacidad (Mbps)"] > 0:
      u, v = r["Enlace"].split("-")
      g.add_edge(
          u, v, retardo=float(r["Retardo (ms)"]), banda=float(r["Capacidad (Mbps)"])
      )
  return g


st.title("Laboratorio: Optimalidad y Sink Tree")
st.markdown(
    "Basado en Johal (2008) · Origen H, destino B · Datos en ms y Mbps de"
    " ejemplo"
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

st.sidebar.header("Función objetivo")
criterio = st.sidebar.selectbox("Criterio", MODOS)

st.sidebar.subheader("Pesos (multicriterio)")
alpha = st.sidebar.slider("α (saltos)", 0.0, 1.0, 0.5)
beta = st.sidebar.slider("β (retardo)", 0.0, 1.0, 0.35)
gamma = st.sidebar.slider("γ (baja capacidad)", 0.0, 1.0, 0.15)

df = st.session_state.df_enlaces
G = construir_grafo(df)

st.subheader("1. Tabla de enlaces")
st.dataframe(df, use_container_width=True)


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
      if b_val < banda_minima:
        banda_minima = b_val
    else:
      return None
  return saltos, retardo_total, banda_minima


resultados_estaticos = []
camino_optimo_nodos = ["H", "D", "A", "B"]

for nombre_ruta, path in RUTAS.items():
  res = evaluar_camino(path, G)
  if res:
    s, r, b = res
    resultados_estaticos.append(
        {
            "Ruta": nombre_ruta,
            "Camino": "-".join(path),
            "Disponible": True,
            "Saltos H(P)": s,
            "Retardo D(P) ms": r,
            "Banda B(P) Mbps": b,
            "Costo C(P)": round(
                alpha * (s / 3) + beta * (r / 30) + gamma * (100 / b), 3
            ),
        }
    )

df_rutas = pd.DataFrame(resultados_estaticos)

st.subheader("2. Ruta estática vs. ruta óptima")
st.markdown(
    "$$G = (V,E), \\quad H(P) = \\sum_{(i,j)\\in P} h_{ij}, h_{ij} = 1$$"
)
st.markdown(
    "$$D(P) = \\sum d_{ij}, \\quad B(P) = \\min b_{ij}, \\quad C(P) =" " \\sum \\left[\\alpha \\frac{d_{ij}}{d_{ref}} + \\gamma" " \\frac{b_{ref}}{b_{ij}}\\right]$$"
)

if not df_rutas.empty:
  st.dataframe(df_rutas, use_container_width=True)
  best_idx = df_rutas["Costo C(P)"].idxmin()
  optima_str = df_rutas.loc[best_idx]["Camino"]
  camino_optimo_nodos = optima_str.split("-")
  st.success(f"Óptimo recalculado: {optima_str}")

# --- VISUALIZACIÓN INTERACTIVA DE LA RED ---
st.subheader("Visualización Interactiva de la Red")
pares_optimos = set(
    zip(camino_optimo_nodos[:-1], camino_optimo_nodos[1:])
).union(set(zip(camino_optimo_nodos[1:], camino_optimo_nodos[:-1])))

edge_x, edge_y, edge_x_opt, edge_y_opt = [], [], [], []
for u, v, data in G.edges(data=True):
  x0, y0 = POS[u]
  x1, y1 = POS[v]
  if (u, v) in pares_optimos:
    edge_x_opt.extend([x0, x1, None])
    edge_y_opt.extend([y0, y1, None])
  else:
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

trace_normal = go.Scatter(
    x=edge_x,
    y=edge_y,
    line=dict(width=2, color="#7f8c8d"),
    hoverinfo="none",
    mode="lines",
)
trace_opt = go.Scatter(
    x=edge_x_opt,
    y=edge_y_opt,
    line=dict(width=4, color="#3498db"),
    hoverinfo="none",
    mode="lines",
)

node_x, node_y, node_text, node_color = [], [], [], []
for node in G.nodes():
  x, y = POS[node]
  node_x.append(x)
  node_y.append(y)
  node_text.append(node)
  node_color.append(
      "#2ecc71" if node == ORIGEN else "#e67e22" if node == DESTINO else "#3498db"
  )

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers+text",
    text=node_text,
    textposition="bottom center",
    marker=dict(color=node_color, size=30, line=dict(width=2, color="#fff")),
)

fig = go.Figure(
    data=[trace_normal, trace_opt, node_trace],
    layout=go.Layout(
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400,
    ),
)
st.plotly_chart(fig, use_container_width=True)

# --- SINK TREE CON GRAFO DIRIGIDO Y TABLA ---
st.subheader(f"3. Sink Tree hacia {DESTINO}")
sink_edges_x, sink_edges_y = [], []
sink_data = []

if nx.has_path(G, ORIGEN, DESTINO):
  for node in G.nodes():
    if node != DESTINO and nx.has_path(G, node, DESTINO):
      path = nx.shortest_path(G, source=node, target=DESTINO, weight="retardo")
      siguiente = path[1]
      costo_ac = len(path) - 1
      sink_data.append(
          {
              "Router": node,
              "Siguiente salto hacia B": siguiente,
              "Costo acumulado": costo_ac,
          }
      )
      # Coordenadas para las flechas del Sink Tree
      x0, y0 = POS[node]
      x1, y1 = POS[siguiente]
      sink_edges_x.extend([x0, x1, None])
      sink_edges_y.extend([y0, y1, None])

# Grafo visual del Sink Tree
trace_sink_edges = go.Scatter(
    x=sink_edges_x,
    y=sink_edges_y,
    line=dict(width=3, color="#2ecc71"),
    mode="lines+markers",
    marker=dict(size=[10 if i % 3 == 2 else 0 for i in range(len(sink_edges_x))]),
)

fig_sink = go.Figure(
    data=[trace_normal, trace_sink_edges, node_trace],
    layout=go.Layout(
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, show
