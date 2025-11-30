
# pages/home.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard Ekonomi", layout="wide", page_icon="📊")

# ---------------------------
# CSS: biru pastel (theme)
# ---------------------------
st.markdown("""
<style>
.section-title {
    background: #7db0ff;
    color: white;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 10px;
}
.card {
    background: white;
    padding: 14px;
    border-radius: 10px;
    border: 2px solid #cfe5ff;
    margin-bottom: 16px;
}
.kpi-value {
    font-size: 26px;
    font-weight: 800;
    color: #123a6a;
}
.kpi-label {
    font-size: 13px;
    color: #406a9a;
}
.small-note { color: #6b879f; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Data files mapping (10 indikator)
# Sesuaikan nama file di folder data/ jika beda
# ---------------------------
DATA_DIR = "data"
FILES = {
    "GDP growth (%)": "1.3 GDP growth (%).csv",
    "GDP per capita": "1.2. GDP PER CAPITA.csv",
    "GDP (current US$)": "1.1. GDP (CURRENT US$).csv",
    "Unemployment rate": "2.2 Unemployment rate.csv",
    "Labor force participation": "2.1 Labor force participation rate.csv",
    "Inflation (CPI)": "3.1 Inflation, consumer prices (%).csv",
    "Exports (% of GDP)": "4.1 Exports.csv",
    "FDI (net inflow)": "5.1 Foreign Direct Investment (FDI).csv",
    "GINI index": "7.2 GINI.csv",
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
# Util: load table tolerant
# ---------------------------
@st.cache_data
def load_table(path: str) -> pd.DataFrame:
    if not path or not os.path.exists(path):
        return pd.DataFrame()
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in (".xls", ".xlsx"):
            return pd.read_excel(path)
    except Exception:
        pass
    # try separators
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception:
        return pd.DataFrame()

def detect_year_columns(df):
    return [c for c in df.columns if str(c).isdigit() and len(str(c)) == 4]

def to_long_if_wide(df):
    """Return dataframe long: country, year, value. Works for wide (years as cols) or simple long (has 'year')."""
    if df.empty:
        return pd.DataFrame()
    cols = [str(c).strip() for c in df.columns]
    lower = [c.lower() for c in cols]
    # long if 'year' col exists
    if "year" in lower:
        df2 = df.copy()
        # find country col
        country_cols = [c for c in df2.columns if str(c).strip().lower() in ("country name","country","negara","entity")]
        country_col = country_cols[0] if country_cols else df2.columns[0]
        # find value col(s)
        value_cols = [c for c in df2.columns if c not in [country_col, "Year", "year"]]
        if not value_cols:
            return pd.DataFrame()
        value_col = value_cols[0]
        long = df2[[country_col, "Year" if "Year" in df2.columns else "year", value_col]].rename(
            columns={country_col: "country", value_col: "value", "Year": "year"}
        )
        long["year"] = pd.to_numeric(long["year"], errors="coerce")
        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        return long.dropna(subset=["year","value"])
    # wide -> melt
    years = detect_year_columns(df)
    if years:
        country_col = df.columns[0]
        long = df.melt(id_vars=[country_col], value_vars=years, var_name="year", value_name="value")
        long = long.rename(columns={country_col: "country"})
        long["year"] = pd.to_numeric(long["year"], errors="coerce")
        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        return long.dropna(subset=["value"])
    return pd.DataFrame()

def latest_value_from_df(df):
    years = detect_year_columns(df)
    if not years:
        return None, None
    last = str(sorted(int(y) for y in years)[-1])
    vals = pd.to_numeric(df[last], errors="coerce").dropna()
    if vals.empty:
        return None, last
    return float(vals.mean()), last

# ---------------------------
# Header
# ---------------------------
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center">
  <div>
    <h1 style="margin:0;color:#123a6a">📊 DASHBOARD EKONOMI</h1>
    <div class="small-note">Ringkasan 10 indikator utama — otomatis membaca file di folder <code>data/</code></div>
  </div>
  <div class="small-note">Sumber: World Bank / File lokal</div>
</div>
""", unsafe_allow_html=True)

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
        dfk = load_table(os.path.join(DATA_DIR, fname))
        val, yr = latest_value_from_df(dfk) if not dfk.empty else (None, None)
        icon = ICONS.get(key, "📊")
        with col:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:14px;color:#406a9a'>{icon} <strong>{key}</strong></div>", unsafe_allow_html=True)
            if val is None:
                st.markdown("<div class='kpi-value'>—</div>", unsafe_allow_html=True)
                st.markdown("<div class='kpi-label'>Tahun: -</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='kpi-value'>{val:,.2f}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='kpi-label'>Tahun: {yr}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ---------------------------
# Trend area: 10 mini-trend (2 rows of 5)
# ---------------------------
st.markdown("<div class='section-title'>📈 Tren Singkat (10 indikator)</div>", unsafe_allow_html=True)
trend_rows = [kpi_keys[:5], kpi_keys[5:10]]
for row in trend_rows:
    cols = st.columns(5, gap="small")
    for key, col in zip(row, cols):
        fname = FILES.get(key, "")
        dfk = load_table(os.path.join(DATA_DIR, fname))
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
    sel_df = load_table(os.path.join(DATA_DIR, sel_file))
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
                st.error("Gagal membuat peta. Periksa nama negara (harus country names standar).")
                st.exception(e)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ---------------------------
# Grid ringkasan 10 indikator utama (small cards)
# ---------------------------
st.markdown("<div class='section-title'>📦 Ringkasan 10 Indikator</div>", unsafe_allow_html=True)
grid_cols = st.columns(5, gap="small")
for i, key in enumerate(kpi_keys):
    col = grid_cols[i % 5]
    fname = FILES.get(key, "")
    dfk = load_table(os.path.join(DATA_DIR, fname))
    lg = to_long_if_wide(dfk)
    latest, latest_year = latest_value_from_df(dfk) if not dfk.empty else (None, None)
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
st.caption("Tip: pastikan file CSV/XLSX berada di folder 'data/' dan kolom tahun konsisten (mis. 2000,2001,...).")
