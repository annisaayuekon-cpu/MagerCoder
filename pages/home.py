
# pages/home.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard Ekonomi - Home", layout="wide", page_icon="📊")

# ---------------- Theme / CSS (biru pastel)
st.markdown("""
<style>
.section-title { background:#7db0ff; color:white; padding:10px 14px; border-radius:8px; font-weight:700; margin-bottom:10px; }
.card { background:#fff; padding:12px; border-radius:10px; border:2px solid #cfe5ff; margin-bottom:12px; }
.kpi-value { font-size:24px; font-weight:800; color:#123a6a; }
.kpi-label { font-size:13px; color:#406a9a; }
.small-note { color:#6b879f; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ---------------- Files mapping (sesuaikan jika perlu)
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
    "GINI index": "6.2. GINI INDEX.csv",
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

# ---------------- Robust loader (tahan terhadap separator/format)
def read_file_try(path):
    if not path or not os.path.exists(path):
        return pd.DataFrame()
    ext = os.path.splitext(path)[1].lower()
    # try excel
    if ext in (".xls", ".xlsx"):
        try:
            return pd.read_excel(path)
        except Exception:
            pass
    # try common separators
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception:
        return pd.DataFrame()

def clean_df_strings(df):
    if df is None or df.empty:
        return df
    df = df.rename(columns=lambda c: str(c).strip())
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].astype(str).str.strip().replace({"": None, "NA": None, "N/A": None, "..": None, "-": None})
    return df

def detect_year_columns(df):
    if df is None or df.empty:
        return []
    cols = [str(c).strip() for c in df.columns]
    return [c for c in cols if c.isdigit() and len(c) == 4]

def to_long_if_wide(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df = clean_df_strings(df.copy())
    cols = list(df.columns)
    lower = [c.lower() for c in cols]
    # long format: has 'year'
    if "year" in lower:
        year_col = cols[lower.index("year")]
        country_col = next((c for c in cols if c.lower() in ("country name","country","negara","entity")), cols[0])
        # choose value column (first non-country/year)
        candidates = [c for c in cols if c not in (country_col, year_col)]
        val_col = candidates[0] if candidates else None
        if val_col is None:
            return pd.DataFrame()
        long = df[[country_col, year_col, val_col]].rename(columns={country_col: "country", year_col: "year", val_col: "value"})
        long["value"] = long["value"].astype(str).str.replace(",", "").str.replace(" ", "")
        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        long["year"] = pd.to_numeric(long["year"], errors="coerce")
        return long.dropna(subset=["year", "value"])
    # wide format: years as columns
    years = detect_year_columns(df)
    if years:
        country_col = next((c for c in cols if c.lower() in ("country name","country","negara","entity")), cols[0])
        long = df.melt(id_vars=[country_col], value_vars=years, var_name="year", value_name="value")
        long["value"] = long["value"].astype(str).str.replace(",", "").str.replace(" ", "")
        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        long["year"] = pd.to_numeric(long["year"], errors="coerce")
        long = long.rename(columns={country_col: "country"})
        return long.dropna(subset=["value"])
    return pd.DataFrame()

def latest_value_from_df(df):
    if df is None or df.empty:
        return None, None
    years = detect_year_columns(df)
    if years:
        sorted_years = sorted(int(y) for y in years)
        last = str(sorted_years[-1])
        if last in df.columns:
            vals = pd.to_numeric(df[last], errors="coerce").dropna()
            if not vals.empty:
                return float(vals.mean()), last
            return None, last
    # fallback long form
    lg = to_long_if_wide(df)
    if not lg.empty:
        last = int(lg["year"].max())
        vals = lg[lg["year"] == last]["value"].dropna()
        if not vals.empty:
            return float(vals.mean()), str(last)
        return None, str(last)
    return None, None

# ---------------- Header
st.markdown("<div style='display:flex; justify-content:space-between; align-items:center'>"
            "<div><h1 style='margin:0;color:#123a6a'>📊 Dashboard Ekonomi</h1>"
            "<div class='small-note'>Ringkasan 10 indikator utama — data dari folder <code>data/</code></div></div>"
            "<div class='small-note'>Sumber: World Bank / file lokal</div></div>", unsafe_allow_html=True)
st.write("")

# ---------------- Controls (useful, bukan kosong)
controls_col1, controls_col2, controls_col3 = st.columns([3,2,2])
with controls_col1:
    country_query = st.text_input("🔎 Cari negara (opsional)", placeholder="ketik nama negara untuk highlight di grafik/peta")
with controls_col2:
    map_indicator = st.selectbox("Indikator untuk peta", list(FILES.keys()), index=0)
with controls_col3:
    debug_mode = st.checkbox("Tampilkan debug ringan", value=False)

st.write("")

# ---------------- KPI cards (2 baris x 5)
st.markdown("<div class='section-title'>📌 KPI Utama</div>", unsafe_allow_html=True)
kpi_keys = list(FILES.keys())
rows = [kpi_keys[:5], kpi_keys[5:10]]
for row in rows:
    cols = st.columns(5, gap="small")
    for key, col in zip(row, cols):
        fname = FILES.get(key, "")
        path = os.path.join(DATA_DIR, fname)
        dfk = read_file_try(path)
        val, yr = latest_value_from_df(dfk)
        with col:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:14px;color:#406a9a'>{ICONS.get(key)} <strong>{key}</strong></div>", unsafe_allow_html=True)
            if val is None:
                st.markdown("<div class='kpi-value'>—</div>", unsafe_allow_html=True)
                st.markdown("<div class='kpi-label'>Tahun: -</div>", unsafe_allow_html=True)
            else:
                # formatting number
                if abs(val) >= 1e9:
                    disp = f"{val:,.0f}"
                elif abs(val) >= 1e3:
                    disp = f"{val:,.2f}"
                else:
                    disp = f"{val:.2f}"
                st.markdown(f"<div class='kpi-value'>{disp}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='kpi-label'>Tahun: {yr}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ---------------- Trend: 10 mini-trend
st.markdown("<div class='section-title'>📈 Tren Singkat (10 indikator)</div>", unsafe_allow_html=True)
for row_keys in [kpi_keys[:5], kpi_keys[5:10]]:
    cols = st.columns(5, gap="small")
    for key, col in zip(row_keys, cols):
        dfk = read_file_try(os.path.join(DATA_DIR, FILES.get(key)))
        lg = to_long_if_wide(dfk)
        with col:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:14px;color:#406a9a'>{ICONS.get(key)} <strong>{key}</strong></div>", unsafe_allow_html=True)
            if lg.empty:
                st.write("data tidak tersedia")
            else:
                agg = lg.groupby("year")["value"].mean().reset_index()
                fig = px.line(agg, x="year", y="value", height=130)
                fig.update_layout(margin=dict(t=6,b=6,l=6,r=6), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ---------------- Map summary (choose indicator + year)
st.markdown("<div class='section-title'>🌍 Peta Ringkasan</div>", unsafe_allow_html=True)
map_col, map_ctrl = st.columns([3,1])
with map_ctrl:
    sel_file = FILES.get(map_indicator)
    sel_df = read_file_try(os.path.join(DATA_DIR, sel_file))
    sel_long = to_long_if_wide(sel_df)
    years_avail = sorted(sel_long["year"].unique().astype(int).tolist()) if not sel_long.empty else []
    year_choice = st.select_slider("Tahun", years_avail, value=years_avail[-1] if years_avail else None) if years_avail else None

with map_col:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if sel_long.empty or year_choice is None:
        st.info("Pilih indikator dengan data tahun (cek file di folder data/).")
    else:
        df_map = sel_long[sel_long["year"] == int(year_choice)]
        if df_map.empty:
            st.warning("Tidak ada data untuk tahun yang dipilih.")
        else:
            try:
                fig = px.choropleth(df_map, locations="country", locationmode="country names",
                                    color="value", hover_name="country",
                                    color_continuous_scale="Blues",
                                    title=f"{map_indicator} — {year_choice}")
                fig.update_layout(margin=dict(t=40,l=0,r=0,b=0), height=520)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error("Gagal membuat peta (periksa nama negara).")
                if debug_mode:
                    st.exception(e)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ---------------- Grid ringkasan (small cards)
st.markdown("<div class='section-title'>📦 Ringkasan 10 Indikator</div>", unsafe_allow_html=True)
grid_cols = st.columns(5, gap="small")
for i, key in enumerate(kpi_keys):
    col = grid_cols[i % 5]
    dfk = read_file_try(os.path.join(DATA_DIR, FILES.get(key)))
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
                fig = px.line(agg, x="year", y="value", height=90)
                fig.update_layout(margin=dict(t=6,b=6,l=6,r=6), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass
        st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.caption("Tip: jika indikator kosong — periksa file CSV/XLSX di folder 'data/' apakah berformat wide (tahun kolom) atau long (Country, Year, Value). Aktifkan debug ringan jika perlu.")
