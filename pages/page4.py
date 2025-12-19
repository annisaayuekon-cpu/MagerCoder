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
# PANDUAN INTERPRETASI (ringkas)
# -----------------------------------------------------------------------------
with st.expander("📌 Panduan interpretasi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**Exports of goods and services** merekam nilai ekspor barang dan jasa. Angka tinggi biasanya terkait kapasitas produksi dan akses pasar luar negeri, tetapi perlu dibaca bersama struktur komoditas, basis manufaktur, dan siklus permintaan global.

**Imports of goods and services** merekam nilai impor barang dan jasa. Angka tinggi sering muncul pada ekonomi yang terintegrasi dalam rantai pasok global atau membutuhkan input impor untuk produksi domestik.

**Tariff rates** menggambarkan tingkat pungutan bea masuk atas impor. Angka lebih tinggi umumnya menambah friksi perdagangan dan dapat mengubah struktur insentif produksi, tetapi dampak bersihnya tetap bergantung pada desain tarif dan kebijakan non-tarif.

**Trade openness** dipakai sebagai proksi intensitas perdagangan relatif terhadap ukuran ekonomi. Angka tinggi mengarah pada eksposur yang lebih besar terhadap arus global dan guncangan eksternal, sementara angka rendah lebih mudah dipahami jika disejajarkan dengan ukuran ekonomi dan struktur sektor.
"""
    )

# -----------------------------
# Lokasi folder data & mapping file
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Exports of goods and services": "4.1 Exports of goods and services.csv",
    "Imports of goods and services": "4.2 Imports of goods and services.csv",
    "Tariff rates": "4.3 Tariff rates.csv",
    "Trade openness": "4.4 Trade openness.csv",
}

# -----------------------------
# Helper baca CSV (lebih toleran)
# -----------------------------
@st.cache_data
def load_csv_tolerant(path: str) -> pd.DataFrame:
    """
    Coba baca CSV dengan beberapa delimiter dan lewati baris bermasalah.
    """
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            continue

    df = pd.read_csv(path, engine="python", on_bad_lines="skip")
    return df


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


def _orientation(label: str) -> str:
    """
    Mengatur arah interpretasi: tarif yang lebih tinggi umumnya berarti friksi perdagangan lebih besar.
    """
    if "Tariff" in label:
        return "higher_worse"
    return "neutral"


def _interpret_note(label: str) -> str:
    if label == "Exports of goods and services":
        return (
            "Pada indikator ini, posisi relatif yang lebih tinggi biasanya mencerminkan kapasitas ekspor yang lebih besar pada tahun terpilih. "
            "Pembacaan yang rapi tetap memeriksa apakah dominasi ekspor berbasis komoditas atau manufaktur, karena implikasinya ke volatilitas berbeda."
        )
    if label == "Imports of goods and services":
        return (
            "Pada indikator ini, posisi relatif yang lebih tinggi sering sejalan dengan integrasi rantai pasok dan kebutuhan input impor. "
            "Nilai rendah tidak otomatis berarti substitusi impor berhasil karena bisa terkait hambatan logistik atau keterbatasan kapasitas produksi."
        )
    if label == "Tariff rates":
        return (
            "Pada indikator ini, posisi relatif yang lebih tinggi umumnya berarti friksi tarif lebih kuat. "
            "Efeknya lebih bermakna jika dibaca bersama struktur tarif, barang yang dilindungi, dan kebijakan non-tarif."
        )
    if label == "Trade openness":
        return (
            "Pada indikator ini, posisi relatif yang lebih tinggi berarti eksposur yang lebih besar pada perdagangan global. "
            "Angka ini lebih informatif jika dibaca bersama ukuran ekonomi dan komposisi sektor."
        )
    return "Interpretasi bersifat indikatif dan perlu dibaca bersama konteks statistik dan struktur ekonomi negara."


# -----------------------------------------------------------------------------
# Filter entitas agregat (regional/income group/multilateral) untuk interpretasi
# -----------------------------------------------------------------------------
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
    " income",  # high/low/lower middle/upper middle income
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
    # banyak agregat WDI pakai "&" untuk region
    if " & " in n:
        return True
    n_low = n.lower()
    for token in AGG_SUBSTR:
        if token in n_low:
            return True
    return False


# -----------------------------
# Cek file yang tersedia
# -----------------------------
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

# -----------------------------
# Pilih indikator & load data
# -----------------------------
indicator_label = st.selectbox(
    "Pilih indikator perdagangan internasional", available_indicators
)
file_path = os.path.join(DATA_DIR, FILES[indicator_label])

try:
    df = load_csv_tolerant(file_path)
except Exception as e:
    st.error(f"Gagal membaca file `{os.path.basename(file_path)}`: {e}")
    st.stop()

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

# -----------------------------
# Deteksi kolom tahun & negara
# -----------------------------
cols = [str(c) for c in df.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]

if not year_cols:
    st.error(
        "Tidak ditemukan kolom tahun (misalnya 1990, 2000, dst.) "
        "di file CSV ini. Cek kembali header kolom."
    )
    st.stop()

country_col = None
for cand in ["Country Name", "country", "Country", "Negara", "Entity"]:
    if cand in df.columns:
        country_col = cand
        break

if country_col is None:
    country_col = df.columns[0]

# Ubah ke format long: country, year, value
df_long = df.melt(
    id_vars=[country_col],
    value_vars=year_cols,
    var_name="year",
    value_name="value",
)

df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce").astype("Int64")
df_long = df_long.rename(columns={country_col: "country"})

# Bersihkan format angka
s = df_long["value"].astype(str).str.strip()

# Jika ada koma tapi tidak ada titik, anggap koma sebagai desimal
mask_decimal_comma = s.str.contains(",", na=False) & ~s.str.contains(r"\.", na=False)
s.loc[mask_decimal_comma] = s.loc[mask_decimal_comma].str.replace(",", ".", regex=False)

# Hapus placeholder missing yang umum
s = s.replace({"..": "", "NA": "", "N/A": "", "nan": ""})

df_long["value"] = pd.to_numeric(s, errors="coerce")

df_long = df_long.dropna(subset=["value", "year"])

if df_long.empty:
    st.error("Setelah transformasi, tidak ada data bernilai (semua NaN).")
    st.stop()

df_long["year"] = df_long["year"].astype(int)

# -----------------------------
# Slider tahun untuk peta
# -----------------------------
years = sorted(df_long["year"].unique())
year_min = int(min(years))
year_max = int(max(years))

selected_year = st.slider(
    "Pilih tahun untuk peta dunia", year_min, year_max, year_max
)

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
            "Gagal membuat peta dunia. "
            "Cek apakah nama negara di CSV sesuai standar country names Plotly.\n\n"
            f"Detail error: {e}"
        )

# -----------------------------------------------------------------------------
# INTERPRETASI PETA (pakai df_map_clean untuk kuartil/top-bottom)
# -----------------------------------------------------------------------------
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
            "Untuk tarif, angka yang lebih tinggi dibaca sebagai friksi tarif yang lebih kuat pada tahun tersebut. "
            "Pembacaan yang tegas menilai apakah sebuah negara sudah melampaui Q3 atau masih berada di sekitar median. "
            "Nilai yang sangat rendah lebih masuk akal jika dibaca bersama struktur tarif, non-tariff measures, dan profil industri."
        )
    elif indicator_label == "Trade openness":
        para2 = (
            "Untuk trade openness, angka yang lebih tinggi dibaca sebagai eksposur perdagangan yang lebih besar. "
            "Pembacaan yang tegas menilai apakah sebuah negara berada di atas Q3 atau dekat median, lalu mengaitkannya dengan ukuran ekonomi dan struktur sektor. "
            "Angka rendah lebih mudah dipahami jika ukuran ekonominya besar atau basis permintaan domestik dominan."
        )
    elif indicator_label == "Exports of goods and services":
        para2 = (
            "Untuk ekspor, angka yang lebih tinggi dibaca sebagai kapasitas ekspor yang lebih besar pada tahun tersebut. "
            "Pembacaan yang tegas menilai apakah sebuah negara sudah melampaui Q3 atau masih berada di sekitar median. "
            "Interpretasi perlu mempertimbangkan apakah ekspor didorong komoditas atau manufaktur, karena pola risikonya berbeda."
        )
    else:
        para2 = (
            "Untuk impor, angka yang lebih tinggi dibaca sebagai intensitas impor yang lebih besar pada tahun tersebut. "
            "Pembacaan yang tegas menilai apakah sebuah negara sudah melampaui Q3 atau masih berada di sekitar median. "
            "Angka rendah tidak otomatis berarti substitusi impor berhasil karena bisa terkait hambatan logistik atau daya beli."
        )

    st.markdown(
        f"""
Ringkasan kuartil memecah negara menjadi empat kelompok pada tahun terpilih. Pakai median sebagai patokan untuk menilai posisi relatif. Pakai Q1 dan Q3 untuk menilai extreme point, di mana apabila di bawah Q1 berarti termasuk kelompok terbawah, di atas Q3 berarti masuk kelompok teratas.

{para2}
"""
    )
    st.caption(_interpret_note(indicator_label))

# -----------------------------------------------------------------------------
# ANALISIS DESKRIPTIF (Top & Bottom pakai df_map_clean)
# -----------------------------------------------------------------------------
st.subheader("🧠 Analisis Ekonomi Deskriptif")

if df_map_clean.empty:
    st.write("Analisis deskriptif membutuhkan data pada tahun yang dipilih.")
else:
    df_rank = (
        df_map_clean[["country", "value"]]
        .dropna()
        .sort_values("value", ascending=False)
    )

    top_n = 5
    bottom_n = 5

    top_df = df_rank.head(top_n).copy()
    bottom_pool = df_rank.tail(max(bottom_n * 3, bottom_n)).copy()
    bottom_df = bottom_pool[~bottom_pool["country"].isin(top_df["country"])].tail(bottom_n)
    if bottom_df.empty:
        bottom_df = df_rank.tail(bottom_n)

    top_c = top_df["country"].tolist()
    bottom_c = bottom_df["country"].tolist()

    top_str = ", ".join(top_c) if top_c else "NA"
    bottom_str = ", ".join(bottom_c) if bottom_c else "NA"

    vals_rank = df_rank["value"]
    vmin = float(vals_rank.min())
    vmax = float(vals_rank.max())
    q25r, q50r, q75r = vals_rank.quantile([0.25, 0.50, 0.75]).tolist()
    iqr = float(q75r - q25r)

    st.markdown(
        f"""
Berdasarkan nilai terbaru **{indicator_label}** pada **{selected_year}**, terlihat perbedaan yang jelas antar negara.

• **Kelompok nilai tertinggi didominasi oleh:** **{top_str}**  
• **Kelompok nilai terendah didominasi oleh:** **{bottom_str}**

Rentang nilai pada tahun ini bergerak dari **{_fmt(vmin)}** hingga **{_fmt(vmax)}**, dengan median **{_fmt(q50r)}** dan rentang antar kuartil (Q3–Q1) sebesar **{_fmt(iqr)}**. Analisis ini bersifat deskriptif, tanpa inferensi kausal.
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
Pada trade openness, angka tinggi sering muncul pada ekonomi kecil yang sangat terintegrasi dengan perdagangan global, sementara ekonomi besar bisa tampak lebih “tertutup” secara rasio meski nilai perdagangannya besar. Peta menjadi lebih bermakna jika dibaca sebagai eksposur relatif, lalu dibandingkan dengan struktur sektor dan kerentanan terhadap guncangan eksternal.
"""
        )
    elif indicator_label == "Exports of goods and services":
        st.markdown(
            """
Pada ekspor, posisi tinggi bisa mencerminkan basis produksi dan akses pasar yang kuat, tetapi karakter ekspornya penting. Ekspor berbasis komoditas cenderung lebih sensitif pada siklus harga dunia. Ekspor berbasis manufaktur biasanya lebih terkait kapasitas industri, produktivitas, dan integrasi rantai pasok.
"""
        )
    else:
        st.markdown(
            """
Pada impor, posisi tinggi sering konsisten dengan kebutuhan input impor, pola konsumsi, atau integrasi rantai pasok. Nilai impor yang tinggi tidak selalu “buruk” karena dapat mencerminkan aktivitas produksi yang kuat. Yang lebih informatif adalah pembacaan bersama ekspor, kurs, dan komposisi barang yang diperdagangkan.
"""
        )

    # pastikan blok tambahan ini INDENT-nya sama dengan st.caption / with st.expander
    st.markdown(
        """
Perdagangan menjelaskan cara sebuah ekonomi “terhubung” dengan dunia. Angka ekspor yang tinggi pada peta berarti negara tersebut punya kapasitas menjual barang dan jasa ke luar negeri dalam skala besar pada tahun itu. Itu biasanya datang dari kombinasi ukuran ekonomi, kemampuan produksi, jaringan perusahaan, dan logistik yang mendukung arus keluar masuk barang. Angka ekspor yang rendah lebih sering muncul pada negara dengan basis produksi kecil atau keterisolasian pasar, bukan semata karena kebijakan. Di sini, perbedaan antarnegara paling tepat dibaca sebagai perbedaan kemampuan masuk dan bertahan di pasar global, karena biaya perdagangan dan friksi lintas batas tetap menjadi penentu utama arus dagang. [1][2]

Dampaknya ke ekonomi berjalan lewat tiga jalur yang jelas. Jalur pertama, ekspor menambah permintaan dan mengangkat output sektor tradable, sehingga efeknya cepat terasa pada aktivitas produksi dan kesempatan kerja di sektor yang terhubung ke pasar dunia. Jalur kedua, impor input dan barang modal memberi dorongan produktivitas dan efisiensi, karena banyak industri modern bergantung pada komponen, mesin, dan intermediate goods dari luar untuk menghasilkan output bernilai tambah. Jalur ketiga, perdagangan mendorong spesialisasi dan peningkatan kualitas produk melalui kompetisi dan standar, sehingga negara yang mampu naik kelas dalam rantai nilai biasanya menunjukkan ekspor yang lebih stabil dan lebih beragam. Literatur perdagangan menempatkan mekanisme ini sebagai alasan mengapa integrasi perdagangan sering terkait dengan produktivitas dan perubahan struktur ekonomi. [2][3][4]

Risikonya juga nyata dan perlu dibaca sejak awal. Ketergantungan ekspor pada sedikit komoditas atau sedikit mitra membuat kinerja ekonomi sangat sensitif pada perubahan harga dunia dan guncangan permintaan eksternal. Ketergantungan impor tertentu membuat inflasi dan biaya produksi cepat terdorong saat logistik terganggu atau nilai tukar melemah. Tarif dan friksi perdagangan memengaruhi harga input, insentif produksi, dan alokasi sumber daya antar sektor, sehingga perubahan kecil pada hambatan dagang bisa terasa besar pada industri tertentu. Karena itu, angka perdagangan paling kuat maknanya jika dibaca bersama komposisi barang yang diperdagangkan dan ruang kebijakan untuk meredam guncangan eksternal. [1][4][5]
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

        )
        st.link_button("American Economic Review (AER)", "https://www.aeaweb.org/journals/aer")
        st.link_button("Journal of International Economics", "https://www.sciencedirect.com/journal/journal-of-international-economics")
        st.link_button("Journal of Development Economics", "https://www.sciencedirect.com/journal/journal-of-development-economics")
        st.link_button("World Development", "https://www.sciencedirect.com/journal/world-development")
        st.link_button("Review of Economics and Statistics", "https://direct.mit.edu/rest")

