# pages/page5.py

import streamlit as st
import pandas as pd
import os
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

st.title("💰 Investasi & Pembentukan Modal — Peta Dunia + Time Series + Analisis")
st.write(
    "Halaman ini menampilkan indikator terkait investasi dan pembentukan modal "
    "berdasarkan file CSV lokal di folder data/, lengkap dengan analisis statistik dan interpretasi otomatis."
)

# -----------------------------
# Lokasi folder data & mapping file
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Foreign direct investment (FDI)": "5.1 Foreign Direct Investment (FDI).csv",
    "Gross capital formation": "5.2 Gross capital formation.csv",
}

# -----------------------------
# Helper baca CSV (lebih toleran)
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


def guess_scale_and_unit(series: pd.Series) -> str:
    """
    Heuristik sederhana untuk memberi petunjuk skala/unit.
    (Karena file CSV berbeda-beda; ini hanya "hint", bukan kepastian.)
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return "Unit tidak terdeteksi (data kosong)."
    med = float(np.nanmedian(np.abs(s.values)))
    mx = float(np.nanmax(np.abs(s.values)))

    # heuristik
    if mx <= 300 and med <= 50:
        return "Nilai tampak seperti *persentase (%)* (perkiraan)."
    if med >= 1e9:
        return "Nilai tampak seperti *US$ (miliar)* atau skala besar (perkiraan)."
    if med >= 1e6:
        return "Nilai tampak seperti *US$* atau skala jutaan (perkiraan)."
    return "Skala/unit bervariasi (tidak jelas) — cek metadata file jika ada."


def compute_country_metrics(df_country: pd.DataFrame, indicator_label: str) -> dict:
    """
    Menghitung metrik penting untuk interpretasi negara terpilih.
    df_country harus punya kolom: year (int), value (float)
    """
    out = {}
    d = df_country.dropna(subset=["year", "value"]).sort_values("year").copy()
    if d.empty:
        return out

    out["n_obs"] = len(d)
    out["year_min"] = int(d["year"].min())
    out["year_max"] = int(d["year"].max())

    # latest & previous
    last_row = d.iloc[-1]
    out["latest_year"] = int(last_row["year"])
    out["latest_value"] = float(last_row["value"])

    prev = d.iloc[-2] if len(d) >= 2 else None
    if prev is not None:
        out["prev_year"] = int(prev["year"])
        out["prev_value"] = float(prev["value"])
        out["yoy_abs"] = out["latest_value"] - out["prev_value"]
        # yoy % (hati-hati jika prev_value = 0)
        out["yoy_pct"] = (out["yoy_abs"] / out["prev_value"] * 100) if out["prev_value"] != 0 else np.nan
    else:
        out["prev_year"] = None
        out["prev_value"] = None
        out["yoy_abs"] = np.nan
        out["yoy_pct"] = np.nan

    # mean last 5/10 years (jika cukup)
    def mean_last_n_years(n: int):
        y0 = out["latest_year"] - (n - 1)
        sub = d[d["year"] >= y0]
        return float(sub["value"].mean()) if not sub.empty else np.nan

    out["mean_5y"] = mean_last_n_years(5)
    out["mean_10y"] = mean_last_n_years(10)

    # volatilitas
    out["std_all"] = float(d["value"].std(ddof=0)) if len(d) >= 2 else np.nan
    out["mean_all"] = float(d["value"].mean())
    out["cv_all"] = (out["std_all"] / out["mean_all"]) if out["mean_all"] not in [0, np.nan] else np.nan

    # tren slope linear
    if len(d) >= 2:
        x = d["year"].values.astype(float)
        y = d["value"].values.astype(float)
        try:
            slope = np.polyfit(x, y, 1)[0]
        except Exception:
            slope = np.nan
        out["slope_per_year"] = float(slope) if slope is not None else np.nan
    else:
        out["slope_per_year"] = np.nan

    # CAGR (indikatif)
    if len(d) >= 2 and d.iloc[0]["value"] not in [0, np.nan]:
        y_first = float(d.iloc[0]["value"])
        y_last = float(d.iloc[-1]["value"])
        t = float(d.iloc[-1]["year"] - d.iloc[0]["year"])
        if t > 0 and y_first != 0:
            # kalau y_first negatif, CAGR jadi tidak bermakna -> set NaN
            if y_first > 0 and y_last > 0:
                out["cagr_pct"] = float(((y_last / y_first) ** (1 / t) - 1) * 100)
            else:
                out["cagr_pct"] = np.nan
        else:
            out["cagr_pct"] = np.nan
    else:
        out["cagr_pct"] = np.nan

    return out


def interpret_country(metrics: dict, rank_info: dict, scale_hint: str, indicator_label: str, country: str) -> str:
    """
    Membuat narasi interpretasi (markdown) dari metrik & posisi ranking.
    """
    if not metrics:
        return "Tidak cukup data untuk membuat interpretasi."

    latest_year = metrics.get("latest_year")
    latest_value = metrics.get("latest_value")
    yoy_abs = metrics.get("yoy_abs", np.nan)
    yoy_pct = metrics.get("yoy_pct", np.nan)
    slope = metrics.get("slope_per_year", np.nan)
    std_all = metrics.get("std_all", np.nan)
    mean_5y = metrics.get("mean_5y", np.nan)
    mean_10y = metrics.get("mean_10y", np.nan)
    cagr = metrics.get("cagr_pct", np.nan)

    rank = rank_info.get("rank", None)
    total = rank_info.get("total", None)
    pct = rank_info.get("percentile", None)

    # kategori tren
    trend_label = "cenderung *stabil*"
    if pd.notna(slope):
        if abs(slope) < 1e-9:
            trend_label = "cenderung *stabil*"
        else:
            trend_label = "cenderung *naik" if slope > 0 else "cenderung **turun*"

    # yoy kalimat
    yoy_text = "Tidak ada pembanding tahun sebelumnya (data hanya 1 titik)."
    if pd.notna(yoy_abs):
        direction = "naik" if yoy_abs > 0 else ("turun" if yoy_abs < 0 else "tidak berubah")
        if pd.notna(yoy_pct):
            yoy_text = f"Perubahan terakhir *{direction}* sebesar *{yoy_abs:,.4g}* (≈ *{yoy_pct:,.2f}%*) dibanding tahun sebelumnya."
        else:
            yoy_text = f"Perubahan terakhir *{direction}* sebesar *{yoy_abs:,.4g}* dibanding tahun sebelumnya."

    # ranking kalimat
    rank_text = ""
    if rank is not None and total is not None and total > 0:
        rank_text = f"Posisi pada tahun {latest_year}: peringkat *#{rank} dari {total} negara* (≈ persentil *{pct:.1f}*)."

    # volatilitas kalimat
    vol_text = ""
    if pd.notna(std_all):
        vol_text = f"Volatilitas historis (std) ≈ *{std_all:,.4g}*; semakin besar nilainya berarti pergerakan antar-tahun makin fluktuatif."
    else:
        vol_text = "Volatilitas tidak dapat dihitung (data terlalu sedikit)."

    # CAGR kalimat
    cagr_text = ""
    if pd.notna(cagr):
        cagr_text = f"Pertumbuhan rata-rata jangka panjang (CAGR, indikatif): *{cagr:,.2f}% per tahun*."
    else:
        cagr_text = "CAGR tidak ditampilkan (nilai awal/akhir tidak cocok untuk perhitungan CAGR)."

    # mean 5y/10y
    avg_text = ""
    parts = []
    if pd.notna(mean_5y):
        parts.append(f"rata-rata 5 tahun terakhir ≈ *{mean_5y:,.4g}*")
    if pd.notna(mean_10y):
        parts.append(f"rata-rata 10 tahun terakhir ≈ *{mean_10y:,.4g}*")
    if parts:
        avg_text = "Ringkasan level terbaru vs historis: " + "; ".join(parts) + "."
    else:
        avg_text = "Rata-rata 5/10 tahun tidak cukup data."

    md = f"""
