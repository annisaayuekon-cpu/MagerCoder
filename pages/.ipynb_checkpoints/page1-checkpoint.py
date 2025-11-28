# pages/page1.py
import streamlit as st
import pandas as pd
import os, glob, csv
import plotly.express as px

# optional dependency: pycountry (digunakan hanya untuk fallback ISO, jika tersedia)
try:
    import pycountry
    _HAS_PYCOUNTRY = True
except Exception:
    _HAS_PYCOUNTRY = False

st.set_page_config(layout="wide", page_title="Pertumbuhan Ekonomi & GDP")
st.title("📈 Pertumbuhan Ekonomi & GDP")
st.markdown(
    "<small>Halaman ini ditujukan untuk menampilkan data indikator ekonomi berupa <b>pertumbuhan ekonomi</b> (GDP dan indikator terkait).</small>",
    unsafe_allow_html=True,
)
st.write("Pilih file indikator dari folder `data/`")

DATA_DIR = "data"

# -------------------------
# helper: list csv files
# -------------------------
def list_csv_files(folder: str):
    return sorted(glob.glob(os.path.join(folder, "*.csv")))

csv_files = list_csv_files(DATA_DIR)
if not csv_files:
    st.warning(f"Tidak menemukan file CSV di `{DATA_DIR}/`. Silakan upload CSV ke folder tersebut lalu refresh.")
    st.stop()

def short_label(path):
    return os.path.splitext(os.path.basename(path))[0]

# build label -> path mapping (hilangkan .csv di label)
label_to_path = {}
counts = {}
for p in csv_files:
    base = short_label(p)
    if base in counts:
        counts[base] += 1
        label = f"{base} ({counts[base]})"
    else:
        counts[base] = 0
        label = base
    label_to_path[label] = p

labels = sorted(label_to_path.keys())
choice_label = st.selectbox("Pilih indikator (tanpa .csv)", labels, index=0)
selected_path = label_to_path[choice_label]
st.caption(f"File: `{os.path.basename(selected_path)}`")

# -------------------------
# robust csv reader
# -------------------------
@st.cache_data
def read_csv_robust(path: str) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    separators = [",", ";", "\t", "|"]
    last_err = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                sample_lines = []
                for _ in range(120):
                    try:
                        sample_lines.append(next(f))
                    except StopIteration:
                        break
                sample = "".join(sample_lines)
        except Exception as e:
            last_err = e
            continue

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
    raise last_err or Exception("Gagal membaca file CSV (encoding/delimiter).")

