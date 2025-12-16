@st.cache_data
def load_indicator(filename):
    path = os.path.join(DATA_DIR, filename)

    # Baca semua baris dulu
    raw = pd.read_csv(
        path,
        sep=None,
        engine="python",
        encoding="latin1",
        header=None,
        on_bad_lines="skip"
    )

    # Cari baris header yang mengandung "Country Name"
    header_row = None
    for i in range(len(raw)):
        if raw.iloc[i].astype(str).str.contains("Country Name").any():
            header_row = i
            break

    if header_row is None:
        st.error(f"❌ Header 'Country Name' tidak ditemukan di {filename}")
        st.stop()

    # Baca ulang dengan header yang benar
    df = pd.read_csv(
        path,
        sep=None,
        engine="python",
        encoding="latin1",
        header=header_row,
        on_bad_lines="skip"
    )

    df.columns = df.columns.str.strip()

    # Rename kolom utama
    df = df.rename(columns={
        "Country Name": "country",
        "Country Code": "code"
    })

    # Ambil kolom tahun saja
    year_cols = [c for c in df.columns if str(c).isdigit()]

    if len(year_cols) == 0:
        st.error(f"❌ Tidak ada kolom tahun di {filename}")
        st.stop()

    df = df[["country", "code"] + year_cols]

    # Wide → Long
    df = df.melt(
        id_vars=["country", "code"],
        var_name="year",
        value_name="value"
    )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df.dropna(subset=["year"])