# -----------------------------
# Time series per negara
# -----------------------------
st.subheader("📈 Time Series per Negara")

country_list = sorted(df_long["country"].dropna().unique().tolist())
selected_country = st.selectbox(
    "Pilih negara untuk grafik time series", country_list
)

df_country = (
    df_long[df_long["country"] == selected_country]
    .sort_values("year")
)

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
    fig_ts.update_layout(
        xaxis_title="Tahun",
        yaxis_title=indicator_label,
    )
    st.plotly_chart(fig_ts, use_container_width=True)

    # -----------------------------------------------------------------------------
    # INTERPRETASI TIME SERIES
    # -----------------------------------------------------------------------------
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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tahun terakhir", f"{last_year}")
    col2.metric("Nilai terakhir", _fmt(last_val))
    col3.metric(f"Perubahan ({window_label})", _fmt(delta))
    col4.metric("Rata-rata perubahan per tahun", _fmt(avg_change))

    orient = _orientation(indicator_label)

    if orient == "higher_worse":
        if avg_change > 0:
            st.markdown(
                "Tren meningkat pada periode pengamatan mengarah pada friksi tarif yang lebih kuat. "
                "Validasi biasanya melihat perubahan kebijakan tarif, barang yang dilindungi, dan dinamika impor."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun pada periode pengamatan mengarah pada pelonggaran friksi tarif. "
                "Pembacaan yang lebih kuat melihat respons impor, biaya input, dan perubahan komposisi barang yang diperdagangkan."
            )
        else:
            st.markdown(
                "Nilai relatif stabil pada periode pengamatan. Perubahan kecil tetap bermakna bila level tarif awal tinggi."
            )
    else:
        if avg_change > 0:
            st.markdown(
                "Tren meningkat menunjukkan indikator bergerak naik pada periode pengamatan. "
                "Makna ekonominya lebih tajam jika dibaca bersama kurs, siklus komoditas, dan perubahan struktur perdagangan."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun menunjukkan indikator melemah pada periode pengamatan. "
                "Pembacaan yang rapi memeriksa pergeseran permintaan eksternal, shock harga, dan faktor kebijakan."
            )
        else:
            st.markdown(
                "Nilai relatif stabil pada periode pengamatan. Pola sebelum dan sesudah episode guncangan besar bisa memberi konteks tambahan jika tahun tersedia."
            )

    st.dataframe(df_country.reset_index(drop=True))

# -----------------------------
# Tabel lengkap & download
# -----------------------------
st.subheader("📘 Data Lengkap (long format)")
st.dataframe(df_long.reset_index(drop=True), use_container_width=True)

csv_download = df_long.to_csv(index=False)
st.download_button(
    "⬇ Download data (CSV)",
    csv_download,
    file_name=f"page4_perdagangan_{indicator_label.replace(' ', '_')}.csv",
    mime="text/csv",
)
