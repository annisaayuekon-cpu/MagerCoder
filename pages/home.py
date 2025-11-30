# home.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

DATA_DIR = "data"

# 10 indikator utama + nama file CSV-nya
MAIN_INDICATORS = {
    "GDP per capita (current US$)": "1.2. GDP PER CAPITA.csv",
    "GDP growth (%)": "1.3 GDP growth (%).csv",
    "Unemployment rate (%)": "2.2 Unemployment rate.csv",
    "Labor force participation rate (%)": "2.1 Labor force participation rate.csv",
    "Inflation, consumer prices (%)": "3.1 Inflation, consumer prices (%).csv",
    "Trade openness (% of GDP)": "4.4 Trade openness.csv",
    "FDI inflows (current US$)": "5.1 Foreign Direct Investment (FDI).csv",
    "Poverty headcount ratio ($4.20/day) (%)": "6.1. POVERTY HEADCOUNT RATIO AT $4.20 A DAY.csv",
    "GINI index": "6.2. GINI INDEX.csv",
    "CO₂ emissions (t per capita)": "10.1. CO EMISSIONS.csv",
}

# ---------------- Utilitas umum ----------------
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    # coba beberapa separator
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] >= 5:
                return df
        except Exception:
            continue
    # fallback
    return pd.read_csv(path, engine="python", on_bad_lines="skip")


def detect_year_columns(df: pd.DataFrame):
    return [c for c in df.columns if str(c).isdigit() and len(str(c)) == 4]


def detect_country_col(df: pd.DataFrame):
    for cand in ["Country Name", "Country", "Negara", "Entity", "country"]:
        if cand in df.columns:
            return cand
    return df.columns[0]


def long_one_country(df: pd.DataFrame, country: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    years = detect_year_columns(df)
    if not years:
        return pd.DataFrame()
    ccol = detect_country_col(df)
    sub = df[df[ccol] == country]
    if sub.empty:
        return pd.DataFrame()
    row = sub.iloc[0].copy()
    data = []
    for y in sorted([int(y) for y in years]):
        val = pd.to_numeric([row[str(y)]], errors="coerce")[0]
        if pd.notna(val):
            data.append({"year": int(y), "value": float(val)})
    return pd.DataFrame(data)


def latest_value_country(df: pd.DataFrame, country: str):
    """
    Ambil nilai terakhir (tahun terbaru yang tidak NaN) untuk negara tertentu.
    Return: (value, year) atau (None, None)
    """
    ts = long_one_country(df, country)
    if ts.empty:
        return None, None
    last_row = ts.sort_values("year").iloc[-1]
    return float(last_row["value"]), int(last_row["year"])


def long_all_countries(df: pd.DataFrame) -> pd.DataFrame:
    years = detect_year_columns(df)
    if not years:
        return pd.DataFrame()
    ccol = detect_country_col(df)
    df_long = df.melt(
        id_vars=[ccol],
        value_vars=years,
        var_name="year",
        value_name="value",
    )
    df_long = df_long.rename(columns={ccol: "country"})
    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["value"])
    return df_long


# ---------------- Header ----------------
st.markdown("<h1 style='margin:0;'>🏠 Ringkasan Utama Dashboard Ekonomi</h1>", unsafe_allow_html=True)
st.markdown("Pilih negara, lalu lihat **KPI utama**, tren singkat, peta dunia, dan ringkasan indikator dari 10 tema ekonomi.")

# ---------------- Pilih negara untuk KPI & tren ----------------
# ambil list negara dari salah satu file (GDP per capita)
sample_file = list(MAIN_INDICATORS.values())[0]
sample_df = load_csv(os.path.join(DATA_DIR, sample_file))
if sample_df.empty:
    st.error("Tidak bisa memuat data negara dari file referensi. Cek folder `data/`.")
    st.stop()

country_col = detect_country_col(sample_df)
countries = sorted(sample_df[country_col].dropna().unique().tolist())
default_country = "Indonesia" if "Indonesia" in countries else countries[0]

st.markdown("### 🌍 Pilih Negara")
selected_country = st.selectbox("Negara untuk KPI dan tren utama:", countries, index=countries.index(default_country))

st.write("---")

# ---------------- KPI Cards (berdasarkan negara) ----------------
st.markdown("### 🎯 KPI Utama per Negara")

kpi_meta = [
    ("GDP per capita (current US$)", "💰"),
    ("GDP growth (%)", "📈"),
    ("Unemployment rate (%)", "👷"),
    ("Labor force participation rate (%)", "🧑‍💼"),
    ("Inflation, consumer prices (%)", "🔥"),
    ("Trade openness (% of GDP)", "🌐"),
    ("FDI inflows (current US$)", "🏦"),
    ("Poverty headcount ratio ($4.20/day) (%)", "📉"),
    ("GINI index", "⚖️"),
    ("CO₂ emissions (t per capita)", "🌫️"),
]

