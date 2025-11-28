# ==============================
# 📌 Step 1 — Import Library
# ==============================
import pandas as pd
import matplotlib.pyplot as plt

# (Wajib jika ingin tampil interaktif di notebook)
%matplotlib inline


# ==============================
# 📌 Step 2 — Load Dataset
# ==============================
inflasi = pd.read_excel("/mnt/data/3.1 Inflation, consumer prices (%).xls")
konsumsi = pd.read_excel("/mnt/data/3.2. CONSUMER EXPENDITURE.xls")

print("Preview Inflasi:")
display(inflasi.head())

print("\nPreview Consumer Expenditure:")
display(konsumsi.head())


# ==============================
# 📌 Step 3 — Deteksi Kolom Tahun
# ==============================
tahun_inflasi = [c for c in inflasi.columns if str(c).isdigit()]
tahun_konsumsi = [c for c in konsumsi.columns if str(c).isdigit()]

print("\nKolom tahun inflasi:", tahun_inflasi[:10])
print("Kolom tahun konsumsi:", tahun_konsumsi[:10])


# ==============================
# 📌 Step 4 — Pilih 1 negara untuk analisis
# ==============================
negara = inflasi.iloc[0,0]  # ganti ke negara lain jika ingin manual
print(f"\nNegara otomatis terbaca: {negara}")

df_i = inflasi[inflasi[inflasi.columns[0]] == negara].melt(id_vars=inflasi.columns[0], value_vars=tahun_inflasi,
                                                           var_name="tahun", value_name="inflasi")

df_k = konsumsi[konsumsi[konsumsi.columns[0]] == negara].melt(id_vars=konsumsi.columns[0], value_vars=tahun_konsumsi,
                                                             var_name="tahun", value_name="belanja_konsumen")

df_i["tahun"] = df_i["tahun"].astype(int)
df_k["tahun"] = df_k["tahun"].astype(int)


# ==============================
# 📌 Step 5 — Merge dua variabel
# ==============================
gabungan = pd.merge(df_i, df_k, on=["tahun"], how="inner")
display(gabungan.head())


# ==============================
# 📊 VISUALISASI 1:
#  TIME SERIES INFLASI vs CONSUMER EXPENDITURE
# ==============================
plt.figure(figsize=(10,5))
plt.plot(gabungan["tahun"], gabungan["inflasi"], label="Inflasi (%)")
plt.plot(gabungan["tahun"], gabungan["belanja_konsumen"], label="Belanja Konsumen")
plt.title(f"Inflasi vs Belanja Konsumen — {negara}")
plt.xlabel("Tahun")
plt.ylabel("Nilai (%) / USD")
plt.legend()
plt.grid()
plt.show()


# ==============================
# 📊 VISUALISASI 2:
#  SCATTER HUBUNGAN INFLASI x PENGELUARAN KONSUMEN
# ==============================
plt.figure(figsize=(6,5))
plt.scatter(gabungan["inflasi"], gabungan["belanja_konsumen"])
plt.title(f"Korelasi Inflasi & Pengeluaran Konsumen — {negara}")
plt.xlabel("Inflasi (%)")
plt.ylabel("Belanja Konsumen")
plt.grid()
plt.show()

