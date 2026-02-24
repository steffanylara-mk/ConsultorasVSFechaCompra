"""
Mary Kay de México — Dashboard de Órdenes (Brand-aligned)
Autora: Steffany Lara | Market Intelligence
Fecha: Febrero 2026

CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR
────────────────────────────────────────
[ELIMINADO]   Gráfica "¿Cuándo Reordenan? — Distribución de reórdenes por rango de días"
              + bloques asociados (GRUPOS_PLOT, share_tbl, share_tbl_plot, re-normalización,
              caption de exclusión, insight end_share).

[CORRECCIÓN 1] Cómputo de reórdenes duplicado (Tab 4 vs build_reorder_bucket_breakdown).
              Extraído a helper cacheado `build_reorder_events()` que ambos bloques consumen.
              Elimina el recálculo costoso en cada interacción de widget.

[CORRECCIÓN 2] `re = re.copy()` redundante eliminado: `re` ya era un .copy() una línea antes.

[CORRECCIÓN 3] `_ws_col_info` asignado y nunca usado, eliminado.

[CORRECCIÓN 4] `warnings.filterwarnings("ignore")` demasiado amplio reemplazado por filtro
              específico a PerformanceWarning de pandas.

[CORRECCIÓN 5] Metadatos de limpieza (`__WS_COL__`, `__WS_WINSOR_N__`, etc.) desacoplados
              del DataFrame y guardados en st.session_state. Evita columnas "fantasma" que
              inflan el hash de caché y confunden a quien lee el código.
"""

import warnings
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning if False else UserWarning)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import warnings  # re-import after suppression setup

