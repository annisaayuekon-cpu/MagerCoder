# pages/home.py

import streamlit as st
import pandas as pd
import os
import plotly.express as px

<<<<<<< HEAD
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
=======
st.set_page_config(
    page_title="Ringkasan Dashboard Ekonomi",
    layout="wide",
    page_icon="🏠",
)

>>>>>>> d5e53f63e7b2c285f9a80937433a970cb665fd86
DATA_DIR = "data"

# -------------------------------------------------
# Semua indikator yang tersedia
# -------------------------------------------------
FILES = {
    # 1.x – Output & income
    "GDP (current US$)": "1.1. GDP (CURRENT US$).csv",
    "GDP per capita": "1.2. GDP PER CAPITA.csv",
    "GDP growth (%)": "1.3 GDP growth (%).csv",
    "GNI": "1.4 Gross National Income (GNI).csv",
    "GDP by sector": "1.5 GDP by sector (pertanian, industri, jasa).csv",

    # 2.x – Labour
    "Labor force participation": "2.1 Labor force participation rate.csv",
    "Unemployment rate": "2.2 Unemployment rate.csv",
    "Youth unemployment": "2.3 Youth unemployment.csv",
    "Employment by sector": "2.4 Employment by sector.csv",

    # 3.x – Prices & demand
    "Inflation (CPI)": "3.1 Inflation, consumer prices (%).csv",
<<<<<<< HEAD
    "Exports (% of GDP)": "4.1 Exports of goods and services.csv",
    "FDI (net inflow)": "5.1 Foreign Direct Investment (FDI).csv",
    "GINI index": "6.2. GINI INDEX.csv",
    "CO2 per capita": "10.1. CO EMISSIONS.csv",
=======
    "Consumer expenditure": "3.2. CONSUMER EXPENDITURE.csv",

    # 4.x – Trade
    "Exports of goods and services": "4.1 Exports of goods and services.csv",
    "Imports of goods and services": "4.2 Imports of goods and services.csv",
    "Tariff rates": "4.3 Tariff rates.csv",
    "Trade openness": "4.4 Trade openness.csv",

    # 5.x – Investment
    "Foreign direct investment (FDI)": "5.1 Foreign Direct Investment (FDI).csv",
    "Gross capital formation": "5.2 Gross capital formation.csv",

    # 6.x – Poverty & inequality
    "Poverty headcount ratio at $4.20 a day": "6.1. POVERTY HEADCOUNT RATIO AT $4.20 A DAY.csv",
    "Gini index": "6.2. GINI INDEX.csv",
    "Income share held by lowest 20%": "6.3. INCOME SHARE HELD BY LOWER 20%.csv",

    # 7.x – Population & demography
    "Total population": "7.1. TOTAL POPULATION.csv",
    "Urban population": "7.2. URBAN POPULATION.csv",
    "Fertility rate": "7.3. FERTILITY RATE.csv",
    "Life expectancy at birth": "7.4. LIFE EXPECTANCY AT BIRTH.csv",

    # 8.x – Education
    "School enrollment": "8.1. SCHOOL ENROLLMENT.csv",
    "Government expenditure on education": "8.2. GOVERNMENT EXPENDITURE ON EDUCATION.csv",

    # 9.x – Health & water
    "Health expenditure": "9.1. HEALTH EXPENDITURE.csv",
    "Maternal mortality": "9.2. MATERNAL MORTALITY.csv",
    "Infant mortality": "9.3. INFANT MORTALITY.csv",
    "People using safely managed drinking water": "9.4. PEOPLE USING SAFELY MANAGED DRINKING WATER.csv",

    # 10.x – Environment & energy
    "CO emissions": "10.1. CO EMISSIONS.csv",
    "Renewable energy consumption": "10.2. RENEWABLE ENERGY CONSUMPTION.csv",
    "Forest area": "10.3. FOREST AREA.csv",
    "Electricity access": "10.4. ELECTRICITY ACCESS.csv",
>>>>>>> d5e53f63e7b2c285f9a80937433a970cb665fd86
}

