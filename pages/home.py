
# pages/home.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

st.set_page_config(page_title="Dashboard Ekonomi (home)", layout="wide", page_icon="📊")

# ---------------------------
# Config: file mapping (sesuaikan jika ada beda nama)
# ---------------------------
DATA_DIR = "data"
FILES = {
    "GDP growth (%)": "1.3 GDP growth (%).csv",
    "GDP per capita": "1.2. GDP PER CAPITA.csv",
    "GDP (current US$)": "1.1. GDP (CURRENT US$).csv",
    "Unemployment rate": "2.2 Unemployment rate.csv",
    "Labor force participation": "2.1 Labor force participation rate.csv",
    "Inflation (CPI)": "3.1 Inflation, consumer prices (%).csv",
    "Exports (% of GDP)": "4.1 Exports of goods and services.csv",
    "FDI (net inflow)": "5.1 Foreign Direct Investment (FDI).csv",
    "GINI index": "6.2. GINI INDEX.csv",   # per daftar file kamu
    "CO2 per capita": "10.1. CO EMISSIONS.csv",
}

ICONS = {
    "GDP growth (%)": "📈",
    "GDP per capita": "💰",
    "GDP (current US$)": "🌐",
    "Unemployment rate": "👥",
    "Labor force participation": "🧑‍💼",
    "Inflation (CPI)": "🔥",
    "Exports (% of GDP)": "🚢",
    "FDI (net inflow)": "💼",
    "GINI index": "⚖️",
    "CO2 per capita": "🌍",
}

