"""Optimalidad y Sink Tree en Streamlit (modelo del informe, Johal 2008).
Ejecutar: streamlit run app.py"""
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Optimalidad y Sink Tree", layout="wide")

ORIGEN, DESTINO = "H", "B"
ENLACES = [  # (enlace, retardo ms, capacidad Mbps)
    ("H–D", 8, 100), ("D–A", 9, 100), ("A–B", 7, 100), ("H–E", 5, 50), ("E–J", 10, 50),
    ("J–C", 8, 100), ("C–B", 6, 100), ("H–O", 7, 50), ("O–N", 9, 50), ("N–J", 9, 50),
]
RUTAS = {  # preconfiguradas, en orden de prioridad (Johal)
    "PSRC": ["H", "D", "A", "B"],
    "SSRC": ["H", "E", "J", "C", "B"],
    "TSRC": ["H", "O", "N", "J", "C", "B"],
}
POS = {"H": (0, 1), "D": (1.2, 2.2), "A": (3.2, 2.2), "B": (5, 1), "E": (1.2, 1),
       "J": (2.6, 1), "C": (3.8, 1), "O": (1.2, -0.2), "N": (2.6, -0.2)}
MODOS = ["Mínimo de saltos", "Mínimo retardo", "Multicriterio"]


def construir_grafo(df):
    g = nx.Graph()
    for _, r in df.iterrows():
        if r["Disponible"] and r["Retardo (ms)"] > 0 and r["Capacidad (Mbps)"] > 0:
            u, v = r["Enlace"].split("–")
            g.add_edge(u, v, d=float(r["Retardo (ms)"]), b=float(r["Capacidad (Mbps)"]))
    return g


def costo_enlace(g, u, v, modo, pesos, d_ref, b_ref):
    d, b = g[u][v]["d"], g[u][v]["b"]
    if modo == MODOS[0]:
        return 1.0
    if modo == MODOS[1]:
        return d
    a, be, ga = pesos
    return a + be * d / d_ref + ga * b_ref / b


def metricas(g, camino, pesos, d_ref, b_ref):
    pares = list(zip(camino, camino[1:]))
    if not all(g.has_edge(u, v) for u, v in pares):
        return None
    return {
        "Saltos": len(pares),
        "Retardo (ms)": sum(g[u][v]["d"] for u, v in pares),
        "Capacidad (Mbps)": min(g[u][v]["b"] for u, v in pares),
        "C(P)": round(sum(costo_enlace(g, u, v, MODOS[2], pesos, d_ref, b_ref) for u, v in pares), 3),
    }


# ---------------- Barra lateral ----------------
st.sidebar.header("Parámetros")
modo = st.sidebar.radio("Función objetivo", MODOS)
st.sidebar.caption("Origen H · Destino B")
alfa = st.sidebar.slider("α (saltos)", 0.0, 1.0, 0.5, 0.05)
beta = st.sidebar.slider("β (retardo)", 0.0, 1.0, 0.35, 0.05)
gamma = st.sidebar.slider("γ (baja capacidad)", 0.0, 1.0, 0.15, 0.05)
suma = alfa + beta + gamma
pesos = (alfa / suma, beta / suma, gamma / suma) if suma > 0 else (1 / 3, 1 / 3, 1 / 3)
st.sidebar.caption(f"Pesos normalizados: α={pesos[0]:.2f}, β={pesos[1]:.2f}, γ={pesos[2]:.2f}")

st.title("Optimalidad y Sink Tree: laboratorio de rutas óptimas")
st.caption("Basado en Johal (2008). Retardos, capacidades y función multicriterio son datos de ejemplo del laboratorio.")

st.subheader("Tabla de enlaces (editable)")
base = pd.DataFrame(ENLACES, columns=["Enlace", "Retardo (ms)", "Capacidad (Mbps)"])
base.insert(1, "Disponible", True)
df = st.data_editor(
    base, hide_index=True, width="stretch", disabled=["Enlace"],
    column_config={
        "Retardo (ms)": st.column_config.NumberColumn(min_value=1, step=1),
        "Capacidad (Mbps)": st.column_config.NumberColumn(min_value=1, step=1),
    },
)

