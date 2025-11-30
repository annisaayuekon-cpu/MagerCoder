# pages/page9.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Kesehatan", page_icon="🏥")

st.title("🏥 Kesehatan — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator Kesehatan berdasarkan file CSV di folder `data/`.\n"
    "Script otomatis mendeteksi format file (wide atau long) sehingga file long/wide keduanya bisa dipakai."
)

# -----------------------------
# folder data & mapping file
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Health expenditure (current US$ or % of GDP)": "9.1. HEALTH EXPENDITURE.csv",
    "Maternal mortality (per 100,000 live births)": "9.2. MATERNAL MORTALITY.csv",
    "Infant mortality (per 1,000 live births)": "9.3. INFANT MORTALITY.csv",
    "People using safely managed drinking water services (%)": "9.4. PEOPLE USING SAFELY MANAGED DRINKING WATER SERVICES.csv",
}

# -----------------------------
# flexible CSV loader
# -----------------------------
@st.cache_data
def load_csv_clean(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
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

# -----------------------------
# detect which files exist
# -----------------------------
available_files = []
for k, v in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, v)):
        available_files.append(k)

if not available_files:
    st.error(f"Tidak ada file CSV Page 9 ditemukan di `{DATA_DIR}/`. Silakan tambahkan file CSV.")
    st.stop()

# -----------------------------
# select indicator and load
# -----------------------------
indicator = st.selectbox("📌 Pilih indikator Kesehatan:", available_files)
file_path = os.path.join(DATA_DIR, FILES[indicator])

df = load_csv_clean(file_path)
if df.empty:
    st.error(f"File `{os.path.basename(file_path)}` kosong atau gagal dibaca.")
    st.stop()

st.subheader("📄 Preview data (sample)")
st.dataframe(df.head(15), use_container_width=True)

# -----------------------------
# helper functions
# -----------------------------
def find_country_col(df_cols):
    candidates = ["country name", "country", "negara", "entity"]
    for cand in candidates:
        for c in df_cols:
            if c.lower() == cand:
                return c
    return df_cols[0]

# -----------------------------
# detect format long vs wide
# -----------------------------
cols_raw = [str(c).strip() for c in df.columns]
cols_lower = [c.lower() for c in cols_raw]

df_long = pd.DataFrame()

if "year" in cols_lower:
    st.info("Format terdeteksi: LONG (country-year-value).")
    # normalize col names
    rename_map = {}
    for c in df.columns:
        if c.lower() in ["country", "country name", "negara", "entity"]:
            rename_map[c] = "country"
        if c.lower() == "year":
            rename_map[c] = "year"
    df2 = df.rename(columns=rename_map)
    if "country" not in df2.columns or "year" not in df2.columns:
        st.error("Kolom country/year tidak ditemukan setelah normalisasi. Periksa header CSV.")
        st.stop()
    value_cols = [c for c in df2.columns if c not in ["country", "year"]]
    if len(value_cols) == 0:
        st.error("Tidak ditemukan kolom nilai pada file long-format.")
        st.stop()
    value_col = value_cols[0] if len(value_cols) == 1 else value_cols[-1]
    df_long = df2[["country", "year", value_col]].copy().rename(columns={value_col: "value"})
    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["year", "value"])
else:
    years = [c for c in cols_raw if c.isdigit() and len(c) == 4]
    if not years:
        st.error("Tidak ditemukan kolom tahun (mis. 1990, 2005) di file ini. Periksa header CSV.")
        st.stop()
    st.info("Format terdeteksi: WIDE (kolom tahun di header).")
    country_col = find_country_col(df.columns)
    try:
        df_long = df.melt(
            id_vars=[country_col],
            value_vars=years,
            var_name="year",
            value_name="value"
        ).rename(columns={country_col: "country"})
        df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
        df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
        df_long = df_long.dropna(subset=["value"])
    except Exception as e:
        st.error("Gagal transformasi wide->long. Periksa struktur CSV.")
        st.exception(e)
        st.stop()

if df_long.empty:
    st.error("Data kosong setelah transformasi. Periksa file.")
    st.stop()

