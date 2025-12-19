# pages/page8.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🎓 Pendidikan — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator **pendidikan global** seperti *School Enrollment* "
    "dan *Government Expenditure on Education* berdasarkan file CSV lokal di folder `data/`."
)

# -----------------------------------------------------------------------------
# PANDUAN INTERPRETASI + DEFINISI VARIABEL (format disamakan dengan page4)
# -----------------------------------------------------------------------------
with st.expander("📌 Panduan interpretasi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**School Enrollment (%)** menggambarkan tingkat partisipasi sekolah (umumnya berbentuk persen). Nilai yang lebih tinggi biasanya mengindikasikan **akses pendidikan** yang lebih baik, tetapi interpretasi lebih kuat jika dibaca bersama kualitas pembelajaran, tingkat putus sekolah, dan completion rate.

**Government Expenditure on Education (% of GDP)** menggambarkan besarnya belanja pendidikan pemerintah relatif terhadap ukuran ekonomi (persen dari PDB). Nilai yang lebih tinggi dapat menandakan **prioritas fiskal** pada pendidikan, tetapi “lebih tinggi” tidak otomatis lebih baik bila efisiensi belanja rendah atau alokasi tidak tepat (mis. dominan belanja rutin tanpa peningkatan outcome).
"""
    )

DATA_DIR = "data"

FILES = {
    "School Enrollment (%)": "8.1. SCHOOL ENROLLMENT.csv",
    "Government Expenditure on Education (% of GDP)": "8.2. GOVENRMENT EXPENDITURE ON EDUCATION.csv",
}

# -----------------------------
# Loader CSV toleran (samakan pola page4)
# -----------------------------
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
    # Samakan dengan page4: rapikan "..", NA, koma desimal, dsb.
    s = raw.astype(str).str.strip()
    s = s.replace({"..": "", "NA": "", "N/A": "", "nan": "", "None": ""})

    has_comma = s.str.contains(",", na=False)
    has_dot = s.str.contains(r"\.", na=False)

    # 1,234.56 -> 1234.56
    s.loc[has_comma & has_dot] = s.loc[has_comma & has_dot].str.replace(",", "", regex=False)
    # 55,00 -> 55.00
    s.loc[has_comma & ~has_dot] = s.loc[has_comma & ~has_dot].str.replace(",", ".", regex=False)

    # hapus spasi non-breaking
    s = s.str.replace("\u00a0", "", regex=False)
    # hapus persen kalau ada
    s = s.str.replace("%", "", regex=False)

    return pd.to_numeric(s, errors="coerce")


def _orientation(label: str) -> str:
    # pendidikan umumnya "higher better", tapi belanja pendidikan tidak selalu linear
    if label == "School Enrollment (%)":
        return "higher_better"
    if label == "Government Expenditure on Education (% of GDP)":
        return "neutral"
    return "neutral"


def _interpret_note(label: str) -> str:
    if label == "School Enrollment (%)":
        return (
            "Enrollment tinggi lebih kuat maknanya jika dibaca bersama **completion rate**, putus sekolah, "
            "dan indikator kualitas (mis. learning outcomes)."
        )
    if label == "Government Expenditure on Education (% of GDP)":
        return (
            "Belanja pendidikan tinggi perlu dibaca bersama **efektivitas** dan komposisi belanja (rutin vs modal), "
            "serta indikator hasil (literasi, capaian belajar)."
        )
    return "Interpretasi bersifat deskriptif dan perlu dibaca bersama konteks kebijakan pendidikan negara."


# -----------------------------
# Filter entitas agregat (samakan dengan page4)
# -----------------------------
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


# -----------------------------
# Cek file yang tersedia
# -----------------------------
available_indicators = []
for label, fname in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, fname)):
        available_indicators.append(label)

if not available_indicators:
    st.error(
        f"Tidak ada file CSV Page 8 yang ditemukan di folder `{DATA_DIR}/`. "
        "Pastikan file 8.1 dan/atau 8.2 sudah diletakkan di sana."
    )
    st.stop()

# -----------------------------
# Pilih indikator & load data
# -----------------------------
indicator_label = st.selectbox("Pilih indikator pendidikan", available_indicators)
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
    st.error("Tidak ditemukan kolom tahun (mis. 1990, 2000, dst.) di file CSV ini. Cek header kolom.")
    st.stop()

country_col = None
for cand in ["Country Name", "country", "Country", "Negara", "Entity"]:
    if cand in df.columns:
        country_col = cand
        break
if country_col is None:
    country_col = df.columns[0]

# -----------------------------
# Long format
# -----------------------------
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
# ✅ STATISTIK RINGKAS (nilai terbaru per negara) — sama seperti page4
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

# -----------------------------------------------------------------------------
# PETA DUNIA
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# INTERPRETASI PETA (kuartil + catatan)
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

    if indicator_label == "School Enrollment (%)":
        para2 = (
            "Untuk enrollment, nilai yang lebih tinggi biasanya berarti partisipasi sekolah lebih tinggi. "
            "Negara yang berada di atas Q3 dapat dikategorikan memiliki tingkat partisipasi relatif tinggi pada tahun itu. "
            "Namun interpretasi yang kuat perlu membaca apakah kenaikan enrollment juga diikuti perbaikan kualitas dan penurunan putus sekolah."
        )
    else:
        para2 = (
            "Untuk belanja pendidikan (% PDB), nilai yang lebih tinggi menandakan porsi belanja pendidikan relatif lebih besar "
            "dibanding ukuran ekonomi. Ini dapat mencerminkan prioritas kebijakan, tetapi efektivitasnya bergantung pada komposisi belanja "
            "dan tata kelola."
        )

    st.markdown(
        f"""
Ringkasan kuartil memecah negara menjadi empat kelompok pada tahun terpilih. Median dipakai sebagai patokan posisi relatif. Q1 dan Q3 menunjukkan batas kelompok bawah dan atas.

{para2}
"""
    )
    st.caption(_interpret_note(indicator_label))

# -----------------------------------------------------------------------------
# ANALISIS DESKRIPTIF (Top/Bottom 5 tahun terpilih) — sama gaya page4
# -----------------------------------------------------------------------------
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
Berdasarkan nilai **{indicator_label}** pada **{selected_year}**, terlihat perbedaan yang jelas antar negara.

• **Kelompok nilai tertinggi didominasi oleh:** **{top_str}**  
• **Kelompok nilai terendah didominasi oleh:** **{bottom_str}**

Rentang nilai bergerak dari **{_fmt(vmin)}** hingga **{_fmt(vmax)}**, median **{_fmt(q50r)}**, dan rentang antar kuartil (Q3–Q1) sebesar **{_fmt(iqr)}**. Analisis ini bersifat deskriptif.
"""
    )

    if indicator_label == "School Enrollment (%)":
        st.markdown(
            """
Pada enrollment, negara dengan nilai tinggi biasanya menandakan akses/partisipasi sekolah yang lebih luas pada tahun itu. Akan tetapi, gap antar negara dapat berasal dari perbedaan kapasitas layanan pendidikan, kondisi sosial-ekonomi, kebijakan wajib belajar, dan stabilitas institusi. Nilai rendah tidak selalu berarti “tidak ada pendidikan”, tetapi bisa mencerminkan keterbatasan akses, konflik, atau keterbatasan pencatatan statistik.
"""
        )
    else:
        st.markdown(
            """
Pada belanja pendidikan (% PDB), negara dengan nilai tinggi menunjukkan porsi belanja pendidikan lebih besar relatif terhadap PDB. Ini bisa terkait prioritas fiskal, struktur demografi, dan desain sistem pendidikan. Namun belanja tinggi tidak otomatis menghasilkan outcome lebih baik jika tata kelola, efisiensi, atau penargetan program lemah—sehingga perlu dibaca bersama indikator hasil.
"""
        )

    st.markdown(
        """
Indikator pendidikan penting karena memengaruhi **modal manusia** yang pada akhirnya terkait produktivitas dan pertumbuhan. Enrollment (akses) adalah pintu masuk; belanja pendidikan adalah salah satu instrumen kebijakan. Keduanya lebih kuat maknanya jika dibaca bersama kualitas pembelajaran, pemerataan akses, dan efektivitas belanja. [1][2][3]
"""
    )

    st.caption("Catatan: Analisis ini bersifat deskriptif dan tidak dimaksudkan sebagai inferensi kausal.")

    with st.expander("📚 Referensi jurnal (tautan) — dasar interpretasi", expanded=False):
        st.markdown(
            """
[1] Human capital dan pertumbuhan ekonomi (bukti lintas negara).  
[2] Pengaruh belanja pendidikan terhadap outcome dan efisiensi belanja.  
[3] Akses sekolah, partisipasi, dan faktor sosial-ekonomi.
"""
        )
        st.link_button("Economics of Education Review", "https://www.sciencedirect.com/journal/economics-of-education-review")
        st.link_button("Journal of Development Economics", "https://www.sciencedirect.com/journal/journal-of-development-economics")
        st.link_button("World Development", "https://www.sciencedirect.com/journal/world-development")
        st.link_button("Education Economics", "https://www.tandfonline.com/journals/cede20")
        st.link_button("Comparative Education Review", "https://www.journals.uchicago.edu/toc/cer/current")

