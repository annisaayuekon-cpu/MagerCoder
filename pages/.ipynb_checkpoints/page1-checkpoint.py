# pages/page1.py
import streamlit as st
import pandas as pd
import os, glob
import plotly.express as px

# Optional: try pycountry for ISO3 lookup (best-effort)
try:
    import pycountry
    _HAS_PYCOUNTRY = True
except Exception:
    _HAS_PYCOUNTRY = False

st.set_page_config(layout="wide", page_title="Pertumbuhan Ekonomi & GDP")
st.title("📈 Pertumbuhan Ekonomi & GDP — Visualisasi & Peta Dunia")
st.write("Baca file CSV di folder `data/`. Tersedia auto-mapping nama negara & opsi quantile-bucket untuk peta.")

DATA_DIR = "data"

# --- helper: common name mapping (extendable)
COMMON_COUNTRY_MAP = {
    "Viet Nam": "Vietnam",
    "United States of America": "United States",
    "United States of America (the)": "United States",
    "United States": "United States",
    "Korea, Rep.": "South Korea",
    "Korea, Dem. People's Rep.": "North Korea",
    "Russian Federation": "Russia",
    "Syrian Arab Republic": "Syria",
    "Iran (Islamic Republic of)": "Iran",
    "Egypt, Arab Rep.": "Egypt",
    "Czech Republic": "Czechia",
    "Slovak Republic": "Slovakia",
    "Lao PDR": "Laos",
    "Venezuela, RB": "Venezuela",
    "Bolivia (Plurinational State of)": "Bolivia",
    "Tanzania, United Republic of": "Tanzania",
    "United Kingdom": "United Kingdom",
    "Bahamas, The": "Bahamas",
    "Gambia, The": "Gambia",
    # add more rules here as needed
}

def normalize_country_name(name: str) -> str:
    if not isinstance(name, str):
        return name
    n = name.strip()
    # quick replacements
    if n in COMMON_COUNTRY_MAP:
        return COMMON_COUNTRY_MAP[n]
    # small normalizations
    n2 = n.replace("�", "").replace("\u00A0", " ").strip()
    # remove extra parenthetical notes
    if "(" in n2 and ")" in n2:
        n3 = n2.split("(")[0].strip()
        if n3:
            n2 = n3
    return n2

def try_get_iso3_from_name(name: str):
    """Return ISO3 code if pycountry available and match found; else None"""
    if not _HAS_PYCOUNTRY:
        return None
    try:
        # try direct lookup
        c = pycountry.countries.get(name=name)
        if c:
            return c.alpha_3
        # try by common name
        c = pycountry.countries.search_fuzzy(name)
        if c:
            return c[0].alpha_3
    except Exception:
        return None
    return None

# --- load CSVs
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
if not csv_files:
    st.warning(f"Tidak menemukan file CSV di `{DATA_DIR}/`. Taruh CSV hasil convert ke folder tersebut.")
    st.stop()

file_labels = [os.path.basename(p) for p in csv_files]
choice_label = st.selectbox("Pilih file (indikator)", file_labels, index=0)
file_path = os.path.join(DATA_DIR, choice_label)

