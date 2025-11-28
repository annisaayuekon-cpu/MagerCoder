# pages/page1.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📈 Pertumbuhan Ekonomi & GDP")
st.write("Pilih indikator dan tahun untuk melihat peta choropleth (nilai per negara).")

# -----------------------------
# Lokasi folder data & file
# -----------------------------
DATA_DIR = "data"
files = {
    "GDP (current US$)": "1.1. GDP (CURRENT US$).xlsx",
    "GDP per capita (current US$)": "1.2. GDP PER CAPITA.xlsx",
    "GDP growth (annual %)": "1.3 GDP growth (%).xlsx",
    "Gross National Income (GNI)": "1.4 Gross National Income (GNI).xlsx",
    "GDP by sector (Agriculture, Industry, Services)": "1.5 GDP by sector (pertanian, industri, jasa).xlsx"
}

# helper: load file if exists
@st.cache_data
def load_excel(path):
    return pd.read_excel(path)

available_indicators = [k for k, fname in files.items() if os.path.exists(os.path.join(DATA_DIR, fname))]
if not available_indicators:
    st.warning(f"Tidak menemukan file indikator di `{DATA_DIR}/`. Pastikan file .xlsx ada.")
    st.stop()

# -----------------------------
# Pilihan indikator & file
# -----------------------------
indicator = st.selectbox("Pilih indikator", available_indicators)
file_path = os.path.join(DATA_DIR, files[indicator])

# Load df
try:
    df = load_excel(file_path)
except Exception as e:
    st.error(f"Gagal membaca file: {e}")
    st.stop()

st.subheader("📄 Preview data (baris atas)")
st.dataframe(df.head(10), use_container_width=True)

# -----------------------------
# Deteksi kolom tahun & nama negara
# -----------------------------
cols = [str(c) for c in df.columns]
# year-like columns: 4-digit numeric
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
# country column heuristic
country_col = None
for cand in ["Country Name", "country", "Country", "Negara", "Entity"]:
    if cand in df.columns:
        country_col = cand
        break
if country_col is None:
    # assume first column is country
    country_col = df.columns[0]

if not year_cols:
    st.error("Tidak ditemukan kolom tahun (mis. '1990','1991',...). Pastikan file memiliki kolom tahun.")
    st.stop()

# -----------------------------
# Pilih tahun untuk peta
# -----------------------------
years = sorted([int(y) for y in year_cols])
year_min, year_max = min(years), max(years)
sel_year = st.slider("Pilih tahun pada peta", year_min, year_max, (max(years),))[0]

# -----------------------------
# Membuat dataframe long (country, year, value)
# -----------------------------
df_long = df.melt(id_vars=[country_col], value_vars=year_cols, var_name="year", value_name="value")
df_long["year"] = df_long["year"].astype(int)
# drop NaN values
df_long = df_long.dropna(subset=["value"])

# -----------------------------
# Peta dunia: ambil data tahun terpilih
# -----------------------------
df_map = df_long[df_long["year"] == sel_year].copy()

# Plot choropleth
st.subheader(f"🌎 Peta dunia — {indicator} ({sel_year})")

# Prefer using country names; Plotly can use locationmode='country names'
# But sometimes country names in dataset mismatch plotly; we attempt as-is first.
if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
    try:
        fig = px.choropleth(
            df_map,
            locations=country_col,
            locationmode="country names",
            color="value",
            hover_name=country_col,
            color_continuous_scale="Viridis",
            title=f"{indicator} — {sel_year}",
            labels={"value": indicator}
        )
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.write("Gagal membuat peta otomatis dengan 'country names'. Coba gunakan map dengan ISO3 (fallback).")
        st.write("Error:", e)
        # Fallback: attempt to map common country columns if available (ISO codes)
        # If dataset already has ISO3 column, try that:
        iso_cols = [c for c in df.columns if str(c).lower() in ("iso3", "iso", "iso3 code", "country code")]
        if iso_cols:
            iso_col = iso_cols[0]
            df_map_iso = df.loc[df[year_cols].notna().any(axis=1), [country_col] + [iso_col] + year_cols]
            df_map_iso = df_map_iso.melt(id_vars=[country_col, iso_col], value_vars=year_cols, var_name="year", value_name="value")
            df_map_iso["year"] = df_map_iso["year"].astype(int)
            df_map_iso = df_map_iso[df_map_iso["year"]==sel_year].dropna(subset=["value"])
            if not df_map_iso.empty:
                fig2 = px.choropleth(
                    df_map_iso,
                    locations=iso_col,
                    color="value",
                    hover_name=country_col,
                    title=f"{indicator} — {sel_year}",
                    color_continuous_scale="Viridis"
                )
                fig2.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.error("Fallback dengan ISO gagal: tidak ada data ISO / nilai untuk tahun ini.")
        else:
            st.error("Tidak ada kolom ISO untuk fallback — periksa nama negara agar cocok dengan Plotly (country names).")

# -----------------------------
# Time series per negara (line chart)
# -----------------------------
st.subheader("📈 Time series: pilih negara untuk menampilkan grafik")
countries = df_long[country_col].dropna().unique().tolist()
sel_country = st.selectbox("Pilih negara (time series)", countries, index=0)

df_country_ts = df_long[df_long[country_col] == sel_country].sort_values("year")
if not df_country_ts.empty:
    st.line_chart(df_country_ts.set_index("year")["value"], height=350)
    st.dataframe(df_country_ts.reset_index(drop=True).tail(50))
else:
    st.write("Tidak ada time series untuk negara ini.")

# -----------------------------
# Download data filtered (opsional)
# -----------------------------
st.subheader("⬇ Unduh data (CSV)")
csv = df_long.to_csv(index=False)
st.download_button("Download semua data (long format)", csv, file_name=f"{indicator.replace(' ','_')}_long.csv")
