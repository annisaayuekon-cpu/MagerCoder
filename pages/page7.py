import streamlit as st
import pandas as pd
import os
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🌍 Populasi, Urbanisasi, Fertilitas & Harapan Hidup — Peta Dunia + Time Series + Analisis")
st.write(
    "Halaman ini menampilkan indikator **demografi global** seperti *Population, Urban Population, Fertility Rate & Life Expectancy* "
    "berdasarkan file CSV yang berada dalam folder `data/`, lengkap dengan analisis statistik dan interpretasi otomatis."
)

# -----------------------------
# Folder dataset
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Total Population": "7.1. TOTAL POPULATION.csv",
    "Urban Population (%)": "7.2. URBAN POPULATION.csv",
    "Fertility Rate": "7.3. FERTILITY RATE.csv",
    "Life Expectancy at Birth": "7.4. LIFE EXPECTANCY AT BIRTH.csv",
}

# -----------------------------
# Loader CSV fleksibel
# -----------------------------
@st.cache_data
def load_csv_clean(path: str) -> pd.DataFrame:
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    return pd.read_csv(path, engine="python", on_bad_lines="skip")


def guess_unit_demography(indicator: str, series: pd.Series) -> str:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return "Unit tidak terdeteksi (data kosong)."

    mx = float(np.nanmax(s.values))
    med = float(np.nanmedian(s.values))

    if indicator == "Total Population":
        return "Umumnya **jumlah penduduk (jiwa)**. Nilai besar berarti populasi lebih besar."
    if indicator == "Urban Population (%)":
        return "Umumnya **persentase (%)** penduduk yang tinggal di kawasan perkotaan."
    if indicator == "Fertility Rate":
        return "Umumnya **kelahiran per perempuan** (children per woman)."
    if indicator == "Life Expectancy at Birth":
        return "Umumnya **tahun (years)** harapan hidup saat lahir."

    # fallback heuristik
    if mx <= 150 and med <= 80:
        return "Nilai tampak seperti **persentase/indeks** (perkiraan)."
    return "Skala/unit bervariasi (tidak jelas) — cek metadata file jika ada."


def compute_country_metrics(df_country: pd.DataFrame, indicator: str) -> dict:
    d = df_country.dropna(subset=["year", "value"]).sort_values("year").copy()
    if d.empty:
        return {}

    out = {}
    out["n_obs"] = len(d)
    out["year_min"] = int(d["year"].min())
    out["year_max"] = int(d["year"].max())

    out["latest_year"] = int(d.iloc[-1]["year"])
    out["latest_value"] = float(d.iloc[-1]["value"])

    if len(d) >= 2:
        out["prev_year"] = int(d.iloc[-2]["year"])
        out["prev_value"] = float(d.iloc[-2]["value"])
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

    # slope tren linear
    if len(d) >= 2:
        x = d["year"].values.astype(float)
        y = d["value"].values.astype(float)
        try:
            out["slope_per_year"] = float(np.polyfit(x, y, 1)[0])
        except Exception:
            out["slope_per_year"] = np.nan
    else:
        out["slope_per_year"] = np.nan

    # CAGR (indikatif) - aman untuk populasi (positif); untuk indikator lain juga bisa sebagai ringkasan
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


