# pages/Home.py
import streamlit as st
import pandas as pd
import glob, os
import numpy as np
import plotly.express as px
from pathlib import Path
from typing import Optional

st.set_page_config(page_title="Home — Ringkasan Indikator", layout="wide")

# ---------- Controls (pilihan negara & tahun) ----------
st.markdown("## 🌍 Dashboard Ekonomi (Ringkasan)")
st.write("Ringkasan cepat untuk beberapa indikator utama. Pilih negara dan rentang tahun untuk memperbarui tampilan.")


# ---------- Helper: robust csv load ----------
@st.cache_data
def try_load_csv(path: str) -> Optional[pd.DataFrame]:
    """
    Simple robust loader: try common encodings and separators.
    Returns DataFrame or None if fail.
    """
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    seps = [",", ";", "\t", "|"]
    for enc in encodings:
        for sep in seps:
            try:
                df = pd.read_csv(path, encoding=enc, sep=sep, engine="python")
                if df.shape[0] == 0:
                    return None
                # Normalize column names (strip)
                df.columns = [str(c).strip() for c in df.columns]
                return df
            except Exception:
                continue
        # try pandas auto (python engine)
        try:
            df = pd.read_csv(path, encoding=enc, sep=None, engine="python")
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception:
            continue
    return None

# ---------- small utils ----------
def pretty_label(fname: str) -> str:
    """Make a nicer label from filename: remove extension and numbers prefix."""
    base = os.path.basename(fname)
    name = os.path.splitext(base)[0]
    # remove leading numbering like "1.1 " or "01_"
    name = name.lstrip("0123456789. _-")
    return name.strip()

def detect_country_col(df: pd.DataFrame) -> Optional[str]:
    cands = ["Country Name","Country","country","country name","Entity","Negara","entity"]
    for c in cands:
        if c in df.columns:
            return c
    # fallback: if first column looks like strings and many unique values -> treat as country
    first = df.columns[0]
    if df[first].apply(lambda x: isinstance(x, str)).sum() > len(df)*0.5:
        return first
    return None

def detect_year_cols(df: pd.DataFrame):
    # return list of columns that look like years (4-digit) or that are numeric index-like
    years = [c for c in df.columns if str(c).isdigit() and len(str(c)) == 4]
    return years

def compute_latest_and_pct(series: pd.Series):
    # series indexed by year or by position; we take last non-null and previous non-null
    vals = series.dropna().astype(float)
    if vals.empty:
        return None, None
    latest = vals.iloc[-1]
    prev = vals.iloc[-2] if len(vals) >= 2 else None
    pct = None
    if prev is not None and prev != 0:
        pct = (latest - prev) / abs(prev) * 100.0
    return latest, pct

# ---------- Main ----------
st.title("🏠 Home — Ringkasan Indikator Ekonomi")
st.write("Halaman ini menampilkan ringkasan cepat dari file indikator yang ada di folder `data/` — nilai terakhir, perubahan, dan preview small-table. Klik nama indikator untuk melihat detail pada halaman indikator masing-masing.")

DATA_DIR = "data"
files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
if not files:
    st.warning(f"Tidak menemukan file CSV pada `{DATA_DIR}/`. Silakan taruh CSV indikator di folder tersebut lalu refresh.")
    st.stop()

# Info top
col_top1, col_top2, col_top3 = st.columns([1,2,2])
with col_top1:
    st.metric("Jumlah indikator (file)", len(files))
with col_top2:
    st.write("**Files ditemukan:**")
    st.write(", ".join(pretty_label(f) for f in files))
with col_top3:
    if st.button("Refresh data"):
        st.experimental_rerun()

st.markdown("---")

# We'll show cards in rows of 3
cards_per_row = 3
rows = (len(files) + cards_per_row - 1) // cards_per_row

for r in range(rows):
    cols = st.columns(cards_per_row)
    for i in range(cards_per_row):
        idx = r*cards_per_row + i
        if idx >= len(files):
            break
        fpath = files[idx]
        label = pretty_label(fpath)
        with cols[i]:
            # card header
            st.subheader(f"📄 {label}")
            df = try_load_csv(fpath)
            if df is None:
                st.warning("Gagal baca CSV atau file kosong.")
                continue

            # Try detect wide format: country + year columns
            country_col = detect_country_col(df)
            year_cols = detect_year_cols(df)

            # prepare long format if possible
            if country_col and year_cols:
                try:
                    df_long = df.melt(id_vars=[country_col], value_vars=year_cols,
                                      var_name="year", value_name="value")
                    # convert types
                    df_long = df_long.dropna(subset=[country_col, "value"])
                    df_long["value"] = df_long["value"].apply(lambda x: pd.to_numeric(x, errors="coerce"))
                    # choose global latest (sum across countries?) -> for summary we display global sum or top country?
                    # here: sum of values across countries for latest year as a simple aggregate
                    grouped = df_long.groupby("year")["value"].sum().dropna().sort_index()
                    latest, pct = compute_latest_and_pct(grouped)
                    latest_label = f"{latest:,.0f}" if latest is not None else "–"
                except Exception:
                    latest = None
                    pct = None
                    latest_label = "–"
            else:
                # try long format: columns like country, year, value
                cols_lower = [c.lower() for c in df.columns]
                if "year" in cols_lower and "value" in cols_lower:
                    # normalize column names
                    colmap = {c: c for c in df.columns}
                    yr = [c for c in df.columns if c.lower()=="year"][0]
                    val = [c for c in df.columns if c.lower()=="value"][0]
                    df_l = df[[yr, val]].copy()
                    df_l[yr] = pd.to_numeric(df_l[yr], errors="coerce")
                    df_l[val] = pd.to_numeric(df_l[val], errors="coerce")
                    grp = df_l.groupby(yr)[val].sum().dropna().sort_index()
                    latest, pct = compute_latest_and_pct(grp)
                    latest_label = f"{latest:,.0f}" if latest is not None else "–"
                else:
                    latest = None; pct = None; latest_label = "–"

            # display metric + pct
            # color icon for pct
            pct_str = "–"
            if pct is not None:
                pct_sign = "▲" if pct > 0 else ("▼" if pct < 0 else "•")
                pct_str = f"{pct_sign} {pct:.2f}%"
            st.markdown(f"**Terakhir (aggregate)**: `{latest_label}`  \nPerubahan: {pct_str}")

            # small sparkline using the grouped timeseries if exists
            try:
                if 'grouped' in locals() and not grouped.empty:
                    fig = px.line(grouped.reset_index(), x=grouped.index.astype(str), y="value", height=100)
                    fig.update_traces(showlegend=False, line=dict(width=2))
                    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(visible=False), yaxis=dict(visible=False))
                    st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

            # show small preview table (top rows)
            st.write("Preview:")
            try:
                st.dataframe(df.head(8), use_container_width=True)
            except Exception:
                st.write("Tidak dapat menampilkan preview.")

            # link hint to page (if page name exists)
            page_hint = label.lower().replace(" ", "-")
            st.caption(f"Klik menu sebelah kiri untuk membuka halaman indikator {label} (jika tersedia).")
    st.markdown("---")

st.info("Tip: Untuk tampilan lebih detail, buka masing-masing halaman indikator di menu. Jika ada file baru, unggah ke folder `data/` lalu klik *Refresh data*.")
