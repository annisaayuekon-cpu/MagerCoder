






# app.py
import streamlit as st

st.set_page_config(
    page_title="Dashboard Ekonomi Dunia – Kelompok",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Dashboard Ekonomi Dunia – Kelompok")

st.markdown("""
Selamat datang di aplikasi **Dashboard Ekonomi** berbasis data **World Bank**.  
Gunakan menu **Pages** di sidebar untuk melihat data ekonomi per kategori.
""")

st.header("📌 Daftar Halaman (Page 1–10)")
st.markdown("""
### 1️⃣ 📈 Pertumbuhan Ekonomi & GDP  
### 2️⃣ 💰 GDP Per Kapita & Struktur Ekonomi  
### 3️⃣ 🔥 Inflasi & Harga Konsumen  
### 4️⃣ 👷 Pengangguran  
### 5️⃣ 🌐 Perdagangan Internasional  
### 6️⃣ 💼 Investasi (FDI & Kapital)  
### 7️⃣ 📉 Kemiskinan & Ketimpangan (GINI)  
### 8️⃣ 👥 Populasi & Demografi  
### 9️⃣ 🏥 Kesehatan & Pendidikan  
### 🔟 🌱 Energi & Lingkungan  
""")

st.header("👥 Anggota Kelompok")
st.markdown("""
- Annisa Ayu   
- Nama Anggota 2  
- Nama Anggota 3  
- Nama Anggota 4  
""")

st.info("Pilih halaman di sidebar untuk melihat data World Bank.")
