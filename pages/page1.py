# pages/page1.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os, glob, csv
from pathlib import Path

# optional pycountry (tidak wajib)
try:
    import pycountry
    _HAS_PYCOUNTRY = True
except Exception:
    _HAS_PYCOUNTRY = False

st.set_page_config(layout="wide", page_title="Pertumbuhan Ekonomi & GDP")
st.title("📈 Pertumbuhan Ekonomi & GDP")
st.markdown("Halaman ini menampilkan indikator ekonomi terkait **pertumbuhan ekonomi** (GDP dan turunan).")

DATA_DIR = Path("data")

# -------------------------
# Robust CSV loader
# -------------------------
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    last_err = None

    # read sample for sniff
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                sample_lines = []
                for _ in range(200):
                    try:
                        sample_lines.append(next(f))
                    except StopIteration:
                        break
                sample = "".join(sample_lines) if sample_lines else ""
        except Exception as e:
            last_err = e
            continue

        # sniff delimiter
        sep_candidates = []
        try:
            if sample:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                if getattr(dialect, "delimiter", None):
                    sep_candidates.append(dialect.delimiter)
        except Exception:
            pass

        for s in [",", ";", "\t", "|"]:
            if s not in sep_candidates:
                sep_candidates.append(s)

        for sep in sep_candidates + [None]:
            try:
                if sep is None:
                    df = pd.read_csv(path, sep=None, engine="python", encoding=enc)
                else:
                    df = pd.read_csv(path, sep=sep, engine="python", encoding=enc)
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except Exception as e2:
                last_err = e2
                continue

    raise last_err or Exception("Gagal membaca CSV.")

# -------------------------
# Helpers
# -------------------------
COMMON_COUNTRY_MAP = {
    "Viet Nam": "Vietnam",
    "United States of America": "United States",
    "Russian Federation": "Russia",
    "Korea, Rep.": "South Korea",
    "Czech Republic": "Czechia",
    "Lao PDR": "Laos",
    "Egypt, Arab Rep.": "Egypt",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
}

def normalize_country_name(name: str):
    if not isinstance(name, str):
        return name
    s = name.strip()
    if s in COMMON_COUNTRY_MAP:
        return COMMON_COUNTRY_MAP[s]
    if "(" in s and ")" in s:
        s0 = s.split("(")[0].strip()
        if s0:
            s = s0
    return s

def try_get_iso3(name: str):
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
# List CSV files
# -------------------------
csv_files = sorted(DATA_DIR.glob("*.csv"))
if not csv_files:
    st.warning(f"Tidak menemukan file CSV di `{DATA_DIR}/`. Masukkan file CSV lalu refresh.")
    st.stop()

# labels tanpa ekstensi
file_labels = [f.stem for f in csv_files]
choice_label = st.selectbox("Pilih file (indikator)", file_labels, index=0)
# dapatkan path file sesuai pilihan (ambil first match)
selected_file = next((f for f in csv_files if f.stem == choice_label), None)
if selected_file is None:
    st.error("File tidak ditemukan (internal).")
    st.stop()

# load
try:
    df_raw = load_csv(str(selected_file))
except Exception as e:
    st.error("Gagal membaca CSV: " + str(e))
    st.stop()

# tampilkan preview (sembunyikan kolom iso jika ada)
preview = df_raw.copy()
for c in list(preview.columns):
    if c.lower() in ("iso3", "iso_3", "iso", "country code", "alpha3"):
        preview = preview.drop(columns=[c])
st.subheader("Preview data (sample)")
st.dataframe(preview.head(8), use_container_width=True)