g = construir_grafo(df)
d_ref = max((x["d"] for _, _, x in g.edges(data=True)), default=1)  # máximos de la tabla actual
b_ref = max((x["b"] for _, _, x in g.edges(data=True)), default=1)
for u, v in g.edges:
    g[u][v]["w"] = costo_enlace(g, u, v, modo, pesos, d_ref, b_ref)

# ---------------- Sink Tree y ruta óptima ----------------
if DESTINO not in g or ORIGEN not in g:
    st.error("Con estos enlaces H o B quedaron aislados. Activa más enlaces.")
    st.stop()
dist, caminos = nx.single_source_dijkstra(g, DESTINO, weight="w")
arbol = {n: c[-2] for n, c in caminos.items() if n != DESTINO}  # un solo siguiente salto por router
optima = list(reversed(caminos[ORIGEN])) if ORIGEN in caminos else None

nombre_est, ruta_est = next(((n, c) for n, c in RUTAS.items()
                             if metricas(g, c, pesos, d_ref, b_ref)), (None, None))

# ---------------- Resultados ----------------
c1, c2 = st.columns(2)
c1.metric("Ruta estática seleccionada", f"{nombre_est}: {'–'.join(ruta_est)}" if ruta_est else "Ninguna disponible")
c2.metric("Ruta óptima recalculada", "–".join(optima) if optima else "Sin camino")
if ruta_est and optima and ruta_est != optima:
    st.warning("La ruta estática NO coincide con la óptima recalculada con esta función objetivo.")
elif ruta_est and optima:
    st.success("La ruta estática coincide con la óptima.")

st.subheader("Rutas preconfiguradas")
filas = []
for n, c in RUTAS.items():
    m = metricas(g, c, pesos, d_ref, b_ref)
    filas.append({"Ruta": n, "Camino": "–".join(c), "Disponible": bool(m), **(m or {})})
st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
st.caption(f"Con d_ref = {d_ref:g} ms y b_ref = {b_ref:g} Mbps. Capacidad = mínimo de la ruta; "
           "la penalización b_ref/b_ij es un costo que se suma, no Mbps.")

izq, der = st.columns([3, 2])
with izq:
    fig = go.Figure()
    def trazo(pares, color, ancho, nombre, dash=None):
        xs, ys = [], []
        for u, v in pares:
            xs += [POS[u][0], POS[v][0], None]
            ys += [POS[u][1], POS[v][1], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=nombre,
                                 line=dict(color=color, width=ancho, dash=dash)))
    trazo(list(g.edges), "#b0b7c3", 2, "Enlaces activos")
    trazo([(n, s) for n, s in arbol.items()], "#2a9d8f", 4, "Sink Tree", "dot")
    if optima:
        trazo(list(zip(optima, optima[1:])), "#e07a1f", 7, "Ruta óptima")
    fig.add_trace(go.Scatter(x=[POS[n][0] for n in POS], y=[POS[n][1] for n in POS], mode="markers+text",
                             text=list(POS), textposition="middle center", showlegend=False,
                             marker=dict(size=34, color="#14213d"), textfont=dict(color="white")))
    fig.update_layout(height=430, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, width="stretch")
with der:
    st.subheader("Sink Tree hacia B")
    st.dataframe(pd.DataFrame({"Router": list(arbol), "Siguiente salto": list(arbol.values()),
                               "Distancia a B": [round(dist[n], 3) for n in arbol]}),
                 hide_index=True, width="stretch")

# ---------------- Registro de experimentos ----------------
if "registro" not in st.session_state:
    st.session_state.registro = []
if st.button("Guardar experimento"):
    st.session_state.registro.append({
        "Función": modo, "α": round(pesos[0], 2), "β": round(pesos[1], 2), "γ": round(pesos[2], 2),
        "d_ref": d_ref, "b_ref": b_ref,
        "Enlaces caídos": ", ".join(df.loc[~df["Disponible"], "Enlace"]) or "ninguno",
        "Ruta estática": "–".join(ruta_est) if ruta_est else "",
        "Ruta óptima": "–".join(optima) if optima else "",
    })
if st.session_state.registro:
    reg = pd.DataFrame(st.session_state.registro)
    st.dataframe(reg, hide_index=True, width="stretch")
    st.download_button("Descargar resultados_experimentos.csv", reg.to_csv(index=False).encode("utf-8"),
                       "resultados_experimentos.csv", "text/csv")
