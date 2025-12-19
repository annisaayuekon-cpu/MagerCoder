# pages/page4.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🌐 Perdagangan Internasional — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator perdagangan internasional "
    "berdasarkan data referensi lokal (file CSV) yang ada di folder `data/`."
)

# -----------------------------------------------------------------------------
# PANDUAN INTERPRETASI + DEFINISI VARIABEL (format sama seperti template page lain)
# -----------------------------------------------------------------------------
with st.expander("📌 Panduan interpretasi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**Exports of goods and services** mengukur nilai ekspor barang dan jasa suatu negara. Pada statistik World Bank, indikator ini paling sering disajikan sebagai **persen terhadap Produk Domestik Bruto** untuk menggambarkan intensitas ekspor relatif terhadap ukuran ekonomi. Nilai tinggi biasanya selaras dengan kapasitas produksi sektor tradable dan akses pasar global, tetapi maknanya banyak ditentukan oleh struktur ekspor (komoditas vs manufaktur).

**Imports of goods and services** mengukur nilai impor barang dan jasa. Pada banyak dataset World Bank, indikator ini juga disajikan sebagai **persen terhadap Produk Domestik Bruto**. Nilai tinggi sering terkait kebutuhan input produksi, barang modal, dan integrasi rantai pasok. Nilai rendah perlu dibaca bersama kapasitas produksi domestik, biaya perdagangan, dan daya beli.

**Trade openness** umumnya dipakai sebagai ukuran keterbukaan perdagangan, lazimnya dihitung sebagai **(ekspor + impor) dibagi Produk Domestik Bruto**. Nilai tinggi sering muncul pada ekonomi kecil yang sangat terintegrasi pada perdagangan global. Ekonomi besar bisa terlihat lebih rendah secara rasio walaupun nilai perdagangan absolutnya besar.

**Tariff rates** mengukur tingkat tarif impor yang dikenakan, biasanya berupa **rata-rata tarif terapan** (dalam persen). Nilai tinggi mengarah pada friksi tarif yang lebih kuat dan potensi kenaikan biaya input impor. Pembacaan yang lebih kuat memeriksa struktur tarif dan kebijakan non-tarif yang berjalan bersamaan.
"""
    )

DATA_DIR = "data"

FILES = {
    "Exports of goods and services": "4.1 Exports of goods and services.csv",
    "Imports of goods and services": "4.2 Imports of goods and services.csv",
    "Trade openness": "4.3 Trade openness.csv",
    "Tariff rates": "4.4 Tariff rates.csv",
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

    # 1,234.56 -> 1234.56
    s.loc[has_comma & has_dot] = s.loc[has_comma & has_dot].str.replace(",", "", regex=False)
    # 55,00 -> 55.00
    s.loc[has_comma & ~has_dot] = s.loc[has_comma & ~has_dot].str.replace(",", ".", regex=False)

    s = s.str.replace("\u00a0", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _orientation(label: str) -> str:
    if label == "Tariff rates":
        return "higher_worse"
    return "neutral"


def _interpret_note(label: str) -> str:
    if label == "Exports of goods and services":
        return (
            "Angka tinggi pada ekspor lebih kuat maknanya jika dibaca bersama struktur ekspor (komoditas atau manufaktur) "
            "karena profil risikonya berbeda."
        )
    if label == "Imports of goods and services":
        return (
            "Angka impor tinggi sering selaras dengan kebutuhan input produksi dan keterhubungan rantai pasok. "
            "Angka rendah perlu dibaca bersama kapasitas produksi, hambatan biaya perdagangan, dan daya beli."
        )
    if label == "Tariff rates":
        return (
            "Tarif yang tinggi berarti friksi tarif lebih kuat. Angka ini paling informatif jika disejajarkan dengan struktur tarif "
            "dan kebijakan non-tarif."
        )
    if label == "Trade openness":
        return (
            "Trade openness membaca eksposur perdagangan relatif terhadap ukuran ekonomi. Ekonomi besar bisa tampak lebih rendah secara rasio "
            "meski nilai perdagangan absolutnya besar."
        )
    return "Interpretasi bersifat deskriptif dan perlu dibaca bersama konteks statistik dan struktur ekonomi negara."


# Filter entitas agregat untuk interpretasi (regional/income group/multilateral)
AGG_EXACT = {
    "World",
    "European Union",
    "Euro area",
    "OECD members",
    "OECD: High income",
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
    "ida", "ibrd", "hipc",
    "oecd", "euro area", "european union",
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


# Cek file yang tersedia
available_indicators = []
for label, fname in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, fname)):
        available_indicators.append(label)

if not available_indicators:
    st.error(
        f"Tidak ada file CSV Page 4 yang ditemukan di folder `{DATA_DIR}/`. "
        "Pastikan file 4.1–4.4 sudah diletakkan di sana."
    )
    st.stop()


indicator_label = st.selectbox("Pilih indikator perdagangan internasional", available_indicators)
file_path = os.path.join(DATA_DIR, FILES[indicator_label])

try:
    df = load_csv_tolerant(file_path)
except Exception as e:
    st.error(f"Gagal membaca file `{os.path.basename(file_path)}`: {e}")
    st.stop()

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

# Deteksi kolom tahun & negara
cols = [str(c) for c in df.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]

if not year_cols:
    st.error(
        "Tidak ditemukan kolom tahun (misalnya 1990, 2000, dst.) di file CSV ini. "
        "Cek kembali header kolom."
    )
    st.stop()

country_col = None
for cand in ["Country Name", "country", "Country", "Negara", "Entity"]:
    if cand in df.columns:
        country_col = cand
        break
if country_col is None:
    country_col = df.columns[0]

# Long format
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

# -----------------------------------------------------------------------------
# ✅ STATISTIK RINGKAS (nilai terbaru per negara)  [TAMBAHAN, format sama]
# -----------------------------------------------------------------------------
st.subheader("🔎 Statistik Ringkas (nilai terbaru per negara)")

df_latest = (
    df_long.sort_values(["country", "year"])
          .groupby("country", as_index=False)
          .tail(1)
          .rename(columns={"year": "latest_year", "value": "latest_value"})
)

df_latest_clean = df_latest[~df_latest["country"].apply(is_aggregate_entity)].copy()

top10 = df_latest_clean.sort_values("latest_value", ascending=False).head(10)
bottom10 = df_latest_clean.sort_values("latest_value", ascending=True).head(10)

colL, colR = st.columns(2)
with colL:
    st.markdown("**Top 10 (terbesar)**")
    st.dataframe(top10[["country", "latest_value"]], use_container_width=True)
with colR:
    st.markdown("**Bottom 10 (terendah)**")
    st.dataframe(bottom10[["country", "latest_value"]], use_container_width=True)

# Slider tahun untuk peta
years = sorted(df_long["year"].unique().tolist())
year_min = int(min(years))
year_max = int(max(years))

selected_year = st.slider("Pilih tahun untuk peta dunia", year_min, year_max, year_max)

df_map = df_long[df_long["year"] == selected_year].copy()

st.subheader(f"🌍 Peta Dunia — {indicator_label} ({selected_year})")

if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
    try:
        fig = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            hover_name="country",
            color_continuous_scale="Viridis",
            title=f"{indicator_label} — {selected_year}",
            labels={"value": indicator_label},
        )
        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(
            "Gagal membuat peta dunia. Nama negara di CSV perlu sesuai standar country names Plotly.\n\n"
            f"Detail error: {e}"
        )

# Interpretasi peta (pakai df_map_clean untuk kuartil/top-bottom)
st.subheader("🧠 Interpretasi peta (tahun terpilih)")

df_map_clean = df_map[~df_map["country"].apply(is_aggregate_entity)].copy()

vals = df_map_clean["value"].dropna()
n_countries = int(vals.shape[0])

if n_countries < 5:
    st.write("Data pada tahun terpilih terlalu sedikit untuk interpretasi distribusi.")
else:
    q25, q50, q75 = vals.quantile([0.25, 0.50, 0.75]).tolist()

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Jumlah negara (ada data)", f"{n_countries:,}")
    colB.metric("Kuartil 1 (Q1)", _fmt(q25))
    colC.metric("Median (Q2)", _fmt(q50))
    colD.metric("Kuartil 3 (Q3)", _fmt(q75))

    if indicator_label == "Tariff rates":
        para2 = (
            "Untuk tarif, angka yang lebih tinggi berarti friksi tarif lebih kuat pada tahun itu. "
            "Pembacaan yang tegas melihat apakah sebuah negara sudah melampaui Q3 atau masih berada di sekitar median. "
            "Nilai yang sangat rendah masuk akal jika selaras dengan struktur tarif dan kebijakan non-tarif."
        )
    elif indicator_label == "Trade openness":
        para2 = (
            "Untuk trade openness, angka yang lebih tinggi berarti eksposur perdagangan yang lebih besar. "
            "Pembacaan yang tegas melihat apakah sebuah negara berada di atas Q3 atau dekat median, lalu menautkannya dengan ukuran ekonomi dan struktur sektor. "
            "Angka rendah sering muncul pada ekonomi besar dengan basis permintaan domestik kuat."
        )
    elif indicator_label == "Exports of goods and services":
        para2 = (
            "Untuk ekspor, angka yang lebih tinggi berarti kapasitas ekspor yang lebih besar pada tahun itu. "
            "Pembacaan yang tegas melihat apakah sebuah negara sudah melampaui Q3 atau masih berada di sekitar median. "
            "Maknanya berubah ketika ekspor didorong komoditas dibanding manufaktur."
        )
    else:
        para2 = (
            "Untuk impor, angka yang lebih tinggi berarti intensitas impor yang lebih besar pada tahun itu. "
            "Pembacaan yang tegas melihat apakah sebuah negara sudah melampaui Q3 atau masih berada di sekitar median. "
            "Nilai rendah tidak otomatis berarti substitusi impor berhasil."
        )

    st.markdown(
        f"""
Ringkasan kuartil memecah negara menjadi empat kelompok pada tahun terpilih. Median dipakai sebagai patokan untuk posisi relatif. Q1 dan Q3 menunjukkan titik pemisah kelompok bawah dan atas.

{para2}
"""
    )
    st.caption(_interpret_note(indicator_label))

# Analisis deskriptif (Top & Bottom pakai df_map_clean)
st.subheader("🧠 Analisis Ekonomi Deskriptif")

if df_map_clean.empty:
    st.write("Analisis deskriptif membutuhkan data pada tahun yang dipilih.")
else:
    df_rank = (
        df_map_clean[["country", "value"]]
        .dropna()
        .sort_values("value", ascending=False)
        .drop_duplicates(subset=["country"], keep="first")
    )

    top_n = 5
    bottom_n = 5

    top_df = df_rank.head(top_n).copy()
    bottom_df = df_rank[~df_rank["country"].isin(top_df["country"])].tail(bottom_n).copy()
    if bottom_df.empty:
        bottom_df = df_rank.tail(bottom_n).copy()

    top_str = ", ".join(top_df["country"].tolist()) if not top_df.empty else "NA"
    bottom_str = ", ".join(bottom_df["country"].tolist()) if not bottom_df.empty else "NA"

    vmin = float(df_rank["value"].min())
    vmax = float(df_rank["value"].max())
    q25r, q50r, q75r = df_rank["value"].quantile([0.25, 0.50, 0.75]).tolist()
    iqr = float(q75r - q25r)

    st.markdown(
        f"""
Berdasarkan nilai terbaru **{indicator_label}** pada **{selected_year}**, terlihat perbedaan yang jelas antar negara.

• **Kelompok nilai tertinggi didominasi oleh:** **{top_str}**  
• **Kelompok nilai terendah didominasi oleh:** **{bottom_str}**

Rentang nilai bergerak dari **{_fmt(vmin)}** hingga **{_fmt(vmax)}**, median **{_fmt(q50r)}**, dan rentang antar kuartil (Q3–Q1) sebesar **{_fmt(iqr)}**. Analisis ini bersifat deskriptif.
"""
    )

    if indicator_label == "Tariff rates":
        st.markdown(
            """
Pada tarif, negara di kelompok atas (di atas Q3) biasanya menandakan hambatan tarif yang relatif lebih kuat. Perbedaan angka sering terkait desain proteksi sektoral, strategi industrial, dan respons terhadap tekanan eksternal. Nilai rendah lebih konsisten dengan rezim tarif yang lebih terbuka, tetapi pembacaan tetap memeriksa instrumen non-tarif.
"""
        )
    elif indicator_label == "Trade openness":
        st.markdown(
            """
Pada trade openness, angka tinggi sering muncul pada ekonomi kecil yang sangat terintegrasi dengan perdagangan global, sementara ekonomi besar bisa tampak lebih rendah secara rasio meski nilai perdagangan absolutnya besar. Peta lebih bermakna jika dibaca sebagai eksposur relatif, lalu dibandingkan dengan struktur sektor dan kerentanan terhadap guncangan eksternal.
"""
        )
    elif indicator_label == "Exports of goods and services":
        st.markdown(
            """
Pada ekspor, posisi tinggi bisa mencerminkan basis produksi dan akses pasar yang kuat, tetapi karakter ekspornya penting. Ekspor berbasis komoditas lebih sensitif pada siklus harga dunia. Ekspor berbasis manufaktur lebih terkait kapasitas industri, produktivitas, dan integrasi rantai pasok.
"""
        )
    else:
        st.markdown(
            """
Pada impor, posisi tinggi sering konsisten dengan kebutuhan input impor, pola konsumsi, atau integrasi rantai pasok. Nilai impor yang tinggi tidak otomatis buruk karena dapat selaras dengan aktivitas produksi yang kuat. Pembacaan yang lebih informatif melihatnya bersama ekspor, kurs, dan komposisi barang yang diperdagangkan.
"""
        )

    st.markdown(
        """
Perdagangan menjelaskan cara sebuah ekonomi terhubung dengan dunia. Angka yang tinggi pada peta berarti kapasitas transaksi lintas batas terjadi dalam skala besar pada tahun itu, didorong oleh ukuran ekonomi, kemampuan produksi, jejaring perusahaan, dan kelancaran logistik. Angka yang rendah lebih sering terkait basis produksi yang kecil atau keterbatasan konektivitas, bukan semata pilihan kebijakan. Pembacaan yang rapi menempatkan angka ini sebagai ukuran keterlibatan dalam pasar global dan besarnya friksi perdagangan yang dihadapi. [1][2]

Dampak perdagangan ke ekonomi berjalan lewat tiga jalur. Ekspor menambah permintaan dan mengangkat output sektor tradable sehingga efeknya terlihat pada aktivitas produksi dan kesempatan kerja di sektor terkait. Impor input dan barang modal mendorong produktivitas karena banyak industri bergantung pada komponen, mesin, dan intermediate goods dari luar. Perdagangan juga mendorong spesialisasi dan peningkatan mutu lewat kompetisi dan standar, sehingga diversifikasi dan upgrading lebih kuat pada ekonomi yang berhasil memanfaatkan perdagangan untuk naik kelas. [2][3][4]

Risiko ikut terbawa. Ketergantungan pada sedikit komoditas atau sedikit mitra membuat ekonomi sensitif pada harga dunia dan guncangan permintaan eksternal. Ketergantungan impor tertentu membuat biaya produksi dan inflasi mudah terdorong saat logistik terganggu atau nilai tukar melemah. Tarif dan friksi perdagangan mengubah harga input serta insentif produksi, sehingga dampaknya sering terkonsentrasi pada sektor tertentu. Karena itu, angka perdagangan paling kuat maknanya jika dibaca bersama komposisi ekspor impor dan ruang kebijakan untuk meredam guncangan. [1][4][5]
"""
    )

    st.caption("Catatan: Analisis ini bersifat deskriptif dan tidak dimaksudkan sebagai inferensi kausal.")

    with st.expander("📚 Referensi jurnal (tautan) — dasar interpretasi", expanded=False):
        st.markdown(
            """
[1] Gravity model, trade costs, dan friksi perdagangan.  
[2] Keterkaitan perdagangan dan pertumbuhan (evidence lintas negara).  
[3] Trade liberalization dan dinamika pertumbuhan.  
[4] Heterogenitas perusahaan dan respons ekspor.  
[5] Tarif, hambatan perdagangan, dan implikasi kebijakan perdagangan.
"""
        )
        st.link_button("American Economic Review (AER)", "https://www.aeaweb.org/journals/aer")
        st.link_button("Journal of International Economics", "https://www.sciencedirect.com/journal/journal-of-international-economics")
        st.link_button("Journal of Development Economics", "https://www.sciencedirect.com/journal/journal-of-development-economics")
        st.link_button("World Development", "https://www.sciencedirect.com/journal/world-development")
        st.link_button("Review of Economics and Statistics", "https://direct.mit.edu/rest")

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
        title=f"{indicator_label} — {selected_country}",
    )
    fig_ts.update_layout(xaxis_title="Tahun", yaxis_title=indicator_label)
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
        start_val = float(df_window.loc[df_window["year"] == start_year, "value"].iloc[0])
        window_label = f"{start_year}–{last_year}"

    delta = last_val - start_val
    years_span = max(1, last_year - start_year)
    avg_change = delta / years_span

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tahun terakhir", f"{last_year}")
    c2.metric("Nilai terakhir", _fmt(last_val))
    c3.metric(f"Perubahan ({window_label})", _fmt(delta))
    c4.metric("Rata-rata perubahan per tahun", _fmt(avg_change))

    orient = _orientation(indicator_label)

    if orient == "higher_worse":
        if avg_change > 0:
            st.markdown(
                "Tren meningkat mengarah pada friksi tarif yang lebih kuat pada periode pengamatan. "
                "Cek episode perubahan kebijakan tarif dan sektor yang paling terdampak."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun mengarah pada pelonggaran friksi tarif pada periode pengamatan. "
                "Cek respons impor dan perubahan biaya input."
            )
        else:
            st.markdown("Nilai relatif stabil pada periode pengamatan.")
    else:
        if avg_change > 0:
            st.markdown(
                "Tren meningkat menunjukkan indikator bergerak naik pada periode pengamatan. "
                "Cek konteks kurs, harga komoditas, dan perubahan struktur perdagangan."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun menunjukkan indikator melemah pada periode pengamatan. "
                "Cek konteks shock permintaan global, hambatan biaya perdagangan, dan perubahan komposisi ekspor impor."
            )
        else:
            st.markdown("Nilai relatif stabil pada periode pengamatan.")

    st.dataframe(df_country.reset_index(drop=True), use_container_width=True)

# Data lengkap -> tombol download saja (format sama seperti template)
st.subheader("📘 Data Lengkap (long format)")

csv_download = df_long.to_csv(index=False)
st.download_button(
    "⬇ Download data (CSV)",
    csv_download,
    file_name=f"page4_perdagangan_{indicator_label.replace(' ', '_')}.csv",
    mime="text/csv",
)