def interpret_demography(indicator: str, country: str, metrics: dict, unit_hint: str, rank_info: dict) -> str:
    if not metrics:
        return "Tidak cukup data untuk membuat interpretasi."

    latest_year = metrics["latest_year"]
    latest_value = metrics["latest_value"]
    yoy_abs = metrics.get("yoy_abs", np.nan)
    yoy_pct = metrics.get("yoy_pct", np.nan)
    slope = metrics.get("slope_per_year", np.nan)
    std_all = metrics.get("std_all", np.nan)
    mean_5y = metrics.get("mean_5y", np.nan)
    mean_10y = metrics.get("mean_10y", np.nan)
    cagr = metrics.get("cagr_pct", np.nan)

    # interpretasi arah indikator (good/bad)
    meaning = {
        "Total Population": "menggambarkan **jumlah penduduk**. Kenaikan biasanya berarti basis tenaga kerja & pasar domestik membesar, namun juga menambah tekanan layanan publik jika tidak diimbangi produktivitas.",
        "Urban Population (%)": "menggambarkan **tingkat urbanisasi**. Kenaikan biasanya terkait transformasi struktural & konsentrasi aktivitas ekonomi, namun dapat meningkatkan risiko kepadatan, kebutuhan infrastruktur, dan ketimpangan kota-desa.",
        "Fertility Rate": "menggambarkan **rata-rata jumlah anak per perempuan**. Penurunan sering berkaitan dengan transisi demografi, pendidikan, dan urbanisasi; berdampak pada struktur umur dan bonus demografi.",
        "Life Expectancy at Birth": "menggambarkan **kualitas kesehatan & harapan hidup**. Kenaikan mengindikasikan perbaikan kesehatan, gizi, dan layanan medis."
    }.get(indicator, "menggambarkan dinamika demografi.")

    # tren
    if pd.isna(slope) or abs(slope) < 1e-9:
        trend_label = "cenderung **stabil**"
    else:
        trend_label = "cenderung **meningkat**" if slope > 0 else "cenderung **menurun**"

    # YoY
    yoy_text = "Tidak ada pembanding tahun sebelumnya (data hanya 1 titik)."
    if pd.notna(yoy_abs):
        direction = "naik" if yoy_abs > 0 else ("turun" if yoy_abs < 0 else "tidak berubah")
        if pd.notna(yoy_pct):
            yoy_text = f"Perubahan terakhir **{direction}** sebesar **{yoy_abs:,.4g}** (≈ **{yoy_pct:,.2f}%**) dibanding tahun sebelumnya."
        else:
            yoy_text = f"Perubahan terakhir **{direction}** sebesar **{yoy_abs:,.4g}** dibanding tahun sebelumnya."

    # ringkasan historis
    parts = []
    if pd.notna(mean_5y): parts.append(f"rata-rata 5 tahun terakhir ≈ **{mean_5y:,.4g}**")
    if pd.notna(mean_10y): parts.append(f"rata-rata 10 tahun terakhir ≈ **{mean_10y:,.4g}**")
    avg_text = "; ".join(parts) + "." if parts else "Rata-rata 5/10 tahun tidak cukup data."

    # ranking
    rank_text = ""
    if rank_info.get("rank") is not None:
        rank_text = f"Posisi relatif pada tahun {latest_year}: **#{rank_info['rank']} dari {rank_info['total']} negara** (≈ persentil **{rank_info['percentile']:.1f}**)."

    # volatilitas
    vol_text = f"Volatilitas historis (std) ≈ **{std_all:,.4g}**." if pd.notna(std_all) else "Volatilitas tidak dapat dihitung (data terlalu sedikit)."

    # CAGR
    cagr_text = f"Pertumbuhan rata-rata jangka panjang (CAGR, indikatif): **{cagr:,.2f}% per tahun**." if pd.notna(cagr) else "CAGR tidak ditampilkan (nilai awal/akhir tidak cocok)."

    md = f"""
**Interpretasi otomatis — {country} ({indicator})**

- **Makna indikator**: {meaning}  
- **Nilai terbaru**: tahun **{latest_year}** = **{latest_value:,.4g}**  
- **Dinamika jangka pendek (YoY)**: {yoy_text}  
- **Arah tren jangka panjang**: {trend_label} (slope ≈ **{slope:,.4g} per tahun**).  
- **Ringkasan historis**: {avg_text}  
- **Stabilitas/variasi**: {vol_text}  
- **Posisi relatif global**: {rank_text}  
- **Pertumbuhan jangka panjang**: {cagr_text}  
- **Catatan unit**: {unit_hint}

**Catatan analitis:**
- Untuk *Urban Population (%)*, kenaikan cepat dapat menandakan migrasi desa-kota & perubahan struktur ekonomi.  
- Untuk *Fertility Rate*, tren turun biasanya selaras dengan transisi demografi dan dapat memengaruhi struktur umur ke depan.  
- Untuk *Life Expectancy*, tren naik kuat sering mencerminkan perbaikan kesehatan, namun juga meningkatkan kebutuhan layanan lansia.
"""
    return md.strip()