*Interpretasi otomatis — {country} ({indicator_label})*

- *Nilai terbaru: tahun *{latest_year}* = *{latest_value:,.4g}**  
- *Dinamika jangka pendek (YoY)*: {yoy_text}  
- *Arah tren: secara garis besar {trend_label} (slope linear ≈ *{slope:,.4g} per tahun**).  
- *Level historis*: {avg_text}  
- *Stabilitas/risiko fluktuasi*: {vol_text}  
- *Posisi relatif global*: {rank_text}  
- *Pertumbuhan jangka panjang*: {cagr_text}  
- *Catatan unit/skala*: {scale_hint}

*Cara membaca hasil ini (singkat):*
- Jika indikator ini positif dan trennya naik → sinyal penguatan aktivitas investasi/pembentukan modal.  
- Jika turun tajam YoY atau volatilitas tinggi → perlu cek faktor shock (krisis, kebijakan, pandemi, perubahan harga komoditas, dsb.).  
- Jika peringkat relatif tinggi → negara tersebut termasuk kelompok dengan nilai indikator “besar” dibanding negara lain pada tahun yang sama.  
"""
    return md.strip()


# -----------------------------
# Cek file yang tersedia
# -----------------------------
available_indicators = []
for label, fname in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, fname)):
        available_indicators.append(label)

if not available_indicators:
    st.error(
        f"Tidak ada file CSV Page 5 yang ditemukan di folder {DATA_DIR}/. "
        "Pastikan file 5.1 dan 5.2 sudah diletakkan di sana."
    )
    st.stop()

# -----------------------------
# Pilih indikator & load data
# -----------------------------
indicator_label = st.selectbox("📌 Pilih indikator:", available_indicators)
file_path = os.path.join(DATA_DIR, FILES[indicator_label])

try:
    df = load_csv_tolerant(file_path)
except Exception as e:
    st.error(f"Gagal membaca file {os.path.basename(file_path)}: {e}")
    st.stop()

# -----------------------------
# Preview mentah
# -----------------------------
with st.expander("📄 Preview Data Mentah (klik untuk buka)", expanded=True):
    st.dataframe(df.head(20), use_container_width=True)

# -----------------------------
# Deteksi kolom tahun & negara
# -----------------------------
cols = [str(c) for c in df.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]

if not year_cols:
    st.error("Tidak ditemukan kolom tahun (misal 1990, 2000, dst.) di file CSV ini. Cek kembali header kolom.")
    st.stop()

country_col = None
for cand in ["Country Name", "country", "Country", "Negara", "Entity"]:
    if cand in df.columns:
        country_col = cand
        break
if country_col is None:
    country_col = df.columns[0]

# -----------------------------
# Transform long format
# -----------------------------
df_long = df.melt(id_vars=[country_col], value_vars=year_cols, var_name="year", value_name="value")
df_long = df_long.rename(columns={country_col: "country"})

df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
df_long = df_long.dropna(subset=["country", "year", "value"])
df_long["year"] = df_long["year"].astype(int)

if df_long.empty:
    st.error("Setelah transformasi, tidak ada data bernilai (semua NaN).")
    st.stop()

# info unit/skala (heuristik)
scale_hint = guess_scale_and_unit(df_long["value"])

# -----------------------------
# Tabs utama (Visual + Analisis)
# -----------------------------
tab_viz, tab_analysis, tab_download = st.tabs(["🗺️ Visualisasi", "📊 Analisis & Interpretasi", "📥 Download"])

# =========================================================
# TAB 1 — VISUALISASI
# =========================================================
with tab_viz:
    st.subheader("🌍 Peta Dunia")
    years = sorted(df_long["year"].unique())
    year_min, year_max = int(min(years)), int(max(years))

    selected_year = st.slider("Pilih tahun untuk peta dunia", year_min, year_max, year_max, key="map_year")
    df_map = df_long[df_long["year"] == selected_year]

    st.caption(f"Catatan skala/unit: {scale_hint}")

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
                "Gagal membuat peta dunia. Cek apakah nama negara di CSV sesuai standar country names Plotly.\n\n"
                f"Detail error: {e}"
            )

    st.subheader("📈 Time Series")
    country_list = sorted(df_long["country"].dropna().unique().tolist())
    if not country_list:
        st.error("Daftar negara kosong (kolom negara tidak terbaca dengan benar).")
        st.stop()

    default_country = "Indonesia" if "Indonesia" in country_list else country_list[0]
    selected_countries = st.multiselect(
        "Pilih negara (bisa lebih dari satu):",
        country_list,
        default=[default_country],
        key="ts_countries"
    )

    df_ts = df_long[df_long["country"].isin(selected_countries)].sort_values(["country", "year"])
    if df_ts.empty:
        st.info("Tidak ada data time series untuk negara yang dipilih.")
    else:
        fig_ts = px.line(
            df_ts,
            x="year",
            y="value",
            color="country",
            markers=True,
            title=f"Time Series — {indicator_label}",
            labels={"year": "Tahun", "value": indicator_label, "country": "Negara"},
        )
        fig_ts.update_layout(
            xaxis_title="Tahun",
            yaxis_title=indicator_label,
            xaxis=dict(dtick=5),
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
        )
        st.plotly_chart(fig_ts, use_container_width=True)

        with st.expander("📄 Lihat tabel data time series (long)", expanded=False):
            st.dataframe(df_ts.reset_index(drop=True), use_container_width=True)

# =========================================================
# TAB 2 — ANALISIS & INTERPRETASI
# =========================================================
with tab_analysis:
    st.subheader("🔎 Analisis Statistik Global + Interpretasi Otomatis")

    # -------- Ringkasan kualitas data
    n_country = df_long["country"].nunique()
    n_year = df_long["year"].nunique()
    st.write(f"- Negara: *{n_country:,}* | Tahun: *{df_long['year'].min()}–{df_long['year'].max()}* | Observasi: *{len(df_long):,}*")
    st.caption(f"Catatan skala/unit: {scale_hint}")

    # coverage per negara
    coverage = (
        df_long.groupby("country")["year"]
        .nunique()
        .reset_index(name="n_years_available")
        .sort_values("n_years_available", ascending=False)
    )
    coverage["coverage_pct"] = (coverage["n_years_available"] / n_year * 100).round(1)

    with st.expander("✅ Kualitas Data: coverage per negara", expanded=False):
        st.dataframe(coverage.head(60), use_container_width=True)
        fig_cov = px.histogram(coverage, x="n_years_available", title="Distribusi jumlah tahun tersedia per negara")
        st.plotly_chart(fig_cov, use_container_width=True)

    # -------- Statistik global per tahun
    yearly_stats = (
        df_long.groupby("year")["value"]
        .agg(mean="mean", median="median", min="min", max="max", std="std", n="count")
        .reset_index()
        .sort_values("year")
    )

    col1, col2 = st.columns(2)
    with col1:
        st.write("*Statistik keseluruhan (semua negara & tahun)*")
        st.dataframe(df_long["value"].describe().to_frame("overall"), use_container_width=True)
    with col2:
        st.write("*Statistik global per tahun (tail)*")
        st.dataframe(yearly_stats.tail(15), use_container_width=True)

    fig_mean = px.line(yearly_stats, x="year", y="mean", markers=True, title="Rata-rata global per tahun")
    st.plotly_chart(fig_mean, use_container_width=True)

    fig_dist = px.histogram(df_long, x="value", nbins=60, title="Distribusi nilai (semua negara & tahun)")
    st.plotly_chart(fig_dist, use_container_width=True)

    # -------- Ranking tahun (top/bottom) + posisi negara fokus
    st.markdown("---")
    st.subheader("🏆 Ranking Tahun (Top/Bottom) + Posisi Negara")

    year_rank = st.slider(
        "Pilih tahun untuk ranking:",
        int(df_long["year"].min()),
        int(df_long["year"].max()),
        int(df_long["year"].max()),
        key="rank_year",
    )

    df_rank = df_long[df_long["year"] == year_rank].dropna(subset=["value"]).copy()
    if df_rank.empty:
        st.warning("Tidak ada data pada tahun ranking yang dipilih.")
    else:
        top_n = st.number_input("Top N", 5, 50, 10, 1)
        bottom_n = st.number_input("Bottom N", 5, 50, 10, 1)

        df_top = df_rank.sort_values("value", ascending=False).head(int(top_n))
        df_bottom = df_rank.sort_values("value", ascending=True).head(int(bottom_n))

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"*Top {int(top_n)} — {indicator_label} ({year_rank})*")
            st.dataframe(df_top.reset_index(drop=True), use_container_width=True)
        with c2:
            st.write(f"*Bottom {int(bottom_n)} — {indicator_label} ({year_rank})*")
            st.dataframe(df_bottom.reset_index(drop=True), use_container_width=True)

        df_bar = pd.concat([df_top.assign(group="Top"), df_bottom.assign(group="Bottom")], ignore_index=True)
        fig_bar = px.bar(df_bar, x="country", y="value", color="group", title=f"Top vs Bottom — {indicator_label} ({year_rank})")
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

    # -------- Analisis negara terpilih + interpretasi otomatis
    st.markdown("---")
    st.subheader("🧭 Analisis Negara Terpilih (Tren, YoY, Volatilitas, Outlier)")

    country_list = sorted(df_long["country"].dropna().unique().tolist())
    focus_country = st.selectbox("Pilih negara untuk interpretasi:", country_list, index=(country_list.index("Indonesia") if "Indonesia" in country_list else 0))

    df_country = df_long[df_long["country"] == focus_country].sort_values("year").copy()
    if df_country.empty:
        st.info("Tidak ada data untuk negara ini.")
        st.stop()

    # hitung metrik
    metrics = compute_country_metrics(df_country[["year", "value"]], indicator_label)

    # ranking untuk latest_year (jika tersedia)
    rank_info = {"rank": None, "total": None, "percentile": None}
    latest_year = metrics.get("latest_year", None)
    if latest_year is not None:
        df_latest = df_long[df_long["year"] == latest_year].dropna(subset=["value"]).copy()
        if not df_latest.empty and focus_country in df_latest["country"].values:
            df_latest = df_latest.sort_values("value", ascending=False).reset_index(drop=True)
            rank = int(df_latest.index[df_latest["country"] == focus_country][0] + 1)
            total = int(len(df_latest))
            # persentil: makin kecil rank makin tinggi
            percentile = (1 - (rank - 1) / max(total - 1, 1)) * 100
            rank_info = {"rank": rank, "total": total, "percentile": float(percentile)}

    # hitung YoY dan rolling
    df_country2 = df_country.copy()
    df_country2["yoy_change"] = df_country2["value"].diff(1)
    window = st.slider("Rolling window (tahun)", 2, 10, 3, key="roll_window_country")
    df_country2["rolling_mean"] = df_country2["value"].rolling(window=window, min_periods=1).mean()

    # grafik detail negara
    fig_country = px.line(df_country2, x="year", y="value", markers=True, title=f"{indicator_label} — {focus_country}")
    st.plotly_chart(fig_country, use_container_width=True)

    fig_roll = px.line(df_country2, x="year", y="rolling_mean", markers=True, title=f"Rolling Mean ({window} tahun) — {focus_country}")
    st.plotly_chart(fig_roll, use_container_width=True)

    fig_yoy = px.line(df_country2, x="year", y="yoy_change", markers=True, title=f"Perubahan YoY (diff tahunan) — {focus_country}")
    st.plotly_chart(fig_yoy, use_container_width=True)

    # outlier negara (z-score dalam seri negara tersebut)
    st.subheader("🚩 Outlier (dalam seri negara ini)")
    z_thr = st.slider("Ambang |Z|", 2.0, 5.0, 3.0, 0.1, key="zthr_country")

    s = df_country2["value"].dropna()
    if len(s) >= 3 and s.std(ddof=0) != 0:
        z = (df_country2["value"] - s.mean()) / s.std(ddof=0)
        df_country2["z"] = z
        outliers = df_country2[df_country2["z"].abs() >= z_thr].copy()
        st.write(f"Outlier terdeteksi: *{len(outliers)}* baris (|Z| ≥ {z_thr})")
        st.dataframe(outliers[["year", "value", "z"]].sort_values("z", ascending=False), use_container_width=True)
    else:
        st.info("Outlier (Z-score) butuh minimal ~3 titik data dan standar deviasi tidak nol.")

    # tabel ringkas negara
    with st.expander("📄 Tabel negara (detail)", expanded=False):
        st.dataframe(df_country2.reset_index(drop=True), use_container_width=True)

    # INTERPRETASI OTOMATIS (narasi)
    st.markdown("---")
    st.subheader("📝 Interpretasi Otomatis")
    st.markdown(interpret_country(metrics, rank_info, scale_hint, indicator_label, focus_country))

    # Tambahan interpretasi global sederhana: “konteks tahun terbaru”
    st.subheader("🌐 Konteks Global (tahun terbaru negara)")
    if latest_year is not None:
        df_latest = df_long[df_long["year"] == latest_year].dropna(subset=["value"]).copy()
        if not df_latest.empty:
            p10 = np.nanpercentile(df_latest["value"], 10)
            p50 = np.nanpercentile(df_latest["value"], 50)
            p90 = np.nanpercentile(df_latest["value"], 90)
            st.write(
                f"Pada tahun *{latest_year}*, distribusi global kira-kira:\n"
                f"- P10 ≈ *{p10:,.4g}, Median (P50) ≈ *{p50:,.4g}*, P90 ≈ *{p90:,.4g}**.\n"
                f"\nBandingkan nilai {focus_country} (*{metrics.get('latest_value'):,.4g}*) terhadap tiga titik ini untuk memahami apakah berada di level rendah/menengah/tinggi secara global."
            )

# =========================================================
# TAB 3 — DOWNLOAD
# =========================================================
with tab_download:
    st.subheader("📘 Data Lengkap (long format)")
    st.dataframe(df_long.reset_index(drop=True), use_container_width=True)

    csv_download = df_long.to_csv(index=False)
    st.download_button(
        "⬇ Download data (CSV)",
        csv_download,
        file_name=f"page5_investment_{indicator_label.replace(' ', '_')}.csv",
        mime="text/csv",
    )

