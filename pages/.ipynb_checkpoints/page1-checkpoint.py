# pages/page1.py
import streamlit as st
import pandas as pd
import os, glob, csv
import plotly.express as px

# optional ISO lookup (tidak wajib)
try:
    import pycountry
    _HAS_PYCOUNTRY = True
except Exception:
    _HAS_PYCOUNTRY = False

st.set_page_config(layout="wide", page_title="Pertumbuhan Ekonomi & GDP")
st.title("📈 Pertumbuhan Ekonomi & GDP — Visualisasi & Peta Dunia")
st.write("Pilih indikator dari folder `data/`. Loader mencoba beberapa encoding & delimiter jika diperlukan.")

DATA_DIR = "data"

# -------------------------
# util: cari semua csv di folder data
# -------------------------
def list_csv_files(folder: str):
    pattern = os.path.join(folder, "*.csv")
    return sorted(glob.glob(pattern))

csv_files = list_csv_files(DATA_DIR)
if not csv_files:
    st.warning(f"Tidak menemukan file CSV di `{DATA_DIR}/`. Silakan upload file CSV lalu refresh.")
    st.stop()

# -------------------------
# buat label tanpa ekstensi (unik) -> mapping ke path
# -------------------------
def short_label(path):
    return os.path.splitext(os.path.basename(path))[0]

label_to_path = {}
counts = {}
for p in csv_files:
    label = short_label(p)
    if label in counts:
        counts[label] += 1
        label_display = f"{label} ({counts[label]})"
    else:
        counts[label] = 0
        label_display = label
    label_to_path[label_display] = p

labels = sorted(label_to_path.keys())

choice_label = st.selectbox("Pilih indikator (tanpa .csv)", labels, index=0)
selected_path = label_to_path[choice_label]
st.caption(f"File: `{os.path.basename(selected_path)}` — path: `{selected_path}`")

# -------------------------
# Robust CSV loader (try different encodings & delimiters)
# -------------------------
@st.cache_data
def read_csv_robust(path: str) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    separators = [",", ";", "\t", "|"]
    last_err = None

    # try reading small sample to let csv.Sniffer guess delimiter
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                sample = "".join([next(f) for _ in range(50)]) if f else ""
        except Exception as e:
            last_err = e
            continue

        # try sniff delimiter
        sniffed = []
        try:
            if sample:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                delim = getattr(dialect, "delimiter", None)
                if delim:
                    sniffed.append(delim)
        except Exception:
            pass

        # try sniffed first, then common list
        tries = sniffed + [s for s in separators if s not in sniffed] + [None]
        for sep in tries:
            try:
                if sep is None:
                    df = pd.read_csv(path, sep=None, engine="python", encoding=enc)
                else:
                    df = pd.read_csv(path, sep=sep, engine="python", encoding=enc)
                # normalize column names
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except Exception as e2:
                last_err = e2
                continue

    raise last_err or Exception("Gagal membaca CSV — tidak dapat menentukan encoding/delimiter.")

# -------------------------
# helper: country name normalization + try iso
# -------------------------
COMMON_COUNTRY_MAP = {
    "Viet Nam": "Vietnam",
    "United States of America": "United States",
    "Russian Federation": "Russia",
    "Korea, Rep.": "South Korea",
    "Czech Republic": "Czechia",
    "Lao PDR": "Laos",
    "Syrian Arab Republic": "Syria",
    "Iran (Islamic Republic of)": "Iran",
    "Egypt, Arab Rep.": "Egypt",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
}

def normalize_country(name):
    if not isinstance(name, str):
        return name
    n = name.strip()
    if n in COMMON_COUNTRY_MAP:
        return COMMON_COUNTRY_MAP[n]
    # remove trailing parenthesis notes: "X (something)" -> "X"
    if "(" in n and ")" in n:
        n0 = n.split("(")[0].strip()
        if n0:
            n = n0
    return n

