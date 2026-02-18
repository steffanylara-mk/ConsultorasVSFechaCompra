"""
Mary Kay de México — Dashboard de Órdenes (Brand-aligned)
Autora: Steffany Lara | Market Intelligence
Fecha: Febrero 2026

Ejecutar con:
    streamlit run app_marykay_brand.py

Notas:
- UI sin emojis (por requerimiento).
- Estética: fondo blanco, acentos rosa, tipografía limpia, cortes diagonales.
- Evita tablas oscuras y decoraciones tipo “corazones en fila”.
- Corrige errores comunes de Streamlit Styler + Plotly fillcolor.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import warnings
warnings.filterwarnings("ignore")

# -----------------------------
# Config
# -----------------------------
st.set_page_config(
    page_title="Mary Kay · Órdenes",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Brand tokens (ajusta si quieres)
# -----------------------------
# Rosa principal (tu elección previa, funciona bien)
MK_PINK = "#E91E8C"
MK_PINK_DARK = "#C2185B"
MK_PINK_SOFT = "#FCE4EC"
MK_GRAY_900 = "#1F2937"
MK_GRAY_700 = "#374151"
MK_GRAY_500 = "#6B7280"
MK_GRAY_200 = "#E5E7EB"
MK_WHITE = "#FFFFFF"

# Para gráficos (4 grupos)
GRUPO_ORDER = ["Días 1-8", "Días 9-16", "Días 17-24", "Días 25-fin"]
COLORES_GRUPOS = [MK_PINK, MK_PINK_DARK, "#F06292", MK_GRAY_500]

# Logo (el que pediste)
LOGO_URL = "https://1000marcas.net/wp-content/uploads/2021/05/Mary-Kay-logo.jpg"

# -----------------------------
# CSS (Brand-aligned, limpio)
# -----------------------------
st.markdown(
    f"""