# -----------------------------------------------------------------------------
# TIME SERIES PER NEGARA + INTERPRETASI TREN (samakan gaya page4)
# -----------------------------------------------------------------------------
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

    if orient == "higher_better":
        if avg_change > 0:
            st.markdown(
                "Tren meningkat mengarah pada perbaikan indikator pada periode pengamatan. "
                "Untuk interpretasi yang kuat, cek apakah peningkatan ini juga diikuti perbaikan kualitas atau pemerataan."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun mengarah pada pelemahan indikator pada periode pengamatan. "
                "Cek faktor akses (biaya, infrastruktur, kebijakan) dan perubahan definisi statistik bila ada."
            )
        else:
            st.markdown("Nilai relatif stabil pada periode pengamatan.")
    else:
        if avg_change > 0:
            st.markdown(
                "Tren meningkat menunjukkan indikator bergerak naik pada periode pengamatan. "
                "Pada belanja pendidikan, perlu dibaca bersama efektivitas belanja dan indikator hasil."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun menunjukkan indikator melemah pada periode pengamatan. "
                "Pada belanja pendidikan, cek siklus fiskal, realokasi anggaran, dan prioritas belanja."
            )
        else:
            st.markdown("Nilai relatif stabil pada periode pengamatan.")

    st.dataframe(df_country.reset_index(drop=True), use_container_width=True)

# -----------------------------------------------------------------------------
# DOWNLOAD (samakan seperti template page4: tidak perlu tampilkan tabel full)
# -----------------------------------------------------------------------------
st.subheader("📘 Data Lengkap (long format)")

csv_download = df_long.to_csv(index=False)
st.download_button(
    "⬇ Download data (CSV)",
    csv_download,
    file_name=f"page8_pendidikan_{indicator_label.replace(' ', '_')}.csv",
    mime="text/csv",
)