# -------------------------
# Deteksi kolom country & year
# -------------------------
cols = [str(c) for c in df_raw.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
country_candidates = ["Country Name", "country", "Country", "Negara", "Entity", cols[0]]
country_col = None
for cand in country_candidates:
    if cand in df_raw.columns:
        country_col = cand
        break

if country_col is None:
    st.error("Tidak menemukan kolom nama negara. Pastikan ada kolom nama negara (contoh: 'Country Name').")
    st.stop()

# Jika wide format
if year_cols:
    df_long = df_raw.melt(id_vars=[country_col], value_vars=year_cols, var_name="year", value_name="value")
else:
    # coba long format (country, year, value)
    lower_cols = [c.lower() for c in df_raw.columns]
    if set(["year","value"]).issubset(set(lower_cols)):
        # temukan exact col names
        col_map = {c.lower(): c for c in df_raw.columns}
        df_long = df_raw.rename(columns={col_map["year"]:"year", col_map["value"]:"value"})
        if country_col not in df_long.columns:
            st.error("Format long terdeteksi tapi kolom negara tidak ada.")
            st.stop()
        df_long = df_long[[country_col, "year", "value"]].copy()
    else:
        st.error("Tidak terdeteksi kolom tahun. Gunakan wide-format (kolom tahun seperti 1990,1991...) atau long-format (country, year, value).")
        st.stop()

# bersihkan & konversi
df_long = df_long.dropna(subset=[country_col, "value"]).copy()
df_long[country_col] = df_long[country_col].apply(lambda x: normalize_country_name(str(x)))
def to_num(x):
    try:
        return float(str(x).replace(",","").replace(" ", "").strip())
    except:
        return None
df_long["value"] = df_long["value"].apply(to_num)
df_long = df_long.dropna(subset=["value"]).copy()

# year -> int jika memungkinkan
try:
    df_long["year"] = df_long["year"].astype(int)
except Exception:
    # biarkan string jika memang bukan int
    pass

# -------------------------
# Usahakan dapatkan ISO3 dari sumber kolom ISO di raw (jika ada)
# -------------------------
iso_candidates = [c for c in df_raw.columns if c.lower() in ("iso3","iso_3","iso","country code","alpha3")]
df_long["iso3_auto"] = None
if iso_candidates:
    iso_col = iso_candidates[0]
    try:
        if year_cols:
            iso_long = df_raw[[country_col, iso_col] + year_cols].melt(id_vars=[country_col, iso_col], value_vars=year_cols, var_name="year", value_name="value")
            # normalisasi year & names
            try:
                iso_long["year"] = iso_long["year"].astype(int)
            except:
                pass
            iso_merge = iso_long[[country_col, iso_col, "year"]].drop_duplicates()
            iso_merge = iso_merge.rename(columns={iso_col: "iso3_auto"})
            # merge dengan df_long (hindari duplikat kolom)
            df_long = df_long.merge(iso_merge, on=[country_col, "year"], how="left")
        else:
            # kalau long format, coba merge via country only
            iso_map = df_raw[[country_col, iso_col]].drop_duplicates().set_index(country_col)[iso_col].to_dict()
            df_long["iso3_auto"] = df_long[country_col].map(iso_map)
    except Exception:
        df_long["iso3_auto"] = df_long.get("iso3_auto")

# jika ada beberapa kolom bernama iso3_auto karena merge, hilangkan duplikat (keep first)
if any([c == "iso3_auto" for c in df_long.columns]):
    # pastikan hanya satu kolom bernama iso3_auto
    cols_seen = []
    new_cols = []
    for c in df_long.columns:
        if c not in cols_seen:
            new_cols.append(c)
            cols_seen.append(c)
    df_long = df_long.loc[:, new_cols]

# kalau pycountry terpasang, coba isi iso untuk nama yang belum ada
if _HAS_PYCOUNTRY:
    missing_names = df_long[df_long["iso3_auto"].isna()][country_col].dropna().unique().tolist()
    iso_map = {}
    for nm in missing_names:
        code = try_get_iso3(nm)
        if code:
            iso_map[nm] = code
    if iso_map:
        df_long["iso3_auto"] = df_long["iso3_auto"].fillna(df_long[country_col].map(iso_map))

# -------------------------
# Sidebar (opsi peta)
# -------------------------
st.sidebar.header("Opsi Peta")
color_mode = st.sidebar.radio("Mode warna peta", ("Continuous (nilai)", "Quantile (buckets)"))
if color_mode == "Quantile (buckets)":
    n_buckets = st.sidebar.slider("Jumlah bucket (quantile)", 3, 9, 5)
else:
    n_buckets = None
color_scale = st.sidebar.selectbox("Color scale (continuous)", px.colors.named_colorscales(), index=0)

# -------------------------
# Peta choropleth
# -------------------------
st.subheader("🌎 Peta Dunia (Choropleth)")
years = sorted(pd.unique(df_long["year"]))
# slider aman: jika year bukan numeric, tunjukkan pilihan selectbox
if all(isinstance(y, (int, float)) for y in years):
    sel_year = st.slider("Pilih tahun", int(min(years)), int(max(years)), int(max(years)))
else:
    sel_year = st.selectbox("Pilih tahun (non-numeric)", years, index=len(years)-1)

df_map = df_long[df_long["year"] == sel_year].copy()
if df_map.empty:
    st.warning("Tidak ada data untuk tahun ini.")
else:
    # drop repeated columns (jaga satu kolom iso3_auto)
    if df_map.columns.duplicated().any():
        df_map = df_map.loc[:, ~df_map.columns.duplicated()].copy()

    # buat warna: quantile atau continuous
    discrete = False
    if color_mode == "Quantile (buckets)":
        try:
            df_map["bucket"] = pd.qcut(df_map["value"].rank(method="first"), q=n_buckets, duplicates="drop")
            df_map["bucket_str"] = df_map["bucket"].astype(str)
            color_col = "bucket_str"
            discrete = True
        except Exception as e:
            st.warning("Gagal buat quantile buckets: " + str(e))
            color_col = "value"
            discrete = False
    else:
        color_col = "value"
        discrete = False

    plotted = False
    # Coba plot berdasarkan country names
    try:
        fig = px.choropleth(
            df_map,
            locations=country_col,
            locationmode="country names",
            color=color_col,
            hover_name=country_col,
            color_continuous_scale=color_scale if not discrete else None,
            title=f"{choice_label} — {sel_year}",
            labels={color_col: choice_label}
        )
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
        plotted = True
    except Exception as e:
        st.info("Plot berdasarkan nama negara gagal — akan mencoba fallback (ISO-3) jika tersedia.")

    # fallback ISO3
    if not plotted and "iso3_auto" in df_map.columns and df_map["iso3_auto"].notna().any():
        try:
            fig2 = px.choropleth(
                df_map,
                locations="iso3_auto",
                color=color_col,
                hover_name=country_col,
                title=f"{choice_label} — {sel_year} (ISO-3 fallback)",
                color_continuous_scale=color_scale if not discrete else None
            )
            # paksa locationmode ISO-3 (Plotly biasanya otomatis mendeteksi kode ISO)
            fig2.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig2, use_container_width=True)
            plotted = True
        except Exception as e2:
            st.warning("Fallback ISO3 gagal: " + str(e2))

    if not plotted:
        st.error("Gagal membuat peta otomatis. Periksa ejaan nama negara, tambahkan kolom ISO3 pada CSV, atau kirimkan contoh nama negara yang tidak muncul.")
        st.write("Contoh nama negara (sample):", list(pd.unique(df_map[country_col])[:30]))

