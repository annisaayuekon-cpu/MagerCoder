import streamlit as st

# =========================================================
# STYLE (biru-abu, konsisten dengan feel dashboard kamu)
# =========================================================
st.markdown(
    """
<style>
/* layout helpers */
.block-title {font-size: 34px; font-weight: 800; margin: 0 0 6px 0;}
.block-sub {font-size: 16px; opacity: 0.85; margin: 0 0 10px 0;}
.small-muted {font-size: 13px; opacity: 0.7;}

/* card styles */
.card {
  background: rgba(2, 132, 199, 0.07);
  border: 1px solid rgba(2, 132, 199, 0.18);
  border-radius: 18px;
  padding: 16px 16px 14px 16px;
  margin-bottom: 12px;
}
.card2 {
  background: rgba(15, 23, 42, 0.04);
  border: 1px solid rgba(15, 23, 42, 0.10);
  border-radius: 18px;
  padding: 16px 16px 14px 16px;
  margin-bottom: 12px;
}
.badge {
  display:inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(30, 64, 175, 0.10);
  border: 1px solid rgba(30, 64, 175, 0.16);
  font-size: 12px;
  font-weight: 700;
  opacity: 0.95;
}
.hr-soft {height:1px; background: rgba(15, 23, 42, 0.10); border:0; margin: 14px 0;}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# HEADER
# =========================================================
logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/OECD_logo.svg/1024px-OECD_logo.svg.png"

c1, c2 = st.columns([1.2, 5])
with c1:
    st.image(logo_url, use_container_width=True)
with c2:
    st.markdown('<div class="block-title">Navigasi Aksesi OECD</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="block-sub">Halaman ini memakai <b>report</b> dan <b>outlook</b> OECD untuk menyikapi angka World Bank di dashboard: angka diperlakukan sebagai sinyal, lalu dibaca dengan konteks struktur ekonomi, institusi, dan risiko kebijakan.</div>',
        unsafe_allow_html=True,
    )

st.info(
    "Definisi pemakaian sumber: report/outlook OECD di bawah dipakai sebagai rujukan untuk membaca pola, membangun pembanding lintas negara, dan menilai implikasi kebijakan dari indikator World Bank. Fokusnya interpretasi, bukan klaim kausal."
)

# =========================================================
# CATATAN DATA (teks kamu, ditaruh di tempat yang jelas)
# =========================================================
with st.expander("Catatan data: OECD dan World Bank", expanded=False):
    st.markdown(
        """
World Development Indicators milik World Bank dikompilasi dari berbagai sumber internasional, dan sebagian indikatornya juga bersumber dari statistik OECD.
Implikasinya, indikator Indonesia yang biasa dipakai lewat World Bank punya irisan yang kuat dengan ekosistem indikator OECD, sehingga keterbandingan lintas negara lebih mudah dibangun.

OECD juga menjalankan Data Collection Programme yang mengumpulkan data dari produsen statistik resmi negara melalui kuesioner, web queries, platform online, dan SDMX.
Dalam konteks aksesi, kanal pengumpulan data ini membuat profil data Indonesia di OECD berpotensi makin kaya karena ada kebutuhan pelaporan yang lebih terstruktur dan periodik.

OECD menyusun publikasi berbasis evidence dan peer review, termasuk OECD Economic Surveys untuk Indonesia, yang menunjukkan OECD memang melakukan pengumpulan, konsolidasi, dan validasi data untuk analisis kebijakan.
"""
    )

st.markdown('<hr class="hr-soft">', unsafe_allow_html=True)

# =========================================================
# ALIGNMENT + ROADMAP (ringkas, tetap “masuk” ke dashboard)
# =========================================================
st.markdown("## Alignment Indonesia ke OECD dan Roadmap")
a1, a2, a3 = st.columns(3)

with a1:
    st.markdown(
        """
<div class="card">
<span class="badge">Rules & guidelines</span>
<h4 style="margin:10px 0 6px 0;">Roadmap aksesi</h4>
<div class="small-muted">
Roadmap menetapkan urutan proses, ruang lingkup review teknis, dan cara kerja evaluasi alignment. Ini dipakai sebagai “kerangka baca” saat kamu membandingkan indikator Indonesia dengan negara OECD.
</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.link_button("Buka Roadmap (PDF)", "https://one.oecd.org/document/C(2024)66/FINAL/en/pdf")

with a2:
    st.markdown(
        """
<div class="card">
<span class="badge">Peer review</span>
<h4 style="margin:10px 0 6px 0;">Komite teknis dan metode OECD</h4>
<div class="small-muted">
Aksesi dijalankan lewat review berbasis standar OECD dan praktik peer review. Artinya, data dan kebijakan dibaca sebagai paket: konsistensi aturan main, kapasitas institusi, dan hasil yang terukur.
</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.link_button("Accession process (OECD)", "https://www.oecd.org/en/about/legal/oecd-accession-process.html")

with a3:
    st.markdown(
        """
<div class="card">
<span class="badge">Data companion</span>
<h4 style="margin:10px 0 6px 0;">Menghubungkan WDI ke publikasi OECD</h4>
<div class="small-muted">
Angka World Bank memberi peta “berapa dan di mana”. Publikasi OECD membantu menjawab “kenapa”, “seberapa rentan”, dan “reform apa yang biasanya dipilih negara pembanding”.
</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.link_button(
        "OECD Economic Surveys: Indonesia",
        "https://www.oecd.org/en/publications/oecd-economic-surveys-indonesia-2024_de87555a-en.html",
    )

st.markdown('<hr class="hr-soft">', unsafe_allow_html=True)

# =========================================================
# OUTLOOK + REPORT NAVIGATOR (dipakai untuk interpretasi indikator WDI)
# =========================================================
st.markdown("## Outlook dan report OECD untuk menyikapi indikator World Bank")

st.caption(
    "Pilih tema. Di tiap tema, kamu dapat daftar publikasi OECD yang paling relevan untuk membaca indikator World Bank di dashboard ini."
)

THEMES = [
    "Makro, inflasi, dan stabilitas",
    "Pasar kerja dan produktivitas",
    "Perdagangan dan integrasi global",
    "Investasi, bisnis, dan tata kelola",
    "Pendidikan, kesehatan, dan kesejahteraan",
]

theme = st.selectbox("Tema", THEMES, index=0)

resources = {
    "Makro, inflasi, dan stabilitas": [
        {
            "tag": "Country note",
            "title": "OECD Economic Outlook — Indonesia",
            "why": "Dipakai untuk membaca GDP, inflasi, dan dinamika permintaan agregat. Cocok untuk menguji apakah angka terbaru di WDI sejalan dengan proyeksi dan narasi kebijakan makro OECD.",
            "use_for": "GDP, GDP growth, inflation proxy, konsumsi, investasi, trade shock",
            "url": "https://www.oecd.org/en/publications/oecd-economic-outlook-volume-2025-issue-2_9f653ca1-en/full-report/indonesia_21d4d16b.html",
            "ref": "[4]",
        },
        {
            "tag": "Country review",
            "title": "OECD Economic Surveys: Indonesia 2024",
            "why": "Dipakai sebagai bacaan utama untuk memaknai angka WDI Indonesia: struktur ekonomi, reform prioritas, serta konteks institusi yang sering tidak tercermin di angka mentah.",
            "use_for": "GDP, produktivitas, inflasi, fiskal, reform struktural",
            "url": "https://www.oecd.org/en/publications/oecd-economic-surveys-indonesia-2024_de87555a-en.html",
            "ref": "[3]",
        },
        {
            "tag": "Structural reform",
            "title": "Going for Growth 2025",
            "why": "Dipakai untuk membaca indikator sebagai problem prioritas dan trade-off kebijakan, terutama saat kamu membandingkan Indonesia dengan negara pembanding di kuartil atas.",
            "use_for": "pertumbuhan jangka menengah, produktivitas, reform agenda",
            "url": "https://www.oecd.org/en/publications/going-for-growth-2025_50613c70-en.html",
            "ref": "[5]",
        },
    ],
    "Pasar kerja dan produktivitas": [
        {
            "tag": "Flagship outlook",
            "title": "OECD Employment Outlook 2025",
            "why": "Dipakai untuk membaca LFPR, pengangguran, dan kualitas pekerjaan sebagai satu paket. Cocok untuk memberi bahasa kebijakan saat indikator pasar kerja terlihat ekstrem pada peta.",
            "use_for": "LFPR, unemployment, youth unemployment, job quality",
            "url": "https://www.oecd.org/en/publications/oecd-employment-outlook-2025_5d0e6655-en.html",
            "ref": "[6]",
        },
        {
            "tag": "Social indicators",
            "title": "Society at a Glance 2025",
            "why": "Dipakai untuk konteks sosial-ekonomi yang mengapit indikator pasar kerja, kemiskinan, dan ketimpangan. Membantu menghindari interpretasi yang terlalu sempit dari satu angka.",
            "use_for": "kemiskinan, ketimpangan, indikator sosial, resilience",
            "url": "https://www.oecd.org/en/publications/society-at-a-glance-2025_c51363b5-en.html",
            "ref": "[10]",
        },
    ],
    "Perdagangan dan integrasi global": [
        {
            "tag": "Trade structure",
            "title": "OECD Trade in Value Added (TiVA)",
            "why": "Dipakai untuk membaca ekspor/impor dengan perspektif rantai nilai. Cocok saat angka ekspor tinggi tetapi nilai tambah domestik belum tentu tinggi.",
            "use_for": "exports, imports, value added, global value chains",
            "url": "https://www.oecd.org/en/data/datasets/trade-in-value-added.html",
            "ref": "[11]",
        },
        {
            "tag": "Trade frictions",
            "title": "OECD Trade Facilitation Indicators (TFI)",
            "why": "Dipakai untuk menilai friksi logistik dan administrasi perdagangan yang sering menjelaskan gap antara potensi ekspor dan realisasi.",
            "use_for": "trade costs, customs, logistics, facilitation",
            "url": "https://www.oecd.org/en/data/datasets/trade-facilitation-indicators.html",
            "ref": "[12]",
        },
        {
            "tag": "Services trade",
            "title": "OECD Services Trade Restrictiveness Index (STRI)",
            "why": "Dipakai untuk membaca keterbukaan jasa. Relevan saat trade openness terlihat tinggi, tetapi jasa masih berhambatan sehingga produktivitas dan investasi ikut tertahan.",
            "use_for": "trade openness, services restrictions, competitiveness",
            "url": "https://www.oecd.org/en/data/datasets/services-trade-restrictiveness-index.html",
            "ref": "[13]",
        },
    ],
    "Investasi, bisnis, dan tata kelola": [
        {
            "tag": "FDI framework",
            "title": "OECD FDI Regulatory Restrictiveness Index",
            "why": "Dipakai untuk memaknai FDI sebagai hasil dari aturan main. Angka FDI di WDI lebih masuk akal kalau dibaca bersama rezim regulasi dan kepastian kebijakan.",
            "use_for": "FDI, regulatory barriers, openness to investment",
            "url": "https://www.oecd.org/en/data/datasets/fdi-regulatory-restrictiveness-index.html",
            "ref": "[14]",
        },
        {
            "tag": "Governance benchmark",
            "title": "Government at a Glance: Southeast Asia 2025",
            "why": "Dipakai untuk membaca kapasitas institusi publik sebagai fondasi hasil ekonomi. Cocok untuk menghubungkan indikator WDI dengan kualitas layanan publik dan tata kelola.",
            "use_for": "governance, public service delivery, comparability",
            "url": "https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/12/government-at-a-glance-southeast-asia-2025_1b04332c/bc89cb32-en.pdf",
            "ref": "[9]",
        },
        {
            "tag": "Tax & admin",
            "title": "Tax Administration 2025: Indonesia",
            "why": "Dipakai untuk membaca kapasitas fiskal dan administrasi yang akhirnya memengaruhi ruang kebijakan pembangunan.",
            "use_for": "tax capacity, administration, fiscal space",
            "url": "https://www.oecd.org/en/publications/tax-administration-2025-indonesia_7b7f6d7a-en.html",
            "ref": "[15]",
        },
    ],
    "Pendidikan, kesehatan, dan kesejahteraan": [
        {
            "tag": "Flagship indicators",
            "title": "Education at a Glance 2025",
            "why": "Dipakai untuk membaca enrolment dan belanja pendidikan sebagai outcome dan input. Membantu mengaitkan angka pendidikan dengan produktivitas jangka panjang.",
            "use_for": "school enrolment, education spending, skills",
            "url": "https://www.oecd.org/en/publications/education-at-a-glance-2025_8f738fff-en.html",
            "ref": "[7]",
        },
        {
            "tag": "Health systems",
            "title": "Health at a Glance 2025",
            "why": "Dipakai untuk membaca belanja kesehatan dan outcome dasar sebagai cermin kapasitas sistem kesehatan, bukan sekadar angka anggaran.",
            "use_for": "health expenditure, mortality, health outcomes",
            "url": "https://www.oecd.org/en/publications/health-at-a-glance-2025_7a7afb35-en.html",
            "ref": "[8]",
        },
        {
            "tag": "Well-being",
            "title": "How’s Life?",
            "why": "Dipakai untuk memperluas interpretasi dari “angka ekonomi” menjadi kesejahteraan. Cocok saat kamu perlu membahas trade-off pertumbuhan dan kualitas hidup.",
            "use_for": "well-being, inequality, quality of life",
            "url": "https://www.oecd.org/en/topics/sub-issues/measuring-well-being-and-progress/how-s-life.html",
            "ref": "[16]",
        },
    ],
}

# =========================================================
# Render resource cards
# =========================================================
items = resources.get(theme, [])
for it in items:
    st.markdown(
        f"""
<div class="card2">
  <span class="badge">{it["tag"]}</span>
  <h4 style="margin:10px 0 6px 0;">{it["title"]} <span class="small-muted">{it["ref"]}</span></h4>
  <div class="small-muted" style="margin-bottom:10px;">Dipakai untuk: <b>{it["use_for"]}</b></div>
  <div>{it["why"]}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.link_button("Buka publikasi", it["url"])

st.markdown('<hr class="hr-soft">', unsafe_allow_html=True)

# =========================================================
# “Cara pakai” yang eksplisit, biar nyambung ke dashboard kamu
# =========================================================
st.markdown("## Cara membaca angka World Bank dengan lensa OECD (praktis)")
st.markdown(
    """
1) Angka WDI dipakai sebagai titik awal: lihat posisi Indonesia dan pembanding pada peta, lalu cek apakah berada di sekitar median atau sudah menembus kuartil atas/bawah.

2) Setelah posisi jelas, baca publikasi OECD untuk mengisi konteks yang biasanya tidak muncul di data mentah: struktur sektor, hambatan institusi, arah kebijakan, dan sumber risiko.

3) Untuk kebutuhan akademik, simpulkan dalam bentuk narasi kebijakan: “angka mengarah ke X”, “OECD menekankan Y”, lalu “implikasi yang logis untuk reform Z”.
"""
)

# =========================================================
# REFERENCES (angka gaya [1], biar konsisten dengan page2)
# =========================================================
with st.expander("📚 Referensi (tautan) — dasar interpretasi", expanded=False):
    st.markdown(
        """
