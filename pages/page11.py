import streamlit as st

st.title("📘 Analisis World Bank Group Annual Report 2025")
st.write("Berikut adalah analisis mendalam berdasarkan 10 isu utama dalam laporan World Bank 2025.")

# 1. Pertumbuhan Ekonomi & GDP
with st.expander("1. Pertumbuhan Ekonomi & GDP"):
    st.write("""
Pertumbuhan ekonomi harus diterjemahkan menjadi penciptaan lapangan kerja nyata.

**Poin penting:**
- Türkiye tumbuh rata-rata 5,4% (2002–2023).
- Maroko melipatgandakan GDP riil sejak 2000.
- Bhutan menargetkan GDP per kapita 2x pada 2029.
- Tantangan utama: *Middle-Income Trap* untuk negara berkembang.
    """)

# 2. Tenaga Kerja & Pengangguran
with st.expander("2. Tenaga Kerja & Pengangguran"):
    st.write("""
Akan ada **1,2 miliar** pemuda memasuki pasar kerja, tetapi hanya **400 juta** pekerjaan tersedia.

**Strategi Bank Dunia:**
1. Infrastruktur dasar  
2. Reformasi regulasi  
3. Mobilisasi modal swasta  

Masalah kritis terjadi di Sub-Sahara Afrika.
""")

# 3. Inflasi & Stabilitas Harga
with st.expander("3. Inflasi & Stabilitas Harga"):
    st.write("""
Fokus pada stabilitas makro:
- Sri Lanka memulihkan stabilitas setelah krisis energi.
- Serbia melakukan konsolidasi fiskal.
- Türkiye memasuki fase pelonggaran setelah stabilisasi moneter.
""")

# 4. Perdagangan Internasional
with st.expander("4. Perdagangan Internasional"):
    st.write("""
Contoh dukungan World Bank:
- Fiji: akses *trade finance* untuk negara kepulauan.
- Maroko: perluasan pelabuhan Tanger Med.
- Turki: dukungan pembiayaan ekspor hijau.
""")

# 5. Investasi & Modal (FDI)
with st.expander("5. Investasi (FDI & Mobilisasi Modal)"):
    st.write("""
Pendekatan baru: mobilisasi modal swasta.
- Target guarantee platform: $20 miliar/tahun (2030).
- IFC menggunakan blended finance.
- Contoh: bond Rwanda, obligasi Amazon Brasil.
""")

# 6. Kemiskinan & Ketimpangan
with st.expander("6. Kemiskinan & Ketimpangan"):
    st.write("""
Contoh negara:
- Madagaskar: 70% penduduk < $3/hari.
- Turki: kemiskinan turun dari >20% → 7,6%.
- Target 2030: 80 juta perempuan dapat akses modal.
""")

# 7. Populasi & Demografi
with st.expander("7. Populasi & Demografi"):
    st.write("""
Youth bulge menjadi tantangan global:
- Bangladesh: usia kerja 50% populasi (2028)
- Afrika: pertumbuhan populasi tercepat
Urbanisasi cepat membutuhkan investasi transportasi besar.
""")

# 8. Pendidikan
with st.expander("8. Pendidikan"):
    st.write("""
Fokus pada skills mismatch.
Program:
- African Centers of Excellence (STEM)
- Debt-for-development (Côte d'Ivoire)
- Pelatihan digital Karibia
""")

# 9. Kesehatan
with st.expander("9. Kesehatan"):
    st.write("""
Target: 1,5 miliar orang mendapat layanan kesehatan berkualitas (2030).

Contoh proyek besar:
- Indonesia: $4 miliar untuk puskesmas & RS.
- Nigeria: penurunan mortalitas balita.
""")

# 10. Energi & Lingkungan
with st.expander("10. Energi & Lingkungan"):
    st.write("""
48% pendanaan World Bank memiliki co-benefits iklim.

Program utama:
- Mission 300: listrik untuk 300 juta orang Afrika.
- Investasi energi surya Tunisia & Uzbekistan.
- Blue loan & obligasi biodiversitas.
""")

st.success("Halaman analisis berhasil ditampilkan.")
