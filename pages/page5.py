# pages/page5.py

import streamlit as st
import pandas as pd
import os

st.title("Page 5 – Investment Indicators")

# ==========================
# KONFIGURASI FILE DATA
# ==========================
DATA_DIR = "data"  # ganti kalau folder datamu beda

DATA_FILES = {
    "Foreign direct investment (FDI)": "5.1 Foreign Direct Investment (FDI).csv",
    "Gross capital formation": "5.2 Gross capital formation.csv",
}


@st.cache_data
def load_and_transform(csv_name: str) -> pd.DataFrame:
    """
    Baca CSV, ubah ke long format (Year, Value) untuk tiap negara.
    Dibuat lebih toleran terhadap format CSV yang berantakan.
    """
    file_path = os.path.join(DATA_DIR, csv_name)

    # 1) Coba baca standar
    try:
        df_raw = pd.read_csv(file_path)
    except pd.errors.ParserError:
        # 2) Coba baca dengan delimiter ';'
        try:
            df_raw = pd.read_csv(file_path, sep=";")
        except pd.errors.ParserError:
            # 3) Last resort: pakai engine python & skip baris bermasalah
            df_raw = pd.read_csv(
                file_path,
                engine="python",
                on_bad_lines="skip"
            )

    # cari kolom tahun (nama kolom berupa angka, misal 1960, 1961, dst.)
    year_cols = [c for c in df_raw.columns if str(c).isdigit()]

    if not year_cols:
        st.error(
            "Tidak menemukan kolom tahun di file: "
            f"{csv_name}. Cek lagi apakah header tahunnya berupa 1960, 1961, dst."
        )
        return pd.DataFrame()

    # wide → long
    df = df_raw.melt(
        id_vars=[col for col in df_raw.columns if col not in year_cols],
        value_vars=year_cols,
        var_name="Year",
        value_name="Value",
    )

    # rapikan tipe data
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    # buang baris kosong
    df = df.dropna(subset=["Year", "Value"])

    # standarisasi nama kolom negara kalau ada
    if "Country Name" not in df.columns:
        possible_country_cols = [
            c for c in df.columns
            if "country" in c.lower() and "name" in c.lower()
        ]
        if possible_country_cols:
            df = df.rename(columns={possible_country_cols[0]: "Country Name"})
        else:
            non_year_cols = [c for c in df.columns if c not in ["Year", "Value"]]
            if non_year_cols:
                df = df.rename(columns={non_year_cols[0]: "Country Name"})

    return df


def main():
    if not DATA_FILES:
        st.warning(
            "Belum ada file yang dikonfigurasi untuk Page 5.\n\n"
            "Silakan isi dictionary DATA_FILES di atas."
        )
        return

    # pilih indikator
    indikator = st.selectbox(
        "Pilih indikator",
        list(DATA_FILES.keys()),
        index=0,
    )

    csv_name = DATA_FILES[indikator]
    df = load_and_transform(csv_name)

    if df.empty:
        st.info("Data untuk indikator ini belum bisa ditampilkan.")
        return

    # pilih negara
    countries = sorted(df["Country Name"].dropna().unique())
    negara = st.selectbox("Pilih negara", countries)

    df_country = df[df["Country Name"] == negara].sort_values("Year")

    st.subheader(f"Time Series {indikator} – {negara}")
    st.line_chart(
        df_country.set_index("Year")["Value"],
        height=400,
    )

    # ringkasan angka terbaru
    latest_year = int(df_country["Year"].max())
    latest_value = df_country[df_country["Year"] == latest_year]["Value"].iloc[0]

    st.caption(
        f"Nilai terbaru ({latest_year}) untuk {indikator} di {negara}: "
        f"**{latest_value:,.2f}**"
    )

    with st.expander("Lihat cuplikan data mentah"):
        st.dataframe(df_country.reset_index(drop=True))


if __name__ == "__main__":
    main()
