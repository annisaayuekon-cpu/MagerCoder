# pages/page8.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Education & Schooling", page_icon="🎓")

st.title("🎓 Education Indicators — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator **Pendidikan & Pengeluaran Pemerintah untuk Edukasi** "
    "berdasarkan file CSV yang berada di folder `data/`. Sistem membaca otomatis format wide/long."
)

# ---------------------------------------------------------
#  Folder & File Map
# ---------------------------------------------------------
DATA_DIR = "data"

FILES = {
    "School Enrollment (%)": "8.1. SCHOOL ENROLLMENT.csv",
    "Government Expenditure on Education (% of GDP)": "8.2. GOVENRMENT EXPENDITURE ON EDUCATION.csv",
}

# ---------------------------------------------------------
#  Loader CSV fleksibel seperti Page10
# ---------------------------------------------------------
@st.cache_data
def load_csv_clean(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except:
            pass
    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except:
        return pd.DataFrame()

# ---------------------------------------------------------
#  Deteksi file tersedia
# ---------------------------------------------------------
available = [l for l,f in FILES.items() if os.path.exists(os.path.join(DATA_DIR,f))]

if not available:
    st.error("Tidak ada file Page 8 di folder `data/`. Pastikan nama file benar.")
    st.stop()

# ---------------------------------------------------------
#  Pilih dataset Education
# ---------------------------------------------------------
indicator = st.selectbox("📌 Pilih indikator pendidikan:", available)
file_path = os.path.join(DATA_DIR, FILES[indicator])

df = load_csv_clean(file_path)
if df.empty:
    st.error(f"File `{file_path}` gagal dibaca!")
    st.stop()

st.subheader("📄 Preview Data (Raw)")
st.dataframe(df.head(15), use_container_width=True)

# ---------------------------------------------------------
#  DETEKSI FORMAT: Wide vs Long
# ---------------------------------------------------------
cols = [str(c) for c in df.columns]
lower = [c.lower() for c in cols]

def detect_country_column(cols):
    candidates = ["country","country name","entity","negara"]
    for c in cols:
        if c.lower() in candidates:
            return c
    return cols[0]

df_long = pd.DataFrame()

# Long Format ("year" exists)
if "year" in lower:
    st.info("Format terdeteksi: **LONG Format** (kolom Year tersedia)")
    
    rename_map = {}
    for c in df.columns:
        if c.lower() in ["country","country name","entity","negara"]:
            rename_map[c] = "country"
        if c.lower()=="year":
            rename_map[c] = "year"
    df2 = df.rename(columns=rename_map)

    value_cols=[c for c in df2.columns if c not in ["country","year"]]
    if not value_cols: 
        st.error("Tidak ditemukan kolom angka selain country/year")
        st.stop()
    value = value_cols[-1]

    df_long = df2[["country","year",value]].rename(columns={value:"value"})
    df_long["year"]=pd.to_numeric(df_long["year"], errors="coerce")
    df_long["value"]=pd.to_numeric(df_long["value"], errors="coerce")
    df_long=df_long.dropna(subset=["value"])

# Wide Format (tahun pada header)
else:
    years=[c for c in cols if c.isdigit() and len(c)==4]
    if not years:
        st.error("Tidak ditemukan kolom tahun. Format CSV salah.")
        st.stop()

    st.info("Format terdeteksi: **WIDE Format** (kolom tahun sebagai header)")
    ccol=detect_country_column(df.columns)

    df_long=df.melt(id_vars=[ccol], value_vars=years, var_name="year", value_name="value")
    df_long=df_long.rename(columns={ccol:"country"})
    df_long["year"]=pd.to_numeric(df_long["year"], errors="coerce")
    df_long["value"]=pd.to_numeric(df_long["value"], errors="coerce")
    df_long=df_long.dropna(subset=["value"])

if df_long.empty:
    st.error("Data kosong setelah transformasi.")
    st.stop()

# ---------------------------------------------------------
#  Peta Dunia
# ---------------------------------------------------------
years_sorted = sorted(df_long["year"].unique().astype(int).tolist())

st.subheader("🌍 World Map")
year=st.slider("Pilih Tahun", min(years_sorted), max(years_sorted), max(years_sorted))

df_year=df_long[df_long["year"]==year]

try:
    fig=px.choropleth(
        df_year,
        locations="country",
        locationmode="country names",
        color="value",
        title=f"{indicator} — {year}",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(margin={"t":30,"l":0,"r":0,"b":0})
    st.plotly_chart(fig,use_container_width=True)
except Exception as e:
    st.error("❌ Nama negara tidak sesuai standar. Perbaiki CSV.")
    st.exception(e)

# ---------------------------------------------------------
#  Grafik Time Series Multi Negara
# ---------------------------------------------------------
st.subheader("📈 Grafik Time Series Negara")

countries=sorted(df_long["country"].unique())
default="Indonesia" if "Indonesia" in countries else countries[0]

selected=st.multiselect("Pilih negara:", countries, default=[default])
df_ts=df_long[df_long["country"].isin(selected)]

fig_ts=px.line(df_ts,x="year",y="value",color="country",markers=True,
               labels={"value":indicator,"year":"Tahun"})
fig_ts.update_layout(xaxis=dict(dtick=5))
st.plotly_chart(fig_ts,use_container_width=True)

st.dataframe(df_ts.reset_index(drop=True),use_container_width=True)

# ---------------------------------------------------------
# Statistik Ringkas
# ---------------------------------------------------------
st.subheader("📊 Statistik Ringkas")

agg=(df_long.groupby("country")
     .apply(lambda x:x[x["year"]==x["year"].max()]["value"].mean())
     .reset_index().rename(columns={0:"latest"}).dropna()
     .sort_values("latest",ascending=False)
    )

col1,col2=st.columns(2)
col1.write("### 🔺 Top 10 Highest")
col1.table(agg.head(10))

col2.write("### 🔻 Bottom 10 Lowest")
col2.table(agg.tail(10))

# ---------------------------------------------------------
# Download
# ---------------------------------------------------------
st.subheader("📥 Download CSV (Long Format)")
csv=df_long.to_csv(index=False)
st.download_button("⬇ Download Dataset", csv, file_name=f"education_{indicator}.csv",mime="text/csv")
