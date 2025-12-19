# pages/page1.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Pertumbuhan Ekonomi & GDP", page_icon="📈")

st.title("📈 Pertumbuhan Ekonomi & GDP")
st.write(
    "Halaman ini menampilkan indikator makro utama berbasis data World Bank style CSV yang tersimpan di folder `data/`. "
    "Visualisasi mencakup statistik ringkas nilai terbaru per negara, peta dunia per tahun, interpretasi distribusi, serta time series per negara."
)

with st.expander("📌 Definisi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**GDP (Current US$)** menggambarkan nilai Produk Domestik Bruto dalam dolar Amerika pada harga berjalan. Angka ini menangkap skala ekonomi, tetapi sensitif terhadap inflasi domestik dan perubahan nilai tukar.

**GDP per Capita (US$)** menggambarkan Produk Domestik Bruto dibagi jumlah penduduk. Indikator ini sering dipakai sebagai proksi pendapatan rata rata, lalu dibaca bersama distribusi pendapatan dan struktur pekerjaan.

**GDP Growth (%)** menggambarkan laju pertumbuhan tahunan output riil. Nilai positif berarti ekspansi, nilai negatif berarti kontraksi pada tahun tersebut.

**Gross National Income (GNI)** menggambarkan pendapatan nasional bruto, yaitu GDP yang disesuaikan dengan arus pendapatan faktor dari dan ke luar negeri. Indikator ini membantu membaca pendapatan yang menjadi milik penduduk, terutama ketika remitansi atau pendapatan investasi lintas batas berperan besar.
"""
    )

DATA_DIR = "data"

FILES = {
    "GDP (Current US$)": [
        "1.1. GDP (CURRENT US$).csv",
        "1.1 GDP (current US$).csv",
        "1.1 GDP (CURRENT US$).csv",
        "1.1 GDP current US$.csv",
    ],
    "GDP per Capita (US$)": [
        "1.2. GDP PER CAPITA.csv",
        "1.2 GDP per capita.csv",
        "1.2 GDP per Capita.csv",
        "1.2 GDP PER CAPITA.csv",
    ],
    "GDP Growth (%)": [
        "1.3 GDP growth (%).csv",
        "1.3 GDP Growth (%).csv",
        "1.3. GDP growth (%).csv",
    ],
    "Gross National Income (GNI)": [
        "1.4 Gross National Income (GNI).csv",
        "1.4. Gross National Income (GNI).csv",
        "1.4 GNI.csv",
    ],
}

@st.cache_data
def load_csv_tolerant(path: str) -> pd.DataFrame:
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    return pd.read_csv(path, engine="python", on_bad_lines="skip")


def _pick_existing_file(candidates: list[str]) -> str | None:
    for fname in candidates:
        if os.path.exists(os.path.join(DATA_DIR, fname)):
            return fname

    if not os.path.isdir(DATA_DIR):
        return None
    all_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".csv")]
    for cand in candidates:
        key = cand.lower().replace(".csv", "")
        for f in all_files:
            if key in f.lower():
                return f
    return None


def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def _fmt(v, digits=2):
    v = _to_float(v)
    if v is None:
        return "NA"
    return f"{v:,.{digits}f}"


def _clean_numeric_series(raw: pd.Series) -> pd.Series:
    s = raw.astype(str).str.strip()
    s = s.replace({"..": "", "NA": "", "N/A": "", "nan": "", "None": ""})

    has_comma = s.str.contains(",", na=False)
    has_dot = s.str.contains(r"\.", na=False)

    s.loc[has_comma & has_dot] = s.loc[has_comma & has_dot].str.replace(",", "", regex=False)
    s.loc[has_comma & ~has_dot] = s.loc[has_comma & ~has_dot].str.replace(",", ".", regex=False)

    s = s.str.replace("\u00a0", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


AGG_EXACT = {
    "World",
    "European Union",
    "Euro area",
    "OECD members",
    "IDA & IBRD total",
    "IBRD only",
    "IDA total",
    "IDA blend",
    "IDA only",
    "Heavily indebted poor countries (HIPC)",
    "Least developed countries: UN classification",
    "Fragile and conflict affected situations",
}

AGG_SUBSTR = [
    " income",
    "oecd",
    "ida",
    "ibrd",
    "hipc",
    "euro area",
    "european union",
    "arab world",
    "central europe and the baltics",
    "east asia & pacific",
    "europe & central asia",
    "latin america & caribbean",
    "middle east & north africa",
    "north america",
    "south asia",
    "sub-saharan africa",
    "small states",
    "developing",
    "dividend",
    "total",
    "excluding",
    "members",
]

def is_aggregate_entity(name: str) -> bool:
    if not isinstance(name, str):
        return True
    n = name.strip()
    if n in AGG_EXACT:
        return True
    if " & " in n:
        return True
    low = n.lower()
    for t in AGG_SUBSTR:
        if t in low:
            return True
    return False


# Map label -> WDI code (untuk sumber)
WDI_CODES = {
    "GDP (Current US$)": "NY.GDP.MKTP.CD",
    "GDP per Capita (US$)": "NY.GDP.PCAP.CD",
    "GDP Growth (%)": "NY.GDP.MKTP.KD.ZG",
    "Gross National Income (GNI)": "NY.GNP.MKTP.CD",
}

available_indicators = []
resolved_files = {}
for label, candidates in FILES.items():
    found = _pick_existing_file(candidates)
    if found:
        available_indicators.append(label)
        resolved_files[label] = found

if not available_indicators:
    st.error(f"Tidak ada file CSV Page 1 yang ditemukan di folder `{DATA_DIR}/`.")
    st.stop()

indicator = st.selectbox("Pilih indikator", available_indicators)
file_path = os.path.join(DATA_DIR, resolved_files[indicator])

try:
    df = load_csv_tolerant(file_path)
except Exception as e:
    st.error(f"Gagal membaca file `{os.path.basename(file_path)}`: {e}")
    st.stop()

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

cols = [str(c) for c in df.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
if not year_cols:
    st.error("Tidak ditemukan kolom tahun (format 4 digit) pada file CSV.")
    st.stop()

country_col = None
for cand in ["Country Name", "country", "Country", "Negara", "Entity"]:
    if cand in df.columns:
        country_col = cand
        break
if country_col is None:
    country_col = df.columns[0]

df_long = df.melt(
    id_vars=[country_col],
    value_vars=year_cols,
    var_name="year",
    value_name="value",
)
df_long = df_long.rename(columns={country_col: "country"})
df_long["country"] = df_long["country"].astype(str).str.strip()
df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce").astype("Int64")
df_long["value"] = _clean_numeric_series(df_long["value"])
df_long = df_long.dropna(subset=["year", "value"])
if df_long.empty:
    st.error("Setelah transformasi, tidak ada data bernilai (semua NA).")
    st.stop()
df_long["year"] = df_long["year"].astype(int)

# filter agregat
df_long = df_long[~df_long["country"].apply(is_aggregate_entity)].copy()

# Statistik ringkas
st.subheader("🔎 Statistik Ringkas (nilai terbaru per negara)")

df_latest = (
    df_long.sort_values(["country", "year"])
          .groupby("country", as_index=False)
          .tail(1)
          .rename(columns={"year": "latest_year", "value": "latest_value"})
)

top10 = df_latest.sort_values("latest_value", ascending=False).head(10)
bottom10 = df_latest.sort_values("latest_value", ascending=True).head(10)

cL, cR = st.columns(2)
with cL:
    st.markdown("**Top 10 (terbesar)**")
    st.dataframe(top10[["country", "latest_value"]], use_container_width=True)
with cR:
    st.markdown("**Bottom 10 (terendah)**")
    st.dataframe(bottom10[["country", "latest_value"]], use_container_width=True)

# Peta dunia
years = sorted(df_long["year"].unique().tolist())
year_min = int(min(years))
year_max = int(max(years))

selected_year = st.slider("Pilih tahun untuk peta dunia", year_min, year_max, year_max)
df_map = df_long[df_long["year"] == selected_year].copy()

st.subheader(f"🌍 Peta Dunia ({selected_year})")

if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
    try:
        fig_map = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            hover_name="country",
            color_continuous_scale="Viridis",
            title=f"{indicator} ({selected_year})",
            labels={"value": indicator},
        )
        fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception as e:
        st.error(
            "Gagal membuat peta. Nama negara perlu sesuai standar Plotly.\n\n"
            f"Detail error: {e}"
        )

# Interpretasi peta
st.subheader("🧠 Interpretasi peta (tahun terpilih)")

vals = df_map["value"].dropna()
n = int(vals.shape[0])

if n < 5:
    st.write("Data pada tahun terpilih terlalu sedikit untuk interpretasi distribusi.")
else:
    q25, q50, q75 = vals.quantile([0.25, 0.50, 0.75]).tolist()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Jumlah negara (ada data)", f"{n:,}")
    m2.metric("Kuartil 1 (Q1)", _fmt(q25))
    m3.metric("Median (Q2)", _fmt(q50))
    m4.metric("Kuartil 3 (Q3)", _fmt(q75))

    if indicator == "GDP Growth (%)":
        st.markdown(
            """
Pertumbuhan menggambarkan dinamika siklus pada tahun terpilih. Posisi di atas Q3 berarti masuk kelompok pertumbuhan tinggi pada tahun tersebut, sedangkan posisi di bawah Q1 berarti masuk kelompok pertumbuhan rendah atau kontraksi. Pembacaan yang rapi menautkan angka dengan konteks shock, misalnya guncangan harga komoditas, krisis keuangan, atau gangguan rantai pasok.

Perbandingan lintas negara pada pertumbuhan lebih stabil dibanding level nominal, karena pertumbuhan biasanya dihitung dari seri riil. Tahun dengan deviasi besar dari median sering mencerminkan perubahan tajam pada permintaan global, kebijakan makro, atau faktor struktural seperti ketergantungan sektor tertentu.
"""
        )
    elif indicator == "GDP per Capita (US$)":
        st.markdown(
            """
GDP per kapita dipakai untuk membaca perbedaan tingkat pendapatan rata rata lintas negara pada tahun terpilih. Posisi di atas Q3 berarti masuk kelompok dengan level lebih tinggi, sedangkan posisi di bawah Q1 berarti masuk kelompok dengan level lebih rendah. Interpretasi yang lebih kuat menempatkan angka ini sebagai indikator ringkas produktivitas dan kapasitas menghasilkan pendapatan, lalu diperiksa bersama struktur ekonomi dan kualitas pekerjaan.

Karena satuan US$ dipengaruhi kurs dan inflasi, perubahan posisi lintas tahun bisa terjadi walau ekonomi riil bergerak lebih stabil. Pembacaan tren akan lebih informatif dibanding satu titik tahun, terutama untuk negara yang mengalami volatilitas kurs.
"""
        )
    else:
        st.markdown(
            """
Indikator level dalam US$ paling sering mencerminkan skala ekonomi pada tahun terpilih. Posisi di atas Q3 berarti kelompok skala besar secara nominal, sedangkan posisi di bawah Q1 berarti kelompok skala kecil. Perbedaan ini muncul dari ukuran penduduk, produktivitas, struktur sektor, serta perbedaan harga dan kurs.

Untuk GNI, perbedaan terhadap GDP menjadi relevan ketika arus pendapatan lintas batas besar, misalnya remitansi, pendapatan investasi, atau operasi perusahaan multinasional. Pada kondisi tersebut, level pendapatan yang menjadi milik penduduk dapat berbeda dari nilai output yang diproduksi di dalam negeri.
"""
        )

# Analisis deskriptif (dipanjangkan selevel page lain)
st.subheader("🧠 Analisis Ekonomi Deskriptif")

if df_latest.empty:
    st.write("Analisis deskriptif membutuhkan data nilai terbaru per negara.")
else:
    top5 = df_latest.sort_values("latest_value", ascending=False).head(5).copy()
    bottom5 = df_latest.sort_values("latest_value", ascending=True).head(5).copy()

    top5_names = ", ".join(top5["country"].tolist())
    bottom5_names = ", ".join(bottom5["country"].tolist())

    latest_vals = df_latest["latest_value"].dropna()
    vmin = float(latest_vals.min()) if not latest_vals.empty else None
    vmax = float(latest_vals.max()) if not latest_vals.empty else None
    q25l, q50l, q75l = latest_vals.quantile([0.25, 0.50, 0.75]).tolist() if latest_vals.shape[0] >= 5 else (None, None, None)
    iqr = (q75l - q25l) if (q75l is not None and q25l is not None) else None

    st.markdown(
        f"""
Pada **{indicator}**, kelompok nilai tertinggi pada nilai terbaru cenderung didominasi oleh **{top5_names}**. Kelompok nilai terendah cenderung didominasi oleh **{bottom5_names}**. Pola ini menunjukkan posisi relatif antar negara pada indikator yang sama, sehingga pembacaan paling aman dilakukan sebagai perbandingan distribusi, bukan sebagai penilaian tunggal “baik” atau “buruk”.

Rentang nilai terbaru bergerak dari **{_fmt(vmin)}** hingga **{_fmt(vmax)}**. Median berada pada **{_fmt(q50l)}**, dengan rentang antar kuartil (Q3–Q1) sekitar **{_fmt(iqr)}**. Rentang yang lebar biasanya mencerminkan heterogenitas struktur ekonomi dunia, sehingga perbedaan nilai sering berasal dari kombinasi skala penduduk, produktivitas, kapasitas produksi sektor tradable, serta perbedaan harga dan kurs dalam pengukuran US$.

Interpretasi indikator perlu menyesuaikan tipe metrik. Untuk indikator level nominal seperti GDP current US$ dan GNI, pembacaan yang paling informatif berangkat dari skala ekonomi dan keterkaitan dengan ukuran pasar. Untuk GDP per kapita, fokus bergeser ke pendapatan rata rata yang lebih dekat dengan produktivitas. Untuk GDP growth, fokus berada pada perubahan tahunan dan episode shock, sehingga pembacaan tren sepuluh tahun terakhir biasanya lebih relevan dibanding satu titik tahun. [1][2][3]
"""
    )

    if indicator in ["GDP (Current US$)", "Gross National Income (GNI)"]:
        st.markdown(
            """
Pada indikator level nominal, pergeseran peringkat dapat terjadi karena dua alasan yang berjalan bersamaan. Pertama, perubahan output dan harga domestik. Kedua, perubahan nilai tukar terhadap US$, terutama pada negara dengan volatilitas kurs. Karena itu, tren level nominal sebaiknya selalu dibaca bersama indikator riil atau pertumbuhan agar pembacaan tidak terjebak pada efek kurs saja. [1][2]
"""
        )

    if indicator == "GDP per Capita (US$)":
        st.markdown(
            """
Pada GDP per kapita, pembacaan lintas negara lebih kuat jika ditempatkan sebagai sinyal kasar tingkat pendapatan rata rata, lalu ditopang oleh indikator pelengkap seperti struktur pekerjaan, kualitas pendidikan, atau produktivitas sektor. Kesenjangan yang sangat besar biasanya mencerminkan perbedaan produktivitas, diversifikasi ekonomi, serta kapasitas institusional yang berkembang dalam jangka panjang. [2][3]
"""
        )

    if indicator == "GDP Growth (%)":
        st.markdown(
            """
Pada pertumbuhan, angka tinggi pada satu tahun tidak selalu berarti lintasan jangka panjang lebih baik, karena base effect dan rebound pasca kontraksi dapat menghasilkan pertumbuhan besar sementara. Pembacaan yang lebih stabil mengecek apakah pertumbuhan konsisten di atas median dalam rentang tahun yang cukup panjang, lalu mengaitkannya dengan investasi, produktivitas, dan stabilitas makro. [2][4]
"""
        )

    st.caption("Catatan: Analisis ini bersifat deskriptif dan tidak dimaksudkan sebagai inferensi kausal.")

# Time series per negara
st.subheader("📈 Time Series per Negara")

country_list = sorted(df_long["country"].dropna().unique().tolist())
selected_country = st.selectbox("Pilih negara untuk grafik time series", country_list)

df_country = df_long[df_long["country"] == selected_country].sort_values("year")

if df_country.empty:
    st.write("Tidak ada data time series untuk negara ini.")
else:
    fig_ts = px.line(
        df_country,
        x="year",
        y="value",
        markers=True,
        title=f"{indicator} — {selected_country}",
    )
    fig_ts.update_layout(xaxis_title="Tahun", yaxis_title=indicator)
    st.plotly_chart(fig_ts, use_container_width=True)

    st.subheader("🧾 Interpretasi tren (negara terpilih)")

    last_year = int(df_country["year"].max())
    last_val = float(df_country.loc[df_country["year"] == last_year, "value"].iloc[0])

    start_year_candidate = last_year - 10
    df_window = df_country[df_country["year"] >= start_year_candidate].copy()

    if df_window.shape[0] < 2:
        start_year = int(df_country["year"].min())
        start_val = float(df_country.loc[df_country["year"] == start_year, "value"].iloc[0])
        window_label = f"sejak {start_year}"
    else:
        start_year = int(df_window["year"].min())
        start_val = float(df_country.loc[df_country["year"] == start_year, "value"].iloc[0])
        window_label = f"{start_year}–{last_year}"

    delta = last_val - start_val
    years_span = max(1, last_year - start_year)
    avg_change = delta / years_span

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tahun terakhir", f"{last_year}")
    k2.metric("Nilai terakhir", _fmt(last_val))
    k3.metric(f"Perubahan ({window_label})", _fmt(delta))
    k4.metric("Rata rata perubahan per tahun", _fmt(avg_change))

    if indicator == "GDP Growth (%)":
        if avg_change > 0:
            st.markdown(
                "Rata rata pertumbuhan bergerak naik pada periode pengamatan. Pembacaan yang rapi mengecek apakah kenaikan ini konsisten atau dipengaruhi beberapa tahun ekstrem."
            )
        elif avg_change < 0:
            st.markdown(
                "Rata rata pertumbuhan bergerak turun pada periode pengamatan. Tahun kontraksi dan sumber shock biasanya membantu menjelaskan perubahan."
            )
        else:
            st.markdown(
                "Rata rata pertumbuhan relatif stabil pada periode pengamatan. Variasi tahunan tetap penting untuk dibaca, terutama pada periode shock."
            )
    else:
        if avg_change > 0:
            st.markdown(
                "Level indikator bergerak naik pada periode pengamatan. Untuk indikator US$, perubahan kurs dan inflasi ikut memengaruhi pembacaan nominal."
            )
        elif avg_change < 0:
            st.markdown(
                "Level indikator bergerak turun pada periode pengamatan. Untuk indikator US$, kontraksi output dan depresiasi kurs sering ikut berperan."
            )
        else:
            st.markdown(
                "Level indikator relatif stabil pada periode pengamatan. Pembacaan lanjutan biasanya membandingkan sebelum dan sesudah tahun shock."
            )

# Sources (ditambahkan, format seperti page lain)
with st.expander("📚 Sources dan referensi", expanded=False):
    code = WDI_CODES.get(indicator, "")
    st.markdown(
        f"""
**Data**
[1] World Bank, World Development Indicators (WDI), indikator kode **{code}**.

**Referensi interpretasi**
[2] World Bank. World Development Indicators: Metadata dan catatan metodologi (National Accounts, GDP, GNI, constant vs current prices).  
[3] United Nations, System of National Accounts (SNA): kerangka konseptual pengukuran output dan pendapatan nasional.  
[4] Barro, R. J. (1991). Economic growth in a cross section of countries. *Quarterly Journal of Economics*.  
[5] Mankiw, N. G., Romer, D., & Weil, D. N. (1992). A contribution to the empirics of economic growth. *Quarterly Journal of Economics*.
"""
    )

    st.link_button("World Bank WDI (home)", "https://databank.worldbank.org/source/world-development-indicators")
    if code:
        st.link_button(f"World Bank Indicator {code}", f"https://data.worldbank.org/indicator/{code}")
    st.link_button("UN System of National Accounts (SNA)", "https://unstats.un.org/unsd/nationalaccount/sna.asp")
    st.link_button("Barro (1991) QJE", "https://academic.oup.com/qje/article-abstract/106/2/407/1904219")
    st.link_button("Mankiw Romer Weil (1992) QJE", "https://academic.oup.com/qje/article-abstract/107/2/407/1849776")

# Data lengkap long format -> tombol saja
st.subheader("📘 Data Lengkap (long format)")

csv_download = df_long.to_csv(index=False)
st.download_button(
    "⬇ Download data (CSV)",
    csv_download,
    file_name=f"page1_pertumbuhan_gdp_{indicator.replace(' ', '_').replace('(', '').replace(')', '').replace('%','pct')}.csv",
    mime="text/csv",
)
