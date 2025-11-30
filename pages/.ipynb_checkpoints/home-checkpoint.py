

# pages/home.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Home — Ringkasan 10 Indikator", layout="wide", page_icon="🏠")

DATA_DIR = "data"

# --- 10 indikator utama (key -> filename in data/)
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

# ----------------- util: tolerant loader -----------------
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
    # try common separators
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
    """Return long format (country, year, value) if possible. Supports wide and simple long."""
    if df.empty:
        return pd.DataFrame()
    cols = [str(c).strip() for c in df.columns]
    lower = [c.lower() for c in cols]
    # long if 'year' in columns
    if "year" in lower:
        # normalize
        df2 = df.copy()
        # find country col
        country_cols = [c for c in df2.columns if str(c).strip().lower() in ("country name","country","negara","entity")]
        country_col = country_cols[0] if country_cols else df2.columns[0]
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
    # otherwise wide -> melt
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

# ----------------- Header (layout similar to contoh) -----------------
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <div>
        <h1 style="margin:0">🏠 Ringkasan 10 Indikator Utama</h1>
        <div style="color:gray">KPI — Tren — Peta — Ringkasan singkat</div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:12px; color:gray">Sumber: World Bank / Data Lokal</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")  # spacer

# ----------------- KPI cards 10 indikator (2 rows of 5) -----------------
st.subheader("KPI Utama")
kpi_keys = list(FILES.keys())
# make 2 rows of 5
rows = [kpi_keys[:5], kpi_keys[5:10]]
for row in rows:
    cols = st.columns(5, gap="small")
    for key, col in zip(row, cols):
        fname = FILES.get(key, "")
        dfk = load_table(os.path.join(DATA_DIR, fname))
        val, yr = latest_value_from_df(dfk) if not dfk.empty else (None, None)
        icon = ICONS.get(key, "📊")
        bg = "#f6fbff"
        card_html = f"""
            <div style="background:{bg}; padding:10px; border-radius:8px; min-height:90px;">
              <div style="font-size:16px;">{icon} <strong>{key}</strong></div>
              <div style="font-size:20px; margin-top:6px;">{f'{val:,.2f}' if val is not None else '—'}</div>
              <div style="color:gray; font-size:12px;">Tahun: {yr if yr else '-'}</div>
            </div>
        """
        col.markdown(card_html, unsafe_allow_html=True)

st.write("---")

# ----------------- Trend area: 10 mini trends -----------------
st.subheader("Tren Singkat 10 Indikator")
trend_cols = st.columns(5)
mini_cols = st.columns(5)
# we will show 10 trends in two rows: first 5 in trend_cols, next 5 in mini_cols
for i, key in enumerate(kpi_keys):
    fname = FILES.get(key, "")
    dfk = load_table(os.path.join(DATA_DIR, fname))
    lg = to_long_if_wide(dfk)
    target_col = trend_cols[i] if i < 5 else mini_cols[i - 5]
    target_col.markdown(f"**{ICONS.get(key,'')} {key}**")
    if not lg.empty:
        agg = lg.groupby("year")["value"].mean().reset_index()
        fig = px.line(agg, x="year", y="value")
        fig.update_layout(height=120, margin=dict(t=6,b=6,l=6,r=6))
        target_col.plotly_chart(fig, use_container_width=True)
    else:
        target_col.write("data tidak tersedia")

st.write("---")

# ----------------- Summary map (pilih indikator & tahun) -----------------
st.subheader("Peta Ringkasan")
map_left, map_right = st.columns([3,1])
with map_right:
    sel_indicator = st.selectbox("Pilih indikator untuk peta", kpi_keys, index=0)
    # load and prepare long
    sel_file = FILES.get(sel_indicator,"")
    sel_df = load_table(os.path.join(DATA_DIR, sel_file))
    sel_long = to_long_if_wide(sel_df)
    years_avail = sorted(sel_long["year"].unique().astype(int).tolist()) if not sel_long.empty else []
    year_map = st.select_slider("Tahun", years_avail, value=years_avail[-1] if years_avail else None) if years_avail else None

with map_left:
    if sel_long.empty or year_map is None:
        st.info("Pilih indikator yang memiliki data (file ada dan kolom tahun).")
    else:
        df_map = sel_long[sel_long["year"] == int(year_map)]
        if df_map.empty:
            st.warning("Tidak ada data untuk tahun yang dipilih.")
        else:
            try:
                fig = px.choropleth(df_map, locations="country", locationmode="country names",
                                    color="value", hover_name="country",
                                    color_continuous_scale="Viridis",
                                    title=f"{sel_indicator} — {year_map}")
                fig.update_layout(margin=dict(t=40,l=0,r=0,b=0), height=520)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error("Gagal menggambar peta. Pastikan nama negara sesuai 'country names'.")
                st.exception(e)

st.write("---")

# ----------------- Grid ringkasan 10 indikator utama -----------------
st.subheader("Ringkasan 10 Indikator Utama")
grid_cols = st.columns(5)
for i, key in enumerate(kpi_keys):
    col = grid_cols[i % 5]
    fname = FILES.get(key,"")
    dfk = load_table(os.path.join(DATA_DIR, fname))
    lg = to_long_if_wide(dfk)
    # latest value
    latest = None
    latest_year = None
    if not dfk.empty:
        latest, latest_year = latest_value_from_df(dfk)
    col.markdown(f"**{ICONS.get(key)} {key}**")
    if latest is None:
        col.write("— data tidak tersedia")
    else:
        col.metric(f"Tahun {latest_year}", f"{latest:,.2f}")
    # small sparkline if long available
    if not lg.empty:
        agg = lg.groupby("year")["value"].mean().reset_index().tail(8)
        try:
            fig = px.line(agg, x="year", y="value")
            fig.update_layout(height=100, margin=dict(t=6,b=6,l=6,r=6))
            col.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

st.write("")
st.caption("Tip: pastikan file CSV ada di folder 'data/' dan kolom tahun konsisten (mis. 2000, 2001, ...).")