# -----------------------------
# Cek file tersedia?
# -----------------------------
available_files = [
    label for label, fname in FILES.items()
    if os.path.exists(os.path.join(DATA_DIR, fname))
]

if not available_files:
    st.error(f"Tidak ada file Page 7 ditemukan dalam folder `{DATA_DIR}/`.")
    st.stop()

# -----------------------------
# Pilih indikator dataset
# -----------------------------
indicator = st.selectbox("📌 Pilih indikator demografi :", available_files)
file_path = os.path.join(DATA_DIR, FILES[indicator])

try:
    df = load_csv_clean(file_path)
except Exception as e:
    st.error(f"❌ File gagal dibaca: `{os.path.basename(file_path)}`\n\n{e}")
    st.stop()

with st.expander("📄 Preview Data Mentah (klik untuk buka)", expanded=True):
    st.dataframe(df.head(20), use_container_width=True)

# -----------------------------
# Identifikasi Tahun & Negara
# -----------------------------
cols = [str(c) for c in df.columns]
years = [c for c in cols if c.isdigit() and len(c) == 4]

if not years:
    st.error("Tidak ditemukan kolom tahun (contoh 1990, 2005). Periksa format CSV.")
    st.stop()

country_col = next((c for c in df.columns if c in ["Country Name", "Country", "Negara", "Entity", "country"]), df.columns[0])

df_long = df.melt(id_vars=[country_col], value_vars=years, var_name="year", value_name="value")
df_long = df_long.rename(columns={country_col: "country"})

# rapikan tipe
df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
df_long = df_long.dropna(subset=["country", "year", "value"])
df_long["year"] = df_long["year"].astype(int)

if df_long.empty:
    st.error("Data kosong setelah transformasi long — kemungkinan format tidak sesuai.")
    st.stop()

unit_hint = guess_unit_demography(indicator, df_long["value"])

# -----------------------------
# Tabs utama
# -----------------------------
tab_viz, tab_analysis, tab_download = st.tabs(["🗺️ Visualisasi", "📊 Analisis & Interpretasi", "📥 Download"])

# =========================================================
# TAB 1 — VISUALISASI
# =========================================================
with tab_viz:
    st.subheader("🌍 World Map View")
    years_sorted = sorted(df_long["year"].unique())
    year_select = st.slider("Pilih tahun untuk peta", int(min(years_sorted)), int(max(years_sorted)), int(max(years_sorted)), key="map_year")

    df_map = df_long[df_long["year"] == year_select]
    st.caption(f"Catatan unit: {unit_hint}")

    try:
        fig = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            color_continuous_scale="Turbo",
            hover_name="country",
            title=f"{indicator} — {year_select}",
        )
        fig.update_layout(margin={"r": 0, "l": 0, "t": 40, "b": 0})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("⚠ Peta gagal ditampilkan — cek format nama negara.\n" + str(e))

    st.subheader("📈 Grafik Time Series (Multi Negara)")
    countries = sorted(df_long["country"].dropna().unique().tolist())
    default = "Indonesia" if "Indonesia" in countries else countries[0]

    selected = st.multiselect("Pilih negara:", countries, default=[default], key="ts_countries")
    df_ts = df_long[df_long["country"].isin(selected)].sort_values(["country", "year"])

    if df_ts.empty:
        st.warning("Tidak ada data untuk negara tersebut.")
    else:
        fig_ts = px.line(
            df_ts,
            x="year",
            y="value",
            color="country",
            markers=True,
            labels={"value": indicator, "year": "Tahun", "country": "Negara"},
            title=f"Time Series — {indicator}"
        )
        fig_ts.update_layout(xaxis=dict(dtick=5), margin={"t": 40, "l": 0, "r": 0, "b": 0})
        st.plotly_chart(fig_ts, use_container_width=True)

        with st.expander("📄 Tabel time series (long)", expanded=False):
            st.dataframe(df_ts.reset_index(drop=True), use_container_width=True)