# -------------------------------------------------
# Daftar agregat regional / income group / forum
# yang di-exclude dari Top/Bottom 10
# -------------------------------------------------
EXCLUDED_AGGREGATES = {
    "World",
    "High income",
    "Low income",
    "Lower middle income",
    "Upper middle income",
    "Middle income",
    "Low & middle income",
    "Euro area",
    "European Union",
    "OECD members",
    "Arab World",
    "East Asia & Pacific",
    "East Asia & Pacific (excluding high income)",
    "East Asia & Pacific (IDA & IBRD countries)",
    "Europe & Central Asia",
    "Europe & Central Asia (excluding high income)",
    "Europe & Central Asia (IDA & IBRD countries)",
    "Latin America & Caribbean",
    "Latin America & Caribbean (excluding high income)",
    "Latin America & Caribbean (IDA & IBRD countries)",
    "Middle East & North Africa",
    "Middle East & North Africa (IDA & IBRD countries)",
    "South Asia",
    "Sub-Saharan Africa",
    "Sub-Saharan Africa (excluding high income)",
    "Sub-Saharan Africa (IDA & IBRD countries)",
    "IDA only",
    "IDA total",
    "IDA blend",
    "IBRD only",
    "Small states",
    "Other small states",
    "Fragile and conflict affected situations",
    "Heavily indebted poor countries (HIPC)",
    "Least developed countries: UN classification",
}

<<<<<<< HEAD
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
=======
# -------------------------------------------------
# Helper: tolerant CSV loader
# -------------------------------------------------
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
>>>>>>> d5e53f63e7b2c285f9a80937433a970cb665fd86
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(
                path,
                sep=sep,
                engine="python",
                on_bad_lines="skip",
            )
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
<<<<<<< HEAD
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
=======
    return pd.read_csv(path, engine="python", on_bad_lines="skip")


def detect_year_columns(df: pd.DataFrame):
    return [c for c in df.columns if str(c).isdigit() and len(str(c)) == 4]


def ensure_iso3(df: pd.DataFrame):
    lower_cols = [c.lower() for c in df.columns]
    for cand in ("iso3", "iso_code", "iso"):
        if cand in lower_cols:
            return df.columns[lower_cols.index(cand)]
    return None


def pivot_long_first_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """country, year, value (long format)."""
    years = detect_year_columns(df)
    if not years:
        return pd.DataFrame()
    idcol = df.columns[0]
    long = df.melt(
        id_vars=[idcol],
        value_vars=years,
        var_name="year",
        value_name="value",
    )
    long = long.rename(columns={idcol: "country"})
    long["year"] = pd.to_numeric(long["year"], errors="coerce").astype("Int64")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["value", "year"])
    long["year"] = long["year"].astype(int)
    return long


def latest_value(df: pd.DataFrame):
    years = detect_year_columns(df)
    if not years:
        return None, None
    sorted_years = sorted([int(y) for y in years])
    last = str(sorted_years[-1])
    vals = pd.to_numeric(df[last], errors="coerce").dropna()
    if vals.empty:
        return None, last
    return float(vals.mean()), last  # rata-rata global