df_long["country"] = df_long["country"].astype(str).str.strip()

# -----------------------------
# peta options + color
# -----------------------------
years_sorted = sorted(df_long["year"].unique().astype(int).tolist())
if not years_sorted:
    st.error("Tidak ada tahun valid setelah parsing.")
    st.stop()

st.subheader("🔢 Opsi Peta")
cp1, cp2 = st.columns([3,1])
with cp2:
    mode = st.radio("Mode warna peta", ("Continuous (nilai)", "Quantile (buckets)"))
    color_scale = st.selectbox("Color scale (continuous):", ["Viridis", "Plasma", "Cividis", "Turbo", "Blues"], index=0)
with cp1:
    year_select = st.slider("Pilih tahun untuk peta dunia:", int(min(years_sorted)), int(max(years_sorted)), int(max(years_sorted)))

df_map = df_long[df_long["year"] == int(year_select)]

st.subheader(f"🌍 Peta Dunia — {indicator} ({year_select})")
if df_map.empty:
    st.warning("Tidak ada data untuk tahun ini.")
else:
    try:
        fig = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            hover_name="country",
            color_continuous_scale=color_scale.lower() if color_scale.lower() in px.colors.named_colorscales() else "Viridis",
            labels={"value": indicator},
            title=f"{indicator} — {year_select}"
        )
        fig.update_layout(margin={"r":0,"l":0,"t":30,"b":0}, height=520)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("❌ Peta gagal dibuat. Periksa nama negara di CSV (gunakan country names).")
        st.exception(e)

# -----------------------------
# time series
# -----------------------------
st.subheader("📈 Grafik Time Series per Negara")
country_list = sorted(df_long["country"].dropna().unique().tolist())
if not country_list:
    st.info("Tidak ada negara tersedia.")
else:
    default_country = "Indonesia" if "Indonesia" in country_list else country_list[0]
    selected = st.multiselect("Pilih negara (bisa lebih dari satu):", country_list, default=[default_country])
    df_ts = df_long[df_long["country"].isin(selected)].sort_values(["country","year"])
    if df_ts.empty:
        st.info("Tidak ada data time series untuk negara yang dipilih.")
    else:
        fig_ts = px.line(
            df_ts,
            x="year",
            y="value",
            color="country",
            markers=True,
            labels={"year":"Tahun","value":indicator,"country":"Negara"},
            title=f"Time series — {indicator}"
        )
        fig_ts.update_layout(xaxis=dict(dtick=5), margin={"l":0,"r":0,"t":30,"b":0})
        st.plotly_chart(fig_ts, use_container_width=True)
        st.dataframe(df_ts.reset_index(drop=True), use_container_width=True)

# -----------------------------
# ringkasan statistik top/bottom
# -----------------------------
st.subheader("🔎 Statistik Ringkas")
agg_latest = df_long.groupby("country").apply(lambda g: g[g["year"]==g["year"].max()]["value"].mean() if not g.empty else None).reset_index()
agg_latest.columns = ["country","latest_value"]
agg_latest = agg_latest.dropna(subset=["latest_value"]).sort_values("latest_value", ascending=False)

ct1, ct2 = st.columns(2)
with ct1:
    st.markdown("**Top 10 (terbesar)**")
    st.table(agg_latest.head(10).style.format({"latest_value":"{:,.2f}"}))
with ct2:
    st.markdown("**Bottom 10 (terendah)**")
    st.table(agg_latest.tail(10).sort_values("latest_value", ascending=True).style.format({"latest_value":"{:,.2f}"}))

# -----------------------------
# download data
# -----------------------------
st.subheader("📥 Ekspor Data (long format)")
csv = df_long.to_csv(index=False)
safe_name = indicator.replace(" ","_").replace("/","_").replace("(","").replace(")","")
st.download_button(label="⬇ Download CSV (long)", data=csv, file_name=f"page9_{safe_name}_{year_select}.csv", mime="text/csv")

st.caption("Tip: jika banyak negara kosong di peta, periksa nama negara di CSV. Jika kamu kirim file ISO3/region, aku bantu map otomatis.")