[1] Roadmap for the OECD Accession Process of Indonesia (C(2024)66/FINAL) — https://one.oecd.org/document/C(2024)66/FINAL/en/pdf  
[2] OECD Accession process overview — https://www.oecd.org/en/about/legal/oecd-accession-process.html  
[3] OECD Economic Surveys: Indonesia 2024 — https://www.oecd.org/en/publications/oecd-economic-surveys-indonesia-2024_de87555a-en.html  
[4] OECD Economic Outlook (Country note: Indonesia, 2025 Issue 2) — https://www.oecd.org/en/publications/oecd-economic-outlook-volume-2025-issue-2_9f653ca1-en/full-report/indonesia_21d4d16b.html  
[5] Going for Growth 2025 — https://www.oecd.org/en/publications/going-for-growth-2025_50613c70-en.html  
[6] OECD Employment Outlook 2025 — https://www.oecd.org/en/publications/oecd-employment-outlook-2025_5d0e6655-en.html  
[7] Education at a Glance 2025 — https://www.oecd.org/en/publications/education-at-a-glance-2025_8f738fff-en.html  
[8] Health at a Glance 2025 — https://www.oecd.org/en/publications/health-at-a-glance-2025_7a7afb35-en.html  
[9] Government at a Glance: Southeast Asia 2025 — https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/12/government-at-a-glance-southeast-asia-2025_1b04332c/bc89cb32-en.pdf  
[10] Society at a Glance 2025 — https://www.oecd.org/en/publications/society-at-a-glance-2025_c51363b5-en.html  
[11] OECD TiVA dataset — https://www.oecd.org/en/data/datasets/trade-in-value-added.html  
[12] OECD Trade Facilitation Indicators — https://www.oecd.org/en/data/datasets/trade-facilitation-indicators.html  
[13] OECD STRI dataset — https://www.oecd.org/en/data/datasets/services-trade-restrictiveness-index.html  
[14] OECD FDI Regulatory Restrictiveness Index — https://www.oecd.org/en/data/datasets/fdi-regulatory-restrictiveness-index.html  
[15] Tax Administration 2025: Indonesia — https://www.oecd.org/en/publications/tax-administration-2025-indonesia_7b7f6d7a-en.html  
[16] How’s Life? — https://www.oecd.org/en/topics/sub-issues/measuring-well-being-and-progress/how-s-life.html  
"""
    )

st.caption("Catatan: Halaman ini ditulis untuk interpretasi deskriptif dan penyusunan narasi akademik. Tidak dimaksudkan sebagai inferensi kausal.")