<style>
    /* Base */
    .stApp {{
        background: {MK_WHITE};
        color: {MK_GRAY_900};
    }}
    .main .block-container {{
        max-width: 1400px;
        padding-top: 1.25rem;
        padding-bottom: 2.0rem;
    }}

    /* Sidebar sobrio, con rosa muy suave */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {MK_WHITE} 0%, {MK_PINK_SOFT} 100%);
        border-right: 1px solid {MK_GRAY_200};
    }}
    [data-testid="stSidebar"] * {{
        color: {MK_GRAY_900} !important;
    }}

    /* Tipografía: sin depender de fuentes instaladas */
    h1, h2, h3 {{
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
        letter-spacing: -0.02em;
    }}
    p, div, span, label {{
        font-family: ui-serif, Georgia, "Times New Roman", serif;
    }}

    /* Header con “corte diagonal” (45°) como lenguaje visual */
    .mk-header {{
        position: relative;
        background: {MK_WHITE};
        border: 1px solid {MK_GRAY_200};
        border-radius: 18px;
        padding: 22px 24px;
        overflow: hidden;
        box-shadow: 0 8px 18px rgba(31,41,55,0.06);
        margin-bottom: 14px;
    }}
    .mk-header:before {{
        content: "";
        position: absolute;
        top: -40px;
        right: -60px;
        width: 240px;
        height: 240px;
        background: {MK_PINK_SOFT};
        transform: rotate(45deg);
        border-radius: 26px;
        border: 1px solid rgba(233,30,140,0.10);
    }}
    .mk-title {{
        margin: 0;
        color: {MK_PINK_DARK};
        font-size: 2.2rem;
        font-weight: 800;
    }}
    .mk-subtitle {{
        margin-top: 6px;
        margin-bottom: 0;
        color: {MK_GRAY_700};
        font-size: 1.02rem;
    }}

    /* KPI Cards */
    .mk-kpi {{
        background: {MK_WHITE};
        border: 1px solid {MK_GRAY_200};
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: 0 6px 14px rgba(31,41,55,0.05);
        height: 100%;
        position: relative;
        overflow: hidden;
    }}
    .mk-kpi:after {{
        content: "";
        position: absolute;
        bottom: -30px;
        left: -60px;
        width: 160px;
        height: 160px;
        background: rgba(233,30,140,0.08);
        transform: rotate(45deg);
        border-radius: 18px;
    }}
    .mk-kpi-label {{
        color: {MK_GRAY_700};
        font-size: 0.9rem;
        margin-bottom: 6px;
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial;
        font-weight: 600;
    }}
    .mk-kpi-value {{
        color: {MK_PINK_DARK};
        font-size: 1.9rem;
        font-weight: 900;
        margin: 0;
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial;
    }}
    .mk-kpi-note {{
        color: {MK_GRAY_500};
        font-size: 0.85rem;
        margin-top: 6px;
    }}

    /* Section cards */
    .mk-card {{
        background: {MK_WHITE};
        border: 1px solid {MK_GRAY_200};
        border-radius: 16px;
        padding: 16px 16px;
        box-shadow: 0 6px 14px rgba(31,41,55,0.05);
        margin-top: 10px;
    }}
    .mk-card-title {{
        margin: 0 0 10px 0;
        color: {MK_GRAY_900};
        font-weight: 800;
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial;
    }}

    /* Buttons */
    .stButton>button {{
        background: {MK_PINK_DARK};
        color: {MK_WHITE};
        border: none;
        border-radius: 999px;
        padding: 10px 18px;
        font-weight: 700;
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial;
    }}
    .stButton>button:hover {{
        opacity: 0.92;
    }}

    /* Tabs - limpios */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
        border-bottom: 1px solid {MK_GRAY_200};
    }}
    .stTabs [data-baseweb="tab"] {{
        background: {MK_WHITE};
        border: 1px solid {MK_GRAY_200};
        border-bottom: none;
        border-radius: 12px 12px 0 0;
        color: {MK_GRAY_700};
        font-weight: 700;
        padding: 10px 14px;
    }}
    .stTabs [aria-selected="true"] {{
        background: {MK_PINK_SOFT} !important;
        color: {MK_PINK_DARK} !important;
        border-color: rgba(233,30,140,0.25) !important;
    }}

    /* Dataframe container spacing */
    [data-testid="stDataFrame"] {{
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid {MK_GRAY_200};
    }}

    /* Caption */
    .mk-caption {{
        color: {MK_GRAY_500};
        font-size: 0.9rem;
        margin-top: 2px;
    }}

    /* Insight box */
    .mk-insight {{
        background: linear-gradient(90deg, rgba(233,30,140,0.10), rgba(233,30,140,0.04));
        border: 1px solid rgba(233,30,140,0.18);
        border-left: 6px solid {MK_PINK_DARK};
        border-radius: 14px;
        padding: 14px 16px;
        color: {MK_GRAY_900};
        font-family: ui-serif, Georgia, "Times New Roman", serif;
        margin-top: 12px;
    }}