@st.cache_data
def load_csv(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    return df

try:
    df_raw = load_csv(file_path)
except Exception as e:
    st.error(f"Gagal membaca CSV: {e}")
    st.stop()

st.subheader("Preview data (baris atas)")
st.dataframe(df_raw.head(8), use_container_width=True)

# detect country & year columns
cols = [str(c) for c in df_raw.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
country_candidates = ["Country Name", "country", "Country", "Negara", "Entity", cols[0]]
country_col = None
for cand in country_candidates:
    if cand in df_raw.columns:
        country_col = cand
        break
if country_col is None:
    st.error("Tidak menemukan kolom nama negara. Pastikan file punya kolom negara.")
    st.stop()
if not year_cols:
    st.error("Tidak terdeteksi kolom tahun (contoh: '1990','1991',...). Pastikan file wide-format dengan header tahun.")
    st.stop()

# convert to long format
df = df_raw.copy()
df_long = df.melt(id_vars=[country_col], value_vars=year_cols, var_name="year", value_name="value")
df_long = df_long.dropna(subset=[country_col, "value"]).copy()

# normalize country names
df_long[country_col] = df_long[country_col].apply(normalize_country_name)

# convert numeric values (handle thousands separators)
def to_num_safe(x):
    try:
        return float(str(x).replace(",", "").strip())
    except:
        return None

df_long["value"] = df_long["value"].apply(to_num_safe)
df_long = df_long.dropna(subset=["value"]).copy()
df_long["year"] = df_long["year"].astype(int)

# try detect ISO column if present in original dataset
iso_candidates = [c for c in df_raw.columns if c.lower() in ("iso3", "iso_3", "iso", "country code", "alpha3")]
iso_col = iso_candidates[0] if iso_candidates else None

# if no iso_col, attempt to create iso3 via pycountry (best-effort)
if not iso_col and _HAS_PYCOUNTRY:
    st.info("pycountry tersedia: mencoba lookup ISO3 otomatis (best-effort).")
    # Create mapping dict from unique country names to ISO3 where found
    unique_countries = pd.Series(df_long[country_col].unique()).dropna().tolist()
    iso_map = {}
    for cname in unique_countries:
        code = try_get_iso3_from_name(cname)
        if code:
            iso_map[cname] = code
    # create iso3 column in long df if any mapped
    if iso_map:
        df_long["iso3_auto"] = df_long[country_col].map(iso_map)
    else:
        df_long["iso3_auto"] = None
else:
    if iso_col:
        # merge iso column into long df (if original had wide format iso in rows)
        # If original had iso in each row, we need to melt iso too; otherwise try left-join
        try:
            # If iso column exists in wide: attempt to melt same as values
            if iso_col in df.columns:
                iso_long = df[[country_col, iso_col] + year_cols].melt(id_vars=[country_col, iso_col], value_vars=year_cols,
                                                                       var_name="year", value_name="value")
                iso_long["year"] = iso_long["year"].astype(int)
                iso_long = iso_long[[country_col, iso_col, "year"]]
                df_long = df_long.merge(iso_long, on=[country_col, "year"], how="left")
                # standardize name to iso3_col
                df_long.rename(columns={iso_col: "iso3_auto"}, inplace=True)
            else:
                df_long["iso3_auto"] = None
        except Exception:
            df_long["iso3_auto"] = None
    else:
        df_long["iso3_auto"] = None

# UI: map options
st.sidebar.header("Opsi Peta")
color_mode = st.sidebar.radio("Mode warna peta", ("Continuous (nilai)", "Quantile (buckets)"))
if color_mode == "Quantile (buckets)":
    n_buckets = st.sidebar.slider("Jumlah bucket (quantile)", 3, 9, 5)
else:
    n_buckets = None
color_scale = st.sidebar.selectbox("Pilih color scale (continuous)", px.colors.named_colorscales(), index=0)

# Choropleth
st.subheader("🌎 Peta Dunia (Choropleth)")
years = sorted(df_long["year"].unique().tolist())
sel_year = st.slider("Pilih tahun", min(years), max(years), max(years))

df_map = df_long[df_long["year"] == sel_year].copy()
if df_map.empty:
    st.warning("Tidak ada data untuk tahun ini.")
else:
    # if quantile buckets requested
    if color_mode == "Quantile (buckets)":
        # create buckets
        try:
            df_map["bucket"] = pd.qcut(df_map["value"], q=n_buckets, duplicates="drop")
            # map bucket to string labels
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
    # first try country names mapping
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
        if discrete:
            # ensure categories are ordered by bucket lower bound (qcut order is preserved)
            fig.update_traces(marker_line_width=0.2)
        fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
        plotted = True
    except Exception as e:
        st.warning("Plot berdasarkan country-names gagal. Error: " + str(e))

    # fallback: try iso3 column if available
    if not plotted:
        if df_map.get("iso3_auto").notna().any():
            try:
                # use iso3 column for locations
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
        else:
            # extra: try to auto-get iso3 for missing via pycountry if available
            if _HAS_PYCOUNTRY:
                try:
                    missing = df_map[df_map["iso3_auto"].isna()][country_col].unique().tolist()
                    # try to fill some via pycountry
                    iso_found = {}
                    for cname in missing:
                        code = try_get_iso3_from_name(cname)
                        if code:
                            iso_found[cname] = code
                    if iso_found:
                        df_map["iso3_try"] = df_map[country_col].map(iso_found)
                        df_map["iso3_final"] = df_map["iso3_auto"].fillna(df_map.get("iso3_try"))
                        fig3 = px.choropleth(df_map, locations="iso3_final", color=color_col, hover_name=country_col,
                                             title=f"{choice_label} — {sel_year} (ISO3 try fallback)",
                                             color_continuous_scale=color_scale if not discrete else None)
                        fig3.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                        st.plotly_chart(fig3, use_container_width=True)
                        plotted = True
                except Exception as e3:
                    st.warning("Auto ISO3 with pycountry failed: " + str(e3))

    if not plotted:
        st.error("Gagal membuat peta otomatis. Periksa ejaan nama negara, tambahkan kolom ISO3, atau kirim contoh nama negara yang tidak muncul.")
        st.write("Contoh nama negara (sample):", df_map[country_col].unique()[:30].tolist())

# Time series + ranking
st.subheader("📈 Time Series per Negara")
countries = sorted(df_long[country_col].dropna().unique().tolist())
sel_country = st.selectbox("Pilih negara", countries, index=0)
df_country = df_long[df_long[country_col] == sel_country].sort_values("year")
if not df_country.empty:
    st.line_chart(df_country.set_index("year")["value"], height=360)
    st.dataframe(df_country.reset_index(drop=True).tail(50), use_container_width=True)
else:
    st.write("Tidak ada time series untuk negara ini.")

st.subheader(f"📋 Ranking negara — {sel_year}")
df_rank = df_map[[country_col, "value"]].sort_values("value", ascending=False).reset_index(drop=True)
st.dataframe(df_rank.head(200), use_container_width=True)

# download standardized long-format
st.subheader("⬇ Unduh data (long-format)")
csv_out = df_long.to_csv(index=False)
st.download_button("Download CSV (long-format)", csv_out, file_name=f"{os.path.splitext(choice_label)[0]}_long.csv")

st.markdown("---")
st.info("Tip: Jika beberapa negara tidak muncul, perbaiki ejaan di CSV atau tambahkan kolom ISO3 (nama: iso3). Jika ingin, aku bisa bantu mapping nama yang tidak muncul — kirimkan 10 contoh nama negara yang tidak terpetakan.")