def render_kpi_card(col, title, emoji, country):
    fname = MAIN_INDICATORS.get(title, "")
    path = os.path.join(DATA_DIR, fname) if fname else ""
    df = load_csv(path) if path else pd.DataFrame()
    val, yr = latest_value_country(df, country)
    if val is None:
        value_txt = "—"
        year_txt = "-"
    else:
        # format beda sedikit utk persen vs level
        if "%" in title:
            value_txt = f"{val:,.2f}%"
        else:
            value_txt = f"{val:,.2f}"
        year_txt = str(yr)

    card_html = f"""
    <div style="
        border:1px solid #3182ce;
        border-radius:12px;
        padding:12px 14px;
        background-color:#ffffff;
        height:120px;
        display:flex;
        flex-direction:column;
        justify-content:space-between;
    ">
      <div style="font-size:18px;">{emoji} <strong>{title}</strong></div>
      <div style="font-size:24px; margin-top:4px;">{value_txt}</div>
      <div style="color:#555; font-size:11px;">Negara: {country} • Tahun: {year_txt}</div>
    </div>
    """
    col.markdown(card_html, unsafe_allow_html=True)


row1 = st.columns(5)
row2 = st.columns(5)

for (title, emoji), col in zip(kpi_meta[:5], row1):
    render_kpi_card(col, title, emoji, selected_country)

for (title, emoji), col in zip(kpi_meta[5:], row2):
    render_kpi_card(col, title, emoji, selected_country)

st.write("---")

# ---------------- Tren singkat 10 indikator (per negara) ----------------
st.markdown("### 📈 Tren Singkat per Negara")

row_t1 = st.columns(5)
row_t2 = st.columns(5)

for (title, _), col in zip(kpi_meta[:5], row_t1):
    fname = MAIN_INDICATORS.get(title, "")
    df = load_csv(os.path.join(DATA_DIR, fname)) if fname else pd.DataFrame()
    ts = long_one_country(df, selected_country)
    col.markdown(f"**{title}**")
    if ts.empty:
        col.caption("Data tidak tersedia.")
    else:
        fig = px.line(ts, x="year", y="value", markers=True)
        fig.update_layout(
            height=160,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="",
            yaxis_title="",
        )
        col.plotly_chart(fig, use_container_width=True)

for (title, _), col in zip(kpi_meta[5:], row_t2):
    fname = MAIN_INDICATORS.get(title, "")
    df = load_csv(os.path.join(DATA_DIR, fname)) if fname else pd.DataFrame()
    ts = long_one_country(df, selected_country)
    col.markdown(f"**{title}**")
    if ts.empty:
        col.caption("Data tidak tersedia.")
    else:
        fig = px.line(ts, x="year", y="value", markers=True)
        fig.update_layout(
            height=160,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="",
            yaxis_title="",
        )
        col.plotly_chart(fig, use_container_width=True)

st.write("---")

# ---------------- Peta ringkasan (pilih 1 indikator) ----------------
st.markdown("### 🗺️ Peta Dunia per Indikator")

indicator_for_map = st.selectbox("Pilih indikator untuk peta dunia:", list(MAIN_INDICATORS.keys()))
map_file = MAIN_INDICATORS[indicator_for_map]
df_map_raw = load_csv(os.path.join(DATA_DIR, map_file))
df_long_all = long_all_countries(df_map_raw)

if df_long_all.empty:
    st.info("Data untuk peta dunia belum tersedia / format tidak sesuai.")
else:
    years_avail = sorted(df_long_all["year"].unique())
    year_map = st.slider(
        "Pilih tahun:",
        int(min(years_avail)),
        int(max(years_avail)),
        int(max(years_avail)),
    )

    df_year = df_long_all[df_long_all["year"] == year_map].copy()
    st.caption(f"Peta nilai {indicator_for_map} pada tahun {year_map}.")

    fig_map = px.choropleth(
        df_year,
        locations="country",
        locationmode="country names",
        color="value",
        hover_name="country",
        color_continuous_scale="Viridis",
        title=f"{indicator_for_map} — {year_map}",
    )
    fig_map.update_layout(margin=dict(t=40, r=0, l=0, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

st.write("---")

# ---------------- Grid ringkasan (global, semua negara) ----------------
st.markdown("### 📦 Ringkasan Cepat 10 Indikator (Global)")

def latest_global_mean(df: pd.DataFrame):
    years = detect_year_columns(df)
    if not years:
        return None, None
    years_int = sorted([int(y) for y in years])
    for y in reversed(years_int):
        col_y = str(y)
        vals = pd.to_numeric(df[col_y], errors="coerce").dropna()
        if not vals.empty:
            return float(vals.mean()), y
    return None, None

rows = []
items = list(MAIN_INDICATORS.items())
for i in range(0, len(items), 2):
    rows.append(items[i:i+2])

for pair in rows:
    cols = st.columns(len(pair))
    for (label, fname), col in zip(pair, cols):
        df = load_csv(os.path.join(DATA_DIR, fname))
        val, yr = latest_global_mean(df)
        col.markdown(f"**{label}**")
        if val is None:
            col.caption("Ringkasan global belum tersedia.")
        else:
            col.metric(f"Rata-rata global {yr}", f"{val:,.2f}")
            long_df = long_all_countries(df)
            if not long_df.empty:
                agg = (
                    long_df.groupby("year")["value"]
                    .mean()
                    .reset_index()
                    .tail(15)
                )
                fig_g = px.line(agg, x="year", y="value")
                fig_g.update_layout(
                    height=130,
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis_title="",
                    yaxis_title="",
                )
                col.plotly_chart(fig_g, use_container_width=True)

st.info("Gunakan sidebar untuk berpindah ke halaman 1–10 dan melihat detail masing-masing kelompok indikator.")