</style>
""",
    unsafe_allow_html=True
)

# -----------------------------
# Helpers
# -----------------------------
def asignar_grupo(day: int) -> str:
    if 1 <= day <= 8:
        return "Días 1-8"
    if 9 <= day <= 16:
        return "Días 9-16"
    if 17 <= day <= 24:
        return "Días 17-24"
    return "Días 25-fin"


@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos(file) -> pd.DataFrame:
    df = pd.read_csv(file)

    # Normalización robusta de columnas (por si vienen con nombres distintos)
    # Ajusta aquí si tu CSV usa otros nombres reales.
    required = ["OrderDateKEY", "OrderMonthKey", "ConsultantNumber", "OrderKEY"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Falta columna requerida: {col}")

    # TotalWhosale vs TotalWholesale (tu código usaba TotalWhosale)
    if "TotalWhosale" in df.columns:
        ws_col = "TotalWhosale"
    elif "TotalWholesale" in df.columns:
        ws_col = "TotalWholesale"
    else:
        raise ValueError("Falta columna de wholesale: TotalWhosale o TotalWholesale")

    df["__WS_COL__"] = ws_col

    # Parse fechas
    df["OrderDateKEY"] = pd.to_datetime(df["OrderDateKEY"].astype(str), format="%Y%m%d", errors="coerce")
    df["OrderMonthKey"] = pd.to_datetime(df["OrderMonthKey"].astype(str), format="%Y%m", errors="coerce")

    df = df.dropna(subset=["OrderDateKEY", "OrderMonthKey"])

    df["Day"] = df["OrderDateKEY"].dt.day
    df["MonthSort"] = df["OrderMonthKey"]
    df["Month"] = df["OrderMonthKey"].dt.strftime("%b %Y")

    df["GrupoDias"] = df["Day"].apply(asignar_grupo)
    df["GrupoDias"] = pd.Categorical(df["GrupoDias"], categories=GRUPO_ORDER, ordered=True)

    # Asegura wholesale numérico
    df[ws_col] = pd.to_numeric(df[ws_col], errors="coerce").fillna(0)

    return df


@st.cache_data(show_spinner="Procesando análisis...")
def construir_primer(df: pd.DataFrame) -> pd.DataFrame:
    ws_col = df["__WS_COL__"].iloc[0]

    # Ordenar para tomar primer día
    primer = (
        df.sort_values("OrderDateKEY")
        .groupby(["ConsultantNumber", "MonthSort", "Month"], as_index=False)
        .agg(
            PrimerDia=("Day", "first"),
            TotalOrdenes=("OrderKEY", "nunique"),
            TotalWholesale=(ws_col, "sum"),
            CareerLevel=("CareerLevelCode", "first") if "CareerLevelCode" in df.columns else ("OrderKEY", "size"),
            NewRecruit=("NewRecruitIndicator", "first") if "NewRecruitIndicator" in df.columns else ("OrderKEY", "size"),
        )
    )

    # Si no existían esas columnas, reemplazamos por NaN para no romper el UI
    if "CareerLevelCode" not in df.columns:
        primer["CareerLevel"] = np.nan
    if "NewRecruitIndicator" not in df.columns:
        primer["NewRecruit"] = np.nan

    primer["GrupoPrimerOrden"] = primer["PrimerDia"].apply(asignar_grupo)
    primer["GrupoPrimerOrden"] = pd.Categorical(primer["GrupoPrimerOrden"], categories=GRUPO_ORDER, ordered=True)

    primer["Reordena"] = primer["TotalOrdenes"] > 1
    primer["AvgWholesale"] = np.where(primer["TotalOrdenes"] > 0, primer["TotalWholesale"] / primer["TotalOrdenes"], 0)

    return primer


def mk_plotly_layout(fig: go.Figure, title: str, y_title: str = "") -> go.Figure:
    # Layout corporativo: blanco, grid suave, tipografía consistente
    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=16, color=MK_GRAY_900)),
        paper_bgcolor=MK_WHITE,
        plot_bgcolor=MK_WHITE,
        margin=dict(t=60, b=40, l=50, r=20),
        font=dict(family='ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial',
                  color=MK_GRAY_700),
        xaxis=dict(
            showgrid=False,
            linecolor=MK_GRAY_200,
            tickfont=dict(color=MK_GRAY_700),
        ),
        yaxis=dict(
            title=y_title,
            gridcolor="rgba(229,231,235,0.9)",  # MK_GRAY_200 suave
            zeroline=False,
            tickfont=dict(color=MK_GRAY_700),
        ),
        legend=dict(orientation="h", y=-0.2),
    )
    return fig


def safe_rgba(hex_color: str, alpha: float) -> str:
    # Plotly no acepta hex con alpha tipo #RRGGBBAA; usa rgba.
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.image(LOGO_URL, use_container_width=True)
    st.markdown("### Filtros")
    st.markdown("---")

    uploaded = st.file_uploader(
        "Cargar CSV de órdenes",
        type=["csv"],
        help="Archivo analysis_MonthlyOrdersByDay_PV.csv",
    )

    st.markdown("---")
    st.markdown(
        "<div class='mk-caption'>Market Intelligence · Mary Kay de México<br>"
        "Steffany Lara · Febrero 2026</div>",
        unsafe_allow_html=True,
    )

# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
<div class="mk-header">
  <h1 class="mk-title">Análisis de Comportamiento de Órdenes</h1>
  <p class="mk-subtitle">Mary Kay de México · Jul 2025 – Ene 2026</p>
</div>
""",
    unsafe_allow_html=True
)

