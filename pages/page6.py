# pages/page6.py

import streamlit as st
import pandas as pd
import os
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📉 Kemiskinan & Ketimpangan — Peta Dunia + Time Series + Analisis")
st.write(
    "Halaman ini menampilkan indikator kemiskinan dan ketimpangan "
    "berdasarkan file CSV lokal di folder `data/`, lengkap dengan analisis statistik dan interpretasi otomatis."
)

# -----------------------------
# Lokasi folder data & mapping file
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Poverty headcount ratio at $4.20 a day": "6.1. POVERTY HEADCOUNT RATIO AT $4.20 A DAY.csv",
    "Gini index": "6.2. GINI INDEX.csv",
    "Income share held by lowest 20%": "6.3. INCOME SHARE HELD BY LOWER 20%.csv",
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


def guess_scale_and_unit(series: pd.Series, indicator_label: str) -> str:
    """
    Heuristik sederhana untuk memberi petunjuk skala/unit.
    Untuk page kemiskinan/ketimpangan, sebagian besar biasanya persen atau indeks.
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return "Unit tidak terdeteksi (data kosong)."

    mx = float(np.nanmax(np.abs(s.values)))
    med = float(np.nanmedian(np.abs(s.values)))

    # indikator spesifik
    if "Gini" in indicator_label:
        return "Umumnya **indeks (0–100)** atau (0–1) tergantung sumber; di dataset ini terlihat sesuai rentang data."
    if "Income share" in indicator_label:
        return "Umumnya **persentase (%)** dari total pendapatan nasional."
    if "Poverty headcount" in indicator_label:
        return "Umumnya **persentase (%) penduduk** di bawah garis kemiskinan (sesuai threshold yang disebut)."

    # fallback heuristik umum
    if mx <= 1.5:
        return "Nilai tampak seperti **indeks (0–1)** (perkiraan)."
    if mx <= 120 and med <= 60:
        return "Nilai tampak seperti **persentase (%)** atau **indeks 0–100** (perkiraan)."
    return "Skala/unit bervariasi (tidak jelas) — cek metadata file jika ada."


def compute_country_metrics(df_country: pd.DataFrame) -> dict:
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

    last_row = d.iloc[-1]
    out["latest_year"] = int(last_row["year"])
    out["latest_value"] = float(last_row["value"])

    prev = d.iloc[-2] if len(d) >= 2 else None
    if prev is not None:
        out["prev_year"] = int(prev["year"])
        out["prev_value"] = float(prev["value"])
        out["yoy_abs"] = out["latest_value"] - out["prev_value"]
        out["yoy_pct"] = (out["yoy_abs"] / out["prev_value"] * 100) if out["prev_value"] != 0 else np.nan
    else:
        out["prev_year"] = None
        out["prev_value"] = None
        out["yoy_abs"] = np.nan
        out["yoy_pct"] = np.nan

    def mean_last_n_years(n: int):
        y0 = out["latest_year"] - (n - 1)
        sub = d[d["year"] >= y0]
        return float(sub["value"].mean()) if not sub.empty else np.nan

    out["mean_5y"] = mean_last_n_years(5)
    out["mean_10y"] = mean_last_n_years(10)

    out["std_all"] = float(d["value"].std(ddof=0)) if len(d) >= 2 else np.nan
    out["mean_all"] = float(d["value"].mean())
    out["cv_all"] = (out["std_all"] / out["mean_all"]) if (pd.notna(out["std_all"]) and out["mean_all"] != 0) else np.nan

    if len(d) >= 2:
        x = d["year"].values.astype(float)
        y = d["value"].values.astype(float)
        try:
            slope = np.polyfit(x, y, 1)[0]
        except Exception:
            slope = np.nan
        out["slope_per_year"] = float(slope)
    else:
        out["slope_per_year"] = np.nan

    # CAGR indikatif (hanya jika positif)
    if len(d) >= 2:
        y_first = float(d.iloc[0]["value"])
        y_last = float(d.iloc[-1]["value"])
        t = float(d.iloc[-1]["year"] - d.iloc[0]["year"])
        if t > 0 and y_first > 0 and y_last > 0:
            out["cagr_pct"] = float(((y_last / y_first) ** (1 / t) - 1) * 100)
        else:
            out["cagr_pct"] = np.nan
    else:
        out["cagr_pct"] = np.nan

    return out


def interpret_country(indicator_label: str, country: str, metrics: dict, rank_info: dict, scale_hint: str) -> str:
    """
    Narasi interpretasi skripsi-style, disesuaikan dengan indikator.
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

    rank = rank_info.get("rank")
    total = rank_info.get("total")
    pct = rank_info.get("percentile")

    # arah tren
    if pd.isna(slope) or abs(slope) < 1e-9:
        trend_label = "cenderung **stabil**"
    else:
        trend_label = "cenderung **meningkat**" if slope > 0 else "cenderung **menurun**"

    # interpretasi arah: beda indikator (kemiskinan vs pemerataan)
    lower_is_better = False
    if "Poverty headcount" in indicator_label or "Gini" in indicator_label:
        lower_is_better = True
    if "Income share held by lowest 20%" in indicator_label:
        lower_is_better = False  # makin tinggi -> lebih pro-poor / lebih merata (biasanya)

    # yoy kalimat
    yoy_text = "Tidak ada pembanding tahun sebelumnya (data hanya 1 titik)."
    if pd.notna(yoy_abs):
        direction = "naik" if yoy_abs > 0 else ("turun" if yoy_abs < 0 else "tidak berubah")
        if pd.notna(yoy_pct):
            yoy_text = f"Perubahan terakhir **{direction}** sebesar **{yoy_abs:,.4g}** (≈ **{yoy_pct:,.2f}%**) dibanding tahun sebelumnya."
        else:
            yoy_text = f"Perubahan terakhir **{direction}** sebesar **{yoy_abs:,.4g}** dibanding tahun sebelumnya."

    # ranking
    rank_text = ""
    if rank is not None and total is not None and total > 0:
        rank_text = f"Posisi pada tahun {latest_year}: **#{rank} dari {total} negara** (≈ persentil **{pct:.1f}**)."

    # volatilitas
    if pd.notna(std_all):
        vol_text = f"Volatilitas historis (std) ≈ **{std_all:,.4g}**; nilai lebih besar → fluktuasi antar-tahun makin tinggi."
    else:
        vol_text = "Volatilitas tidak dapat dihitung (data terlalu sedikit)."

    # ringkasan historis
    parts = []
    if pd.notna(mean_5y):
        parts.append(f"rata-rata 5 tahun terakhir ≈ **{mean_5y:,.4g}**")
    if pd.notna(mean_10y):
        parts.append(f"rata-rata 10 tahun terakhir ≈ **{mean_10y:,.4g}**")
    avg_text = "; ".join(parts) + "." if parts else "Rata-rata 5/10 tahun tidak cukup data."

    # interpretasi indikator-spesifik
    if "Poverty headcount" in indicator_label:
        meaning = (
            "Indikator ini menggambarkan **proporsi penduduk** yang berada di bawah garis kemiskinan "
            f"({indicator_label})."
        )
        better_note = "Nilai **lebih rendah** → kemiskinan **lebih rendah**."
    elif "Gini" in indicator_label:
        meaning = (
            "Indikator Gini mengukur **ketimpangan distribusi pendapatan**. Semakin tinggi Gini, "
            "semakin timpang distribusi pendapatan."
        )
        better_note = "Nilai **lebih rendah** → ketimpangan **lebih rendah** (lebih merata)."
    else:
        meaning = (
            "Indikator ini menggambarkan **porsi pendapatan nasional** yang diterima oleh kelompok 20% terbawah."
        )
        better_note = "Nilai **lebih tinggi** → kelompok terbawah menerima porsi lebih besar (indikasi lebih merata)."

    # tren interpretasi: baik/buruk
    trend_quality = ""
    if pd.notna(slope):
        if lower_is_better:
            # kalau slope turun -> membaik
            if slope < 0:
                trend_quality = "Secara tren, ini mengindikasikan **perbaikan** (arah menurun pada indikator yang lebih baik bila rendah)."
            elif slope > 0:
                trend_quality = "Secara tren, ini mengindikasikan **pelemahan** (arah meningkat pada indikator yang lebih baik bila rendah)."
        else:
            if slope > 0:
                trend_quality = "Secara tren, ini mengindikasikan **perbaikan** (arah meningkat pada indikator yang lebih baik bila tinggi)."
            elif slope < 0:
                trend_quality = "Secara tren, ini mengindikasikan **pelemahan** (arah menurun pada indikator yang lebih baik bila tinggi)."

    md = f"""
**Interpretasi otomatis — {country} ({indicator_label})**

- **Makna indikator**: {meaning}  
- **Nilai terbaru**: tahun **{latest_year}** = **{latest_value:,.4g}**  
- **Dinamika jangka pendek (YoY)**: {yoy_text}  
- **Arah tren**: {trend_label} (slope ≈ **{slope:,.4g} per tahun**). {trend_quality}  
- **Ringkasan historis**: {avg_text}  
- **Stabilitas/risiko fluktuasi**: {vol_text}  
- **Posisi relatif global**: {rank_text}  
- **Cara membaca cepat**: {better_note}  
- **Catatan unit/skala**: {scale_hint}

**Catatan analitis (skripsi-style):**
- Jika kemiskinan menurun tetapi Gini naik → kemungkinan terjadi **perbaikan rata-rata**, namun manfaat pertumbuhan tidak merata.  
- Jika Gini turun dan income share 20% terbawah naik → sinyal **pemerataan** yang lebih baik.  
- Lonjakan/penurunan tajam YoY dapat terkait shock (krisis, pandemi), perubahan kebijakan sosial, atau perubahan metodologi data.
"""
    return md.strip()


