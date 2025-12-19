# pages/page12.py
import streamlit as st
from io import BytesIO
import re

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
.c7{background:linear-gradient(135deg, rgba(244,63,94,.14), rgba(251,113,133,.06)); border-color:rgba(244,63,94,.18);}

/* Separator */
.hr{height:1px;background:var(--line);border:0;margin:14px 0;}

/* Chips */
.chip{
  display:inline-block;
  padding:6px 10px;
  margin:0 8px 8px 0;
  border-radius:999px;
  border:1px solid rgba(15,23,42,.10);
  background:rgba(15,23,42,.04);
  font-size:12px;
  font-weight:700;
  color:rgba(15,23,42,.80);
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# Helpers: fetch, cover dari PDF (kalau PyMuPDF tersedia), fallback og:image, terakhir logo
# =========================================================
@st.cache_data(show_spinner=False)
def _fetch_bytes(url: str) -> bytes:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    return r.content


@st.cache_data(show_spinner=False)
def _fetch_text(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    return r.text


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


@st.cache_data(show_spinner=False)
def _extract_og_image_url(page_url: str):
    """
    Cari og:image atau twitter:image dari HTML OECD publication page.
    Ini bikin galeri cover lebih stabil tanpa mengandalkan PDF yang bisa berubah.
    """
    try:
        html = _fetch_text(page_url)
    except Exception:
        return None

    patterns = [
        r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
        r"<meta[^>]+property='og:image'[^>]+content='([^']+)'",
        r'<meta[^>]+name="twitter:image"[^>]+content="([^"]+)"',
        r"<meta[^>]+name='twitter:image'[^>]+content='([^']+)'",
    ]

    for pat in patterns:
        m = re.search(pat, html, flags=re.IGNORECASE)
        if m:
            url = m.group(1).strip()
            if url.startswith("//"):
                url = "https:" + url
            return url

    return None


def _try_cover(pdf_url: str | None, page_url: str | None, fallback_img_url: str):
    # 1) coba PDF
    if pdf_url:
        try:
            pdf_bytes = _fetch_bytes(pdf_url)
            img = _pdf_first_page_to_image(pdf_bytes)
            if img is not None:
                return img
        except Exception:
            pass

    # 2) coba og:image dari page
    if page_url:
        try:
            og = _extract_og_image_url(page_url)
            if og:
                img_bytes = _fetch_bytes(og)
                return Image.open(BytesIO(img_bytes))
        except Exception:
            pass

    # 3) fallback logo
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

    # Tambahan: definisi OECD dan navigasi
    "about_oecd": "https://www.oecd.org/en/about.html",
    "members_partners": "https://www.oecd.org/en/about/members-partners.html",
    "oecd_indonesia_country": "https://www.oecd.org/en/countries/indonesia.html",

    # Tambahan: pintu data OECD
    "oecd_data_portal": "https://www.oecd.org/en/data.html",
}

# Optional PDF preview sources (yang stabil)
PDF_COVERS = {
    "OECD Economic Surveys: Indonesia 2024": "https://www.oecd.org/content/dam/oecd/en/publications/reports/2024/11/oecd-economic-surveys-indonesia-2024_e3ab8960/de87555a-en.pdf",
    "Government at a Glance: Southeast Asia 2025": REF["gag_sea_2025_pdf"],
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
        '<div class="sub">Halaman ini menggabungkan <b>outlook</b> dan <b>report OECD</b> sebagai lensa untuk membaca angka World Bank di dashboard. Indonesia sedang aksesi ke OECD, sehingga keterbandingan dan keterlacakan data cenderung makin ketat dan data Indonesia makin sering masuk ke analisis OECD.</div>',
        unsafe_allow_html=True,
    )

# Quick chips
st.markdown(
    """
<span class="chip">Makro & risiko global</span>
<span class="chip">Pasar kerja</span>
<span class="chip">Perdagangan & rantai nilai</span>
<span class="chip">FDI & iklim regulasi</span>
<span class="chip">Governance & delivery</span>
<span class="chip">Pendidikan & kesehatan</span>
<span class="chip">Kesejahteraan</span>
""",
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
**OECD** adalah organisasi internasional yang menjadi forum kerja sama kebijakan dan pusat rujukan data serta analisis lintas negara. OECD menerbitkan publikasi berbasis evidence dan peer review, membangun indikator pembanding, dan menyusun rekomendasi kebijakan yang dapat ditelusuri ke bukti data. [17][18]

**Definisi pemakaian sumber di dashboard ini**: report dan outlook OECD dipakai untuk menyikapi data World Bank. Peta dan time series World Bank menunjukkan posisi relatif dan tren. Publikasi OECD dipakai untuk mengisi konteks yang sering hilang dari angka mentah, termasuk sumber pertumbuhan, struktur sektor, kualitas institusi, serta risiko yang membuat angka bergerak cepat.
"""
    )

    st.markdown(
        """
**Aksesi Indonesia ke OECD** membawa implikasi langsung pada praktik data. Proses aksesi bergerak lewat review teknis lintas komite, sehingga kebutuhan transparansi, konsistensi definisi, dan kualitas pelaporan cenderung makin terlihat sebagai prioritas. Data Indonesia juga makin sering dibaca sebagai bahan analisis OECD, terutama melalui produk seperti Economic Surveys dan berbagai publikasi tematik yang dipakai untuk peer review dan policy discussion. [1][2][3]
"""
    )

    st.markdown('<hr class="hr">', unsafe_allow_html=True)

    st.markdown("### Alignment Indonesia ke OECD dan implikasi praktis untuk membaca indikator")

    st.markdown(
        """
Roadmap aksesi memberi urutan proses dan area kebijakan yang dinilai. Logika kerjanya jelas: angka tidak berdiri sendiri. Angka menjadi petunjuk awal untuk melihat gap dan prioritas, lalu dibaca bersama standar, praktik, dan pembanding OECD. Roadmap juga bisa dipakai sebagai daftar pertanyaan saat kamu menulis interpretasi akademik, terutama ketika mengaitkan data dengan reform, kapasitas institusi, dan arah kebijakan. [1]
"""
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
<div class="card c1">
  <span class="badge">Rules and guidelines</span>
  <h4>Roadmap aksesi</h4>
  <div class="kecil">Roadmap dipakai sebagai kerangka baca: area mana yang ditinjau, bagaimana urutan review, dan apa yang dimaksud alignment.</div>
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

    # =========================================================
    # KORESPONDENSI: langsung terlihat (bukan dropdown), warnanya menonjol
    # =========================================================
    st.markdown('<hr class="hr">', unsafe_allow_html=True)
    st.markdown("### Korespondensi data World Bank dan OECD")

    st.markdown(
        """
<div class="card c6">
  <span class="badge">World Bank × OECD</span>
  <h4>Keduanya saling berkorespondensi dalam ekosistem indikator global</h4>
  <div class="kecil" style="margin-top:8px; line-height:1.7;">
    World Bank melalui World Development Indicators berperan sebagai kompilator lintas sumber yang menyatukan statistik resmi dan statistik internasional agar mudah dipakai lintas negara.
    OECD berperan sebagai produsen benchmark dan standar yang memperkuat keterbandingan indikator, lalu menerjemahkannya menjadi diagnosis kebijakan melalui peer review dan publikasi evidence.
    Karena perannya berbeda namun saling melengkapi, banyak indikator yang kamu lihat di World Bank punya korespondensi konsep dengan indikator OECD, baik dari sisi definisi, cakupan, maupun cara menyikapi angkanya. [17][20]
    <br><br>
    Dalam konteks Indonesia yang sedang menjalani proses aksesi, korespondensi ini jadi lebih penting. Angka World Bank tetap berguna untuk peta cepat, sementara publikasi OECD membantu menguji konsistensi narasi, menajamkan benchmark, dan memaksa interpretasi lebih disiplin.
    Praktiknya, OECD dipakai sebagai kacamata baca agar perubahan angka di World Bank tidak langsung ditarik menjadi kesimpulan sempit, melainkan dibaca bersama struktur ekonomi, institusi, dan risiko. [1][2][3]
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
Korespondensi ini bukan berarti datanya selalu identik. World Bank menekankan seri yang konsisten dan mudah diakses untuk banyak negara dan banyak tahun. OECD menekankan keterlacakan metodologi dan pembacaan kebijakan berbasis peer review. Hubungan yang paling berguna adalah triangulasi: World Bank memberi posisi dan tren, OECD memberi pembanding, standar, dan narasi diagnosis yang bisa kamu pakai untuk menulis interpretasi yang stabil. [17][3][4]
"""
    )

    st.markdown("#### Contoh korespondensi yang bisa dipakai di narasi interpretasi")
    st.markdown(
        """
<div class="grid">
  <div class="card c2" style="grid-column:span 6;">
    <span class="badge">Makro</span>
    <h4>GDP dan inflasi</h4>
    <div class="kecil" style="line-height:1.7;">
      World Bank menampilkan GDP dan proksi inflasi sebagai level dan tren.
      OECD membaca angka yang sama dalam kerangka baseline, risiko global, dan diagnosis kebijakan melalui Economic Outlook dan Economic Surveys.
      Korespondensinya ada pada pertanyaan yang sama: apakah pertumbuhan ditopang faktor yang bertahan, dan apakah inflasi bersifat sementara atau sudah menekan struktur biaya. [4][3]
    </div>
  </div>

  <div class="card c5" style="grid-column:span 6;">
    <span class="badge">Labor</span>
    <h4>LFPR dan unemployment</h4>
    <div class="kecil" style="line-height:1.7;">
      World Bank memberi indikator partisipasi kerja dan pengangguran.
      OECD menambahkan cara baca yang lebih tegas: slack, kualitas pekerjaan, dan implikasi demografi.
      Korespondensinya terasa ketika kamu menulis arti “angka tinggi atau rendah” tanpa mengunci satu interpretasi tunggal. [6]
    </div>
  </div>

  <div class="card c1" style="grid-column:span 4;">
    <span class="badge">Trade</span>
    <h4>Exports, imports, openness</h4>
    <div class="kecil" style="line-height:1.7;">
      World Bank memberi ukuran perdagangan sebagai rasio terhadap PDB.
      OECD membantu membaca isi dan mekanismenya lewat TiVA (value added), TFI (friksi), dan STRI (hambatan jasa).
      Korespondensinya ada pada alur logika: perdagangan bukan hanya besar, tetapi bagaimana value added dan friksi membentuk daya saing. [11][12][13]
    </div>
  </div>

  <div class="card c4" style="grid-column:span 4;">
    <span class="badge">Investment</span>
    <h4>FDI dan iklim regulasi</h4>
    <div class="kecil" style="line-height:1.7;">
      World Bank menampilkan FDI sebagai arus masuk.
      OECD memberi pembacaan “mengapa” lewat indeks restriksi dan desain aturan main investasi.
      Korespondensinya muncul saat kamu menjelaskan FDI yang tinggi namun rapuh, atau rendah namun konsisten dengan aturan main tertentu. [14]
    </div>
  </div>

  <div class="card c6" style="grid-column:span 4;">
    <span class="badge">Human capital</span>
    <h4>Pendidikan dan kesehatan</h4>
    <div class="kecil" style="line-height:1.7;">
      World Bank menampilkan enrolment, belanja, dan outcome dasar.
      OECD memberi benchmark dan kerangka baca sistem melalui Education at a Glance dan Health at a Glance.
      Korespondensinya terasa saat kamu menulis bahwa belanja bukan satu-satunya ukuran, lalu mengarah ke kapasitas sistem dan kualitas output. [7][8]
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
Kalimat penutup yang aman untuk dipakai: World Bank memberi gambaran posisi dan tren yang cepat, sedangkan OECD memberi cara baca yang lebih disiplin untuk menjelaskan konteks, benchmark, dan implikasi kebijakan. Jika keduanya dibaca bersama, interpretasi angka lebih stabil dan tidak gampang jatuh pada kesimpulan yang terlalu cepat. [17][20]
"""
    )

    # =========================================================
    # Enrichment: template narasi + poin yang sering salah
    # =========================================================
    st.markdown('<hr class="hr">', unsafe_allow_html=True)
    st.markdown("### Template narasi siap pakai untuk halaman World Bank")

    with st.expander("Buka template narasi (copy-friendly)", expanded=False):
        st.markdown(
            """
**Template 1 (peta + kuartil)**  
“Pada tahun ____, posisi Indonesia berada ____ (di sekitar median/di atas Q3/di bawah Q1). Posisi ini menunjukkan ____ pada indikator ____. Angka ini dibaca bersama ____ karena pergerakan indikator ini sering mengikuti ____.”

**Template 2 (tren time series)**  
“Dalam rentang ____–____, indikator ____ untuk Indonesia bergerak ____. Pola ini selaras/tidak selaras dengan konteks ____ yang dibahas OECD. Pertanyaan kebijakan yang paling relevan adalah ____.”

**Template 3 (mengaitkan dengan report OECD)**  
“OECD menekankan ____ sebagai isu kunci. Ini memberi cara baca yang lebih tajam untuk angka World Bank: bukan hanya tinggi/rendah, tetapi apakah struktur ____, institusi ____, dan risiko ____ mendukung perbaikan yang bertahan.”
"""
        )

    st.markdown(
        """
<div class="grid">
  <div class="card c1" style="grid-column:span 6;">
    <span class="badge">Checklist interpretasi</span>
    <h4>Sebelum menulis 1 paragraf</h4>
    <div class="kecil" style="line-height:1.7;">
      Pastikan sudah jelas: posisi (median/Q1/Q3), arah (tren), konteks (report OECD), dan risiko terdekat (shock eksternal, institusi, struktur sektor).
    </div>
  </div>
  <div class="card c7" style="grid-column:span 6;">
    <span class="badge">Kesalahan yang sering terjadi</span>
    <h4>Yang bikin interpretasi rapuh</h4>
    <div class="kecil" style="line-height:1.7;">
      Menyimpulkan sebab-akibat dari satu angka, mengabaikan definisi indikator, memakai wilayah agregat sebagai pembanding, dan menutup paragraf tanpa konsekuensi kebijakan yang jelas.
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

# =========================================================
# TAB 2
# =========================================================
with tab2:
    st.markdown("## Library report dan outlook")
    st.markdown(
        """
Bagian ini menempatkan report sebagai alat kerja untuk menulis interpretasi data. Tujuannya praktis: kamu bisa menjawab “apa arti angka” dengan konteks yang dapat ditelusuri.

Cara pakai yang paling konsisten: ambil satu temuan diagnosis dan satu implikasi kebijakan dari report, lalu kaitkan dengan pola pada peta atau tren time series World Bank.
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
  <div class="kecil" style="line-height:1.7;">
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
  <div class="kecil" style="line-height:1.7;">
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
  <div class="kecil" style="line-height:1.7;">
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
  <div class="kecil" style="line-height:1.7;">
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
  <div class="kecil" style="line-height:1.7;">
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
  <div class="kecil" style="line-height:1.7;">
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

    st.markdown("## Galeri report (cover) — lebih lengkap")

    show_pdf_preview = st.toggle("Tampilkan preview PDF (jika tersedia)", value=False)
    compact_mode = st.toggle("Mode ringkas (lebih banyak cover per baris)", value=True)

    report_cards = [
        {
            "title": "OECD Economic Surveys: Indonesia 2024",
            "tag": "Economic Survey",
            "use": "Diagnosis struktur ekonomi, reform prioritas, konteks kebijakan untuk membaca GDP, produktivitas, inflasi.",
            "page": REF["surveys_indonesia_2024"],
            "pdf": PDF_COVERS.get("OECD Economic Surveys: Indonesia 2024"),
            "ref": "[3]",
        },
        {
            "title": "OECD Economic Outlook (Indonesia country note)",
            "tag": "Outlook",
            "use": "Baseline proyeksi, risiko global, dan jalur transmisi shock ke GDP, inflasi, serta permintaan agregat.",
            "page": REF["outlook_country_indonesia"],
            "pdf": None,
            "ref": "[4]",
        },
        {
            "title": "OECD Employment Outlook 2025",
            "tag": "Jobs",
            "use": "Membaca LFPR dan pengangguran dengan konteks kualitas kerja, demografi, dan pergeseran struktur pasar tenaga kerja.",
            "page": REF["employment_outlook_2025"],
            "pdf": None,
            "ref": "[6]",
        },
        {
            "title": "Education at a Glance 2025",
            "tag": "Education",
            "use": "Benchmark input–output pendidikan dan cara menyikapi angka enrolment dan spending secara lebih substantif.",
            "page": REF["education_at_a_glance_2025"],
            "pdf": None,
            "ref": "[7]",
        },
        {
            "title": "Health at a Glance 2025",
            "tag": "Health",
            "use": "Cara membaca health spending dan outcome sebagai kapasitas sistem, bukan sekadar belanja.",
            "page": REF["health_at_a_glance_2025"],
            "pdf": None,
            "ref": "[8]",
        },
        {
            "title": "Government at a Glance: Southeast Asia 2025",
            "tag": "Governance",
            "use": "Kapasitas institusi dan delivery sebagai fondasi outcome ekonomi dan sosial.",
            "page": REF["gag_sea_2025_pdf"],
            "pdf": PDF_COVERS.get("Government at a Glance: Southeast Asia 2025"),
            "ref": "[9]",
        },
        {
            "title": "Society at a Glance 2025",
            "tag": "Social",
            "use": "Konteks sosial untuk membaca kemiskinan, ketimpangan, dan resilience, supaya interpretasi tidak sempit.",
            "page": REF["society_at_a_glance_2025"],
            "pdf": None,
            "ref": "[10]",
        },
        {
            "title": "Going for Growth 2025",
            "tag": "Reform",
            "use": "Bahasa reform yang tegas: prioritas, trade-off, dan benchmark lintas negara.",
            "page": REF["going_for_growth_2025"],
            "pdf": None,
            "ref": "[5]",
        },
    ]

    if compact_mode:
        cols = st.columns(4)
        per_row = 4
    else:
        cols = st.columns(3)
        per_row = 3

    for i, it in enumerate(report_cards):
        with cols[i % per_row]:
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

            cover = _try_cover(it.get("pdf"), it.get("page"), OECD_LOGO)
            if cover is not None:
                st.image(cover, use_container_width=True)
            else:
                st.image(OECD_LOGO, use_container_width=True)

            if it.get("pdf") and show_pdf_preview:
                st.components.v1.iframe(it["pdf"], height=520, scrolling=True)

            st.link_button("Buka publikasi", it["page"])

    st.markdown('<hr class="hr">', unsafe_allow_html=True)

    st.markdown("## Cara pakai untuk menulis interpretasi di dashboard World Bank")

    st.markdown(
        """
Langkah yang bekerja paling konsisten:

1) Tetapkan posisi Indonesia di peta World Bank: dekat median, di atas Q3, atau di bawah Q1.  
2) Cek tren 5 sampai 10 tahun terakhir: menguat, melemah, atau datar.  
3) Ambil satu report OECD yang paling relevan untuk indikator itu.  
4) Ambil satu diagnosis dan satu implikasi kebijakan, lalu tulis interpretasi yang menyambungkan angka dengan konteks.  
5) Tutup dengan kalimat konsekuensi kebijakan yang jelas: apa yang perlu diperhatikan jika tren berlanjut, dan apa risiko jika gap dibiarkan.