def iso_from_name(name):
    if not _HAS_PYCOUNTRY or not isinstance(name, str):
        return None
    try:
        res = pycountry.countries.search_fuzzy(name)
        if res:
            return res[0].alpha_3
    except Exception:
        try:
            c = pycountry.countries.get(name=name)
            if c:
                return c.alpha_3
        except Exception:
            return None
    return None

# -------------------------
# load selected CSV
# -------------------------
try:
    df_raw = read_csv_robust(selected_path)
except Exception as e:
    st.error(f"Gagal membaca CSV: {e}")
    st.stop()

st.subheader("Preview data (atas)")
st.dataframe(df_raw.head(8), use_container_width=True)

# -------------------------
# detect country & year/value layout
# -------------------------
cols = [str(c) for c in df_raw.columns]
# year-like columns are four-digit numeric column names
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]

# possible country column names heuristics
country_candidates = ["Country Name", "country", "Country", "Negara", "Entity", cols[0]]
country_col = next((c for c in country_candidates if c in df_raw.columns), None)

if country_col is None:
    st.error("Tidak menemukan kolom nama negara. Pastikan file memiliki kolom nama negara (mis: 'Country Name').")
    st.stop()

if year_cols:
    # wide format: melt years -> long
    df_long = df_raw.melt(id_vars=[country_col], value_vars=year_cols, var_name="year", value_name="value")
else:
    # check long format columns (country, year, value)
    lower_cols = [c.lower() for c in df_raw.columns]
    if set(["year", "value"]).issubset(set(lower_cols)):
        # find original column names for year & value
        col_map = {c.lower(): c for c in df_raw.columns}
        df_long = df_raw.rename(columns={col_map["year"]: "year", col_map["value"]: "value"})
        if country_col not in df_long.columns:
            st.error("Format long terdeteksi tetapi tidak menemukan kolom nama negara yang cocok.")
            st.stop()
        df_long = df_long[[country_col, "year", "value"]].copy()
    else:
        st.error("Tidak terdeteksi kolom tahun. Pastikan file wide (kolom tahun) atau long (year & value).")
        st.stop()

# clean data
df_long = df_long.dropna(subset=[country_col, "value"]).copy()
df_long[country_col] = df_long[country_col].apply(normalize_country)

def to_number(x):
    try:
        return float(str(x).replace(",", "").replace(" ", "").strip())
    except:
        return None

df_long["value"] = df_long["value"].apply(to_number)
df_long = df_long.dropna(subset=["value"]).copy()

# convert year to int if possible
try:
    df_long["year"] = df_long["year"].astype(int)
except Exception:
    pass

# attempt to create iso3 if pycountry present or if CSV had iso columns
iso_candidates = [c for c in df_raw.columns if c.lower() in ("iso3", "iso_3", "iso", "country code", "alpha3")]
df_long["iso3_auto"] = None
if iso_candidates:
    iso_col = iso_candidates[0]
    try:
        if year_cols:
            iso_long = df_raw[[country_col, iso_col] + year_cols].melt(id_vars=[country_col, iso_col], value_vars=year_cols, var_name="year", value_name="value")
            iso_long["year"] = iso_long["year"].astype(int)
            iso_merge = iso_long[[country_col, iso_col, "year"]].drop_duplicates()
            df_long = df_long.merge(iso_merge, on=[country_col, "year"], how="left")
            df_long.rename(columns={iso_col: "iso3_auto"}, inplace=True)
        else:
            # try simpler mapping if long format included iso
            if iso_col in df_raw.columns and "year" in df_raw.columns:
                df_long = df_long.merge(df_raw[[country_col, iso_col, "year"]], on=[country_col, "year"], how="left")
                df_long.rename(columns={iso_col: "iso3_auto"}, inplace=True)
    except Exception:
        pass

if _HAS_PYCOUNTRY:
    unique_countries = pd.Series(df_long[country_col].unique()).dropna().tolist()
    iso_map = {}
    for name in unique_countries:
        code = iso_from_name(name)
        if code:
            iso_map[name] = code
    if iso_map:
        df_long["iso3_auto"] = df_long["iso3_auto"].fillna(df_long[country_col].map(iso_map))