# =========================================================
# TAB 2 — ANALISIS & INTERPRETASI
# =========================================================
with tab_analysis:
    st.subheader("🔎 Analisis Statistik Global + Interpretasi Otomatis")

    n_country = df_long["country"].nunique()
    n_year = df_long["year"].nunique()
    st.write(f"- Negara: **{n_country:,}** | Tahun: **{df_long['year'].min()}–{df_long['year'].max()}** | Observasi: **{len(df_long):,}**")
    st.caption(f"Catatan unit: {unit_hint}")

    tabs2 = st.tabs(["✅ Kualitas Data", "📊 Statistik Global", "🏆 Ranking Tahun", "🧭 Negara Terpilih"])

    # Kualitas data
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

    # Statistik global
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

    # Ranking tahun
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
                st.write(f"**Top {int(top_n)} — {indicator} ({year_rank})**")
                st.dataframe(df_top.reset_index(drop=True), use_container_width=True)
            with c2:
                st.write(f"**Bottom {int(bottom_n)} — {indicator} ({year_rank})**")
                st.dataframe(df_bottom.reset_index(drop=True), use_container_width=True)

            df_bar = pd.concat([df_top.assign(group="Top"), df_bottom.assign(group="Bottom")], ignore_index=True)
            fig_bar = px.bar(df_bar, x="country", y="value", color="group", title=f"Top vs Bottom — {indicator} ({year_rank})")
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)

    # Negara terpilih
    with tabs2[3]:
        country_list = sorted(df_long["country"].dropna().unique().tolist())
        default_country = "Indonesia" if "Indonesia" in country_list else country_list[0]
        focus_country = st.selectbox("Pilih negara untuk interpretasi:", country_list, index=country_list.index(default_country), key="focus_country")

        df_c = df_long[df_long["country"] == focus_country].sort_values("year").copy()
        if df_c.empty:
            st.info("Tidak ada data untuk negara ini.")
        else:
            metrics = compute_country_metrics(df_c[["year", "value"]], indicator)

            # ranking di tahun terbaru negara
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

            # detail: yoy + rolling
            df_c2 = df_c.copy()
            df_c2["yoy_change"] = df_c2["value"].diff(1)

            window = st.slider("Rolling window (tahun)", 2, 10, 3, key="roll_win_country")
            df_c2["rolling_mean"] = df_c2["value"].rolling(window=window, min_periods=1).mean()

            fig1 = px.line(df_c2, x="year", y="value", markers=True, title=f"{indicator} — {focus_country}")
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.line(df_c2, x="year", y="rolling_mean", markers=True, title=f"Rolling Mean ({window} tahun) — {focus_country}")
            st.plotly_chart(fig2, use_container_width=True)

            fig3 = px.line(df_c2, x="year", y="yoy_change", markers=True, title=f"Perubahan YoY (diff tahunan) — {focus_country}")
            st.plotly_chart(fig3, use_container_width=True)

            # outlier
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
            st.markdown(interpret_demography(indicator, focus_country, metrics, unit_hint, rank_info))

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
    st.subheader("📥 Download Dataset (long format)")
    st.dataframe(df_long.reset_index(drop=True), use_container_width=True)

    csv = df_long.to_csv(index=False)
    st.download_button(
        "⬇ Download CSV",
        csv,
        file_name=f"page7_{indicator.replace(' ', '_')}.csv",
        mime="text/csv",
    )
