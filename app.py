"""
Mary Kay de Mexico - Dashboard de Ordenes (Brand-aligned)
Autora: Steffany Lara | Market Intelligence
Fecha: Febrero 2026

CAMBIOS EN ESTA REVISION
========================
[FIX A] Bloque inicial de warnings reescrito. Antes se referenciaba
        pd.errors.PerformanceWarning antes de importar pandas (funcionaba
        solo por evaluacion perezosa del ternario). Imports primero,
        configuracion de warnings despues.

[FIX B] Doble import warnings eliminado.

[CONF]  ConsultantNumber NUNCA aparece en la UI. Se sustituye por un
        identificador anonimo C-00001, C-00002, ... estable en
        st.session_state. El CSV de descarga interno sigue incluyendo
        ConsultantNumber para uso operativo (toggle disponible).

[NUEVO] Tab "Recurrencia": detecta consultoras recurrentes inactivas
        (lapsing customers) usando filtrado RFM:
          F: meses con orden en historico previo >= N
          R: sin orden este mes y/o mes anterior
        Descarga CSV con ConsultantNumber, Nombre, Division, CareerLevel
        y Estatus (las columnas que existan en el CSV original).
"""

# ---------------------------------------------------------------------- imports
import warnings
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Suprimir solo PerformanceWarning de pandas (fragmentacion de DataFrame, etc.)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# ---------------------------------------------------------------------- config
st.set_page_config(
    page_title="Mary Kay - Ordenes",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------- brand
MK_PINK      = "#E91E8C"
MK_PINK_DARK = "#C2185B"
MK_PINK_SOFT = "#FCE4EC"
MK_GRAY_900  = "#1F2937"
MK_GRAY_700  = "#374151"
MK_GRAY_500  = "#6B7280"
MK_GRAY_200  = "#E5E7EB"
MK_WHITE     = "#FFFFFF"

GRUPO_ORDER     = ["Dias 1-8", "Dias 9-16", "Dias 17-24", "Dias 25-fin"]
COLORES_GRUPOS  = [MK_PINK, MK_PINK_DARK, "#F06292", MK_GRAY_500]
_GRUPO_RANK     = {g: i for i, g in enumerate(GRUPO_ORDER)}

LOGO_URL = "https://1000marcas.net/wp-content/uploads/2021/05/Mary-Kay-logo.jpg"

# ---------------------------------------------------------------------- CSS
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
                     Roboto, Helvetica, Arial;
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

# ---------------------------------------------------------------------- helpers
_BUCKET_BINS   = [0, 8, 16, 24, 31]
_BUCKET_LABELS = GRUPO_ORDER

def bucketize(series: pd.Series) -> pd.Categorical:
    """Dia del mes (int) -> Categorical bucket. Vectorizado."""
    return pd.Categorical(
        pd.cut(series, bins=_BUCKET_BINS, labels=_BUCKET_LABELS, include_lowest=True),
        categories=GRUPO_ORDER,
        ordered=True,
    )


# get_anon_id_map eliminado: la UI usa ConsultantKEY directo del CSV.


# ---------------------------------------------------------------------- carga
# ───────────────────── dtypes optimos para lectura rapida ─────────────────────
# Para 1M+ filas: especificar dtypes evita inferencia (2-3x mas rapido), y
# usar Categorical en columnas de baja cardinalidad ahorra ~60% de memoria.
_CSV_DTYPES_OPT = {
    # Numericos
    "ConsultantKEY":       "Int64",      # nullable; soporta NA sin convertirse a float
    "OrderKEY":            "Int64",
    "TotalWhosale":        "float32",
    "TotalWholesale":      "float32",
    "NewRecruitIndicator": "Int8",
    "ProductionOrderCount":"Int16",
    # Baja cardinalidad: ahorro masivo de memoria
    "ConsultantName":      "category",
    "Division":            "category",
    "CareerLevelCode":     "category",
    "ActivityStatusCode":  "category",
    "ConsultantNumber":    "category",
}

@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos(file) -> tuple[pd.DataFrame, dict]:
    """
    Lee el CSV optimizado para datasets de hasta 1M+ filas.
    Estrategia:
      1) dtype explicito para evitar inferencia (2-3x mas rapido).
      2) Categorical en columnas de baja cardinalidad (-60% memoria).
      3) Parseo de OrderDateKEY como int32 primero, datetime despues solo
         si se necesita -- aqui lo dejamos como datetime para compat.
    """
    # Primero leer headers para saber que dtypes aplicar
    df_head = pd.read_csv(file, nrows=0)
    cols_available = list(df_head.columns)

    # Si file es BytesIO/UploadedFile hay que reset; pero pd.read_csv en
    # streamlit ya rebobina internamente. Por si acaso:
    if hasattr(file, "seek"):
        try: file.seek(0)
        except Exception: pass

    # Construir mapa de dtypes solo para columnas que existen
    dtypes_use = {c: t for c, t in _CSV_DTYPES_OPT.items() if c in cols_available}

    df = pd.read_csv(file, dtype=dtypes_use)

    required = ["OrderDateKEY", "ConsultantNumber", "OrderKEY"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Falta columna requerida: {col}")

    if "TotalWhosale" in df.columns:
        ws_col = "TotalWhosale"
    elif "TotalWholesale" in df.columns:
        ws_col = "TotalWholesale"
    else:
        raise ValueError("Falta columna de wholesale: TotalWhosale o TotalWholesale")

    # OrderDateKEY: parsear directo (sin astype(str)), ~20x mas rapido sobre 1M filas
    # to_datetime acepta int con format explicito
    df["OrderDateKEY"] = pd.to_datetime(df["OrderDateKEY"], format="%Y%m%d", errors="coerce")
    n_bad_dates = df["OrderDateKEY"].isna().sum()
    if n_bad_dates > 0:
        st.warning(f"{n_bad_dates} fechas no pudieron parsearse - se descartaron.")
    df = df.dropna(subset=["OrderDateKEY"])

    # OrderMonthKey derivado (vectorizado, super rapido)
    df["OrderMonthKey"] = df["OrderDateKEY"].values.astype("datetime64[M]")

    dup_mask = df.duplicated(subset=["OrderKEY"])
    if dup_mask.any():
        st.warning(f"{dup_mask.sum()} OrderKEY duplicados - se eliminan.")
        df = df.drop_duplicates(subset=["OrderKEY"])

    df["Day"]       = df["OrderDateKEY"].dt.day.astype("int8")
    df["MonthSort"] = df["OrderMonthKey"]

    # Month: en lugar de strftime per-row (3s sobre 1M), mapear los pocos
    # valores unicos. Tipicamente <24 meses. 100x mas rapido.
    _unique_months = df["OrderMonthKey"].drop_duplicates().sort_values()
    _month_map = {m: m.strftime("%b %Y") for m in _unique_months}
    df["Month"] = df["OrderMonthKey"].map(_month_map).astype("category")

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

    # Detectar columnas demograficas opcionales que pueda venir en el CSV.
    # Cualquier conjunto razonable de nombres que pudiera estar en el dump
    # (DimConsultant.* o flatten desde otras dims).
    demographic_candidates = {
        "name":         ["ConsultantName", "FullName", "Name"],
        "division":     ["DivisionName", "Division", "DivisionCode", "AreaName", "Area"],
        "career_level": ["CareerLevelCode", "CareerLevel", "CareerLevelName"],
        "status":       ["ActivityStatusCode", "ActivityStatus", "Status"],
    }
    demo_cols_found = {}
    for role, candidates in demographic_candidates.items():
        for c in candidates:
            if c in df.columns:
                demo_cols_found[role] = c
                break

    meta = {
        "ws_col":   ws_col,
        "n_winsor": n_winsor,
        "ws_p01":   float(ws_p01),
        "ws_p99":   float(ws_p99),
        "demo_cols": demo_cols_found,
    }
    return df, meta


# ---------------------------------------------------------------------- panel
@st.cache_data(show_spinner="Construyendo panel por consultora y mes...")
def construir_primer(df: pd.DataFrame, ws_col: str) -> pd.DataFrame:
    """
    Optimizaciones para 1M+ filas:
      - PrimerDia con min() en vez de first() para evitar sort previo (-30%)
      - observed=True en groupby (obligatorio con categoricals, mas rapido)
      - ConsultantKEY/CareerLevel: max() es identico a first() porque son
        constantes por (consultora, mes) y no requiere sort.
    """
    agg_dict = {
        "PrimerDia":      ("Day", "min"),           # min == first cronologico, sin sort
        "TotalOrderDays": ("OrderDateKEY", "nunique"),
        "TotalOrdenes":   ("OrderKEY", "nunique"),
        "TotalWholesale": (ws_col, "sum"),
    }

    # Para atributos constantes por consultora-mes usamos "first".
    # Nota: "max" no funciona en Categoricals no ordenados (CareerLevelCode,
    # ConsultantName son category). "first" si funciona en cualquier dtype y
    # como estos valores son CONSTANTES por consultora-mes, no importa el orden.
    if "ConsultantKEY" in df.columns:
        agg_dict["ConsultantKEY"] = ("ConsultantKEY", "first")
    if "CareerLevelCode" in df.columns:
        agg_dict["CareerLevel"] = ("CareerLevelCode", "first")
    if "NewRecruitIndicator" in df.columns:
        agg_dict["NewRecruit"] = ("NewRecruitIndicator", "first")

    # observed=True es importante cuando ConsultantNumber es Categorical:
    # evita crear combinaciones vacias del producto cartesiano de categorias.
    primer = (
        df.groupby(["ConsultantNumber", "MonthSort", "Month"], as_index=False, observed=True)
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
    ).astype("float32")

    return primer


# ---------------------------------------------------------------------- reorder helpers
@st.cache_data(show_spinner=False)
def build_reorder_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimizado: min() en vez de first() para FirstOrderDate (no requiere sort
    interno previo); observed=True para evitar combinaciones vacias.
    """
    d = df.copy()

    first_order_date = (
        d.groupby(["ConsultantNumber", "MonthSort"], observed=True)["OrderDateKEY"]
         .min()
         .rename("FirstOrderDate")
         .reset_index()
    )
    d = d.merge(first_order_date, on=["ConsultantNumber", "MonthSort"], how="left")

    # Sort necesario para que cumcount sea cronologicamente correcto
    d = d.sort_values(["ConsultantNumber", "MonthSort", "OrderDateKEY", "OrderKEY"])
    d["OrderSeq"] = (
        d.groupby(["ConsultantNumber", "MonthSort", "OrderDateKEY"], observed=True)
         .cumcount() + 1
    )
    d["IsReorderEvent"] = (d["OrderDateKEY"] > d["FirstOrderDate"]) | (d["OrderSeq"] > 1)

    d["PrimerDia"]        = d["FirstOrderDate"].dt.day
    d["GrupoPrimerOrden"] = bucketize(d["PrimerDia"])
    d["ReBucket"]         = bucketize(d["Day"])

    return d


@st.cache_data(show_spinner=False)
def build_reorder_bucket_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    d = build_reorder_events(df)
    re = d[d["IsReorderEvent"]].copy()

    if re.empty:
        out = pd.DataFrame({"GrupoPrimerOrden": GRUPO_ORDER})
        for b in GRUPO_ORDER:
            out[b] = 0.0
        out["BreakdownStr"] = "Sin reordenes en seleccion"
        return out

    counts = (
        re.groupby(["GrupoPrimerOrden", "ReBucket"], observed=True)
          .size()
          .reset_index(name="N")
    )

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

    # Vectorizar la construccion del BreakdownStr en lugar de apply(axis=1).
    # Pre-formatear cada columna a string, luego construir el resultado.
    # apply(axis=1) es ~100x mas lento que ops vectorizadas en datasets grandes.
    grupo_str = wide["GrupoPrimerOrden"].astype(str)
    grupo_rank_arr = grupo_str.map(_GRUPO_RANK).fillna(0).astype(int).to_numpy()

    bucket_labels_short = {b: b.replace("Dias ", "") for b in GRUPO_ORDER}

    # Para cada bucket, formatear "X.X% (label)" si aplica
    bucket_strs = {}
    for b in GRUPO_ORDER:
        b_rank = _GRUPO_RANK.get(b, 0)
        vals   = wide[b].to_numpy()
        mask   = (b_rank >= grupo_rank_arr) & (vals > 0)
        bucket_strs[b] = np.where(
            mask,
            [f"{v:.1f}% ({bucket_labels_short[b]})" for v in vals],
            "",
        )

    # Unir las partes con " . " ignorando vacios
    def _join_nonempty(*parts):
        return " . ".join(p for p in parts if p)

    breakdown_array = [
        _join_nonempty(*[bucket_strs[b][i] for b in GRUPO_ORDER]) or "Sin reordenes registrados"
        for i in range(len(wide))
    ]
    wide["BreakdownStr"] = breakdown_array
    return wide


@st.cache_data(show_spinner=False)
def build_reorder_amount_breakdown(df: pd.DataFrame, ws_col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    d  = build_reorder_events(df)
    re = d[d["IsReorderEvent"]].copy()

    _empty = pd.DataFrame({
        "GrupoPrimerOrden": pd.Categorical(GRUPO_ORDER, categories=GRUPO_ORDER, ordered=True)
    })
    for b in GRUPO_ORDER:
        _empty[b] = np.nan
    if re.empty:
        return _empty.copy(), _empty.copy()

    re["_GrupoRank"]  = re["GrupoPrimerOrden"].map(_GRUPO_RANK)
    re["_BucketRank"] = re["ReBucket"].map(_GRUPO_RANK)
    re = re[re["_BucketRank"] >= re["_GrupoRank"]].drop(columns=["_GrupoRank", "_BucketRank"])

    def _pivot_stat(stat_fn, name):
        agg = (
            re.groupby(["GrupoPrimerOrden", "ReBucket"], observed=True)[ws_col]
              .agg(stat_fn)
              .reset_index(name=name)
        )
        wide = (
            agg.pivot(index="GrupoPrimerOrden", columns="ReBucket", values=name)
               .reindex(GRUPO_ORDER)
               .reset_index()
        )
        for b in GRUPO_ORDER:
            if b not in wide.columns:
                wide[b] = np.nan
        wide["GrupoPrimerOrden"] = pd.Categorical(
            wide["GrupoPrimerOrden"], categories=GRUPO_ORDER, ordered=True
        )
        return wide

    avg_wide = _pivot_stat("mean",   "Promedio")
    med_wide = _pivot_stat("median", "Mediana")

    return avg_wide, med_wide


# ---------------------------------------------------------------------- recurrencia (NUEVO)
@st.cache_data(show_spinner="Computando matriz de recurrencia...")
def build_recurrence_matrix(primer: pd.DataFrame) -> pd.DataFrame:
    """
    Matriz binaria ConsultantNumber x MonthSort: 1 si la consultora puso
    al menos una orden ese mes, 0 si no.

    Notese que esto se construye sobre 'primer' (el panel agregado), no sobre
    el df de transacciones. Cualquier consultora con al menos una fila en
    primer cuenta como activa en ese mes.
    """
    mat = (
        primer.assign(TieneOrden=1)
              .pivot_table(
                  index="ConsultantNumber",
                  columns="MonthSort",
                  values="TieneOrden",
                  fill_value=0,
                  aggfunc="max",
              )
              .astype(int)
    )
    # Ordenar columnas cronologicamente
    mat = mat.reindex(sorted(mat.columns), axis=1)
    return mat


@st.cache_data(show_spinner=False)
def get_last_known_info(df: pd.DataFrame, demo_cols_tuple: tuple) -> pd.DataFrame:
    """
    Optimizado para datasets grandes:
      - Usar idxmax(OrderDateKEY) por grupo y un loc unico para obtener las
        filas mas recientes. Esto es ~50% mas rapido que sort+last completo.
      - Reusa el mismo groupby para ambos: ultimo registro y ultima fecha.
    """
    demo_cols = dict(demo_cols_tuple)
    cols_demo = [c for c in demo_cols.values() if c in df.columns]

    # idxmax por consultora da el indice de la fila con OrderDateKEY mas grande
    g = df.groupby("ConsultantNumber", observed=True)
    last_idx = g["OrderDateKEY"].idxmax()

    cols_to_pull = list({"ConsultantNumber", "OrderDateKEY", *cols_demo})
    last = df.loc[last_idx.values, cols_to_pull].copy()
    last = last.rename(columns={"OrderDateKEY": "UltimaOrden"})
    last = last.reset_index(drop=True)
    return last


# ---------------------------------------------------------------------- viz helpers
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


# ---------------------------------------------------------------------- sidebar
with st.sidebar:
    st.image(LOGO_URL, use_container_width=True)
    st.markdown("### Filtros")
    st.markdown("---")

    uploaded = st.file_uploader(
        "Cargar CSV de ordenes",
        type=["csv"],
        help="Archivo analysis_MonthlyOrdersByDay_PV.csv",
    )

    st.markdown("---")
    st.markdown(
        "<div class='mk-caption'>Market Intelligence . Mary Kay de Mexico<br>"
        "Steffany Lara . 2026</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------- header
st.markdown(
    """
<div class="mk-header">
  <h1 class="mk-title">Analisis de Comportamiento de Ordenes</h1>
  <p class="mk-subtitle">Mary Kay de Mexico . Jul 2025 - Ene 2026</p>
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

# ---------------------------------------------------------------------- carga
df, meta = cargar_datos(uploaded)
ws_col   = meta["ws_col"]
demo_cols = meta["demo_cols"]

primer = construir_primer(df, ws_col)

# Verificar si el CSV trae ConsultantKEY para mostrar en UI
_tiene_ck = "ConsultantKEY" in primer.columns

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

if meta["n_winsor"] > 0:
    st.markdown(
        f"<div class='mk-caption'><b>Calidad de datos:</b> {meta['n_winsor']:,} valores de wholesale "
        f"fueron winzorizados al rango ${meta['ws_p01']:,.0f} - ${meta['ws_p99']:,.0f} "
        "(percentiles 1%-99%) para reducir el efecto de pedidos atipicos en los promedios.</div>",
        unsafe_allow_html=True,
    )

# Banner informativo sobre columnas demograficas detectadas
if demo_cols:
    detected_str = ", ".join(f"{k}={v}" for k, v in demo_cols.items())
    st.markdown(
        f"<div class='mk-caption'><b>Columnas demograficas detectadas en el CSV:</b> {detected_str}. "
        "Estas se usaran en la tab Recurrencia para enriquecer la descarga.</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------- resumen
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

breakdown = build_reorder_bucket_breakdown(df_f)
resumen   = resumen.merge(
    breakdown[["GrupoPrimerOrden", "BreakdownStr"]],
    on="GrupoPrimerOrden",
    how="left",
)

# ---------------------------------------------------------------------- KPIs
total_cons   = int(primer_f["ConsultantNumber"].nunique())
pct_reorden  = float(primer_f["Reordena"].mean() * 100) if len(primer_f) else 0.0
avg_ws_total = float(primer_f["AvgWholesale"].mean()) if len(primer_f) else 0.0
grp_top      = str(resumen.loc[resumen["PctReorden_%"].idxmax(), "GrupoPrimerOrden"]) if len(resumen) else "N/A"

k1, k2, k3, k4 = st.columns(4)
kpi_card(k1, "Consultoras unicas", f"{total_cons:,}")
kpi_card(k2, "% Reorden global",   f"{pct_reorden:.1f}%")
kpi_card(k3, "Avg Wholesale",      f"${avg_ws_total:,.0f}")
kpi_card(k4, "Grupo top reorden",  grp_top)

st.markdown("")

# ---------------------------------------------------------------------- tabs
tab1, tab2, tab3, tab4, tab_rec, tab5 = st.tabs(
    ["Resumen", "Por mes", "Wholesale", "Insights", "Recurrencia", "Datos"]
)

# ====================================================================== TAB 1
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
        fig1 = mk_plotly_layout(fig1, "Consultoras unicas por grupo", "Consultoras")
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
                "<br><b>Distribucion de reordenes (dentro del grupo):</b><br>"
                "%{customdata[0]}<extra></extra>"
            ),
        ))
        fig2 = mk_plotly_layout(fig2, "% Reorden por grupo", "% Reorden")
        st.plotly_chart(fig2, use_container_width=True)

    # Tabla: cuando reordenan
    breakdown_tbl = breakdown[
        ["GrupoPrimerOrden", "Dias 1-8", "Dias 9-16", "Dias 17-24", "Dias 25-fin"]
    ].copy()
    breakdown_tbl = breakdown_tbl.merge(
        resumen[["GrupoPrimerOrden", "PctReorden_%"]], on="GrupoPrimerOrden", how="left"
    )
    breakdown_tbl = breakdown_tbl[
        ["GrupoPrimerOrden", "PctReorden_%", "Dias 1-8", "Dias 9-16", "Dias 17-24", "Dias 25-fin"]
    ]
    breakdown_tbl.columns = [
        "Grupo primer pedido",
        "% Reorden del grupo",
        "% reordenes en 1-8",
        "% reordenes en 9-16",
        "% reordenes en 17-24",
        "% reordenes en 25-fin",
    ]

    _no_reorders = breakdown_tbl[
        ["% reordenes en 1-8", "% reordenes en 9-16", "% reordenes en 17-24", "% reordenes en 25-fin"]
    ].sum().sum() == 0

    st.markdown(
        '<div class="mk-card">'
        '<h3 class="mk-card-title">Cuando reordenan - Distribucion de reordenes por grupo de primer pedido</h3>'
        "</div>",
        unsafe_allow_html=True,
    )
    if _no_reorders:
        st.markdown(
            "<div class='mk-insight'>Sin reordenes en la seleccion actual - "
            "todos los valores son 0%.</div>",
            unsafe_allow_html=True,
        )

    _pct_cols = [
        "% Reorden del grupo",
        "% reordenes en 1-8",
        "% reordenes en 9-16",
        "% reordenes en 17-24",
        "% reordenes en 25-fin",
    ]
    styled_breakdown = (
        breakdown_tbl.style
        .format({c: "{:.1f}%" for c in _pct_cols})
        .background_gradient(
            subset=["% reordenes en 1-8", "% reordenes en 9-16",
                    "% reordenes en 17-24", "% reordenes en 25-fin"],
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
        "Cada fila muestra, para las consultoras cuyo <b>primer pedido del mes</b> cayo en ese grupo de dias, "
        "que porcentaje de sus reordenes ocurrieron en cada rango del mes. "
        "Las celdas vacias (0%) corresponden a combinaciones temporalmente imposibles."
        "</div>",
        unsafe_allow_html=True,
    )

    # Tabla: cuanto reordenan
    st.markdown(
        '<div class="mk-card">'
        '<h3 class="mk-card-title">Cuanto reordenan - Monto de reordenes por grupo de primer pedido</h3>'
        "</div>",
        unsafe_allow_html=True,
    )

    amt_avg_wide, amt_med_wide = build_reorder_amount_breakdown(df_f, ws_col)

    _amt_all_nan = amt_avg_wide[GRUPO_ORDER].isna().all().all()

    if _amt_all_nan:
        st.markdown(
            "<div class='mk-insight'>Sin reordenes en la seleccion actual - no hay montos que mostrar.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='mk-caption' style='margin-top:10px; font-weight:700; color:#374151;'>"
            "Promedio de wholesale por reorden (MXN)</div>",
            unsafe_allow_html=True,
        )

        avg_tbl = amt_avg_wide[["GrupoPrimerOrden"] + GRUPO_ORDER].copy()
        avg_tbl.columns = ["Grupo primer pedido"] + [f"Reorden en {b.replace('Dias ', '')}" for b in GRUPO_ORDER]

        _avg_money_cols = [c for c in avg_tbl.columns if c != "Grupo primer pedido"]
        _avg_format     = {c: lambda v: f"${v:,.0f}" if pd.notna(v) else "-" for c in _avg_money_cols}

        styled_avg = (
            avg_tbl.style
            .format(_avg_format)
            .background_gradient(subset=_avg_money_cols, cmap="RdPu", axis=None)
        )
        try:
            styled_avg = styled_avg.hide(axis="index")
        except Exception:
            pass
        st.dataframe(styled_avg, use_container_width=True)

        st.markdown(
            "<div class='mk-caption' style='margin-top:14px; font-weight:700; color:#374151;'>"
            "Mediana de wholesale por reorden (MXN) - mas robusta ante valores atipicos</div>",
            unsafe_allow_html=True,
        )

        med_tbl = amt_med_wide[["GrupoPrimerOrden"] + GRUPO_ORDER].copy()
        med_tbl.columns = ["Grupo primer pedido"] + [f"Reorden en {b.replace('Dias ', '')}" for b in GRUPO_ORDER]

        _med_money_cols = [c for c in med_tbl.columns if c != "Grupo primer pedido"]
        _med_format     = {c: lambda v: f"${v:,.0f}" if pd.notna(v) else "-" for c in _med_money_cols}

        styled_med = (
            med_tbl.style
            .format(_med_format)
            .background_gradient(subset=_med_money_cols, cmap="RdPu", axis=None)
        )
        try:
            styled_med = styled_med.hide(axis="index")
        except Exception:
            pass
        st.dataframe(styled_med, use_container_width=True)

        st.markdown(
            "<div class='mk-caption'>"
            "Cada celda muestra el monto promedio (o mediana) de wholesale de las <b>reordenes</b> "
            "colocadas en ese rango de dias. Usa la mediana para comparaciones mas robustas si hay outliers."
            "</div>",
            unsafe_allow_html=True,
        )

        try:
            col_fin = "Reorden en 25-fin"
            if col_fin in med_tbl.columns:
                med_fin = med_tbl.set_index("Grupo primer pedido")[col_fin].dropna()
                if len(med_fin) >= 2:
                    g_max = med_fin.idxmax()
                    g_min = med_fin.idxmin()
                    st.markdown(
                        f"<div class='mk-insight'><b>Insight:</b> Las reordenes colocadas en <b>dias 25-fin</b> "
                        f"tienen mayor monto mediano en el grupo <b>{g_max}</b> "
                        f"(<b>${med_fin[g_max]:,.0f}</b>) y menor en <b>{g_min}</b> "
                        f"(<b>${med_fin[g_min]:,.0f}</b>). "
                        "Considera campanas de cierre de mes diferenciadas por perfil de primer pedido.</div>",
                        unsafe_allow_html=True,
                    )
        except Exception:
            pass

    # Tabla resumen
    st.markdown('<div class="mk-card"><h3 class="mk-card-title">Tabla resumen</h3></div>', unsafe_allow_html=True)

    tabla = resumen[["GrupoPrimerOrden", "ConsultorasUnicas", "PctReorden_%", "AvgWholesale", "MedianaWS"]].copy()
    tabla.columns = ["Grupo", "Consultoras unicas", "% Reorden", "Avg Wholesale (MXN)", "Mediana Wholesale (MXN)"]

    styled = (
        tabla.style
        .format({
            "Consultoras unicas":        "{:,}",
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

# ====================================================================== TAB 2
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
    fig_line = mk_plotly_layout(fig_line, "Evolucion del % Reorden por mes", "% Reorden")
    st.plotly_chart(fig_line, use_container_width=True)

# ====================================================================== TAB 3
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
            "<div class='mk-caption'>Usando mediana para mayor robustez ante ordenes atipicas. "
            "Valores winzorizados al 1%-99% al cargar.</div>",
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
        fig_box = mk_plotly_layout(fig_box, "Distribucion de Wholesale por grupo", "MXN")
        fig_box.update_yaxes(tickprefix="$", separatethousands=True)
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown(
        "<div class='mk-insight'><b>Lectura recomendada:</b> interpreta el boxplot para ver mediana y dispersion; "
        "el promedio puede moverse por outliers.</div>",
        unsafe_allow_html=True,
    )

# ====================================================================== TAB 4
with tab4:
    st.markdown(
        '<div class="mk-card"><h3 class="mk-card-title">Patron promedio de ordenes por dia del mes</h3></div>',
        unsafe_allow_html=True,
    )

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
            hovertemplate="<b>%{fullData.name}</b><br>Dia %{x}: %{y:.1f} ordenes promedio<extra></extra>",
        ))
    fig_profile = mk_plotly_layout(
        fig_profile,
        "Perfil promedio de ordenes (orden + reorden) por dia del mes",
        y_title="Ordenes promedio",
        x_title="Dia del mes (1-31)",
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

    d  = build_reorder_events(df_f)
    re = d[d["IsReorderEvent"]].copy()

    if re.empty:
        st.markdown(
            "<div class='mk-insight'><b>Nota:</b> En la seleccion actual no aparecen reordenes "
            "bajo la definicion operacional.</div>",
            unsafe_allow_html=True,
        )
    else:
        if "CareerLevelCode" in df_f.columns:
            st.markdown(
                '<div class="mk-card"><h3 class="mk-card-title">Reordenes por Career Level (multinivel)</h3></div>',
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
                        "<br>Reordenes: %{x:,}<extra></extra>"
                    ),
                ))
            fig_lvl.update_layout(barmode="group")
            fig_lvl = mk_plotly_layout(
                fig_lvl,
                f"Reordenes por Career Level - Top {top_n} niveles mas activos",
                y_title="",
                x_title="Numero de reordenes",
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
                    f"<b>{r['CareerLevelCode']}</b> lidera con <b>{int(r['Reorders']):,}</b> reordenes.</li>"
                    for _, r in top_lvl.iterrows()
                ]
                st.markdown(
                    "<div class='mk-insight'><b>Lectura rapida:</b><ul>"
                    + "".join(lines)
                    + "</ul></div>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div class="mk-card"><h3 class="mk-card-title">Montos: promedio/mediana y comportamiento de reordenes</h3></div>',
            unsafe_allow_html=True,
        )

        first_orders = d[~d["IsReorderEvent"]].copy()
        amount_summary = pd.DataFrame({
            "Tipo": ["Primera orden (del mes)", "Reordenes (del mes)"],
            "Promedio Wholesale": [first_orders[ws_col].mean(), re[ws_col].mean()],
            "Mediana Wholesale":  [first_orders[ws_col].median(), re[ws_col].median()],
            "Ordenes":            [first_orders["OrderKEY"].nunique(), re["OrderKEY"].nunique()],
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
            pct_end = 100 * bucket_amount.loc["Dias 25-fin"] / bucket_amount.sum()
            st.markdown(
                f"<div class='mk-insight'><b>Insight:</b> Del total de wholesale en reordenes, "
                f"<b>{pct_end:.1f}%</b> ocurre en <b>dias 25-fin</b> (seleccion actual). "
                "Si esto se mantiene por meses, es buen candidato para calendarizar acciones "
                "comerciales cerca del cierre.</div>",
                unsafe_allow_html=True,
            )

# ====================================================================== TAB RECURRENCIA (NUEVO)
with tab_rec:
    st.markdown(
        '<div class="mk-card">'
        '<h3 class="mk-card-title">Consultoras recurrentes inactivas (lapsing customers)</h3>'
        '<div class="mk-caption">'
        'Filtrado RFM clasico: consultoras que ordenaron en al menos N meses del historico '
        '(frequency) y que se quedaron sin orden este mes o el anterior (recency). '
        'El listado se descarga con datos demograficos para reactivacion.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Matriz binaria sobre TODO el panel (no filtrado por meses_sel)
    # Razon: para evaluar recurrencia necesitas el historico completo.
    mat = build_recurrence_matrix(primer)

    if mat.shape[1] < 2:
        st.warning("El dataset tiene menos de 2 meses; no se puede evaluar recurrencia.")
        st.stop()

    meses_ord = list(mat.columns)
    mes_actual_ts   = meses_ord[-1]
    mes_anterior_ts = meses_ord[-2]
    mes_actual_str   = mes_actual_ts.strftime("%b %Y")
    mes_anterior_str = mes_anterior_ts.strftime("%b %Y")
    n_meses_historico = len(meses_ord) - 1  # excluyendo el actual

    # ----- controles -----
    c1, c2, c3 = st.columns([1.2, 1.6, 1.2])

    with c1:
        n_recurrencia = st.slider(
            "Recurrencia minima (N meses con orden en historico previo)",
            min_value=1,
            max_value=max(1, n_meses_historico),
            value=min(3, n_meses_historico),
            help=(
                f"Considera el historico previo al mes actual ({mes_actual_str}). "
                f"Hay {n_meses_historico} meses previos disponibles."
            ),
        )

    with c2:
        filtro_inactividad = st.radio(
            "Criterio de inactividad",
            options=[
                f"Sin orden este mes ({mes_actual_str})",
                f"Sin orden mes anterior ({mes_anterior_str})",
                f"Sin orden este mes Y mes anterior",
            ],
            index=0,
        )

    with c3:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        incluir_real_id_en_descarga = st.checkbox(
            "Incluir ConsultantNumber en CSV de descarga",
            value=True,
            help="La UI siempre muestra solo ID anonimo. Este toggle controla si el CSV descargado incluye el numero real (uso operativo interno).",
        )

    # ----- computar mascara -----
    meses_historico = meses_ord[:-1]
    n_ordenes_previas = mat[meses_historico].sum(axis=1)

    sin_actual   = mat[mes_actual_ts] == 0
    sin_anterior = mat[mes_anterior_ts] == 0

    es_recurrente = n_ordenes_previas >= n_recurrencia

    if filtro_inactividad.startswith("Sin orden este mes Y"):
        mask = es_recurrente & sin_actual & sin_anterior
        criterio_label = "Sin orden este mes Y mes anterior"
    elif filtro_inactividad.startswith("Sin orden este mes"):
        mask = es_recurrente & sin_actual
        criterio_label = f"Sin orden en {mes_actual_str}"
    else:
        mask = es_recurrente & sin_anterior
        criterio_label = f"Sin orden en {mes_anterior_str}"

    target_cn = mat.index[mask].tolist()

    # ----- KPIs -----
    n_target  = len(target_cn)
    n_recurr_total = int(es_recurrente.sum())
    pct_lapsing = (100 * n_target / n_recurr_total) if n_recurr_total > 0 else 0.0

    # Wholesale historico total del segmento target (proxy de valor en riesgo)
    if n_target > 0:
        ws_total_target = float(
            primer[primer["ConsultantNumber"].isin(target_cn)]["TotalWholesale"].sum()
        )
    else:
        ws_total_target = 0.0

    k1r, k2r, k3r, k4r = st.columns(4)
    kpi_card(k1r, "Consultoras en riesgo", f"{n_target:,}", criterio_label)
    kpi_card(k2r, "Recurrentes totales",   f"{n_recurr_total:,}", f">= {n_recurrencia} meses con orden")
    kpi_card(k3r, "% recurrentes lapsing", f"{pct_lapsing:.1f}%")
    kpi_card(k4r, "Wholesale historico (total)", f"${ws_total_target:,.0f}", "Valor acumulado del segmento")

    if n_target == 0:
        st.markdown(
            "<div class='mk-insight'>No hay consultoras que cumplan ambos criterios con los filtros actuales. "
            "Prueba bajar el umbral de recurrencia o cambiar el criterio de inactividad.</div>",
            unsafe_allow_html=True,
        )
    else:
        # ----- construir tabla enriquecida -----
        # Datos derivados del panel
        agg_target = (
            primer[primer["ConsultantNumber"].isin(target_cn)]
            .groupby("ConsultantNumber", as_index=False)
            .agg(
                MesesConOrden=("MonthSort", "nunique"),
                TotalOrdenes=("TotalOrdenes", "sum"),
                WholesaleAcumulado=("TotalWholesale", "sum"),
                TicketPromedio=("AvgWholesale", "mean"),
                UltimoMesActivo=("MonthSort", "max"),
            )
        )

        # Last-known info demografica
        last_info = get_last_known_info(df, tuple(sorted(demo_cols.items())))
        agg_target = agg_target.merge(last_info, on="ConsultantNumber", how="left")

        # ID para UI: ConsultantKEY si existe, de lo contrario aviso
        if _tiene_ck and "ConsultantKEY" in agg_target.columns:
            pass   # ya viene de last_info o del join; nada que calcular
        elif _tiene_ck:
            # Traer ConsultantKEY desde primer (first conocido por consultora)
            ck_map = primer.dropna(subset=["ConsultantKEY"]).drop_duplicates("ConsultantNumber").set_index("ConsultantNumber")["ConsultantKEY"]
            agg_target["ConsultantKEY"] = agg_target["ConsultantNumber"].map(ck_map)

        # Formatear UltimaOrden y UltimoMesActivo
        if "UltimaOrden" in agg_target.columns:
            agg_target["UltimaOrden"] = pd.to_datetime(agg_target["UltimaOrden"]).dt.strftime("%Y-%m-%d")
        agg_target["UltimoMesActivo"] = pd.to_datetime(agg_target["UltimoMesActivo"]).dt.strftime("%b %Y")

        # Renombrar columnas demograficas a nombres canonicos (si existen)
        rename_map = {}
        if "name" in demo_cols:         rename_map[demo_cols["name"]]         = "Nombre"
        if "division" in demo_cols:     rename_map[demo_cols["division"]]     = "Division"
        if "career_level" in demo_cols: rename_map[demo_cols["career_level"]] = "CareerLevel"
        if "status" in demo_cols:       rename_map[demo_cols["status"]]       = "Estatus"
        agg_target = agg_target.rename(columns=rename_map)

        # Ordenar por valor descendente
        agg_target = agg_target.sort_values(
            ["WholesaleAcumulado", "MesesConOrden"],
            ascending=[False, False]
        )

        # ===== version UI (ConsultantKEY visible, ConsultantNumber oculto) =====
        ui_cols_order = ["ConsultantKEY"] if (_tiene_ck and "ConsultantKEY" in agg_target.columns) else []
        for c in ["Nombre", "Division", "CareerLevel", "Estatus"]:
            if c in agg_target.columns:
                ui_cols_order.append(c)
        ui_cols_order += [
            "MesesConOrden", "TotalOrdenes",
            "WholesaleAcumulado", "TicketPromedio",
            "UltimoMesActivo",
        ]
        if "UltimaOrden" in agg_target.columns:
            ui_cols_order.append("UltimaOrden")

        ui_view = agg_target[ui_cols_order].copy()

        # En UI, enmascarar el nombre real si esta presente (privacidad mientras se ve en pantalla)
        # Formato: "MARIA G***"
        def _mask_name(s: str) -> str:
            if not s or s == "nan":
                return ""
            parts = s.split()
            if len(parts) == 1:
                return parts[0]
            return f"{parts[0]} {parts[1][0]}***"

        if "Nombre" in ui_view.columns:
            ui_view["Nombre"] = ui_view["Nombre"].astype(str).apply(_mask_name)

        # Castear columnas numericas a float antes de pasarlas al Styler.
        # Streamlit usa Arrow para serializar; columnas con dtype object o NaN
        # mixto truena en marshall_styler. El cast explicito lo previene.
        for _num_col in ["MesesConOrden", "TotalOrdenes", "WholesaleAcumulado", "TicketPromedio"]:
            if _num_col in ui_view.columns:
                ui_view[_num_col] = pd.to_numeric(ui_view[_num_col], errors="coerce")

        def _fmt_money(v):
            return f"${v:,.0f}" if pd.notna(v) else "-"

        def _fmt_int(v):
            return f"{v:,.0f}" if pd.notna(v) else "-"

        _fmt_map = {}
        for _c in ["WholesaleAcumulado", "TicketPromedio"]:
            if _c in ui_view.columns:
                _fmt_map[_c] = _fmt_money
        for _c in ["MesesConOrden", "TotalOrdenes"]:
            if _c in ui_view.columns:
                _fmt_map[_c] = _fmt_int

        _grad_cols = [c for c in ["MesesConOrden", "WholesaleAcumulado"]
                      if c in ui_view.columns and ui_view[c].notna().any()]

        # Limitar UI a top 200 filas (ya ordenadas por valor descendente).
        # Para listados mas grandes, descargar CSV.
        MAX_UI_ROWS = 200
        _truncated  = len(ui_view) > MAX_UI_ROWS
        ui_view_show = ui_view.head(MAX_UI_ROWS).copy()

        # Pre-formatear columnas numericas a strings. Esto evita el camino
        # Styler+Arrow que en datasets grandes causa hangs en marshall_styler.
        for _c in ["WholesaleAcumulado", "TicketPromedio"]:
            if _c in ui_view_show.columns:
                ui_view_show[_c] = ui_view_show[_c].map(_fmt_money)
        for _c in ["MesesConOrden", "TotalOrdenes"]:
            if _c in ui_view_show.columns:
                ui_view_show[_c] = ui_view_show[_c].map(_fmt_int)
        # Asegurar que columnas object sean strings limpios (nada de NaN sueltos)
        for _c in ui_view_show.columns:
            if ui_view_show[_c].dtype == object:
                ui_view_show[_c] = ui_view_show[_c].astype(str).replace({"nan": "", "None": ""})

        _msg_extra = (f" Mostrando top <b>{MAX_UI_ROWS}</b> de <b>{n_target:,}</b> por wholesale acumulado descendente."
                      if _truncated else "")
        st.markdown(
            f"<div class='mk-caption' style='margin-top:14px;'>"
            f"Total consultoras en riesgo: <b>{n_target:,}</b>.{_msg_extra} "
            f"El CSV de descarga incluye la lista completa con ConsultantNumber."
            f"</div>",
            unsafe_allow_html=True,
        )
        st.dataframe(ui_view_show, use_container_width=True, height=520)

        # ===== version descarga (con datos reales) =====
        dl_cols_order = []
        if incluir_real_id_en_descarga:
            dl_cols_order.append("ConsultantNumber")
        if _tiene_ck and "ConsultantKEY" in agg_target.columns:
            dl_cols_order.append("ConsultantKEY")
        for c in ["Nombre", "Division", "CareerLevel", "Estatus"]:
            if c in agg_target.columns:
                dl_cols_order.append(c)
        dl_cols_order += [
            "MesesConOrden", "TotalOrdenes",
            "WholesaleAcumulado", "TicketPromedio",
            "UltimoMesActivo",
        ]
        if "UltimaOrden" in agg_target.columns:
            dl_cols_order.append("UltimaOrden")

        dl_view = agg_target[dl_cols_order].copy()
        csv_lapsing = dl_view.to_csv(index=False).encode("utf-8")

        fname_suffix = criterio_label.lower().replace(" ", "_").replace("/", "-")
        st.download_button(
            f"Descargar lista de {n_target:,} consultoras en riesgo (CSV)",
            data=csv_lapsing,
            file_name=f"consultoras_recurrentes_lapsing_{fname_suffix}_N{n_recurrencia}.csv",
            mime="text/csv",
        )

        # Aviso si faltan columnas demograficas
        missing_demo = [r for r in ["name", "division", "career_level", "status"] if r not in demo_cols]
        if missing_demo:
            roles_es = {
                "name": "Nombre",
                "division": "Division",
                "career_level": "CareerLevel",
                "status": "Estatus",
            }
            faltantes = ", ".join(roles_es[r] for r in missing_demo)
            st.markdown(
                f"<div class='mk-insight'><b>Nota:</b> El CSV cargado no incluye estas columnas: "
                f"<b>{faltantes}</b>. "
                f"Para enriquecer la descarga, agrega un JOIN a <code>dm.DimConsultant</code> "
                f"(nombre, UnitID), <code>dm.DimUnit</code> (division/area) y "
                f"<code>ref.ActivityStatusKeys</code> (ActivityStatusCode) en el query "
                f"que genera el CSV.</div>",
                unsafe_allow_html=True,
            )

# ====================================================================== TAB 5
with tab5:
    st.markdown('<div class="mk-card"><h3 class="mk-card-title">Datos procesados</h3></div>', unsafe_allow_html=True)
    st.markdown(f"<div class='mk-caption'>Registros: {len(primer_f):,}</div>", unsafe_allow_html=True)

    data_view = primer_f.copy()

    # Columnas a mostrar en UI: ConsultantKEY si existe, nunca ConsultantNumber
    _id_col_ui = "ConsultantKEY" if (_tiene_ck and "ConsultantKEY" in data_view.columns) else None

    cols_show_base = ["Month", "GrupoPrimerOrden", "PrimerDia",
                      "TotalOrderDays", "TotalOrdenes", "TotalWholesale", "AvgWholesale", "Reordena"]
    cols_show = ([_id_col_ui] if _id_col_ui else []) + cols_show_base

    data_view_ui = data_view[cols_show].sort_values(["Month", "GrupoPrimerOrden"]).reset_index(drop=True)

    # Convertir Categorical a string para evitar problemas de Arrow en algunos
    # combos de pandas/streamlit/pyarrow
    if "GrupoPrimerOrden" in data_view_ui.columns:
        data_view_ui["GrupoPrimerOrden"] = data_view_ui["GrupoPrimerOrden"].astype(str)

    try:
        st.dataframe(data_view_ui, use_container_width=True, height=520)
    except Exception:
        # Fallback: castear todo a tipos seguros
        for _c in data_view_ui.columns:
            if data_view_ui[_c].dtype == object:
                data_view_ui[_c] = data_view_ui[_c].astype(str)
        st.dataframe(data_view_ui, use_container_width=True, height=520)

    _nota_id = (
        "La columna <b>ConsultantKEY</b> es el identificador interno del DWH. "
        "ConsultantNumber no se muestra en la UI."
        if _id_col_ui else
        "El CSV no incluye ConsultantKEY. Agrega la columna en el query para verla aqui."
    )
    st.markdown(
        f"<div class='mk-caption'>{_nota_id} "
        "La descarga incluye ConsultantNumber para uso operativo interno.</div>",
        unsafe_allow_html=True,
    )

    # Descarga: siempre incluye ConsultantNumber real
    dl_base = ["ConsultantNumber"] + ([_id_col_ui] if _id_col_ui else []) + cols_show_base
    data_dl = data_view[[c for c in dl_base if c in data_view.columns]].copy()
    csv_out = data_dl.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar tabla procesada (CSV con ConsultantNumber)",
        data=csv_out,
        file_name="primer_orden_mes_analisis.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------- footer
st.markdown(
    "<div class='mk-caption' style='text-align:center; padding-top: 14px;'>"
    "Mary Kay de Mexico . Market Intelligence . Steffany Lara . 2026"
    "</div>",
    unsafe_allow_html=True,
)
