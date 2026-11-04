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


# --- CÁLCULOS DE RUTAS Y MÉTRICAS ---
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
  optima = df_rutas.loc[df_rutas["Costo C(P)"].idxmin()]["Camino"]
  st.success(f"Óptimo recalculado: {optima}")

# --- VISUALIZACIÓN GRAFO ---
st.subheader("Visualización Interactiva de la Red")
edge_x, edge_y = [], []
for edge in G.edges(data=True):
  x0, y0 = POS[edge[0]]
  x1, y1 = POS[edge[1]]
  edge_x.extend([x0, x1, None])
  edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x, y=edge_y, line=dict
    