if uploaded is None:
    st.markdown(
        "<div class='mk-insight'>Carga el archivo CSV desde la barra lateral para comenzar.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# -----------------------------
# Load + process
# -----------------------------
df = cargar_datos(uploaded)
primer = construir_primer(df)

# Meses disponibles y filtro
meses_disponibles = (
    primer[["Month", "MonthSort"]].drop_duplicates().sort_values("MonthSort")["Month"].tolist()
)
with st.sidebar:
    meses_sel = st.multiselect("Meses a analizar", meses_disponibles, default=meses_disponibles)

if not meses_sel:
    st.warning("Selecciona al menos un mes.")
    st.stop()

primer_f = primer[primer["Month"].isin(meses_sel)].copy()

# -----------------------------
# Summary
# -----------------------------
resumen = (
    primer_f.groupby("GrupoPrimerOrden", observed=True)
    .agg(
        ConsultorasUnicas=("ConsultantNumber", "nunique"),
        PctReorden=("Reordena", "mean"),
        AvgWholesale=("AvgWholesale", "mean"),
        MedianaWS=("AvgWholesale", "median"),
    )
    .reset_index()
)

resumen["PctReorden_%"] = (resumen["PctReorden"] * 100).round(1)
resumen["AvgWholesale"] = resumen["AvgWholesale"].round(0)
resumen["MedianaWS"] = resumen["MedianaWS"].round(0)

# KPIs
total_cons = int(primer_f["ConsultantNumber"].nunique())
pct_reorden = float(primer_f["Reordena"].mean() * 100) if len(primer_f) else 0.0
avg_ws_total = float(primer_f["AvgWholesale"].mean()) if len(primer_f) else 0.0
if len(resumen):
    grp_top = str(resumen.loc[resumen["PctReorden_%"].idxmax(), "GrupoPrimerOrden"])
else:
    grp_top = "N/A"

# -----------------------------
# KPI row (cards)
# -----------------------------
k1, k2, k3, k4 = st.columns(4)

def kpi_card(col, label, value, note=""):
    with col:
        st.markdown(
            f"""
<div class="mk-kpi">
  <div class="mk-kpi-label">{label}</div>
  <p class="mk-kpi-value">{value}</p>
  <div class="mk-kpi-note">{note}</div>
</div>
""",
            unsafe_allow_html=True,
        )

kpi_card(k1, "Consultoras únicas", f"{total_cons:,}")
kpi_card(k2, "% Reorden global", f"{pct_reorden:.1f}%")
kpi_card(k3, "Avg Wholesale", f"${avg_ws_total:,.0f}")
kpi_card(k4, "Grupo top reorden", grp_top)

st.markdown("")

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Por mes", "Wholesale", "Datos"])

# -----------------------------
# Tab 1: Resumen
# -----------------------------
with tab1:
    cA, cB = st.columns([1, 1])

    with cA:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=resumen["GrupoPrimerOrden"].astype(str),
            y=resumen["ConsultorasUnicas"],
            marker=dict(color=COLORES_GRUPOS[:len(resumen)], line=dict(color=MK_WHITE, width=1)),
            text=[f"{int(v):,}" for v in resumen["ConsultorasUnicas"]],
            textposition="outside",
            cliponaxis=False,
        ))
        fig1 = mk_plotly_layout(fig1, "Consultoras únicas por grupo", "Consultoras")
        st.plotly_chart(fig1, use_container_width=True)

    with cB:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=resumen["GrupoPrimerOrden"].astype(str),
            y=resumen["PctReorden_%"],
            marker=dict(color=COLORES_GRUPOS[:len(resumen)], line=dict(color=MK_WHITE, width=1)),
            text=[f"{v:.1f}%" for v in resumen["PctReorden_%"]],
            textposition="outside",
            cliponaxis=False,
        ))
        fig2 = mk_plotly_layout(fig2, "% Reorden por grupo", "% Reorden")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="mk-card"><h3 class="mk-card-title">Tabla resumen</h3></div>', unsafe_allow_html=True)

    tabla = resumen[["GrupoPrimerOrden", "ConsultorasUnicas", "PctReorden_%", "AvgWholesale", "MedianaWS"]].copy()
    tabla.columns = ["Grupo", "Consultoras únicas", "% Reorden", "Avg Wholesale (MXN)", "Mediana Wholesale (MXN)"]

    # Styler robusto (sin hide_index en st.dataframe; se oculta desde Styler)
    styled = (
        tabla.style
        .format({
            "Consultoras únicas": "{:,}",
            "% Reorden": "{:.1f}%",
            "Avg Wholesale (MXN)": "${:,.0f}",
            "Mediana Wholesale (MXN)": "${:,.0f}",
        })
        .background_gradient(subset=["% Reorden"], cmap="RdPu")
        .background_gradient(subset=["Avg Wholesale (MXN)"], cmap="RdPu")
    )
    # pandas >= 1.4 generalmente soporta hide(axis="index")
    try:
        styled = styled.hide(axis="index")
    except Exception:
        pass

    st.dataframe(styled, use_container_width=True)

    # Insight: diferencia 1–8 vs 25-fin
    r_idx = resumen.set_index("GrupoPrimerOrden")
    if GRUPO_ORDER[0] in r_idx.index and GRUPO_ORDER[-1] in r_idx.index:
        diff = float(r_idx.loc[GRUPO_ORDER[0], "PctReorden_%"] - r_idx.loc[GRUPO_ORDER[-1], "PctReorden_%"])
        sign = "mayor" if diff >= 0 else "menor"
        st.markdown(
            f"<div class='mk-insight'><b>Insight:</b> Las consultoras que colocan su primer pedido en "
            f"<b>{GRUPO_ORDER[0]}</b> tienen un % de reorden <b>{abs(diff):.1f} puntos porcentuales {sign}</b> "
            f"comparado con <b>{GRUPO_ORDER[-1]}</b>.</div>",
            unsafe_allow_html=True,
        )