# -------------------------
# Sidebar: opsi peta & filter
# -------------------------
st.sidebar.header("Opsi Peta & Filter")
color_mode = st.sidebar.radio("Mode warna", ("Continuous (nilai)", "Quantile (buckets)"))
if color_mode == "Quantile (buckets)":
    n_buckets = st.sidebar.slider("Jumlah bucket (quantile)", 3, 7, 5)
else:
    n_buckets = None

min_year = int(df_long["year"].min())
max_year = int(df_long["year"].max())
sel_year = st.sidebar.slider("Tahun peta", min_year, max_year, max_year)

selected_countries = st.sidebar.multiselect("Highlight negara (opsional)", sorted(df_long[country_col].unique().tolist()), max_selections=5)

# -------------------------
# Map (choropleth)
# -------------------------
st.subheader("🌍 Peta Choropleth")
df_map = df_long[df_long["year"] == sel_year].copy()
if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
    # create buckets if requested
    discrete = False
    if color_mode.startswith("Quantile"):
        try:
            df_map["bucket"] = pd.qcut(df_map["value"], q=n_buckets, duplicates="drop")
            color_col = "bucket"
            discrete = True
        except Exception:
            color_col = "value"
            discrete = False
    else:
        color_col = "value"

    plotted = False
    # 1) try country names mapping
    try:
        fig = px.choropleth(
            df_map,
            locations=country_col,
            locationmode="country names",
            color=color_col,
            hover_name=country_col,
            hover_data={"value": True},
            title=f"{choice_label} — {sel_year}",
            color_continuous_scale=px.colors.sequential.Plasma if not discrete else None
        )
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
        plotted = True
    except Exception as e:
        st.warning("Plot berdasarkan nama negara gagal: " + str(e))

    # 2) fallback: iso3_auto
    if not plotted and df_map.get("iso3_auto").notna().any():
        try:
            fig2 = px.choropleth(
                df_map,
                locations="iso3_auto",
                color=color_col,
                hover_name=country_col,
                hover_data={"value": True},
                title=f"{choice_label} — {sel_year} (ISO3)"
            )
            fig2.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig2, use_container_width=True)
            plotted = True
        except Exception as e2:
            st.warning("Plot fallback ISO3 gagal: " + str(e2))

    if not plotted:
        st.error("Gagal membuat peta otomatis. Periksa ejaan negara atau tambahkan kolom ISO3 pada CSV.")
        st.write("Contoh nama negara yang tersedia:", df_map[country_col].unique()[:50].tolist())

# -------------------------
# Time series & ranking
# -------------------------
st.subheader("📈 Time series & ranking")
countries = sorted(df_long[country_col].dropna().unique().tolist())
sel_country = st.selectbox("Pilih negara untuk time-series", countries, index=0)
df_country = df_long[df_long[country_col] == sel_country].sort_values("year")
if not df_country.empty:
    st.line_chart(df_country.set_index("year")["value"], height=320)
    st.dataframe(df_country.reset_index(drop=True).tail(50), use_container_width=True)
else:
    st.info("Tidak ada data time-series untuk negara ini.")

st.subheader(f"🏆 Ranking negara — {sel_year}")
df_rank = df_map[[country_col, "value"]].sort_values("value", ascending=False).reset_index(drop=True)
st.dataframe(df_rank.head(200), use_container_width=True)

# -------------------------
# Download long csv
# -------------------------
st.subheader("⬇ Unduh data (long-format)")
csv_bytes = df_long.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV (long-format)", csv_bytes, file_name=f"{short_label(selected_path)}_long.csv", mime="text/csv")

st.markdown("---")
st.info("Tip: Jika beberapa negara tidak muncul di peta, kirim contoh nama negara yang tidak terpeta supaya saya bantu mapping ISO3.")
