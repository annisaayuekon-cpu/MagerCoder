# pages/home.py
import streamlit as st
import pandas as pd
import wb_helper as wb  # pastikan wb_helper.py ada di root project

st.set_page_config(layout="wide")

# ---------- Controls (pilihan negara & tahun) ----------
st.markdown("## 🌍 Dashboard Ekonomi (Ringkasan)")
st.write("Ringkasan cepat untuk beberapa indikator utama. Pilih negara dan rentang tahun untuk memperbarui tampilan.")

