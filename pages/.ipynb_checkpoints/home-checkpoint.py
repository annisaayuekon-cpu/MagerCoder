


# pages/home.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Ringkasan Dashboard Ekonomi", layout="wide", page_icon="🏠")

DATA_DIR = "data"

FILES = {
    "GDP (current US$)": "1.1. GDP (CURRENT US$).csv",
    "GDP per capita": "1.2. GDP PER CAPITA.csv",
    "GDP growth (%)": "1.3 GDP growth (%).csv",
    "GNI": "1.4 Gross National Income (GNI).csv",
    "GDP by sector": "1.5 GDP by sector (pertanian, industri, jasa).csv",
    "Labor force participation": "2.1 Labor force participation rate.csv",
    "Unemployment rate": "2.2 Unemployment rate.csv",
    "Youth unemployment": "2.3 Youth unemployment.csv",
    "Employment by sector": "2.4 Employment by sector.csv",
    "Inflation (CPI)": "3.1 Inflation, consumer prices (%).csv",
    "Consumer expenditure": "3.2. CONSUMER EXPENDITURE.csv",
    "Imports of goods": "4.2 Imports of goods and services.csv",
    "Tariff rates": "4.3 Tariff rates.csv",
    "Trade openness": "4.4 Trade openness.csv",
}

# ---------------- tolerant CSV loader ----------------
@st.cache_data
def load_csv(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path, sep=";", engine="python", on_bad_lines="skip")
    except Exception:
        return pd.read_csv(path, sep=",", engine="python", on_bad_lines="skip")

def detect_year_columns(df):
    return [c for c in df.columns if str(c).isdigit() and len(str(c)) == 4]

def ensure_iso3(df):
    # Try to detect an ISO3 column; otherwise leave None
    lower_cols = [c.lower() for c in df.columns]
    for cand in ("iso3", "iso_code", "iso"):
        if cand in lower_cols:
            return df.columns[lower_cols.index(cand)]
    return None

def pivot_long_first_numeric(df):
    """Return long dataframe: country, year, value (use first numeric row if needed)."""
    years = detect_year_columns(df)
    if not years:
        return pd.DataFrame()
    idcol = df.columns[0]
    long = df.melt(id_vars=[idcol], value_vars=years, var_name="year", value_name="value")
    long = long.rename(columns={idcol: "country"})
    long["year"] = long["year"].astype(int)
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value"])
    return long

def latest_value(df):
    years = detect_year_columns(df)
    if not years:
        return None, None
    sorted_years = sorted([int(y) for y in years])
    last = str(sorted_years[-1])
    vals = pd.to_numeric(df[last], errors="coerce").dropna()
    if vals.empty:
        return None, last
    # return mean for global summary or sum depending on indicator — here return mean
    return float(vals.mean()), last

# ---------------- Header ----------------
st.markdown("<h1 style='margin:0;'>📊 Ringkasan Dashboard Ekonomi</h1>", unsafe_allow_html=True)
st.markdown("Ringkasan cepat indikator utama — pilih indikator & tahun untuk melihat peta dan ranking.")

# ---------------- Top controls (indicator + year selector) ----------------
indicator_list = list(FILES.keys())
indicator_selected = st.selectbox("Pilih indikator untuk peta & ranking", indicator_list, index=0)

# prepare df for selected indicator
file_sel = FILES.get(indicator_selected, "")
df_sel = load_csv(os.path.join(DATA_DIR, file_sel)) if file_sel else pd.DataFrame()
long_sel = pivot_long_first_numeric(df_sel) if not df_sel.empty else pd.DataFrame()

years_sel = sorted(long_sel["year"].unique().tolist()) if not long_sel.empty else []
if years_sel:
    year_selected = st.select_slider("Pilih tahun untuk peta & ranking", years_sel, value=years_sel[-1])
else:
    year_selected = None
st.write("")  # spacing

# ---------------- KPI colored cards (4) ----------------
st.subheader("Ringkasan Cepat")
col1, col2, col3, col4 = st.columns(4, gap="large")

kpi_defs = [
    ("GDP growth (%)", "📈", FILES.get("GDP growth (%)", "")),
    ("GDP per capita", "💰", FILES.get("GDP per capita", "")),
    ("Unemployment rate", "👥", FILES.get("Unemployment rate", "")),
    ("Inflation (CPI)", "🔥", FILES.get("Inflation (CPI)", "")),
]

def render_colored_card(col, title, emoji, fname):
    path = os.path.join(DATA_DIR, fname) if fname else ""
    df = load_csv(path) if path else pd.DataFrame()
    val, yr = latest_value(df)
    # choose background color via simple mapping
    colors = {
        "GDP growth (%)": "#ffe8d6",
        "GDP per capita": "#e8f6ff",
        "Unemployment rate": "#fff0f6",
        "Inflation (CPI)": "#f0fff4",
    }
    bg = colors.get(title, "#f7f7f7")
    if val is None:
        display = "—"
    else:
        display = f"{val:,.2f}"
    card_html = f"""
    <div style="background:{bg}; padding:14px; border-radius:8px;">
      <div style="font-size:20px;">{emoji} <strong>{title}</strong></div>
      <div style="font-size:28px; margin-top:6px;">{display}</div>
      <div style="color:gray; font-size:12px;">Tahun: {yr if yr else '-'}</div>
    </div>
    """
    col.write("", unsafe_allow_html=True)
    col.markdown(card_html, unsafe_allow_html=True)

