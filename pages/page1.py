# pages/page1.py
import streamlit as st
import pandas as pd
import os, glob, csv
import plotly.express as px

# optional ISO lookup
try:
    import pycountry
    _HAS_PYCOUNTRY = True
except Exception:
    _HAS_PYCOUNTRY = False

st.set_page_config(layout="wide", page_title="Pertumbuhan Ekonomi & GDP")
st.title("📈 Pertumbuhan Ekonomi & GDP — Visualisasi & Peta Dunia")
st.write("Baca file CSV di folder `data/`. Loader sudah dibuat robust: mencoba beberapa encoding & delimiter.")

DATA_DIR = "data"

# -------------------------
# Robust CSV loader
# -------------------------
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    """
    Try multiple encodings and separators. Use csv.Sniffer to guess delimiter if possible.
    Returns DataFrame or raises the last exception.
    """
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    last_err = None

    # read a sample for sniffer
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                # read up to 200 lines or until EOF for a good sample
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

        # try sniffing delimiter
        sep_candidates = []
        try:
            if sample:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                if getattr(dialect, "delimiter", None):
                    sep_candidates.append(dialect.delimiter)
        except Exception:
            pass

        # common separators priority
        for s in [",", ";", "\t", "|"]:
            if s not in sep_candidates:
                sep_candidates.append(s)

        # try each sep candidate + engine python with sep=None fallback
        for sep in sep_candidates + [None]:
            try:
                if sep is None:
                    # let pandas try to guess (engine python required)
                    df = pd.read_csv(path, sep=None, engine="python", encoding=enc)
                else:
                    df = pd.read_csv(path, sep=sep, engine="python", encoding=enc)
                # normalize columns
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except Exception as e2:
                last_err = e2
                continue

    # if we reach here, raise last error
    raise last_err or Exception("Gagal membaca CSV.")

# -------------------------
# Helper: normalize country names & try ISO3
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
    # add more rules if needed
}

def normalize_country_name(name):
    if not isinstance(name, str):
        return name
    s = name.strip()
    if s in COMMON_COUNTRY_MAP:
        return COMMON_COUNTRY_MAP[s]
    # remove parenthetical remarks
    if "(" in s and ")" in s:
        s0 = s.split("(")[0].strip()
        if s0:
            s = s0
    return s

def try_get_iso3(name):
    if not _HAS_PYCOUNTRY or not isinstance(name, str):
        return None
    try:
        # fuzzy search
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
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
if not csv_files:
    st.warning(f"Tidak menemukan file CSV pada folder `{DATA_DIR}/`. Taruh file CSV di folder tersebut lalu refresh.")
    st.stop()

file_labels = [os.path.basename(p) for p in csv_files]
choice_label = st.selectbox("Pilih file (indikator)", file_labels, index=0)
file_path = os.path.join(DATA_DIR, choice_label)

# load file
try:
    df_raw = load_csv(file_path)
except Exception as e:
    st.error("Gagal membaca CSV: " + str(e))
    st.stop()

st.subheader("Preview data (baris atas)")
st.dataframe(df_raw.head(8), use_container_width=True)

