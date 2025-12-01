# pages/home.py

import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(
    page_title="Ringkasan Dashboard Ekonomi",
    layout="wide",
    page_icon="🏠",
)

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

# -------------------------------------------------
# Helper: tolerant CSV loader
# -------------------------------------------------
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
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
        else:
            col.metric(f"Tahun {yr}", f"{val:,.2f}")
        long = pivot_long_first_numeric(df)
        if not long.empty:
            agg = long.groupby("year")["value"].mean().reset_index().tail(8)
            try:
                fig = px.line(agg, x="year", y="value")
                fig.update_layout(height=100, margin=dict(t=6, b=6, l=6, r=6))
                col.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

st.write("---")
st.info(
    "Gunakan menu di sidebar (Page 1–10) untuk melihat halaman detail per kelompok "
    "indikator. Jika peta atau ranking kosong, periksa nama file di folder 'data/' "
    "dan format kolom tahunnya (mis. 2000, 2001, ...)."
)