# -----------------------------
# Tab 2: Por mes (líneas + heatmap)
# -----------------------------
with tab2:
    resumen_mes = (
        primer_f.groupby(["MonthSort", "Month", "GrupoPrimerOrden"], observed=True)
        .agg(
            ConsultorasUnicas=("ConsultantNumber", "nunique"),
            PctReorden=("Reordena", "mean"),
            AvgWholesale=("AvgWholesale", "mean"),
        )
        .reset_index()
        .sort_values(["MonthSort", "GrupoPrimerOrden"])
    )
    resumen_mes["PctReorden_%"] = (resumen_mes["PctReorden"] * 100).round(1)
    resumen_mes["AvgWholesale"] = resumen_mes["AvgWholesale"].round(0)

    fig_line = go.Figure()
    for grupo, color in zip(GRUPO_ORDER, COLORES_GRUPOS):
        sub = resumen_mes[resumen_mes["GrupoPrimerOrden"] == grupo].sort_values("MonthSort")
        if sub.empty:
            continue
        fig_line.add_trace(go.Scatter(
            x=sub["Month"],
            y=sub["PctReorden_%"],
            mode="lines+markers",
            name=grupo,
            line=dict(color=color, width=3),
            marker=dict(size=8, color=color),
            # (sin fillcolor para evitar el error que te salió)
        ))
    fig_line = mk_plotly_layout(fig_line, "Evolución del % Reorden por mes", "% Reorden")
    st.plotly_chart(fig_line, use_container_width=True)

    # Heatmap
    pivot = resumen_mes.pivot_table(index="GrupoPrimerOrden", columns="Month", values="PctReorden_%")
    # Orden de columnas por MonthSort
    col_order = resumen_mes[["MonthSort", "Month"]].drop_duplicates().sort_values("MonthSort")["Month"].tolist()
    pivot = pivot[[c for c in col_order if c in pivot.columns]]

    z = pivot.values.astype(float)
    text_vals = [[("" if np.isnan(v) else f"{v:.1f}%") for v in row] for row in z]

    heat = go.Figure(go.Heatmap(
        z=z,
        x=list(pivot.columns),
        y=list(pivot.index.astype(str)),
        text=text_vals,
        texttemplate="%{text}",
        colorscale=[[0, MK_WHITE], [0.35, MK_PINK_SOFT], [0.7, MK_PINK], [1, MK_PINK_DARK]],
        showscale=True,
        colorbar=dict(title="%"),
    ))
    heat = mk_plotly_layout(heat, "Heatmap · % Reorden (grupo × mes)")
    heat.update_layout(margin=dict(t=60, b=40, l=140, r=20))
    st.plotly_chart(heat, use_container_width=True)

