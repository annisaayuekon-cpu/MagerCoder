import streamlit as st
import pandas as pd
import altair as alt

# -------------------------------------------------------------------
# Halaman 3 – Inflasi dan Indeks Harga Konsumen (IHK/CPI)
# -------------------------------------------------------------------

st.set_page_config(page_title="Inflasi & IHK", layout="wide")
st.title("📈 Analisis Inflasi dan Indeks Harga Konsumen (IHK/CPI)")

st.write(
    """
    Halaman ini menampilkan visualisasi data **inflasi** dan **indeks harga konsumen (IHK/CPI)**.
    Silakan upload data dalam bentuk file **CSV** atau **Excel**.
    """
)

# -------------------------------------------------------------------
# Fungsi bantu untuk membaca file
# -------------------------------------------------------------------
def load_file(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile | None):
    """Membaca file CSV atau Excel menjadi DataFrame pandas."""
    if uploaded_file is None:
        return None

    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    else:
        st.warning("Format file harus .csv atau .xlsx")
        return None


# -------------------------------------------------------------------
# Upload data
# -------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📂 Upload Data Inflasi")
    inflasi_file = st.file_uploader(
        "Pilih file inflasi (CSV/Excel)", type=["csv", "xlsx"], key="inflasi_file"
    )

with col2:
    st.subheader("📂 Upload Data IHK/CPI")
    cpi_file = st.file_uploader(
        "Pilih file IHK/CPI (CSV/Excel)", type=["csv", "xlsx"], key="cpi_file"
    )

df_inflasi = load_file(inflasi_file)
df_cpi = load_file(cpi_file)

# -------------------------------------------------------------------
# Tabel & grafik inflasi
# -------------------------------------------------------------------
if df_inflasi is not None:
    st.markdown("---")
    st.subheader("📊 Tabel Data Inflasi")
    st.dataframe(df_inflasi, use_container_width=True)

    # Pilih kolom untuk grafik
    st.subheader("📉 Grafik Inflasi")
    cols = df_inflasi.columns.tolist()
    num_cols = df_inflasi.select_dtypes("number").columns.tolist()

    if len(num_cols) >= 1 and len(cols) >= 1:
        x_col = st.selectbox("Pilih kolom sumbu X (waktu/tahun/bulan)", cols, index=0)
        y_col = st.selectbox("Pilih kolom nilai inflasi (Y)", num_cols, index=0)

        chart_inflasi = (
            alt.Chart(df_inflasi)
            .mark_line(point=True)
            .encode(
                x=alt.X(x_col, title=x_col),
                y=alt.Y(y_col, title=y_col),
                tooltip=cols,
            )
            .properties(height=400)
        )
        st.altair_chart(chart_inflasi, use_container_width=True)
    else:
        st.info(
            "Pastikan data inflasi memiliki minimal satu kolom numerik untuk dibuat grafik."
        )

# -------------------------------------------------------------------
# Tabel & grafik IHK / CPI
# -------------------------------------------------------------------
if df_cpi is not None:
    st.markdown("---")
    st.subheader("📊 Tabel Data IHK/CPI")
    st.dataframe(df_cpi, use_container_width=True)

    st.subheader("📉 Grafik IHK/CPI")
    cols_cpi = df_cpi.columns.tolist()
    num_cols_cpi = df_cpi.select_dtypes("number").columns.tolist()

    if len(num_cols_cpi) >= 1 and len(cols_cpi) >= 1:
        x_col_cpi = st.selectbox(
            "Pilih kolom sumbu X (waktu/tahun/bulan) - CPI", cols_cpi, index=0
        )
        y_col_cpi = st.selectbox(
            "Pilih kolom nilai IHK/CPI (Y)", num_cols_cpi, index=0
        )

        chart_cpi = (
            alt.Chart(df_cpi)
            .mark_line(point=True)
            .encode(
                x=alt.X(x_col_cpi, title=x_col_cpi),
                y=alt.Y(y_col_cpi, title=y_col_cpi),
                tooltip=cols_cpi,
            )
            .properties(height=400)
        )
        st.altair_chart(chart_cpi, use_container_width=True)
    else:
        st.info(
            "Pastikan data IHK/CPI memiliki minimal satu kolom numerik untuk dibuat grafik."
        )

# -------------------------------------------------------------------
# Perbandingan Inflasi vs IHK (jika struktur datanya memungkinkan)
# -------------------------------------------------------------------
if df_inflasi is not None and df_cpi is not None:
    st.markdown("---")
    st.subheader("🔍 Perbandingan Inflasi dan IHK/CPI (opsional)")

    try:
        # Coba gabung berdasarkan index (misal sama-sama urut per periode)
        df_compare = pd.DataFrame()
        df_compare["Inflasi"] = df_inflasi.select_dtypes("number").iloc[:, 0]
        df_compare["CPI"] = df_cpi.select_dtypes("number").iloc[:, 0]

        df_compare = df_compare.dropna()

        st.dataframe(df_compare, use_container_width=True)

        chart_compare = (
            alt.Chart(df_compare.reset_index().rename(columns={"index": "Periode"}))
            .transform_fold(["Inflasi", "CPI"], as_=["Jenis", "Nilai"])
            .mark_line(point=True)
            .encode(
                x="Periode:O",
                y="Nilai:Q",
                color="Jenis:N",
                tooltip=["Periode", "Jenis", "Nilai"],
            )
            .properties(height=400)
        )
        st.altair_chart(chart_compare, use_container_width=True)
    except Exception:
        st.info(
            "Struktur data inflasi dan IHK/CPI tidak cocok untuk dibuat grafik perbandingan otomatis. "
            "Pastikan urutan periode dan jumlah barisnya sebanding."
        )