for (title, emoji, fname), col in zip(kpi_defs, (col1, col2, col3, col4)):
    render_colored_card(col, title, emoji, fname)

st.write("---")

# ---------------- Mini trend row (4 small plots) ----------------
st.subheader("Tren Singkat")
m1, m2, m3, m4 = st.columns(4)
mini_titles = ["GDP growth (%)", "GDP per capita", "Unemployment rate", "Labor force participation"]
for title, col in zip(mini_titles, (m1, m2, m3, m4)):
    csv = FILES.get(title, "")
    df = load_csv(os.path.join(DATA_DIR, csv)) if csv else pd.DataFrame()
    long = pivot_long_first_numeric(df)
    col.markdown(f"**{title}**")
    if not long.empty:
        # aggregate (mean) per year for mini-trend
        agg = long.groupby("year")["value"].mean().reset_index()
        fig = px.line(agg, x="year", y="value")
        fig.update_layout(height=140, margin=dict(t=6,b=6,l=6,r=6))
        col.plotly_chart(fig, use_container_width=True)
    else:
        col.write("tidak tersedia")

st.write("---")

# ---------------- Map (choropleth) and Ranking ----------------
st.subheader("Peta Dunia & Ranking Negara")

map_col, table_col = st.columns([2, 1])

with map_col:
    if year_selected is None or long_sel.empty:
        st.info("Pilih indikator dan pastikan data tersedia untuk melihat peta.")
    else:
        df_year = long_sel[long_sel["year"] == int(year_selected)].copy()
        # try find ISO column in original df
        iso_col = ensure_iso3(df_sel)
        if iso_col and iso_col in df_sel.columns:
            # if df_sel had ISO column, merge iso
            iso_df = df_sel[[df_sel.columns[0], iso_col]]
            iso_df = iso_df.rename(columns={df_sel.columns[0]: "country"})
            df_year = df_year.merge(iso_df, on="country", how="left")
            loc_col = iso_col
            fig = px.choropleth(df_year, locations=loc_col, color="value", hover_name="country",
                                color_continuous_scale="Viridis", title=f"{indicator_selected} — {year_selected}")
        else:
            fig = px.choropleth(df_year, locations="country", locationmode="country names",
                                color="value", hover_name="country", color_continuous_scale="Viridis",
                                title=f"{indicator_selected} — {year_selected}")
        fig.update_layout(margin=dict(t=40, r=0, l=0, b=0))
        st.plotly_chart(fig, use_container_width=True, height=520)

with table_col:
    st.markdown("### Top / Bottom 10")
    if year_selected is None or long_sel.empty:
        st.write("Data tidak tersedia")
    else:
        df_year = long_sel[long_sel["year"] == int(year_selected)].copy()
        df_sorted = df_year.sort_values("value", ascending=False)
        top_n = df_sorted.head(10)[["country", "value"]].reset_index(drop=True)
        bottom_n = df_sorted.tail(10)[["country", "value"]].reset_index(drop=True)
        st.markdown("**Top 10**")
        st.table(top_n.style.format({"value": "{:,.2f}"}))
        st.markdown("**Bottom 10**")
        st.table(bottom_n.style.format({"value": "{:,.2f}"}))

st.write("---")

# ---------------- Detailed quick cards grid ----------------
st.subheader("Ringkasan Indikator Lainnya")
rows = []
files_items = list(FILES.items())
for i in range(0, len(files_items), 3):
    trio = files_items[i:i+3]
    cols = st.columns(3)
    for (label, fname), col in zip(trio, cols):
        df = load_csv(os.path.join(DATA_DIR, fname)) if fname else pd.DataFrame()
        val, yr = latest_value(df)
        col.markdown(f"**{label}**")
        if val is None:
            col.write("tidak tersedia")
        else:
            col.metric(f"Tahun {yr}", f"{val:,.2f}")
        # small sparkline:
        long = pivot_long_first_numeric(df)
        if not long.empty:
            agg = long.groupby("year")["value"].mean().reset_index().tail(8)
            try:
                fig = px.line(agg, x="year", y="value")
                fig.update_layout(height=100, margin=dict(t=6,b=6,l=6,r=6))
                col.plotly_chart(fig, use_container_width=True)
            except:
                pass

st.write("---")
st.info("Klik Page X di sidebar untuk ke halaman detail. Jika peta atau ranking kosong, periksa nama file di folder 'data/' dan format kolom tahunnya (mis. 2000,2001,...)")