def exclude_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Hilangkan agregat regional/kelompok dari dataframe ranking."""
    if "country" not in df.columns:
        return df
    return df[~df["country"].isin(EXCLUDED_AGGREGATES)]


# -------------------------------------------------
# Header
# -------------------------------------------------
st.markdown(
    "<h1 style='margin:0;'>📊 Ringkasan Dashboard Ekonomi</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "Ringkasan cepat indikator makro, sosial, dan lingkungan. "
    "Pilih indikator & tahun untuk melihat peta dan ranking negara."
)

# -------------------------------------------------
# Controls atas: indikator & tahun (untuk peta & ranking)
# -------------------------------------------------
indicator_list = list(FILES.keys())
indicator_selected = st.selectbox(
    "Pilih indikator untuk peta & ranking",
    indicator_list,
    index=0,
)

file_sel = FILES.get(indicator_selected, "")
df_sel = load_csv(os.path.join(DATA_DIR, file_sel)) if file_sel else pd.DataFrame()
long_sel = pivot_long_first_numeric(df_sel) if not df_sel.empty else pd.DataFrame()

years_sel = sorted(long_sel["year"].unique().tolist()) if not long_sel.empty else []
if years_sel:
    year_selected = st.select_slider(
        "Pilih tahun acuan untuk peta & ranking "
        "(nilai terbaru ≤ tahun ini akan digunakan)",
        years_sel,
        value=years_sel[-1],
    )
else:
    year_selected = None

st.write("")

# -------------------------------------------------
# Ringkasan Cepat – KPI per negara & per tahun
# -------------------------------------------------
st.subheader("Ringkasan Cepat")

kpi_names = [
    "GDP growth (%)",
    "GDP per capita",
    "Unemployment rate",
    "Inflation (CPI)",
]

kpi_data = {}
kpi_countries = set()
kpi_years = set()

for name in kpi_names:
    fname = FILES.get(name, "")
    df_k = load_csv(os.path.join(DATA_DIR, fname)) if fname else pd.DataFrame()
    long_k = pivot_long_first_numeric(df_k)
    if not long_k.empty:
        kpi_data[name] = long_k
        kpi_countries.update(long_k["country"].dropna().unique().tolist())
        kpi_years.update(long_k["year"].dropna().unique().tolist())

country_options = sorted(kpi_countries) if kpi_countries else []
year_options_kpi = sorted(kpi_years) if kpi_years else []

if country_options and year_options_kpi:
    default_country_idx = (
        country_options.index("Indonesia")
        if "Indonesia" in country_options
        else 0
    )
    kpi_country = st.selectbox(
        "Pilih negara untuk KPI",
        country_options,
        index=default_country_idx,
    )
    kpi_year = st.selectbox(
        "Pilih tahun untuk KPI",
        year_options_kpi,
        index=len(year_options_kpi) - 1,
    )
else:
    kpi_country = None
    kpi_year = None
    st.warning(
        "Data KPI (GDP growth, GDP per capita, pengangguran, inflasi) "
        "belum tersedia lengkap."
    )

col1, col2, col3, col4 = st.columns(4, gap="large")


def render_kpi_card(col, title, emoji, long_df, country, year):
    colors = {
        "GDP growth (%)": "#ffe8d6",
        "GDP per capita": "#e8f6ff",
        "Unemployment rate": "#fff0f6",
        "Inflation (CPI)": "#f0fff4",
    }
    bg = colors.get(title, "#f7f7f7")

    value = None
    if (
        long_df is not None
        and not long_df.empty
        and country is not None
        and year is not None
    ):
        sub = long_df[
            (long_df["country"] == country) & (long_df["year"] == year)
        ]
        if not sub.empty:
            value = float(sub["value"].iloc[0])

    display = "—" if value is None else f"{value:,.2f}"
    subtitle = (
        f"{country}, {year}"
        if (country is not None and year is not None)
        else "Data tidak tersedia"
    )

    card_html = f"""
    <div style="background:{bg}; padding:14px; border-radius:8px;">
      <div style="font-size:20px;">{emoji} <strong>{title}</strong></div>
      <div style="font-size:28px; margin-top:6px;">{display}</div>
      <div style="color:gray; font-size:12px;">{subtitle}</div>
    </div>
    """
    col.markdown(card_html, unsafe_allow_html=True)


for (title, emoji), col in zip(
    zip(kpi_names, ["📈", "💰", "👥", "🔥"]),
    (col1, col2, col3, col4),
):
    render_kpi_card(
        col,
        title,
        emoji,
        kpi_data.get(title),
        kpi_country,
        kpi_year,
    )

st.write("---")

# -------------------------------------------------
# Mini trend – agregat global
# -------------------------------------------------
st.subheader("Tren Singkat")

m1, m2, m3, m4 = st.columns(4)
mini_titles = [
    "GDP growth (%)",
    "Inflation (CPI)",
    "Foreign direct investment (FDI)",
    "CO emissions",
]

for title, col in zip(mini_titles, (m1, m2, m3, m4)):
    csv = FILES.get(title, "")
    df = load_csv(os.path.join(DATA_DIR, csv)) if csv else pd.DataFrame()
    long = pivot_long_first_numeric(df)
    col.markdown(f"**{title}**")
    if not long.empty:
        agg = long.groupby("year")["value"].mean().reset_index()
        fig = px.line(agg, x="year", y="value")
        fig.update_layout(height=140, margin=dict(t=6, b=6, l=6, r=6))
        col.plotly_chart(fig, use_container_width=True)
    else:
        col.write("tidak tersedia")

st.write("---")

# -------------------------------------------------
# Map (choropleth) & ranking (Top/Bottom 10 negara)
# -------------------------------------------------
st.subheader("Peta Dunia & Ranking Negara")

map_col, table_col = st.columns([2, 1])

with map_col:
    if year_selected is None or long_sel.empty:
        st.info("Pilih indikator dan pastikan data tersedia untuk melihat peta.")
    else:
        df_up_to = long_sel[long_sel["year"] <= int(year_selected)]
        if df_up_to.empty:
            st.info("Tidak ada data hingga tahun yang dipilih.")
        else:
            df_year = (
                df_up_to.sort_values(["country", "year"])
                .groupby("country", as_index=False)
                .tail(1)
            )

            iso_col = ensure_iso3(df_sel)
            title_map = (
                f"{indicator_selected} — nilai terbaru per negara "
                f"(≤ {year_selected})"
            )

            if iso_col and iso_col in df_sel.columns:
                iso_df = df_sel[[df_sel.columns[0], iso_col]].rename(
                    columns={df_sel.columns[0]: "country"}
                )
                df_year = df_year.merge(iso_df, on="country", how="left")
                loc_col = iso_col
                fig = px.choropleth(
                    df_year,
                    locations=loc_col,
                    color="value",
                    hover_name="country",
                    hover_data={"year": True},
                    color_continuous_scale="Viridis",
                    title=title_map,
                )
            else:
                fig = px.choropleth(
                    df_year,
                    locations="country",
                    locationmode="country names",
                    color="value",
                    hover_name="country",
                    hover_data={"year": True},
                    color_continuous_scale="Viridis",
                    title=title_map,
                )

            fig.update_layout(margin=dict(t=40, r=0, l=0, b=0))
            st.plotly_chart(fig, use_container_width=True, height=520)

with table_col:
    st.markdown("### Top / Bottom 10 (negara saja)")
    if year_selected is None or long_sel.empty:
        st.write("Data tidak tersedia")
    else:
        df_up_to = long_sel[long_sel["year"] <= int(year_selected)]
        if df_up_to.empty:
            st.write("Tidak ada data hingga tahun yang dipilih.")
        else:
            df_year = (
                df_up_to.sort_values(["country", "year"])
                .groupby("country", as_index=False)
                .tail(1)
            )

            # buang regional, income group, multilateral aggregates
            df_year = exclude_aggregates(df_year)

            if df_year.empty:
                st.write("Tidak ada data negara (non-regional) untuk tahun ini.")
            else:
                df_sorted = df_year.sort_values("value", ascending=False)
                top_n = df_sorted.head(10)[["country", "value"]].reset_index(drop=True)
                bottom_n = (
                    df_sorted.tail(10)[["country", "value"]]
                    .reset_index(drop=True)
                )

                st.markdown("**Top 10**")
                st.table(top_n.style.format({"value": "{:,.2f}"}))
                st.markdown("**Bottom 10**")
                st.table(bottom_n.style.format({"value": "{:,.2f}"}))

st.write("---")

# -------------------------------------------------
# Ringkasan indikator lain (grid)
# -------------------------------------------------
st.subheader("Ringkasan Indikator Lainnya")

files_items = list(FILES.items())
for i in range(0, len(files_items), 3):
    trio = files_items[i : i + 3]
    cols = st.columns(3)
    for (label, fname), col in zip(trio, cols):
        df = load_csv(os.path.join(DATA_DIR, fname)) if fname else pd.DataFrame()
        val, yr = latest_value(df)
        col.markdown(f"**{label}**")
        if val is None:
            col.write("tidak tersedia")
>>>>>>> d5e53f63e7b2c285f9a80937433a970cb665fd86
        else:
            col.metric(f"Tahun {yr}", f"{val:,.2f}")
        long = pivot_long_first_numeric(df)
        if not long.empty:
            agg = long.groupby("year")["value"].mean().reset_index().tail(8)
            try:
<<<<<<< HEAD
                fig = px.line(agg, x="year", y="value", height=90)
                fig.update_layout(margin=dict(t=6,b=6,l=6,r=6), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
=======
                fig = px.line(agg, x="year", y="value")
                fig.update_layout(height=100, margin=dict(t=6, b=6, l=6, r=6))
                col.plotly_chart(fig, use_container_width=True)
>>>>>>> d5e53f63e7b2c285f9a80937433a970cb665fd86
            except Exception:
                pass

<<<<<<< HEAD
st.write("")
st.caption("Tip: jika indikator kosong — periksa file CSV/XLSX di folder 'data/' apakah berformat wide (tahun kolom) atau long (Country, Year, Value). Aktifkan debug ringan jika perlu.")
=======
st.write("---")
st.info(
    "Gunakan menu di sidebar (Page 1–10) untuk melihat halaman detail per kelompok "
    "indikator. Jika peta atau ranking kosong, periksa nama file di folder 'data/' "
    "dan format kolom tahunnya (mis. 2000, 2001, ...)."
)
>>>>>>> d5e53f63e7b2c285f9a80937433a970cb665fd86