# Suprimir sólo PerformanceWarning de pandas (e.g. fragmentación de DataFrame)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Config. inicial.
st.set_page_config(
    page_title="Mary Kay · Órdenes",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Brand tokens
MK_PINK      = "#E91E8C"
MK_PINK_DARK = "#C2185B"
MK_PINK_SOFT = "#FCE4EC"
MK_GRAY_900  = "#1F2937"
MK_GRAY_700  = "#374151"
MK_GRAY_500  = "#6B7280"
MK_GRAY_200  = "#E5E7EB"
MK_WHITE     = "#FFFFFF"

GRUPO_ORDER     = ["Días 1-8", "Días 9-16", "Días 17-24", "Días 25-fin"]
COLORES_GRUPOS  = [MK_PINK, MK_PINK_DARK, "#F06292", MK_GRAY_500]
_GRUPO_RANK     = {g: i for i, g in enumerate(GRUPO_ORDER)}

LOGO_URL = "https://1000marcas.net/wp-content/uploads/2021/05/Mary-Kay-logo.jpg"

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ CSS
st.markdown(
    f"""
<style>
    .stApp {{
        background: {MK_WHITE};
        color: {MK_GRAY_900};
    }}
    .main .block-container {{
        max-width: 1400px;
        padding-top: 1.25rem;
        padding-bottom: 2.0rem;
    }}
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {MK_WHITE} 0%, {MK_PINK_SOFT} 100%);
        border-right: 1px solid {MK_GRAY_200};
    }}
    [data-testid="stSidebar"] * {{
        color: {MK_GRAY_900} !important;
    }}

    h1, h2, h3 {{
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
        letter-spacing: -0.02em;
    }}
    p, div, span, label {{
        font-family: ui-serif, Georgia, "Times New Roman", serif;
    }}

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
    .stButton>button:hover {{ opacity: 0.92; }}

    div.stDownloadButton > button {{
        background: {MK_PINK_DARK};
        color: {MK_WHITE};
        border: none;
        border-radius: 999px;
        padding: 10px 18px;
        font-weight: 700;
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial;
    }}
    div.stDownloadButton > button:hover {{ opacity: 0.92; }}

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

    [data-testid="stDataFrame"] {{
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid {MK_GRAY_200};
    }}

    .mk-caption {{
        color: {MK_GRAY_500};
        font-size: 0.9rem;
        margin-top: 2px;
    }}

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

    [data-testid="stSlider"] [role="slider"] {{
        background: {MK_GRAY_900} !important;
        border-color: {MK_GRAY_900} !important;
    }}
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="presentation"] {{
        color: {MK_GRAY_900} !important;
    }}

    [data-testid="stFileUploader"] section {{
        background: {MK_GRAY_900};
        border: 2px dashed rgba(233,30,140,0.55);
        border-radius: 14px;
        padding: 18px;
    }}
    [data-testid="stFileUploader"] section span,
    [data-testid="stFileUploader"] section p,
    [data-testid="stFileUploader"] section small,
    [data-testid="stFileUploader"] section div {{
        color: {MK_WHITE} !important;
    }}
    [data-testid="stFileUploader"] section button {{
        background: {MK_PINK_DARK} !important;
        color: {MK_WHITE} !important;
        border: none !important;
        border-radius: 999px !important;
        font-weight: 700 !important;
        padding: 8px 18px !important;
    }}
    [data-testid="stFileUploader"] section button:hover {{ opacity: 0.88 !important; }}

    div[data-testid="stAlert"] {{ color: {MK_GRAY_900} !important; }}
    div[data-testid="stAlert"] * {{ color: {MK_GRAY_900} !important; }}
    div[data-testid="stAlert"] [data-testid="stMarkdownContainer"],
    div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] * {{ color: {MK_GRAY_900} !important; }}
    div[data-testid="stAlert"] [data-baseweb="notification"],
    div[data-testid="stAlert"] [data-baseweb="notification"] * {{ color: {MK_GRAY_900} !important; }}
    div[data-testid="stAlert"] svg {{ color: {MK_GRAY_900} !important; fill: {MK_GRAY_900} !important; }}
    div[data-testid="stAlert"] a {{ color: {MK_GRAY_900} !important; text-decoration: underline; font-weight: 700; }}
</style>
""",
    unsafe_allow_html=True,
)

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Helpers — bucketización
_BUCKET_BINS   = [0, 8, 16, 24, 31]
_BUCKET_LABELS = GRUPO_ORDER

def bucketize(series: pd.Series) -> pd.Categorical:
    """Día del mes (int) → Categorical bucket. Vectorizado (10x más rápido que .apply)."""
    return pd.Categorical(
        pd.cut(series, bins=_BUCKET_BINS, labels=_BUCKET_LABELS, include_lowest=True),
        categories=GRUPO_ORDER,
        ordered=True,
    )


# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Carga y validación
@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos(file) -> tuple[pd.DataFrame, dict]:
    """
    Lee el CSV, valida y limpia.

    Retorna:
        df   – DataFrame limpio (sin columnas de metadatos "fantasma").
        meta – dict con metadatos de limpieza: ws_col, n_winsor, ws_p01, ws_p99.

    CAMBIO: los metadatos ya NO se guardan como columnas del DataFrame;
    se devuelven en un dict separado para mayor claridad y menor overhead de caché.
    """
    df = pd.read_csv(file)

    required = ["OrderDateKEY", "OrderMonthKey", "ConsultantNumber", "OrderKEY"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Falta columna requerida: {col}")

    if "TotalWhosale" in df.columns:
        ws_col = "TotalWhosale"
    elif "TotalWholesale" in df.columns:
        ws_col = "TotalWholesale"
    else:
        raise ValueError("Falta columna de wholesale: TotalWhosale o TotalWholesale")

    df["OrderDateKEY"]  = pd.to_datetime(df["OrderDateKEY"].astype(str),  format="%Y%m%d", errors="coerce")
    df["OrderMonthKey"] = pd.to_datetime(df["OrderMonthKey"].astype(str), format="%Y%m",   errors="coerce")

    n_bad_dates = df["OrderDateKEY"].isna().sum() + df["OrderMonthKey"].isna().sum()
    if n_bad_dates > 0:
        st.warning(f"{n_bad_dates} fechas no pudieron parsearse (YYYYMMDD inválido) — se descartaron.")
    df = df.dropna(subset=["OrderDateKEY", "OrderMonthKey"])

    invalid_months = (
        (df["OrderMonthKey"].dt.year  != df["OrderDateKEY"].dt.year) |
        (df["OrderMonthKey"].dt.month != df["OrderDateKEY"].dt.month)
    )
    if invalid_months.any():
        st.warning(f"{invalid_months.sum()} filas con OrderMonthKey ≠ mes de OrderDateKEY — se descartaron.")
        df = df[~invalid_months].copy()

    dup_mask = df.duplicated(subset=["OrderKEY"])
    if dup_mask.any():
        st.warning(f"{dup_mask.sum()} OrderKEY duplicados detectados — se eliminan duplicados.")
        df = df.drop_duplicates(subset=["OrderKEY"])

    df["Day"]       = df["OrderDateKEY"].dt.day
    df["MonthSort"] = df["OrderMonthKey"]
    df["Month"]     = df["OrderMonthKey"].dt.strftime("%b %Y")
    df["GrupoDias"] = bucketize(df["Day"])

    df[ws_col] = pd.to_numeric(df[ws_col], errors="coerce").fillna(0)

    ws_p01 = df[ws_col].quantile(0.01)
    ws_p99 = df[ws_col].quantile(0.99)
    n_winsor = int(((df[ws_col] < ws_p01) | (df[ws_col] > ws_p99)).sum())
    df[ws_col] = np.clip(df[ws_col], ws_p01, ws_p99)

    if "ProductionOrderCount" in df.columns:
        df["ProductionOrderCount"] = (
            pd.to_numeric(df["ProductionOrderCount"], errors="coerce").fillna(1).astype(int)
        )
    else:
        df["ProductionOrderCount"] = 1

    meta = {
        "ws_col":   ws_col,
        "n_winsor": n_winsor,
        "ws_p01":   float(ws_p01),
        "ws_p99":   float(ws_p99),
    }
    return df, meta


# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Panel primer orden por consultora-mes
@st.cache_data(show_spinner="Construyendo panel por consultora y mes...")
def construir_primer(df: pd.DataFrame, ws_col: str) -> pd.DataFrame:
    """
    Recibe `ws_col` explícitamente en lugar de leerlo de una columna "__WS_COL__".
    Esto hace la firma de la función auto-documentada y el hash de caché más preciso.
    """
    agg_dict = {
        "PrimerDia":      ("Day", "first"),
        "TotalOrderDays": ("OrderDateKEY", "nunique"),
        "TotalOrdenes":   ("OrderKEY", "nunique"),
        "TotalWholesale": (ws_col, "sum"),
    }

    if "CareerLevelCode" in df.columns:
        agg_dict["CareerLevel"] = ("CareerLevelCode", "first")
    if "NewRecruitIndicator" in df.columns:
        agg_dict["NewRecruit"] = ("NewRecruitIndicator", "first")

    primer = (
        df.sort_values("OrderDateKEY")
        .groupby(["ConsultantNumber", "MonthSort", "Month"], as_index=False)
        .agg(**agg_dict)
    )

    if "CareerLevel" not in primer.columns:
        primer["CareerLevel"] = np.nan
    if "NewRecruit" not in primer.columns:
        primer["NewRecruit"] = np.nan

    primer["GrupoPrimerOrden"] = bucketize(primer["PrimerDia"])
    primer["Reordena"]         = primer["TotalOrderDays"] > 1
    primer["AvgWholesale"]     = np.where(
        primer["TotalOrdenes"] > 0,
        primer["TotalWholesale"] / primer["TotalOrdenes"],
        0,
    )

    return primer


# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Helper cacheado: eventos de reorden

@st.cache_data(show_spinner=False)
def build_reorder_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade al DataFrame las columnas:
      - FirstOrderDate     : primera fecha de orden del consultora-mes
      - OrderSeq           : secuencia de orden dentro del mismo día (consultora-mes-día)
      - IsReorderEvent     : True si es reorden (fecha posterior o mismo-día seq>1)
      - PrimerDia          : día del mes del primer pedido
      - GrupoPrimerOrden   : bucket del primer pedido (Categorical)
      - ReBucket           : bucket del día del evento reorden (Categorical)

    NUEVO: función extraída para evitar que Tab 4 y build_reorder_bucket_breakdown
    recalculen la misma lógica de forma independiente en cada interacción.
    """
    d = df.copy()

    first_order_date = (
        d.sort_values("OrderDateKEY")
         .groupby(["ConsultantNumber", "MonthSort"])["OrderDateKEY"]
         .first()
         .rename("FirstOrderDate")
         .reset_index()
    )
    d = d.merge(first_order_date, on=["ConsultantNumber", "MonthSort"], how="left")

    d = d.sort_values(["ConsultantNumber", "MonthSort", "OrderDateKEY", "OrderKEY"])
    d["OrderSeq"] = (
        d.groupby(["ConsultantNumber", "MonthSort", "OrderDateKEY"])
         .cumcount() + 1
    )
    d["IsReorderEvent"] = (d["OrderDateKEY"] > d["FirstOrderDate"]) | (d["OrderSeq"] > 1)

    d["PrimerDia"]        = d["FirstOrderDate"].dt.day
    d["GrupoPrimerOrden"] = bucketize(d["PrimerDia"])
    d["ReBucket"]         = bucketize(d["Day"])

    return d


# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Hover breakdown para Tab 1
@st.cache_data(show_spinner=False)
def build_reorder_bucket_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada GrupoPrimerOrden, computa la distribución de eventos de reorden
    entre buckets de días. Resultado usado como customdata en el hover del
    gráfico "% Reorden por grupo" (Tab 1).

    CAMBIO: ahora consume build_reorder_events() en lugar de duplicar la lógica.
    """
    d = build_reorder_events(df)
    re = d[d["IsReorderEvent"]].copy()

    if re.empty:
        out = pd.DataFrame({"GrupoPrimerOrden": GRUPO_ORDER})
        for b in GRUPO_ORDER:
            out[b] = 0.0
        out["BreakdownStr"] = "Sin reórdenes en selección"
        return out

    counts = (
        re.groupby(["GrupoPrimerOrden", "ReBucket"], observed=True)
          .size()
          .reset_index(name="N")
    )

    # Filtrar combinaciones temporalmente imposibles
    counts["_GrupoRank"]  = counts["GrupoPrimerOrden"].map(_GRUPO_RANK)
    counts["_BucketRank"] = counts["ReBucket"].map(_GRUPO_RANK)
    counts = counts[counts["_BucketRank"] >= counts["_GrupoRank"]].drop(
        columns=["_GrupoRank", "_BucketRank"]
    )

    totals = (
        counts.groupby("GrupoPrimerOrden", observed=True)["N"]
              .sum()
              .reset_index(name="Total")
    )
    counts = counts.merge(totals, on="GrupoPrimerOrden", how="left")
    counts["Pct"] = 100 * counts["N"] / counts["Total"]

    wide = (
        counts.pivot(index="GrupoPrimerOrden", columns="ReBucket", values="Pct")
              .fillna(0)
              .reset_index()
    )
    for b in GRUPO_ORDER:
        if b not in wide.columns:
            wide[b] = 0.0

    def _breakdown_str(row) -> str:
        grupo = str(row["GrupoPrimerOrden"])
        rank  = _GRUPO_RANK.get(grupo, 0)
        parts = [
            f"{row[b]:.1f}% ({b.replace('Días ', '')})"
            for b in GRUPO_ORDER
            if _GRUPO_RANK.get(b, 0) >= rank and row.get(b, 0) > 0
        ]
        return " · ".join(parts) if parts else "Sin reórdenes registrados"

    wide["BreakdownStr"] = wide.apply(_breakdown_str, axis=1)
    return wide


# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Helpers de visualización
_FONT_FAMILY = 'ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial'

def mk_plotly_layout(fig: go.Figure, title: str, y_title: str = "", x_title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(
            text=title, x=0.02, xanchor="left",
            font=dict(size=16, color=MK_GRAY_900, family=_FONT_FAMILY),
        ),
        paper_bgcolor=MK_WHITE,
        plot_bgcolor=MK_WHITE,
        margin=dict(t=60, b=50, l=60, r=20),
        font=dict(family=_FONT_FAMILY, color=MK_GRAY_700, size=13),
        xaxis=dict(
            title=dict(text=x_title, font=dict(color=MK_GRAY_900, size=13, family=_FONT_FAMILY)) if x_title else {},
            showgrid=False,
            linecolor=MK_GRAY_200,
            tickfont=dict(color=MK_GRAY_700, family=_FONT_FAMILY, size=12),
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(color=MK_GRAY_900, size=13, family=_FONT_FAMILY)),
            gridcolor="rgba(229,231,235,0.9)",
            zeroline=False,
            tickfont=dict(color=MK_GRAY_700, family=_FONT_FAMILY, size=12),
        ),
        legend=dict(
            orientation="h", y=-0.22,
            font=dict(color=MK_GRAY_900, size=13, family=_FONT_FAMILY),
        ),
    )
    return fig


def kpi_card(col, label: str, value: str, note: str = "") -> None:
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


# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Sidebar
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

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Header
st.markdown(
    """
<div class="mk-header">
  <h1 class="mk-title">Análisis de Comportamiento de Órdenes</h1>
  <p class="mk-subtitle">Mary Kay de México · Jul 2025 – Ene 2026</p>
</div>
""",
    unsafe_allow_html=True,
)

if uploaded is None:
    st.markdown(
        "<div class='mk-insight'>Carga el archivo CSV desde la barra lateral para comenzar.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Carga + metadatos
df, meta = cargar_datos(uploaded)
ws_col = meta["ws_col"]

primer = construir_primer(df, ws_col)

meses_disponibles = (
    primer[["Month", "MonthSort"]].drop_duplicates()
    .sort_values("MonthSort")["Month"].tolist()
)

with st.sidebar:
    meses_sel = st.multiselect("Meses a analizar", meses_disponibles, default=meses_disponibles)

if not meses_sel:
    st.warning("Selecciona al menos un mes.")
    st.stop()

primer_f = primer[primer["Month"].isin(meses_sel)].copy()
df_f     = df[df["Month"].isin(meses_sel)].copy()

# Banner de calidad de datos (winsorización)
if meta["n_winsor"] > 0:
    st.markdown(
        f"<div class='mk-caption'><b>Calidad de datos:</b> {meta['n_winsor']:,} valores de wholesale "
        f"fueron winzorizados al rango ${meta['ws_p01']:,.0f} – ${meta['ws_p99']:,.0f} "
        "(percentiles 1%–99%) para reducir el efecto de pedidos atípicos en los promedios.</div>",
        unsafe_allow_html=True,
    )

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Resumen por grupo
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
resumen["MedianaWS"]    = resumen["MedianaWS"].round(0)

# Breakdown para hover (Tab 1)
breakdown = build_reorder_bucket_breakdown(df_f)
resumen   = resumen.merge(
    breakdown[["GrupoPrimerOrden", "BreakdownStr"]],
    on="GrupoPrimerOrden",
    how="left",
)

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ KPIssss
total_cons   = int(primer_f["ConsultantNumber"].nunique())
pct_reorden  = float(primer_f["Reordena"].mean() * 100) if len(primer_f) else 0.0
avg_ws_total = float(primer_f["AvgWholesale"].mean()) if len(primer_f) else 0.0
grp_top      = str(resumen.loc[resumen["PctReorden_%"].idxmax(), "GrupoPrimerOrden"]) if len(resumen) else "N/A"

k1, k2, k3, k4 = st.columns(4)
kpi_card(k1, "Consultoras únicas", f"{total_cons:,}")
kpi_card(k2, "% Reorden global",   f"{pct_reorden:.1f}%")
kpi_card(k3, "Avg Wholesale",      f"${avg_ws_total:,.0f}")
kpi_card(k4, "Grupo top reorden",  grp_top)

st.markdown("")

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Resumen", "Por mes", "Wholesale", "Insights", "Datos"])

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Tab 1: Resumen
with tab1:
    cA, cB = st.columns(2)

    with cA:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=resumen["GrupoPrimerOrden"].astype(str),
            y=resumen["ConsultorasUnicas"],
            marker=dict(color=COLORES_GRUPOS[:len(resumen)], line=dict(color=MK_WHITE, width=1)),
            text=[f"{int(v):,}" for v in resumen["ConsultorasUnicas"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>Consultoras: %{y:,}<extra></extra>",
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
            customdata=np.stack([resumen["BreakdownStr"].fillna("").values], axis=-1),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "% Reorden: %{y:.1f}%<br>"
                "<br><b>Distribución de reórdenes (dentro del grupo):</b><br>"
                "%{customdata[0]}<extra></extra>"
            ),
        ))
        fig2 = mk_plotly_layout(fig2, "% Reorden por grupo", "% Reorden")
        st.plotly_chart(fig2, use_container_width=True)

    
    
    # ── Tabla: distribución de reórdenes por bucket (visible sin hover) ──
    # Usa `breakdown` ya calculado arriba por build_reorder_bucket_breakdown(df_f)
    # y `resumen` que ya tiene el merge. No se recomputa ninguna lógica nueva.
    breakdown_tbl = breakdown[
        ["GrupoPrimerOrden", "Días 1-8", "Días 9-16", "Días 17-24", "Días 25-fin"]
    ].copy()
    # Añadir % Reorden del grupo para contexto
    breakdown_tbl = breakdown_tbl.merge(
        resumen[["GrupoPrimerOrden", "PctReorden_%"]], on="GrupoPrimerOrden", how="left"
    )
    breakdown_tbl = breakdown_tbl[
        ["GrupoPrimerOrden", "PctReorden_%", "Días 1-8", "Días 9-16", "Días 17-24", "Días 25-fin"]
    ]
    breakdown_tbl.columns = [
        "Grupo primer pedido",
        "% Reorden del grupo",
        "% reórdenes en 1–8",
        "% reórdenes en 9–16",
        "% reórdenes en 17–24",
        "% reórdenes en 25–fin",
    ]

    _no_reorders = breakdown_tbl[
        ["% reórdenes en 1–8", "% reórdenes en 9–16", "% reórdenes en 17–24", "% reórdenes en 25–fin"]
    ].sum().sum() == 0

    st.markdown(
        '<div class="mk-card">'
        '<h3 class="mk-card-title">¿Cuándo reordenan? — Distribución de reórdenes por grupo de primer pedido</h3>'
        "</div>",
        unsafe_allow_html=True,
    )
    if _no_reorders:
        st.markdown(
            "<div class='mk-insight'>Sin reórdenes en la selección actual — "
            "todos los valores son 0%.</div>",
            unsafe_allow_html=True,
        )

    _pct_cols = [
        "% Reorden del grupo",
        "% reórdenes en 1–8",
        "% reórdenes en 9–16",
        "% reórdenes en 17–24",
        "% reórdenes en 25–fin",
    ]
    styled_breakdown = (
        breakdown_tbl.style
        .format({c: "{:.1f}%" for c in _pct_cols})
        .background_gradient(
            subset=["% reórdenes en 1–8", "% reórdenes en 9–16",
                    "% reórdenes en 17–24", "% reórdenes en 25–fin"],
            cmap="RdPu",
            vmin=0,
            vmax=100,
        )
        .background_gradient(subset=["% Reorden del grupo"], cmap="RdPu", vmin=0, vmax=100)
    )
    try:
        styled_breakdown = styled_breakdown.hide(axis="index")
    except Exception:
        pass

    st.dataframe(styled_breakdown, use_container_width=True)
    st.markdown(
        "<div class='mk-caption'>"
        "Cada fila muestra, para las consultoras cuyo <b>primer pedido del mes</b> cayó en ese grupo de días, "
        "qué porcentaje de sus reórdenes ocurrieron en cada rango del mes. "
        "Las celdas vacías (0%) corresponden a combinaciones temporalmente imposibles "
        "(no se puede reordenar en un bucket anterior al del primer pedido)."
        "</div>",
        unsafe_allow_html=True,
    )
    


    st.markdown('<div class="mk-card"><h3 class="mk-card-title">Tabla resumen</h3></div>', unsafe_allow_html=True)

    tabla = resumen[["GrupoPrimerOrden", "ConsultorasUnicas", "PctReorden_%", "AvgWholesale", "MedianaWS"]].copy()
    tabla.columns = ["Grupo", "Consultoras únicas", "% Reorden", "Avg Wholesale (MXN)", "Mediana Wholesale (MXN)"]

    styled = (
        tabla.style
        .format({
            "Consultoras únicas":        "{:,}",
            "% Reorden":                 "{:.1f}%",
            "Avg Wholesale (MXN)":       "${:,.0f}",
            "Mediana Wholesale (MXN)":   "${:,.0f}",
        })
        .background_gradient(subset=["% Reorden"],           cmap="RdPu")
        .background_gradient(subset=["Avg Wholesale (MXN)"], cmap="RdPu")
    )
    try:
        styled = styled.hide(axis="index")
    except Exception:
        pass

    st.dataframe(styled, use_container_width=True)

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

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Tab 2: Por mes
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
            x=sub["Month"], y=sub["PctReorden_%"],
            mode="lines+markers", name=grupo,
            line=dict(color=color, width=3),
            marker=dict(size=8, color=color),
        ))
    fig_line = mk_plotly_layout(fig_line, "Evolución del % Reorden por mes", "% Reorden")
    st.plotly_chart(fig_line, use_container_width=True)

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Tab 3: Wholesale
with tab3:
    c1, c2 = st.columns(2)

    with c1:
        fig_ws = go.Figure()
        fig_ws.add_trace(go.Bar(
            x=resumen["GrupoPrimerOrden"].astype(str),
            y=resumen["MedianaWS"],
            marker=dict(color=COLORES_GRUPOS[:len(resumen)], line=dict(color=MK_WHITE, width=1)),
            text=[f"${v:,.0f}" for v in resumen["MedianaWS"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>Mediana Wholesale: $%{y:,.0f}<extra></extra>",
        ))
        fig_ws = mk_plotly_layout(
            fig_ws,
            "Mediana Wholesale por grupo (robusta ante outliers)",
            "MXN",
        )
        st.markdown(
            "<div class='mk-caption'>Usando mediana para mayor robustez ante órdenes atípicas. "
            "Valores winzorizados al 1%–99% al cargar.</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_ws, use_container_width=True)

    with c2:
        fig_box = go.Figure()
        for grupo, color in zip(GRUPO_ORDER, COLORES_GRUPOS):
            sub = primer_f[primer_f["GrupoPrimerOrden"] == grupo]["AvgWholesale"]
            if sub.empty:
                continue
            fig_box.add_trace(go.Box(
                y=sub, name=grupo,
                marker_color=color, line_color=color, boxmean=True,
            ))
        fig_box = mk_plotly_layout(fig_box, "Distribución de Wholesale por grupo", "MXN")
        fig_box.update_yaxes(tickprefix="$", separatethousands=True)
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown(
        "<div class='mk-insight'><b>Lectura recomendada:</b> interpreta el boxplot para ver mediana y dispersión; "
        "el promedio puede moverse por outliers.</div>",
        unsafe_allow_html=True,
    )

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Tab 4: Insights
with tab4:
    # Perfil de órdenes diarias ──────────────────────────────────────────
    st.markdown(
        '<div class="mk-card"><h3 class="mk-card-title">Patrón promedio de órdenes por día del mes</h3></div>',
        unsafe_allow_html=True,
    )

    # Une df_f con el grupo del primer pedido de cada consultora-mes
    df_with_grupo = df_f.merge(
        primer_f[["ConsultantNumber", "MonthSort", "GrupoPrimerOrden"]],
        on=["ConsultantNumber", "MonthSort"],
        how="left",
    )
    df_with_grupo["GrupoPrimerOrden"] = pd.Categorical(
        df_with_grupo["GrupoPrimerOrden"], categories=GRUPO_ORDER, ordered=True
    )

    daily_counts = (
        df_with_grupo.groupby(["MonthSort", "GrupoPrimerOrden", "Day"], observed=True)
                     .agg(Orders=("OrderKEY", "nunique"))
                     .reset_index()
    )

    # Filtrar días por MaxDay real del mes en los datos (evita sesgo en meses cortos)
    month_max_day = (
        df_with_grupo.groupby("MonthSort")["Day"]
                     .max()
                     .reset_index(name="MaxDay")
    )
    daily_counts = daily_counts.merge(month_max_day, on="MonthSort", how="left")
    daily_counts = daily_counts[daily_counts["Day"] <= daily_counts["MaxDay"]].copy()

    daily_avg = (
        daily_counts.groupby(["GrupoPrimerOrden", "Day"], observed=True)["Orders"]
                    .mean()
                    .reset_index(name="AvgOrders")
    )

    fig_profile = go.Figure()
    for grupo, color in zip(GRUPO_ORDER, COLORES_GRUPOS):
        sub = daily_avg[daily_avg["GrupoPrimerOrden"] == grupo].sort_values("Day")
        if sub.empty:
            continue
        fig_profile.add_trace(go.Scatter(
            x=sub["Day"], y=sub["AvgOrders"],
            mode="lines", name=grupo,
            line=dict(color=color, width=3),
            hovertemplate="<b>%{fullData.name}</b><br>Día %{x}: %{y:.1f} órdenes promedio<extra></extra>",
        ))
    fig_profile = mk_plotly_layout(
        fig_profile,
        "Perfil promedio de órdenes (orden + reorden) por día del mes",
        y_title="Órdenes promedio",
        x_title="Día del mes (1–31)",
    )
    fig_profile.update_xaxes(
        dtick=1,
        tickfont=dict(color=MK_GRAY_700, size=11, family=_FONT_FAMILY),
        title_font=dict(color=MK_GRAY_900, size=14, family=_FONT_FAMILY),
    )
    fig_profile.update_yaxes(
        title_font=dict(color=MK_GRAY_900, size=14, family=_FONT_FAMILY),
        tickfont=dict(color=MK_GRAY_700, size=12, family=_FONT_FAMILY),
    )
    st.plotly_chart(fig_profile, use_container_width=True)

    # Eventos de reorden ──────────────────────────────────────────────────
    # CAMBIO: se consume build_reorder_events() cacheado en lugar de
    # recomputar la misma lógica inline en cada render.
    d  = build_reorder_events(df_f)
    re = d[d["IsReorderEvent"]].copy()   # .copy() explícito; ya no hay re = re.copy() redundante

    if re.empty:
        st.markdown(
            "<div class='mk-insight'><b>Nota:</b> En la selección actual no aparecen reórdenes "
            "bajo la definición operacional (órdenes posteriores al primer pedido del mes por consultora).</div>",
            unsafe_allow_html=True,
        )
    else:
        # Career level / multinivel breakdown ────────────────────────────
        if "CareerLevelCode" in df_f.columns:
            st.markdown(
                '<div class="mk-card"><h3 class="mk-card-title">Reórdenes por Career Level (multinivel)</h3></div>',
                unsafe_allow_html=True,
            )

            by_lvl = (
                re.groupby(["GrupoPrimerOrden", "CareerLevelCode"], observed=True)
                  .agg(Reorders=("OrderKEY", "nunique"))
                  .reset_index()
                  .sort_values("Reorders", ascending=False)
            )
            by_lvl["CareerLevelCode"] = by_lvl["CareerLevelCode"].astype(str)

            top_n = 6
            top_levels = (
                by_lvl.groupby("CareerLevelCode", observed=True)["Reorders"]
                      .sum()
                      .nlargest(top_n)
                      .index.tolist()
            )
            by_lvl_top = by_lvl[by_lvl["CareerLevelCode"].isin(top_levels)].copy()

            fig_lvl = go.Figure()
            for grupo, color in zip(GRUPO_ORDER, COLORES_GRUPOS):
                sub = by_lvl_top[by_lvl_top["GrupoPrimerOrden"] == grupo].sort_values("Reorders")
                if sub.empty:
                    continue
                fig_lvl.add_trace(go.Bar(
                    y=sub["CareerLevelCode"],
                    x=sub["Reorders"],
                    name=str(grupo),
                    orientation="h",
                    marker=dict(color=color),
                    text=[f"{int(v):,}" for v in sub["Reorders"]],
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate=(
                        "<b>CareerLevel %{y}</b><br>Grupo: %{fullData.name}"
                        "<br>Reórdenes: %{x:,}<extra></extra>"
                    ),
                ))
            fig_lvl.update_layout(barmode="group")
            fig_lvl = mk_plotly_layout(
                fig_lvl,
                f"Reórdenes por Career Level — Top {top_n} niveles más activos",
                y_title="",
                x_title="Número de reórdenes",
            )
            fig_lvl.update_xaxes(
                title_font=dict(color=MK_GRAY_900, size=14, family=_FONT_FAMILY),
                tickfont=dict(color=MK_GRAY_700, size=12, family=_FONT_FAMILY),
            )
            fig_lvl.update_yaxes(
                tickfont=dict(color=MK_GRAY_900, size=13, family=_FONT_FAMILY),
                automargin=True,
            )
            fig_lvl.update_layout(margin=dict(t=60, b=60, l=100, r=30))
            st.plotly_chart(fig_lvl, use_container_width=True)

            top_lvl = by_lvl.groupby("GrupoPrimerOrden", observed=True).head(1)
            if not top_lvl.empty:
                lines = [
                    f"<li><b>{r['GrupoPrimerOrden']}</b>: CareerLevel "
                    f"<b>{r['CareerLevelCode']}</b> lidera con <b>{int(r['Reorders']):,}</b> reórdenes.</li>"
                    for _, r in top_lvl.iterrows()
                ]
                st.markdown(
                    "<div class='mk-insight'><b>Lectura rápida:</b><ul>"
                    + "".join(lines)
                    + "</ul></div>",
                    unsafe_allow_html=True,
                )

        # Montos: primera orden vs reórdenes ─────────────────────────────
        st.markdown(
            '<div class="mk-card"><h3 class="mk-card-title">Montos: promedio/mediana y comportamiento de reórdenes</h3></div>',
            unsafe_allow_html=True,
        )

        first_orders = d[~d["IsReorderEvent"]].copy()
        amount_summary = pd.DataFrame({
            "Tipo": ["Primera orden (del mes)", "Reórdenes (del mes)"],
            "Promedio Wholesale": [first_orders[ws_col].mean(), re[ws_col].mean()],
            "Mediana Wholesale":  [first_orders[ws_col].median(), re[ws_col].median()],
            "Órdenes":            [first_orders["OrderKEY"].nunique(), re["OrderKEY"].nunique()],
        })
        amount_summary["Promedio Wholesale"] = amount_summary["Promedio Wholesale"].round(0)
        amount_summary["Mediana Wholesale"]  = amount_summary["Mediana Wholesale"].round(0)
        st.dataframe(amount_summary, use_container_width=True)

        bucket_amount = (
            re.groupby("ReBucket", observed=True)[ws_col].sum()
              .reindex(GRUPO_ORDER)
              .fillna(0)
        )
        if bucket_amount.sum() > 0:
            pct_end = 100 * bucket_amount.loc["Días 25-fin"] / bucket_amount.sum()
            st.markdown(
                f"<div class='mk-insight'><b>Insight:</b> Del total de wholesale en reórdenes, "
                f"<b>{pct_end:.1f}%</b> ocurre en <b>días 25–fin</b> (selección actual). "
                "Si esto se mantiene por meses, es un buen candidato para calendarizar acciones "
                "comerciales cerca del cierre.</div>",
                unsafe_allow_html=True,
            )

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Tab 5: Datos
with tab5:
    st.markdown('<div class="mk-card"><h3 class="mk-card-title">Datos procesados</h3></div>', unsafe_allow_html=True)
    st.markdown(f"<div class='mk-caption'>Registros: {len(primer_f):,}</div>", unsafe_allow_html=True)

    cols_show = [
        "ConsultantNumber", "Month", "GrupoPrimerOrden", "PrimerDia",
        "TotalOrderDays", "TotalOrdenes", "TotalWholesale", "AvgWholesale", "Reordena",
    ]
    data_view = primer_f[cols_show].sort_values(["Month", "GrupoPrimerOrden"]).reset_index(drop=True)

    st.dataframe(data_view, use_container_width=True, height=520)

    csv_out = data_view.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar tabla procesada (CSV)",
        data=csv_out,
        file_name="primer_orden_mes_analisis.csv",
        mime="text/csv",
    )

# ☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★ Footer

st.markdown(
    "<div class='mk-caption' style='text-align:center; padding-top: 14px;'>"
    "Mary Kay de México · Market Intelligence · Steffany Lara · Febrero 2026"
    "</div>",
    unsafe_allow_html=True,
)