# ---------------------------
# Styling (biru pastel theme)
# ---------------------------
st.markdown("""
<style>
.section-title { background:#7db0ff; color:white; padding:8px 12px; border-radius:6px; font-weight:700; margin-bottom:10px; }
.card { background:white; padding:12px; border-radius:10px; border:2px solid #cfe5ff; margin-bottom:12px; }
.kpi-value { font-size:24px; font-weight:800; color:#123a6a; }
.kpi-label { font-size:13px; color:#406a9a; }
.small-note { color:#6b879f; font-size:12px; }
pre.debug { background:#f6f9ff; padding:8px; border-radius:6px; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Robust loader & cleaners
# ---------------------------
def read_file_try(path):
    """Try read CSV/XLSX with different separators; return DataFrame or empty."""
    if not os.path.exists(path):
        return pd.DataFrame()
    ext = os.path.splitext(path)[1].lower()
    # try excel first
    if ext in (".xls", ".xlsx"):
        try:
            return pd.read_excel(path)
        except Exception:
            pass
    # try several separators
    text = None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read(4096)
    except Exception:
        pass
    # heuristics: try ; then , then \t
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    # final fallback try automatic python engine without sep
    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception:
        return pd.DataFrame()

def clean_dataframe_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Trim header/strings and replace common NA placeholders."""
    if df is None or df.empty:
        return df
    # strip columns
    df = df.rename(columns=lambda c: str(c).strip())
    # clean object columns
    for c in df.select_dtypes(include=["object"]).columns:
        # strip whitespace
        df[c] = df[c].astype(str).str.strip()
        # replace common placeholders
        df[c] = df[c].replace({"": None, "NA": None, "N/A": None, "n/a": None, "..": None, "-": None, "null": None})
    return df

def detect_year_columns(df):
    if df is None or df.empty:
        return []
    cols = [str(c).strip() for c in df.columns]
    years = [c for c in cols if c.isdigit() and len(c) == 4]
    return years

def to_long_if_wide(df):
    """Return long dataframe with columns country, year (int), value (float)."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = clean_dataframe_strings(df.copy())
    cols = list(df.columns)
    lower = [c.lower() for c in cols]
    # Case 1: long format (has 'year' column)
    if "year" in lower:
        year_col = cols[lower.index("year")]
        # detect country column
        country_col = next((c for c in cols if c.lower() in ("country name","country","negara","entity")), cols[0])
        # detect value column: first numeric-like column excluding country/year
        cand = [c for c in cols if c not in (country_col, year_col)]
        val_col = None
        for c in cand:
            sample = df[c].dropna().astype(str).head(10).tolist()
            # numeric if at least one entry parseable after removing commas
            if any(s.replace(",","").replace(" ","").replace(".","").lstrip("-").isdigit() for s in sample):
                val_col = c
                break
        if val_col is None and cand:
            val_col = cand[-1]
        long = df[[country_col, year_col, val_col]].rename(columns={country_col:"country", year_col:"year", val_col:"value"})
        # clean numeric strings (remove thousand separators)
        long["value"] = long["value"].astype(str).str.replace(",", "").str.replace(" ", "")
        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        long["year"] = pd.to_numeric(long["year"], errors="coerce")
        return long.dropna(subset=["year","value"])
    # Case 2: wide format (years as cols)
    years = detect_year_columns(df)
    if years:
        country_col = next((c for c in cols if c.lower() in ("country name","country","negara","entity")), cols[0])
        # melt
        long = df.melt(id_vars=[country_col], value_vars=years, var_name="year", value_name="value")
        long["value"] = long["value"].astype(str).str.replace(",", "").str.replace(" ", "")
        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        long["year"] = pd.to_numeric(long["year"], errors="coerce")
        long = long.rename(columns={country_col: "country"})
        return long.dropna(subset=["value"])
    # fallback empty
    return pd.DataFrame()

def latest_value_from_df(df):
    """Return (mean_value, year_of_last) or (None, last_year_str)."""
    if df is None or df.empty:
        return None, None
    years = detect_year_columns(df)
    if not years:
        # if long format, attempt to extract latest year there
        lg = to_long_if_wide(df)
        if lg.empty:
            return None, None
        last = int(lg["year"].max())
        vals = lg[lg["year"] == last]["value"].dropna()
        if vals.empty:
            return None, str(last)
        return float(vals.mean()), str(last)
    # if wide format
    sorted_years = sorted(int(y) for y in years)
    last = str(sorted_years[-1])
    vals = pd.to_numeric(df[last], errors="coerce").dropna() if last in df.columns else pd.Series(dtype=float)
    if vals.empty:
        return None, last
    return float(vals.mean()), last

# ---------------------------
# Debug helper: small preview for file diagnostics
# ---------------------------
def debug_file(path):
    info = {"path": path, "exists": os.path.exists(path)}
    if not info["exists"]:
        return info
    info["ext"] = os.path.splitext(path)[1].lower()
    # preview head (first lines)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            head_lines = [next(f).rstrip("\n") for _ in range(6)]
            info["head"] = head_lines
    except Exception:
        info["head"] = "cannot preview (binary/excel?)"
    # try read with loader
    df = read_file_try(path)
    info["columns"] = list(df.columns)[:30] if not df.empty else []
    info["detected_year_cols"] = detect_year_columns(df)
    # count rows non-empty in first numeric year col (if exists)
    try:
        if info["detected_year_cols"]:
            col = info["detected_year_cols"][-1]
            info["non_null_count_last_year"] = int(df[col].notna().sum())
    except Exception:
        info["non_null_count_last_year"] = None
    return info

# ---------------------------
# Sidebar debug toggle
# ---------------------------
show_debug = st.sidebar.checkbox("Tampilkan diagnostics file (debug)", value=False)

if show_debug:
    st.sidebar.markdown("**Diagnostics file di folder data/**")
    for label, fname in FILES.items():
        p = os.path.join(DATA_DIR, fname)
        d = debug_file(p)
        st.sidebar.markdown(f"**{label}** — `{fname}`")
        st.sidebar.write(d)
    st.sidebar.markdown("---")
    st.sidebar.write("Gunakan diagnostics untuk melihat mengapa file tidak dibaca / kolom tahun tidak terdeteksi.")

# ---------------------------
# UI Header
# ---------------------------
st.markdown("<div style='display:flex; justify-content:space-between; align-items:center'>"
            "<div><h1 style='margin:0;color:#123a6a'>📊 DASHBOARD EKONOMI</h1>"
            "<div class='small-note'>Ringkasan otomatis 10 indikator — membaca file dari folder data/</div></div>"
            "<div class='small-note'>Sumber: World Bank / file lokal</div></div>", unsafe_allow_html=True)

st.write("")

# ---------------------------
# KPI cards (2 rows of 5)
# ---------------------------
st.markdown("<div class='section-title'>📌 KPI Utama</div>", unsafe_allow_html=True)
kpi_keys = list(FILES.keys())
rows = [kpi_keys[:5], kpi_keys[5:10]]
for row in rows:
    cols = st.columns(5, gap="small")
    for key, col in zip(row, cols):
        fname = FILES.get(key, "")
        path = os.path.join(DATA_DIR, fname)
        dfk = read_file_try(path)
        # compute latest
        val, yr = latest_value_from_df(dfk)
        with col:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:14px;color:#406a9a'>{ICONS.get(key)} <strong>{key}</strong></div>", unsafe_allow_html=True)
            if val is None:
                st.markdown("<div class='kpi-value'>—</div>", unsafe_allow_html=True)
                st.markdown("<div class='kpi-label'>Tahun: -</div>", unsafe_allow_html=True)
            else:
                # format large numbers nicely
                if abs(val) >= 1e9:
                    display = f"{val:,.0f}"
                elif abs(val) >= 1e3:
                    display = f"{val:,.2f}"
                else:
                    display = f"{val:.2f}"
                st.markdown(f"<div class='kpi-value'>{display}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='kpi-label'>Tahun: {yr}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ---------------------------
# Trend area (10 mini-trend)
# ---------------------------
st.markdown("<div class='section-title'>📈 Tren Singkat (10 indikator)</div>", unsafe_allow_html=True)
trend_rows = [kpi_keys[:5], kpi_keys[5:10]]
for row in trend_rows:
    cols = st.columns(5, gap="small")
    for key, col in zip(row, cols):
        fname = FILES.get(key, "")
        dfk = read_file_try(os.path.join(DATA_DIR, fname))
        lg = to_long_if_wide(dfk)
        with col:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:14px;color:#406a9a'>{ICONS.get(key)} <strong>{key}</strong></div>", unsafe_allow_html=True)
            if not lg.empty:
                agg = lg.groupby("year")["value"].mean().reset_index()
                fig = px.line(agg, x="year", y="value")
                fig.update_layout(height=120, margin=dict(t=8,b=8,l=8,r=8), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("data tidak tersedia")
            st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ---------------------------
# Map summary (select indicator + year)
# ---------------------------
st.markdown("<div class='section-title'>🌍 Peta Ringkasan</div>", unsafe_allow_html=True)
map_col, ctrl_col = st.columns([3,1])

with ctrl_col:
    sel_indicator = st.selectbox("Pilih indikator untuk peta", kpi_keys, index=0)
    sel_file = FILES.get(sel_indicator, "")
    sel_df = read_file_try(os.path.join(DATA_DIR, sel_file))
    sel_long = to_long_if_wide(sel_df)
    years_avail = sorted(sel_long["year"].unique().astype(int).tolist()) if not sel_long.empty else []
    year_map = st.select_slider("Tahun", years_avail, value=years_avail[-1] if years_avail else None) if years_avail else None

with map_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if sel_long.empty or year_map is None:
        st.info("Pilih indikator yang tersedia (file ada dan berisi kolom tahun).")
    else:
        df_map = sel_long[sel_long["year"] == int(year_map)]
        if df_map.empty:
            st.warning("Tidak ada data untuk tahun terpilih.")
        else:
            try:
                fig = px.choropleth(df_map, locations="country", locationmode="country names",
                                    color="value", hover_name="country",
                                    color_continuous_scale="Blues",
                                    title=f"{sel_indicator} — {year_map}")
                fig.update_layout(margin=dict(t=40,l=0,r=0,b=0), height=520)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error("Gagal membuat peta. Periksa nama negara (standar 'country names').")
                st.exception(e)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ---------------------------
# Grid ringkasan 10 indikator
# ---------------------------
st.markdown("<div class='section-title'>📦 Ringkasan 10 Indikator</div>", unsafe_allow_html=True)
grid_cols = st.columns(5, gap="small")
for i, key in enumerate(kpi_keys):
    col = grid_cols[i % 5]
    dfk = read_file_try(os.path.join(DATA_DIR, FILES.get(key, "")))
    lg = to_long_if_wide(dfk)
    latest, latest_year = latest_value_from_df(dfk)
    with col:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:13px;color:#406a9a'>{ICONS.get(key)} <strong>{key}</strong></div>", unsafe_allow_html=True)
        if latest is None:
            st.markdown("<div style='font-size:18px; margin-top:6px;'>—</div>", unsafe_allow_html=True)
            st.markdown("<div class='kpi-label'>Tahun: -</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-size:18px; margin-top:6px;'>{latest:,.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-label'>Tahun: {latest_year}</div>", unsafe_allow_html=True)
        if not lg.empty:
            agg = lg.groupby("year")["value"].mean().reset_index().tail(8)
            try:
                fig = px.line(agg, x="year", y="value")
                fig.update_layout(height=90, margin=dict(t=6,b=6,l=6,r=6), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass
        st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.caption("Tip: jika indikator tampil '—', buka sidebar Debug dan lihat diagnostics untuk file terkait. Perbaiki nama file atau format kolom tahun (mis. 2000,2001,... atau kolom 'Year').")