# -------------------------
# country normalization + iso helper
# -------------------------
COMMON_COUNTRY_MAP = {
    "Viet Nam": "Vietnam",
    "United States of America": "United States",
    "Russian Federation": "Russia",
    "Korea, Rep.": "South Korea",
    "Korea, Dem. People's Rep.": "North Korea",
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
    s = name.strip()
    if s in COMMON_COUNTRY_MAP:
        return COMMON_COUNTRY_MAP[s]
    # remove parenthetical
    if "(" in s and ")" in s:
        s0 = s.split("(")[0].strip()
        if s0:
            s = s0
    return s

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
# load csv
# -------------------------
try:
    df_raw = read_csv_robust(selected_path)
except Exception as e:
    st.error(f"Gagal membaca CSV: {e}")
    st.stop()

st.subheader("Preview data (atas)")
# show raw preview but hide any iso columns if present in raw
raw_preview = df_raw.copy()
iso_like = [c for c in raw_preview.columns if c.lower() in ("iso3","iso_3","iso","country code","alpha3","iso3_auto")]
raw_preview = raw_preview.drop(columns=[c for c in iso_like if c in raw_preview.columns], errors="ignore")
st.dataframe(raw_preview.head(8), use_container_width=True)

# -------------------------
# detect wide / long format
# -------------------------
cols = [str(c) for c in df_raw.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
country_candidates = ["Country Name", "country", "Country", "Negara", "Entity", cols[0]]
country_col = next((c for c in country_candidates if c in df_raw.columns), None)
if country_col is None:
    st.error("Tidak menemukan kolom nama negara. Pastikan CSV memiliki kolom nama negara (contoh: 'Country Name').")
    st.stop()

if year_cols:
    df_long = df_raw.melt(id_vars=[country_col], value_vars=year_cols, var_name="year", value_name="value")
else:
    lower_cols = {c.lower(): c for c in df_raw.columns}
    if "year" in lower_cols and "value" in lower_cols:
        df_long = df_raw.rename(columns={lower_cols["year"]: "year", lower_cols["value"]: "value"})[[country_col, "year", "value"]].copy()
    else:
        st.error("Tidak terdeteksi kolom tahun. Pastikan file wide (kolom tahun) atau long (year & value).")
        st.stop()

# -------------------------
# clean values
# -------------------------
df_long = df_long.dropna(subset=[country_col, "value"]).copy()
df_long[country_col] = df_long[country_col].apply(normalize_country)

def to_number(x):
    try:
        return float(str(x).replace(",", "").replace(" ", "").strip())
    except:
        return None

df_long["value"] = df_long["value"].apply(to_number)
df_long = df_long.dropna(subset=["value"]).copy()
try:
    df_long["year"] = df_long["year"].astype(int)
except Exception:
    pass

# -------------------------
# safe iso mapping (internal only, kept hidden)
# -------------------------
# remove existing iso3_auto if somehow present (avoid duplicates)
if "iso3_auto" in df_long.columns:
    df_long = df_long.drop(columns=["iso3_auto"])

df_long["iso3_auto"] = None
iso_candidates = [c for c in df_raw.columns if c.lower() in ("iso3","iso_3","iso","country code","alpha3")]
if iso_candidates:
    iso_col = iso_candidates[0]
    try:
        if year_cols:
            iso_long = df_raw[[country_col, iso_col] + year_cols].melt(
                id_vars=[country_col, iso_col],
                value_vars=year_cols,
                var_name="year",
                value_name="value"
            )
            try:
                iso_long["year"] = iso_long["year"].astype(int)
            except Exception:
                pass
            iso_merge = iso_long[[country_col, iso_col, "year"]].drop_duplicates()
            df_long = df_long.merge(iso_merge, on=[country_col, "year"], how="left", suffixes=("", "_iso"))
            # normalize to iso3_auto without leaving duplicate columns
            if iso_col in df_long.columns and iso_col != "iso3_auto":
                df_long["iso3_auto"] = df_long[iso_col]
                df_long = df_long.drop(columns=[iso_col], errors="ignore")
            if (iso_col + "_iso") in df_long.columns:
                df_long["iso3_auto"] = df_long["iso3_auto"].fillna(df_long[iso_col + "_iso"])
                df_long = df_long.drop(columns=[iso_col + "_iso"], errors="ignore")
        else:
            if iso_col in df_raw.columns and "year" in df_raw.columns:
                df_long = df_long.merge(df_raw[[country_col, iso_col, "year"]], on=[country_col, "year"], how="left", suffixes=("", "_iso"))
                if iso_col in df_long.columns and iso_col != "iso3_auto":
                    df_long["iso3_auto"] = df_long[iso_col]
                    df_long = df_long.drop(columns=[iso_col], errors="ignore")
                if (iso_col + "_iso") in df_long.columns:
                    df_long["iso3_auto"] = df_long["iso3_auto"].fillna(df_long[iso_col + "_iso"])
                    df_long = df_long.drop(columns=[iso_col + "_iso"], errors="ignore")
    except Exception:
        # ignore iso merge errors (we still have iso3_auto=None)
        pass

# pycountry fallback (hidden): isi hanya nilai kosong, tidak membuat kolom baru
if _HAS_PYCOUNTRY:
    unique_names = pd.Series(df_long[country_col].unique()).dropna().tolist()
    iso_map = {}
    for nm in unique_names:
        code = iso_from_name(nm)
        if code:
            iso_map[nm] = code
    if iso_map:
        df_long["iso3_auto"] = df_long["iso3_auto"].fillna(df_long[country_col].map(iso_map))

# -------------------------
# sidebar options
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

# -------------------------
# CHOROPLETH (nama negara dulu, iso fallback internal)
# -------------------------
st.subheader("🌍 Peta Dunia")
df_map = df_long[df_long["year"] == sel_year].copy()

if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
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
        discrete = False

    plotted = False
    # coba plot berdasarkan nama negara (primary)
    try:
        fig = px.choropleth(
            df_map,
            locations=country_col,
            locationmode="country names",
            color=color_col,
            hover_name=country_col,
            hover_data={"value": True},
            title=f"{choice_label} — {sel_year}",
        )
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
        plotted = True
    except Exception:
        plotted = False

    # fallback: pakai iso3_auto (internal) jika ada nilai
    if not plotted and df_map.get("iso3_auto", pd.Series()).notna().any():
        try:
            fig2 = px.choropleth(
                df_map,
                locations="iso3_auto",
                color=color_col,
                hover_name=country_col,
                hover_data={"value": True},
                title=f"{choice_label} — {sel_year} (ISO fallback)"
            )
            fig2.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig2, use_container_width=True)
            plotted = True
        except Exception:
            plotted = False

    if not plotted:
        st.error("Gagal membuat peta secara otomatis. Periksa ejaan nama negara atau tambahkan kolom ISO3 pada CSV jika diperlukan.")
        st.write("Contoh nama negara (sample):", df_map[country_col].unique()[:50].tolist())

# -------------------------
# Time series per negara (tidak menampilkan iso)
# -------------------------
st.subheader("📈 Time Series per Negara")
countries = sorted(df_long[country_col].dropna().unique().tolist())
sel_country = st.selectbox("Pilih negara", countries, index=0)
df_country = df_long[df_long[country_col] == sel_country].sort_values("year")
if not df_country.empty:
    # tampilkan grafik dan tabel tanpa kolom iso3_auto
    st.line_chart(df_country.set_index("year")["value"], height=360)
    df_country_view = df_country.drop(columns=["iso3_auto"], errors="ignore").reset_index(drop=True)
    st.dataframe(df_country_view.tail(50), use_container_width=True)
else:
    st.info("Tidak ada data time-series untuk negara ini.")

# -------------------------
# Ranking (hide iso)
# -------------------------
st.subheader(f"📋 Ranking negara — {sel_year}")
df_rank = df_map[[country_col, "value"]].sort_values("value", ascending=False).reset_index(drop=True)
st.dataframe(df_rank.head(200), use_container_width=True)

# -------------------------
# download long csv (hide iso column from download if you prefer; currently include iso internally)
# -------------------------
st.subheader("⬇ Unduh data (long-format)")
# jika ingin mengeluarkan iso dari unduhan, drop kolom iso3_auto di sini:
csv_for_download = df_long.drop(columns=["iso3_auto"], errors="ignore")
csv_bytes = csv_for_download.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV (long-format)", csv_bytes, file_name=f"{short_label(selected_path)}_long.csv", mime="text/csv")

st.markdown("---")
st.info("Tip: Jika beberapa negara tidak muncul di peta, periksa ejaan atau tambahkan kolom ISO3 pada CSV. Jika ingin, kirim 10 contoh nama negara yang tidak terpetakan agar saya bantu mapping.")