# -----------------------------
# Tab 3: Wholesale
# -----------------------------
with tab3:
    c1, c2 = st.columns(2)

    with c1:
        fig_ws = go.Figure()
        fig_ws.add_trace(go.Bar(
            x=resumen["GrupoPrimerOrden"].astype(str),
            y=resumen["AvgWholesale"],
            marker=dict(color=COLORES_GRUPOS[:len(resumen)], line=dict(color=MK_WHITE, width=1)),
            text=[f"${v:,.0f}" for v in resumen["AvgWholesale"]],
            textposition="outside",
            cliponaxis=False,
        ))
        fig_ws = mk_plotly_layout(fig_ws, "Avg Wholesale por grupo (global)", "MXN")
        st.plotly_chart(fig_ws, use_container_width=True)

    with c2:
        fig_box = go.Figure()
        for grupo, color in zip(GRUPO_ORDER, COLORES_GRUPOS):
            sub = primer_f[primer_f["GrupoPrimerOrden"] == grupo]["AvgWholesale"]
            if sub.empty:
                continue
            fig_box.add_trace(go.Box(
                y=sub,
                name=grupo,
                marker_color=color,
                line_color=color,
                boxmean=True,
            ))
        fig_box = mk_plotly_layout(fig_box, "Distribución de Wholesale por grupo", "MXN")
        fig_box.update_yaxes(tickprefix="$", separatethousands=True)
        st.plotly_chart(fig_box, use_container_width=True)

    # Heatmap wholesale
    if not resumen_mes.empty:
        pivot_ws = resumen_mes.pivot_table(index="GrupoPrimerOrden", columns="Month", values="AvgWholesale")
        pivot_ws = pivot_ws[[c for c in col_order if c in pivot_ws.columns]]

        z2 = pivot_ws.values.astype(float)
        text2 = [[("" if np.isnan(v) else f"${v:,.0f}") for v in row] for row in z2]

        heat2 = go.Figure(go.Heatmap(
            z=z2,
            x=list(pivot_ws.columns),
            y=list(pivot_ws.index.astype(str)),
            text=text2,
            texttemplate="%{text}",
            colorscale=[[0, MK_WHITE], [0.35, MK_PINK_SOFT], [0.7, MK_PINK], [1, MK_PINK_DARK]],
            showscale=True,
            colorbar=dict(title="MXN"),
        ))
        heat2 = mk_plotly_layout(heat2, "Heatmap · Avg Wholesale (grupo × mes)")
        heat2.update_layout(margin=dict(t=60, b=40, l=140, r=20))
        st.plotly_chart(heat2, use_container_width=True)

    st.markdown(
        "<div class='mk-insight'><b>Lectura recomendada:</b> interpreta el boxplot para ver mediana y dispersión; "
        "el promedio puede moverse por outliers. El heatmap te ayuda a identificar meses atípicos (por ejemplo, enero).</div>",
        unsafe_allow_html=True,
    )

# -----------------------------
# Tab 4: Datos
# -----------------------------
with tab4:
    st.markdown('<div class="mk-card"><h3 class="mk-card-title">Datos procesados</h3></div>', unsafe_allow_html=True)
    st.markdown(f"<div class='mk-caption'>Registros: {len(primer_f):,}</div>", unsafe_allow_html=True)

    cols_show = [
        "ConsultantNumber", "Month", "GrupoPrimerOrden", "PrimerDia",
        "TotalOrdenes", "TotalWholesale", "AvgWholesale", "Reordena"
    ]
    data_view = primer_f[cols_show].sort_values(["Month", "GrupoPrimerOrden"]).reset_index(drop=True)

    st.dataframe(
        data_view,
        use_container_width=True,
        height=520,
    )

    csv_out = data_view.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar tabla procesada (CSV)",
        data=csv_out,
        file_name="primer_orden_mes_analisis.csv",
        mime="text/csv",
    )

# -----------------------------
# Footer
# -----------------------------
st.markdown(
    "<div class='mk-caption' style='text-align:center; padding-top: 14px;'>"
    "Mary Kay de México · Market Intelligence · Steffany Lara · Febrero 2026"
    "</div>",
    unsafe_allow_html=True,
)