# -------------------------
# Detect country & year columns
# -------------------------
cols = [str(c) for c in df_raw.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
# heuristik nama kolom negara
country_candidates = ["Country Name", "country", "Country", "Negara", "Entity", cols[0]]
country_col = None
for cand in country_candidates:
    if cand in df_raw.columns:
        country_col = cand
        break

if country_col is None:
    st.error("Tidak menemukan kolom nama negara. Pastikan CSV memiliki kolom nama negara (contoh: 'Country Name').")
    st.stop()
if not year_cols:
    # also accept long-format with columns country, year, value
    if set(["year","value"]).issubset(set(df_raw.columns)):
        # assume long format
        df_long = df_raw.rename(columns={country_col:country_col})[[country_col,"year","value"]].copy()
    else:
        st.error("Tidak terdeteksi kolom tahun (contoh: '1990','1991',...). Pastikan file wide-format atau long-format (country, year, value).")
        st.stop()
else:
    # convert wide -> long
    df_long = df_raw.melt(id_vars=[country_col], value_vars=year_cols, var_name="year", value_name="value")

# clean & convert types
df_long = df_long.dropna(subset=[country_col, "value"]).copy()
df_long[country_col] = df_long[country_col].apply(normalize_country_name)

def to_num(x):
    try:
        return float(str(x).replace(",","").replace(" ", "").strip())
    except:
        return None

df_long["value"] = df_long["value"].apply(to_num)
df_long = df_long.dropna(subset=["value"]).copy()
# year to int if possible
try:
    df_long["year"] = df_long["year"].astype(int)
except Exception:
    # keep as is if not convertible
    pass

# detect existing ISO column in original raw
iso_candidates = [c for c in df_raw.columns if c.lower() in ("iso3","iso_3","iso","country code","alpha3")]
iso_col = iso_candidates[0] if iso_candidates else None

# create iso mapping column if possible
if iso_col and iso_col in df_raw.columns:
    # try to melt iso if iso exists alongside year columns
    try:
        if iso_col in df_raw.columns and year_cols:
            iso_long = df_raw[[country_col, iso_col] + year_cols].melt(id_vars=[country_col, iso_col], value_vars=year_cols, var_name="year", value_name="value")
            iso_long["year"] = iso_long["year"].astype(int)
            iso_merge = iso_long[[country_col, iso_col, "year"]].drop_duplicates()
            df_long = df_long.merge(iso_merge, on=[country_col, "year"], how="left")
            df_long.rename(columns={iso_col: "iso3_auto"}, inplace=True)
        else:
            df_long["iso3_auto"] = None
    except Exception:
        df_long["iso3_auto"] = None
else:
    df_long["iso3_auto"] = None

# if pycountry available, try auto ISO for names missing
if _HAS_PYCOUNTRY:
    unique_names = pd.Series(df_long[country_col].unique()).dropna().tolist()
    iso_map = {}
    for nm in unique_names:
        code = try_get_iso3(nm)
        if code:
            iso_map[nm] = code
    if iso_map:
        df_long["iso3_auto"] = df_long["iso3_auto"].fillna(df_long[country_col].map(iso_map))

# -------------------------
# Sidebar options for map
# -------------------------
st.sidebar.header("Opsi Peta")
color_mode = st.sidebar.radio("Mode warna peta", ("Continuous (nilai)", "Quantile (buckets)"))
if color_mode == "Quantile (buckets)":
    n_buckets = st.sidebar.slider("Jumlah bucket (quantile)", 3, 9, 5)
else:
    n_buckets = None
color_scale = st.sidebar.selectbox("Pilih color scale (continuous)", px.colors.named_colorscales(), index=0)

# -------------------------
# Map (choropleth)
# -------------------------
st.subheader("🌎 Peta Dunia (Choropleth)")
years = sorted(df_long["year"].unique().tolist())
sel_year = st.slider("Pilih tahun", min(years), max(years), max(years))

df_map = df_long[df_long["year"] == sel_year].copy()
if df_map.empty:
    st.warning("Tidak ada data untuk tahun ini.")
else:
    if color_mode == "Quantile (buckets)":
        try:
            df_map["bucket"] = pd.qcut(df_map["value"], q=n_buckets, duplicates="drop")
            df_map["bucket_str"] = df_map["bucket"].astype(str)
            color_col = "bucket_str"
            discrete = True
        except Exception as e:
            st.warning("Gagal membuat quantile buckets: " + str(e))
            color_col = "value"
            discrete = False
    else:
        color_col = "value"
        discrete = False

    plotted = False
    # try by country names first
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
        st.warning("Plot dengan 'country names' gagal: " + str(e))

    # fallback to iso column if available
    if not plotted and df_map.get("iso3_auto").notna().any():
        try:
            fig2 = px.choropleth(
                df_map,
                locations="iso3_auto",
                color=color_col,
                hover_name=country_col,
                title=f"{choice_label} — {sel_year} (ISO3 fallback)",
                color_continuous_scale=color_scale if not discrete else None
            )
            fig2.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig2, use_container_width=True)
            plotted = True
        except Exception as e2:
            st.warning("Fallback ISO3 gagal: " + str(e2))

    # try pycountry auto-fill if still not plotted
    if not plotted and _HAS_PYCOUNTRY:
        try:
            missing = df_map[df_map["iso3_auto"].isna()][country_col].unique().tolist()
            iso_found = {}
            for cname in missing:
                code = try_get_iso3(cname)
                if code:
                    iso_found[cname] = code
            if iso_found:
                df_map["iso3_try"] = df_map[country_col].map(iso_found)
                df_map["iso3_final"] = df_map["iso3_auto"].fillna(df_map.get("iso3_try"))
                fig3 = px.choropleth(
                    df_map,
                    locations="iso3_final",
                    color=color_col,
                    hover_name=country_col,
                    title=f"{choice_label} — {sel_year} (ISO3 try fallback)",
                    color_continuous_scale=color_scale if not discrete else None
                )
                fig3.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig3, use_container_width=True)
                plotted = True
        except Exception as e3:
            st.warning("Auto ISO3 with pycountry failed: " + str(e3))

    if not plotted:
        st.error("Gagal membuat peta otomatis. Periksa ejaan nama negara, tambahkan kolom ISO3 pada CSV, atau kirimkan contoh nama negara yang tidak muncul.")
        st.write("Contoh nama negara (sample):", df_map[country_col].unique()[:30].tolist())

# -------------------------
# Time series + ranking
# -------------------------
st.subheader("📈 Time Series per Negara")
countries = sorted(df_long[country_col].dropna().unique().tolist())
sel_country = st.selectbox("Pilih negara", countries, index=0)
df_country = df_long[df_long[country_col] == sel_country].sort_values("year")
if not df_country.empty:
    st.line_chart(df_country.set_index("year")["value"], height=360)
    st.dataframe(df_country.reset_index(drop=True).tail(50), use_container_width=True)
else:
    st.write("Tidak ada data time series untuk negara ini.")

st.subheader(f"📋 Ranking negara — {sel_year}")
df_rank = df_map[[country_col, "value"]].sort_values("value", ascending=False).reset_index(drop=True)
st.dataframe(df_rank.head(200), use_container_width=True)

# -------------------------
# Download long-format CSV
# -------------------------
st.subheader("⬇ Unduh data (long-format)")
csv_out = df_long.to_csv(index=False)
st.download_button("Download CSV (long-format)", csv_out, file_name=f"{os.path.splitext(choice_label)[0]}_long.csv")

st.markdown("---")
st.info("Tip: Jika beberapa negara tidak muncul di peta, periksa ejaan atau tambahkan kolom ISO3. Jika mau, kirimkan 10 contoh nama negara yang tidak terpetakan agar saya bantu mapping.")