# -----------------------------
# Pilih indikator & load data
# -----------------------------
indicator_label = st.selectbox("📌 Pilih indikator kemiskinan/ketimpangan:", list(FILES.keys()))
file_path = os.path.join(DATA_DIR, FILES[indicator_label])

if not os.path.exists(file_path):
    st.error(
        f"File untuk indikator **{indicator_label}** tidak ditemukan.\n\n"
        f"Cari di folder `{DATA_DIR}/` nama: `{FILES[indicator_label]}` "
        "(cek lagi ejaan, spasi, huruf besar-kecil)."
    )
    st.stop()

try:
    df = load_csv_tolerant(file_path)
except Exception as e:
    st.error(f"Gagal membaca file `{os.path.basename(file_path)}`: {e}")
    st.stop()

with st.expander("📄 Preview Data Mentah (klik untuk buka)", expanded=True):
    st.dataframe(df.head(20), use_container_width=True)

# -----------------------------
# Deteksi kolom tahun & negara
# -----------------------------
cols = [str(c) for c in df.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
if not year_cols:
    st.error("Tidak ditemukan kolom tahun (misalnya 1990, 2000, dst.) di file CSV ini. Cek kembali header kolom.")
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

scale_hint = guess_scale_and_unit(df_long["value"], indicator_label)

# -----------------------------
# Tabs utama
# -----------------------------
tab_viz, tab_analysis, tab_download = st.tabs(["🗺️ Visualisasi", "📊 Analisis & Interpretasi", "📥 Download"])

# =========================================================
# TAB 1 — VISUALISASI
# =========================================================
with tab_viz:
    st.subheader("🌍 Peta Dunia (nilai terbaru ≤ tahun acuan)")

    years = sorted(df_long["year"].unique())
    year_min, year_max = int(min(years)), int(max(years))

    selected_year = st.slider("Pilih tahun acuan untuk peta dunia", year_min, year_max, year_max, key="map_year")
    df_up_to = df_long[df_long["year"] <= selected_year]

    st.caption(f"Catatan skala/unit: {scale_hint}")

    if df_up_to.empty:
        st.warning("Tidak ada data hingga tahun yang dipilih.")
    else:
        df_map = (
            df_up_to.sort_values(["country", "year"])
            .groupby("country", as_index=False)
            .tail(1)
        )

        try:
            fig = px.choropleth(
                df_map,
                locations="country",
                locationmode="country names",
                color="value",
                hover_name="country",
                hover_data={"year": True},
                color_continuous_scale="Viridis",
                title=f"{indicator_label} — nilai terbaru per negara (≤ {selected_year})",
                labels={"value": indicator_label, "year": "Tahun data"},
            )
            fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(
                "Gagal membuat peta dunia. Cek apakah nama negara di CSV sesuai standar country names Plotly.\n\n"
                f"Detail error: {e}"
            )

    st.subheader("📈 Time Series per Negara")
    country_list = sorted(df_long["country"].dropna().unique().tolist())
    if not country_list:
        st.error("Daftar negara kosong (kolom negara tidak terbaca dengan benar).")
        st.stop()

    default_country = "Indonesia" if "Indonesia" in country_list else country_list[0]
    selected_country = st.selectbox("Pilih negara untuk grafik time series", country_list, index=country_list.index(default_country))

    df_country = df_long[df_long["country"] == selected_country].sort_values("year").copy()

    if df_country.empty:
        st.write("Tidak ada data time series untuk negara ini.")
    else:
        fig_ts = px.line(df_country, x="year", y="value", markers=True, title=f"{indicator_label} — {selected_country}")
        fig_ts.update_layout(xaxis_title="Tahun", yaxis_title=indicator_label)
        st.plotly_chart(fig_ts, use_container_width=True)

        with st.expander("📄 Tabel time series", expanded=False):
            st.dataframe(df_country.reset_index(drop=True), use_container_width=True)

# =========================================================
# TAB 2 — ANALISIS & INTERPRETASI
# =========================================================
with tab_analysis:
    st.subheader("🔎 Analisis Statistik + Interpretasi Otomatis")

    n_country = df_long["country"].nunique()
    n_year = df_long["year"].nunique()
    st.write(f"- Negara: **{n_country:,}** | Tahun: **{df_long['year'].min()}–{df_long['year'].max()}** | Observasi: **{len(df_long):,}**")
    st.caption(f"Catatan skala/unit: {scale_hint}")

    tabs2 = st.tabs(["✅ Kualitas Data", "📊 Statistik Global", "🏆 Ranking Tahun", "🧭 Negara Terpilih"])

    # --- Kualitas Data
    with tabs2[0]:
        coverage = (
            df_long.groupby("country")["year"]
            .nunique()
            .reset_index(name="n_years_available")
            .sort_values("n_years_available", ascending=False)
        )
        coverage["coverage_pct"] = (coverage["n_years_available"] / n_year * 100).round(1)

        st.dataframe(coverage.head(60), use_container_width=True)
        fig_cov = px.histogram(coverage, x="n_years_available", title="Distribusi jumlah tahun tersedia per negara")
        st.plotly_chart(fig_cov, use_container_width=True)

    # --- Statistik Global
    with tabs2[1]:
        yearly_stats = (
            df_long.groupby("year")["value"]
            .agg(mean="mean", median="median", min="min", max="max", std="std", n="count")
            .reset_index()
            .sort_values("year")
        )

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Statistik keseluruhan**")
            st.dataframe(df_long["value"].describe().to_frame("overall"), use_container_width=True)
        with col2:
            st.write("**Statistik per tahun (tail)**")
            st.dataframe(yearly_stats.tail(15), use_container_width=True)

        fig_mean = px.line(yearly_stats, x="year", y="mean", markers=True, title="Rata-rata global per tahun")
        st.plotly_chart(fig_mean, use_container_width=True)

        fig_dist = px.histogram(df_long, x="value", nbins=60, title="Distribusi nilai (semua negara & tahun)")
        st.plotly_chart(fig_dist, use_container_width=True)

    # --- Ranking Tahun
    with tabs2[2]:
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
            top_n = st.number_input("Top N", 5, 50, 10, 1, key="topn")
            bottom_n = st.number_input("Bottom N", 5, 50, 10, 1, key="bottomn")

            df_top = df_rank.sort_values("value", ascending=False).head(int(top_n))
            df_bottom = df_rank.sort_values("value", ascending=True).head(int(bottom_n))

            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Top {int(top_n)} — {indicator_label} ({year_rank})**")
                st.dataframe(df_top.reset_index(drop=True), use_container_width=True)
            with c2:
                st.write(f"**Bottom {int(bottom_n)} — {indicator_label} ({year_rank})**")
                st.dataframe(df_bottom.reset_index(drop=True), use_container_width=True)

            df_bar = pd.concat([df_top.assign(group="Top"), df_bottom.assign(group="Bottom")], ignore_index=True)
            fig_bar = px.bar(df_bar, x="country", y="value", color="group", title=f"Top vs Bottom — {indicator_label} ({year_rank})")
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- Negara Terpilih (detail + interpretasi)
    with tabs2[3]:
        country_list = sorted(df_long["country"].dropna().unique().tolist())
        default_country = "Indonesia" if "Indonesia" in country_list else country_list[0]
        focus_country = st.selectbox("Pilih negara untuk interpretasi:", country_list, index=country_list.index(default_country), key="focus_country")

        df_c = df_long[df_long["country"] == focus_country].sort_values("year").copy()
        if df_c.empty:
            st.info("Tidak ada data untuk negara ini.")
        else:
            # metrik
            metrics = compute_country_metrics(df_c[["year", "value"]])

            # ranking pada latest_year
            rank_info = {"rank": None, "total": None, "percentile": None}
            latest_year = metrics.get("latest_year", None)
            if latest_year is not None:
                df_latest = df_long[df_long["year"] == latest_year].dropna(subset=["value"]).copy()
                if not df_latest.empty and focus_country in df_latest["country"].values:
                    df_latest = df_latest.sort_values("value", ascending=False).reset_index(drop=True)
                    rank = int(df_latest.index[df_latest["country"] == focus_country][0] + 1)
                    total = int(len(df_latest))
                    percentile = (1 - (rank - 1) / max(total - 1, 1)) * 100
                    rank_info = {"rank": rank, "total": total, "percentile": float(percentile)}

            # YoY & rolling
            df_c2 = df_c.copy()
            df_c2["yoy_change"] = df_c2["value"].diff(1)

            window = st.slider("Rolling window (tahun)", 2, 10, 3, key="roll_win_country")
            df_c2["rolling_mean"] = df_c2["value"].rolling(window=window, min_periods=1).mean()

            fig1 = px.line(df_c2, x="year", y="value", markers=True, title=f"{indicator_label} — {focus_country}")
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.line(df_c2, x="year", y="rolling_mean", markers=True, title=f"Rolling Mean ({window} tahun) — {focus_country}")
            st.plotly_chart(fig2, use_container_width=True)

            fig3 = px.line(df_c2, x="year", y="yoy_change", markers=True, title=f"Perubahan YoY (diff tahunan) — {focus_country}")
            st.plotly_chart(fig3, use_container_width=True)

            # outlier seri negara
            st.subheader("🚩 Outlier (dalam seri negara ini)")
            z_thr = st.slider("Ambang |Z|", 2.0, 5.0, 3.0, 0.1, key="zthr")
            s = df_c2["value"].dropna()
            if len(s) >= 3 and s.std(ddof=0) != 0:
                df_c2["z"] = (df_c2["value"] - s.mean()) / s.std(ddof=0)
                outliers = df_c2[df_c2["z"].abs() >= z_thr].copy()
                st.write(f"Outlier terdeteksi: **{len(outliers)}** baris (|Z| ≥ {z_thr})")
                st.dataframe(outliers[["year", "value", "z"]].sort_values("z", ascending=False), use_container_width=True)
            else:
                st.info("Outlier (Z-score) butuh minimal ~3 titik data dan standar deviasi tidak nol.")

            with st.expander("📄 Tabel negara (detail)", expanded=False):
                st.dataframe(df_c2.reset_index(drop=True), use_container_width=True)

            st.markdown("---")
            st.subheader("📝 Interpretasi Otomatis")
            st.markdown(interpret_country(indicator_label, focus_country, metrics, rank_info, scale_hint))

            st.subheader("🌐 Konteks Global (tahun terbaru negara)")
            if latest_year is not None:
                df_latest = df_long[df_long["year"] == latest_year].dropna(subset=["value"]).copy()
                if not df_latest.empty:
                    p10 = np.nanpercentile(df_latest["value"], 10)
                    p50 = np.nanpercentile(df_latest["value"], 50)
                    p90 = np.nanpercentile(df_latest["value"], 90)
                    st.write(
                        f"Pada tahun **{latest_year}**, distribusi global kira-kira:\n"
                        f"- P10 ≈ **{p10:,.4g}**, Median (P50) ≈ **{p50:,.4g}**, P90 ≈ **{p90:,.4g}**.\n"
                        f"\nBandingkan nilai {focus_country} (**{metrics.get('latest_value'):,.4g}**) "
                        f"untuk memahami apakah berada di level rendah/menengah/tinggi secara global."
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
        file_name=f"page6_poverty_{indicator_label.replace(' ', '_')}.csv",
        mime="text/csv",
    )