# -------------------------
# Time series & ranking
# -------------------------
st.subheader("📈 Time Series per Negara")
countries = sorted(df_long[country_col].dropna().unique().tolist())
sel_country = st.selectbox("Pilih negara", countries, index=0)
df_country = df_long[df_long[country_col] == sel_country].sort_values("year")
if not df_country.empty:
    st.line_chart(df_country.set_index("year")["value"], height=360)
    hide_cols = ["iso3_auto"] if "iso3_auto" in df_country.columns else []
    st.dataframe(df_country.drop(columns=hide_cols).reset_index(drop=True).tail(50), use_container_width=True)
else:
    st.write("Tidak ada data time series untuk negara ini.")

st.subheader(f"📋 Ranking negara — {sel_year}")
if not df_map.empty:
    df_rank = df_map[[country_col, "value"]].sort_values("value", ascending=False).reset_index(drop=True)
    st.dataframe(df_rank.head(200), use_container_width=True)

# -------------------------
# Download long-format CSV
# -------------------------
st.subheader("⬇ Unduh data (long-format)")
csv_out = df_long.to_csv(index=False)
st.download_button("Download CSV (long-format)", csv_out, file_name=f"{choice_label}_long.csv")

st.markdown("---")
st.info("Tip: Jika beberapa negara tidak muncul di peta, periksa ejaan atau tambahkan kolom ISO3. Kalau mau, kirim 10 contoh nama negara yang tidak terpetakan agar saya bantu mapping.")
