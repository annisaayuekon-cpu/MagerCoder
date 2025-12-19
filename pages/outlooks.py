# pages/page12.py
import streamlit as st
from io import BytesIO

import requests
from PIL import Image

st.set_page_config(
    page_title="Indonesia Accession to the OECD",
    page_icon="🏛️",
    layout="wide",
)

# =========================================================
# STYLE: warna warni (biru tua-muda, abu-abu, teal, ungu)
# =========================================================
st.markdown(
    """
<style>
:root{
  --slate:#0f172a;
  --muted:#475569;
  --line:rgba(15, 23, 42, 0.10);
  --card:rgba(15, 23, 42, 0.04);
}

/* Head */
.h1{font-size:34px;font-weight:900;margin:0 0 6px 0;color:var(--slate);}
.sub{font-size:15px;color:rgba(15,23,42,.78);margin:0 0 12px 0;line-height:1.55;}
.kecil{font-size:12.5px;color:rgba(15,23,42,.65);}

/* Cards */
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px;margin:10px 0 8px 0;}
.card{
  border:1px solid var(--line);
  border-radius:18px;
  padding:14px 14px 12px 14px;
  background:var(--card);
}
.card h4{margin:10px 0 6px 0;font-size:16px;}
.badge{
  display:inline-flex;align-items:center;gap:8px;
  font-size:12px;font-weight:800;
  padding:4px 10px;border-radius:999px;
  border:1px solid rgba(29,78,216,.18);
  background:rgba(29,78,216,.10);
  color:rgba(15,23,42,.85);
}

/* Colored cards */
.c1{background:linear-gradient(135deg, rgba(29,78,216,.14), rgba(96,165,250,.06)); border-color:rgba(29,78,216,.20);}
.c2{background:linear-gradient(135deg, rgba(2,132,199,.16), rgba(56,189,248,.06)); border-color:rgba(2,132,199,.20);}
.c3{background:linear-gradient(135deg, rgba(71,85,105,.14), rgba(148,163,184,.06)); border-color:rgba(71,85,105,.18);}
.c4{background:linear-gradient(135deg, rgba(99,102,241,.16), rgba(129,140,248,.06)); border-color:rgba(99,102,241,.18);}
.c5{background:linear-gradient(135deg, rgba(16,185,129,.14), rgba(52,211,153,.06)); border-color:rgba(16,185,129,.18);}
.c6{background:linear-gradient(135deg, rgba(245,158,11,.16), rgba(251,191,36,.06)); border-color:rgba(245,158,11,.18);}

/* Separator */
.hr{height:1px;background:var(--line);border:0;margin:14px 0;}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# Helpers: cover dari PDF (kalau PyMuPDF tersedia), fallback logo
# =========================================================
@st.cache_data(show_spinner=False)
def _fetch_bytes(url: str) -> bytes:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    return r.content


@st.cache_data(show_spinner=False)
def _pdf_first_page_to_image(pdf_bytes: bytes, zoom: float = 1.55):
    try:
        import fitz  # PyMuPDF
    except Exception:
        return None

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(0)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(BytesIO(pix.tobytes("png")))
        return img
    except Exception:
        return None


def _try_cover(pdf_url: str, fallback_img_url: str):
    try:
        pdf_bytes = _fetch_bytes(pdf_url)
        img = _pdf_first_page_to_image(pdf_bytes)
        if img is not None:
            return img
    except Exception:
        pass

    try:
        img_bytes = _fetch_bytes(fallback_img_url)
        return Image.open(BytesIO(img_bytes))
    except Exception:
        return None


# =========================================================
# Links: tetap lengkap (jangan dikurangi)
# =========================================================
OECD_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/OECD_logo.svg/1024px-OECD_logo.svg.png"

REF = {
    # Aksesi
    "roadmap_pdf": "https://one.oecd.org/document/C(2024)66/FINAL/en/pdf",
    "accession_process": "https://www.oecd.org/en/about/legal/oecd-accession-process.html",

    # Flagship country + outlook
    "surveys_indonesia_2024": "https://www.oecd.org/en/publications/oecd-economic-surveys-indonesia-2024_de87555a-en.html",
    "outlook_country_indonesia": "https://www.oecd.org/en/publications/oecd-economic-outlook-volume-2025-issue-2_9f653ca1-en/full-report/indonesia_21d4d16b.html",
    "going_for_growth_2025": "https://www.oecd.org/en/publications/going-for-growth-2025_50613c70-en.html",

    # Employment, Education, Health, Governance, Society, Well-being
    "employment_outlook_2025": "https://www.oecd.org/en/publications/oecd-employment-outlook-2025_5d0e6655-en.html",
    "education_at_a_glance_2025": "https://www.oecd.org/en/publications/education-at-a-glance-2025_8f738fff-en.html",
    "health_at_a_glance_2025": "https://www.oecd.org/en/publications/health-at-a-glance-2025_7a7afb35-en.html",
    "gag_sea_2025_pdf": "https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/12/government-at-a-glance-southeast-asia-2025_1b04332c/bc89cb32-en.pdf",
    "society_at_a_glance_2025": "https://www.oecd.org/en/publications/society-at-a-glance-2025_c51363b5-en.html",
    "tiva": "https://www.oecd.org/en/data/datasets/trade-in-value-added.html",
    "tfi": "https://www.oecd.org/en/data/datasets/trade-facilitation-indicators.html",
    "stri": "https://www.oecd.org/en/data/datasets/services-trade-restrictiveness-index.html",
    "fdi_restrictiveness": "https://www.oecd.org/en/data/datasets/fdi-regulatory-restrictiveness-index.html",
    "tax_admin_2025_id": "https://www.oecd.org/en/publications/tax-administration-2025-indonesia_7b7f6d7a-en.html",
    "hows_life": "https://www.oecd.org/en/topics/sub-issues/measuring-well-being-and-progress/how-s-life.html",

    # Tambahan (biar makin berisi dan tetap konsisten dengan aksesi)
    "about_oecd": "https://www.oecd.org/en/about.html",
    "members_partners": "https://www.oecd.org/en/about/members-partners.html",
    "oecd_indonesia_country": "https://www.oecd.org/en/countries/indonesia.html",
}

# Optional PDF preview sources (kalau bisa di-fetch, cover akan tampil)
# Note: kalau PDF berubah/blocked, fallback otomatis ke logo.
PDF_COVERS = {
    "Economic Surveys: Indonesia 2024": "https://www.oecd.org/content/dam/oecd/en/publications/reports/2024/11/oecd-economic-surveys-indonesia-2024_e3ab8960/de87555a-en.pdf",
    "Government at a Glance: Southeast Asia 2025": REF["gag_sea_2025_pdf"],
    # yang lain sengaja tidak dipaksa PDF agar tidak rapuh
}

# =========================================================
# Header
# =========================================================
h1, h2 = st.columns([1.1, 5])
with h1:
    st.image(OECD_LOGO, use_container_width=True)
with h2:
    st.markdown('<div class="h1">Indonesia Accession to the OECD</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub">Halaman ini menggabungkan <b>outlook</b> dan <b>report OECD</b> sebagai lensa untuk membaca angka World Bank di dashboard. Angka diperlakukan sebagai sinyal, lalu dijelaskan dengan diagnosis kebijakan, struktur ekonomi, dan risiko yang dibahas OECD.</div>',
        unsafe_allow_html=True,
    )

# =========================================================
# 2 subpage (tabs)
# =========================================================
tab1, tab2 = st.tabs(
    [
        "Subpage 1 — Definisi, aksesi, dan alignment",
        "Subpage 2 — Library report, outlook, dan cara pakai",
    ]
)

# =========================================================
# TAB 1
# =========================================================
with tab1:
    st.markdown("## Definisi dan tujuan penggunaan report")

    st.markdown(
        """
**OECD** adalah organisasi internasional yang menjadi forum kerja sama kebijakan dan pusat rujukan data serta analisis lintas negara. OECD menyusun publikasi berbasis evidence dan peer review, membangun indikator pembanding, dan mendorong standar agar praktik kebijakan antarnegara lebih mudah dibandingkan. [17][18]

**Definisi pemakaian sumber di dashboard ini**: report dan outlook OECD dipakai untuk menyikapi data World Bank. Peta dan time series World Bank menunjukkan posisi relatif dan tren. Publikasi OECD dipakai untuk menjawab konteks yang sering hilang dari angka mentah, termasuk sumber pertumbuhan, penjelasan struktur sektor, kualitas institusi, serta risiko yang membuat angka bergerak cepat.
"""
    )

    st.markdown(
        """
**Aksesi Indonesia ke OECD** berjalan bersamaan dengan kebutuhan keterbandingan dan keterlacakan data yang lebih kuat. Proses aksesi membawa mekanisme review teknis dan diskusi lintas komite, sehingga isu transparansi, konsistensi definisi, dan kualitas pelaporan cenderung makin menonjol. Data Indonesia juga semakin sering dibaca sebagai bahan analisis OECD dalam produk seperti Economic Surveys dan publikasi tematik. [1][2]
"""
    )

    st.markdown('<hr class="hr">', unsafe_allow_html=True)

    st.markdown("### Alignment Indonesia ke OECD dan implikasi praktis untuk membaca indikator")

    st.markdown(
        """
Roadmap aksesi memberi urutan proses dan area kebijakan yang dinilai. Logika kerjanya sederhana: angka tidak berdiri sendiri. Angka menjadi petunjuk awal untuk menilai gap dan prioritas, lalu dibaca bersama standar, praktik, dan pembanding OECD. Roadmap juga berguna sebagai daftar pertanyaan saat kamu menulis interpretasi akademik, terutama ketika ingin mengaitkan data dengan reform, kapasitas institusi, dan arah kebijakan. [1]
"""
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
<div class="card c1">
  <span class="badge">Rules and guidelines</span>
  <h4>Roadmap aksesi</h4>
  <div class="kecil">Roadmap dipakai sebagai kerangka membaca: area mana yang ditinjau, bagaimana urutan review, dan apa yang dimaksud “alignment”.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button("Roadmap (PDF)", REF["roadmap_pdf"])
    with c2:
        st.markdown(
            """
<div class="card c2">
  <span class="badge">Peer review</span>
  <h4>Proses aksesi</h4>
  <div class="kecil">Ringkasan proses aksesi membantu menjelaskan kenapa data dan kebijakan dibaca sebagai paket, bukan angka terpisah.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button("Accession process", REF["accession_process"])
    with c3:
        st.markdown(
            """
<div class="card c4">
  <span class="badge">Indonesia focus</span>
  <h4>Profil Indonesia</h4>
  <div class="kecil">Profil negara memudahkan navigasi publikasi OECD yang relevan untuk Indonesia.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button("Indonesia on OECD", REF["oecd_indonesia_country"])

    st.markdown('<hr class="hr">', unsafe_allow_html=True)

    st.markdown("### Menghubungkan indikator World Bank ke rujukan OECD")

    st.markdown(
        """
Mapping berikut dibuat untuk mempermudah interpretasi di halaman World Bank pada dashboard. Satu indikator biasanya perlu dua rujukan: satu untuk baseline dan risiko, satu untuk diagnosis struktural dan rekomendasi kebijakan.
"""
    )

    st.markdown(
        """
<div class="grid">
  <div class="card c3" style="grid-column:span 6;">
    <span class="badge">Makro</span>
    <h4>GDP, GDP growth, inflasi</h4>
    <div class="kecil">
    Economic Outlook dipakai untuk baseline proyeksi dan risiko. Economic Surveys dipakai untuk diagnosis struktur ekonomi dan agenda reform.
    </div>
  </div>

  <div class="card c5" style="grid-column:span 6;">
    <span class="badge">Jobs</span>
    <h4>LFPR, unemployment, youth unemployment</h4>
    <div class="kecil">
    Employment Outlook membantu membaca angka pasar kerja sebagai paket: partisipasi, slack, kualitas kerja, dan tekanan demografi.
    </div>
  </div>

  <div class="card c1" style="grid-column:span 4;">
    <span class="badge">Trade</span>
    <h4>Exports, imports, openness, tariffs</h4>
    <div class="kecil">
    TiVA membaca rantai nilai. TFI membaca friksi fasilitasi. STRI membaca hambatan jasa. Ini membuat interpretasi trade tidak berhenti pada “tinggi atau rendah”.
    </div>
  </div>

  <div class="card c2" style="grid-column:span 4;">
    <span class="badge">Investment</span>
    <h4>FDI dan iklim bisnis</h4>
    <div class="kecil">
    FDI Restrictiveness Index dipakai untuk membaca FDI sebagai hasil rezim regulasi. Ini membantu narasi kebijakan saat angka FDI di WDI terlihat anomali.
    </div>
  </div>

  <div class="card c4" style="grid-column:span 4;">
    <span class="badge">Governance and fiscal</span>
    <h4>Kapasitas institusi dan ruang fiskal</h4>
    <div class="kecil">
    Government at a Glance dan Tax Administration dipakai untuk membaca kapasitas kebijakan. Banyak outcome ekonomi mengikuti kualitas delivery dan administrasi.
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
Catatan tambahan yang relevan untuk dashboard: sebagian indikator World Bank berasal dari berbagai sumber internasional dan sebagian punya irisan dengan ekosistem statistik OECD. Dalam konteks aksesi, kebutuhan pelaporan yang lebih terstruktur dan periodik biasanya membuat profil data Indonesia di OECD lebih kaya, lebih rapi, dan lebih sering dipakai untuk analisis. [6][9]
"""
    )

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

# =========================================================
# TAB 2
# =========================================================
with tab2:
    st.markdown("## Library report dan outlook")
    st.markdown(
        """
Bagian ini menempatkan report sebagai “alat kerja” untuk menulis interpretasi data. Tujuannya bukan menambah daftar bacaan, tetapi membuat langkah baca data lebih tegas dan lebih akademik.

Pemakaian yang paling aman: ambil satu temuan diagnosis dan satu implikasi kebijakan dari report, lalu kaitkan dengan pola pada peta atau tren time series World Bank.
"""
    )

    st.markdown('<hr class="hr">', unsafe_allow_html=True)

    # Pilih fokus bacaan
    focus = st.radio(
        "Pilih fokus interpretasi",
        ["Makro", "Pasar kerja", "Perdagangan", "Investasi dan governance", "Pendidikan dan kesehatan", "Kesejahteraan sosial"],
        horizontal=True,
    )

    if focus == "Makro":
        st.markdown(
            """
<div class="card c2">
  <span class="badge">Makro</span>
  <h4>Baseline, risiko, dan diagnosis</h4>
  <div class="kecil">
  Economic Outlook dipakai untuk baseline dan risiko global yang memengaruhi pertumbuhan dan inflasi.
  Economic Surveys dipakai untuk diagnosis struktur ekonomi Indonesia dan prioritas reform.
  Going for Growth dipakai untuk membingkai reform dalam bahasa benchmark lintas negara.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button("OECD Economic Outlook (Indonesia)", REF["outlook_country_indonesia"])
        st.link_button("OECD Economic Surveys: Indonesia 2024", REF["surveys_indonesia_2024"])
        st.link_button("Going for Growth 2025", REF["going_for_growth_2025"])

    elif focus == "Pasar kerja":
        st.markdown(
            """
<div class="card c5">
  <span class="badge">Jobs</span>
  <h4>Membaca LFPR dan pengangguran sebagai paket</h4>
  <div class="kecil">
  Employment Outlook membantu menghubungkan partisipasi kerja, slack pasar kerja, kualitas pekerjaan, dan tekanan demografi.
  Society at a Glance membantu menempatkan angka pasar kerja dalam konteks sosial.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button("OECD Employment Outlook 2025", REF["employment_outlook_2025"])
        st.link_button("Society at a Glance 2025", REF["society_at_a_glance_2025"])

    elif focus == "Perdagangan":
        st.markdown(
            """
<div class="card c1">
  <span class="badge">Trade</span>
  <h4>Trade angka besar, value added, dan friksi</h4>
  <div class="kecil">
  TiVA membantu membaca trade sebagai rantai nilai. TFI membantu membaca friksi fasilitasi. STRI membantu membaca hambatan jasa.
  Kombinasi ini membuat interpretasi ekspor impor lebih tajam daripada sekadar peringkat peta.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button("OECD TiVA", REF["tiva"])
        st.link_button("OECD Trade Facilitation Indicators", REF["tfi"])
        st.link_button("OECD STRI", REF["stri"])

    elif focus == "Investasi dan governance":
        st.markdown(
            """
<div class="card c4">
  <span class="badge">Investment and governance</span>
  <h4>FDI sebagai hasil aturan main</h4>
  <div class="kecil">
  FDI Restrictiveness Index memberi cara baca yang tegas: FDI tidak dibaca sebagai angka masuk saja, melainkan sebagai hasil rezim regulasi.
  Government at a Glance dan Tax Administration memberi konteks kapasitas institusi dan administrasi yang menentukan ruang kebijakan.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button("FDI Regulatory Restrictiveness Index", REF["fdi_restrictiveness"])
        st.link_button("Government at a Glance: Southeast Asia 2025 (PDF)", REF["gag_sea_2025_pdf"])
        st.link_button("Tax Administration 2025: Indonesia", REF["tax_admin_2025_id"])

    elif focus == "Pendidikan dan kesehatan":
        st.markdown(
            """
<div class="card c6">
  <span class="badge">Human capital</span>
  <h4>Membaca output dan input layanan dasar</h4>
  <div class="kecil">
  Education at a Glance membantu membaca enrolment dan belanja pendidikan sebagai sinyal kualitas sistem.
  Health at a Glance membantu membaca belanja kesehatan dan outcome sebagai kapasitas sistem, bukan sekadar besaran anggaran.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button("Education at a Glance 2025", REF["education_at_a_glance_2025"])
        st.link_button("Health at a Glance 2025", REF["health_at_a_glance_2025"])

    else:
        st.markdown(
            """
<div class="card c3">
  <span class="badge">Well-being</span>
  <h4>Angka ekonomi dan kualitas hidup</h4>
  <div class="kecil">
  Society at a Glance dan How’s Life? memperluas interpretasi dari indikator ekonomi ke kesejahteraan.
  Ini berguna saat kamu menulis implikasi kebijakan dari kemiskinan, ketimpangan, dan outcome sosial.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button("Society at a Glance 2025", REF["society_at_a_glance_2025"])
        st.link_button("How’s Life?", REF["hows_life"])

    st.markdown('<hr class="hr">', unsafe_allow_html=True)

    # Gallery cover
    st.markdown("## Galeri report (cover)")

    show_pdf_preview = st.toggle("Tampilkan preview PDF (jika tersedia)", value=False)

    gallery_items = [
        {
            "title": "OECD Economic Surveys: Indonesia 2024",
            "tag": "Economic Survey",
            "use": "Diagnosis struktur ekonomi, reform prioritas, konteks kebijakan untuk membaca GDP, produktivitas, inflasi.",
            "page": REF["surveys_indonesia_2024"],
            "pdf": PDF_COVERS.get("Economic Surveys: Indonesia 2024"),
            "ref": "[3]",
        },
        {
            "title": "Government at a Glance: Southeast Asia 2025",
            "tag": "Governance",
            "use": "Membaca kapasitas institusi dan delivery kebijakan sebagai fondasi outcome ekonomi.",
            "page": REF["gag_sea_2025_pdf"],
            "pdf": PDF_COVERS.get("Government at a Glance: Southeast Asia 2025"),
            "ref": "[9]",
        },
    ]

    cols = st.columns(2)
    for i, it in enumerate(gallery_items):
        with cols[i % 2]:
            st.markdown(
                f"""
<div class="card c2">
  <span class="badge">{it["tag"]} {it["ref"]}</span>
  <h4>{it["title"]}</h4>
  <div class="kecil">{it["use"]}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            if it.get("pdf"):
                img = _try_cover(it["pdf"], OECD_LOGO)
                if img is not None:
                    st.image(img, use_container_width=True)
                if show_pdf_preview:
                    st.components.v1.iframe(it["pdf"], height=650, scrolling=True)
            else:
                st.image(OECD_LOGO, use_container_width=True)

            st.link_button("Buka publikasi", it["page"])

    st.markdown('<hr class="hr">', unsafe_allow_html=True)

    st.markdown("## Cara pakai untuk menulis interpretasi di dashboard World Bank")

    st.markdown(
        """
Langkah yang bekerja paling konsisten:

1) Tetapkan posisi Indonesia di peta World Bank: dekat median, di atas Q3, atau di bawah Q1.  
2) Cek apakah tren 5 sampai 10 tahun terakhir menguat, melemah, atau datar.  
3) Ambil satu report OECD yang paling relevan untuk indikator itu.  
4) Ambil satu diagnosis dan satu implikasi kebijakan, lalu tulis interpretasi yang menyambungkan angka dengan konteks.  
5) Selesai di narasi yang tegas: apa yang terlihat dari angka, konteks apa yang menjelaskan, dan apa konsekuensi kebijakannya.
"""
    )

    st.caption("Catatan: halaman ini deskriptif dan ditujukan untuk interpretasi data. Inferensi kausal perlu desain empiris terpisah.")

# =========================================================
# REFERENCES (tetap lengkap, minimal sama seperti versi sebelumnya)
# =========================================================
with st.expander("📚 Referensi (tautan) — format sitasi angka seperti page 2", expanded=False):
    st.markdown(
        f"""
[1] Roadmap for the OECD Accession Process of Indonesia (C(2024)66/FINAL) — {REF["roadmap_pdf"]}  
[2] OECD Accession process overview — {REF["accession_process"]}  
[3] OECD Economic Surveys: Indonesia 2024 — {REF["surveys_indonesia_2024"]}  
[4] OECD Economic Outlook (Country note: Indonesia, 2025 Issue 2) — {REF["outlook_country_indonesia"]}  
[5] Going for Growth 2025 — {REF["going_for_growth_2025"]}  
[6] OECD Employment Outlook 2025 — {REF["employment_outlook_2025"]}  
[7] Education at a Glance 2025 — {REF["education_at_a_glance_2025"]}  
[8] Health at a Glance 2025 — {REF["health_at_a_glance_2025"]}  
[9] Government at a Glance: Southeast Asia 2025 (PDF) — {REF["gag_sea_2025_pdf"]}  
[10] Society at a Glance 2025 — {REF["society_at_a_glance_2025"]}  
[11] OECD TiVA dataset — {REF["tiva"]}  
[12] OECD Trade Facilitation Indicators — {REF["tfi"]}  
[13] OECD Services Trade Restrictiveness Index (STRI) — {REF["stri"]}  
[14] OECD FDI Regulatory Restrictiveness Index — {REF["fdi_restrictiveness"]}  
[15] Tax Administration 2025: Indonesia — {REF["tax_admin_2025_id"]}  
[16] How’s Life? — {REF["hows_life"]}  
[17] About the OECD — {REF["about_oecd"]}  
[18] OECD Members and partners — {REF["members_partners"]}  
[19] OECD Indonesia country page — {REF["oecd_indonesia_country"]}  
"""
    )
