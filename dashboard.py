import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard de Ventas", layout="wide")
st.title("📊 Dashboard de Ventas")

df = pd.read_excel("Registros_ventas.xlsx")
df["Beneficio"] = df["Importe venta total"] - df["Importe Coste total"]
df["Margen %"] = df["Beneficio"] / df["Importe venta total"] * 100
df["Días de envío"] = (df["Fecha envío"] - df["Fecha pedido"]).dt.days

# ---------- FILTROS (barra lateral) ----------
st.sidebar.header("🎛️ Filtros")

# Rango de fechas
fecha_min = df["Fecha pedido"].min().date()
fecha_max = df["Fecha pedido"].max().date()
rango = st.sidebar.date_input(
    "Rango de fechas", (fecha_min, fecha_max),
    min_value=fecha_min, max_value=fecha_max
)
if len(rango) != 2:
    st.info("Elige la fecha de inicio y la fecha final en la barra lateral.")
    st.stop()

# Selecciones múltiples
zonas = sorted(df["Zona"].unique())
zonas_elegidas = st.sidebar.multiselect("Zona", zonas, default=zonas)

productos = sorted(df["Tipo de producto"].unique())
productos_elegidos = st.sidebar.multiselect("Tipo de producto", productos, default=productos)

# Canal (botones de opción)
canales = ["Todos"] + sorted(df["Canal de venta"].unique())
canal_elegido = st.sidebar.radio("Canal de venta", canales, horizontal=True)

# Prioridad (casillas)
st.sidebar.markdown("**Prioridad**")
prioridades = sorted(df["Prioridad"].unique())
prioridades_elegidas = [
    p for p in prioridades
    if st.sidebar.checkbox(p, value=True, key=f"prioridad_{p}")
]

# Slider de unidades por pedido
u_min, u_max = int(df["Unidades"].min()), int(df["Unidades"].max())
rango_unidades = st.sidebar.slider("Unidades por pedido", u_min, u_max, (u_min, u_max))

# ---------- OPCIONES DE VISUALIZACIÓN ----------
st.sidebar.header("⚙️ Visualización")
metrica = st.sidebar.selectbox(
    "Métrica de las gráficas",
    ["Importe venta total", "Beneficio", "Unidades", "Importe Coste total"]
)
top_n = st.sidebar.slider("Top de países", 3, 20, 10)

# ---------- APLICAR LOS FILTROS ----------
df_filtrado = df[
    df["Fecha pedido"].dt.date.between(rango[0], rango[1])
    & df["Zona"].isin(zonas_elegidas)
    & df["Tipo de producto"].isin(productos_elegidos)
    & df["Prioridad"].isin(prioridades_elegidas)
    & df["Unidades"].between(rango_unidades[0], rango_unidades[1])
].copy()

if canal_elegido != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Canal de venta"] == canal_elegido]

if df_filtrado.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ---------- INDICADORES ----------
ventas = df_filtrado["Importe venta total"].sum()
beneficio = df_filtrado["Beneficio"].sum()
margen = beneficio / ventas * 100
unidades = df_filtrado["Unidades"].sum()
ticket = df_filtrado["Importe venta total"].mean()

st.caption(f"Mostrando {len(df_filtrado):,} de {len(df):,} pedidos")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Ventas totales", f"${ventas:,.0f}")
c2.metric("Beneficio", f"${beneficio:,.0f}")
c3.metric("Margen", f"{margen:.1f}%")
c4.metric("Unidades", f"{unidades:,}")
c5.metric("Ticket medio", f"${ticket:,.0f}")

st.divider()

# ---------- PESTAÑAS ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Tendencia", "🌍 Geografía", "📦 Productos", "🚚 Logística", "🗂️ Datos"]
)