Kalimat penutup yang aman: “angka menunjukkan ____; OECD menekankan ____; konsekuensi kebijakan yang masuk akal adalah ____.”
"""
    )

    st.markdown(
        """
<div class="grid">
  <div class="card c1" style="grid-column:span 6;">
    <span class="badge">Checklist interpretasi</span>
    <h4>Sebelum menulis 1 paragraf</h4>
    <div class="kecil" style="line-height:1.7;">
      Pastikan sudah jelas: posisi (median/Q1/Q3), arah (tren), konteks (report OECD), dan risiko terdekat (shock eksternal, institusi, struktur sektor).
    </div>
  </div>
  <div class="card c7" style="grid-column:span 6;">
    <span class="badge">Kesalahan yang sering terjadi</span>
    <h4>Yang bikin interpretasi rapuh</h4>
    <div class="kecil" style="line-height:1.7;">
      Menyimpulkan sebab-akibat dari satu angka, mengabaikan definisi indikator, memakai wilayah agregat sebagai pembanding, dan menutup paragraf tanpa konsekuensi kebijakan yang jelas.
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.caption("Catatan: halaman ini deskriptif dan ditujukan untuk interpretasi data. Inferensi kausal perlu desain empiris terpisah.")

# =========================================================
# REFERENCES (tetap lengkap + tidak berkurang)
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
[20] OECD Data portal — {REF["oecd_data_portal"]}  
"""
    )