# ----- Pestaña 1: Tendencia -----
with tab1:
    tipo_grafica = st.radio("Tipo de gráfica", ["Línea", "Barras", "Área"], horizontal=True)

    df_filtrado["Mes"] = df_filtrado["Fecha pedido"].dt.to_period("M").astype(str)
    serie = df_filtrado.groupby("Mes")[metrica].sum().reset_index()

    if tipo_grafica == "Línea":
        fig = px.line(serie, x="Mes", y=metrica, markers=True, title=f"{metrica} por mes")
    elif tipo_grafica == "Barras":
        fig = px.bar(serie, x="Mes", y=metrica, title=f"{metrica} por mes")
    else:
        fig = px.area(serie, x="Mes", y=metrica, title=f"{metrica} por mes")
    st.plotly_chart(fig, width="stretch")

    izq, der = st.columns(2)
    with izq:
        por_canal = df_filtrado.groupby("Canal de venta")[metrica].sum().reset_index()
        fig = px.pie(por_canal, names="Canal de venta", values=metrica,
                     hole=0.4, title="Por canal de venta")
        st.plotly_chart(fig, width="stretch")
    with der:
        por_prioridad = df_filtrado.groupby("Prioridad")[metrica].sum().reset_index()
        fig = px.bar(por_prioridad, x="Prioridad", y=metrica,
                     color="Prioridad", title="Por prioridad")
        st.plotly_chart(fig, width="stretch")

# ----- Pestaña 2: Geografía -----
with tab2:
    por_pais = df_filtrado.groupby("País")[metrica].sum().reset_index()

    izq, der = st.columns([3, 2])
    with izq:
        fig = px.choropleth(
            por_pais, locations="País", locationmode="country names",
            color=metrica, color_continuous_scale="Viridis",
            title=f"{metrica} por país"
        )
        st.plotly_chart(fig, width="stretch")
    with der:
        top = por_pais.nlargest(top_n, metrica).sort_values(metrica)
        fig = px.bar(top, x=metrica, y="País", orientation="h",
                     title=f"Top {top_n} países")
        st.plotly_chart(fig, width="stretch")

# ----- Pestaña 3: Productos -----
with tab3:
    por_producto = df_filtrado.groupby("Tipo de producto")[metrica].sum().reset_index()
    por_producto = por_producto.sort_values(metrica)
    fig = px.bar(por_producto, x=metrica, y="Tipo de producto",
                 orientation="h", title=f"{metrica} por tipo de producto")
    st.plotly_chart(fig, width="stretch")

    fig = px.box(df_filtrado, x="Tipo de producto", y="Margen %",
                 color="Tipo de producto", title="Distribución del margen % por producto")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, width="stretch")

# ----- Pestaña 4: Logística -----
with tab4:
    l1, l2, l3 = st.columns(3)
    l1.metric("Días de envío (promedio)", f"{df_filtrado['Días de envío'].mean():.1f}")
    l2.metric("Mediana", f"{df_filtrado['Días de envío'].median():.0f}")
    l3.metric("Máximo", f"{df_filtrado['Días de envío'].max():.0f}")

    intervalos = st.slider("Intervalos del histograma", 5, 60, 25)
    fig = px.histogram(df_filtrado, x="Días de envío", nbins=intervalos,
                       color="Prioridad", title="Días entre pedido y envío")
    st.plotly_chart(fig, width="stretch")

    fig = px.scatter(df_filtrado, x="Unidades", y="Importe venta total",
                     color="Tipo de producto", hover_data=["ID Pedido", "País"],
                     opacity=0.7, title="Unidades vs importe de venta (cada punto es un pedido)")
    st.plotly_chart(fig, width="stretch")

# ----- Pestaña 5: Datos -----
with tab5:
    columnas = st.multiselect("Columnas a mostrar", list(df_filtrado.columns),
                              default=list(df_filtrado.columns))
    buscar = st.text_input("Buscar por ID de cliente o de pedido")

    tabla = df_filtrado[columnas]
    if buscar:
        coincide = df_filtrado[["ID Cliente", "ID Pedido"]].astype(str).apply(
            lambda col: col.str.contains(buscar, case=False)
        ).any(axis=1)
        tabla = tabla[coincide]

    st.dataframe(tabla, width="stretch", height=400)
    st.download_button(
        "⬇️ Descargar datos filtrados (CSV)",
        tabla.to_csv(index=False).encode("utf-8-sig"),
        file_name="ventas_filtradas.csv",
        mime="text/csv",
    )