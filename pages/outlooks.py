# pages/3_oecd_aksesi.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1) KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="OECD & Aksesi Indonesia",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 6px 6px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #0b4ea2;
        color: white;
    }
    h1, h2, h3 { color: #0b2d5c; }
    .highlight { color: #0b4ea2; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2) SIDEBAR
# -----------------------------------------------------------------------------
OECD_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/OECD_logo.svg/512px-OECD_logo.svg.png"

with st.sidebar:
    st.image(OECD_LOGO, width=180)
    st.title("Navigasi Aksesi OECD")
    st.info(
        "Halaman ini merangkum proses aksesi Indonesia ke OECD, milestone kunci, "
        "serta struktur Roadmap yang menjadi rujukan review teknis, reform agenda, "
        "dan alignment Indonesia di ekosistem OECD serta indikator yang banyak dipakai lintas lembaga (termasuk World Bank)."
    )

    with st.expander("Catatan data: OECD dan World Bank", expanded=False):
        st.markdown(
            """
Sejumlah indikator World Bank dikompilasi dari berbagai sumber internasional, termasuk statistik OECD pada tema-tema tertentu.
Implikasinya, cakupan metrik untuk Indonesia cenderung makin nyambung lintas platform ketika standar data, definisi, dan kebutuhan pelaporan makin selaras.

OECD juga punya mekanisme pengumpulan data dan survei sendiri melalui kuesioner, program data collection, serta peer review berbasis evidence.
Dalam konteks aksesi, kebutuhan review komite biasanya mendorong data Indonesia menjadi lebih terstruktur, periodik, dan mudah dibandingkan lintas negara.
"""
        )

    st.markdown("### Dokumen & rujukan inti")
    st.link_button("OECD Accession Process (Steps)", "https://www.oecd.org/en/about/legal/oecd-accession-process.html")
    st.link_button("Indonesia Accession Roadmap (PDF)", "https://one.oecd.org/document/C%282024%2966/FINAL/en/pdf")
    st.link_button("Press release (20 Feb 2024)", "https://www.oecd.org/en/about/news/press-releases/2024/02/oecd-makes-historic-decision-to-open-accession-discussions-with-indonesia.html")
    st.link_button("Press release (2 May 2024)", "https://www.oecd.org/en/about/news/press-releases/2024/05/ministers-welcome-roadmap-for-accession-discussions-with-indonesia.html")
    st.link_button("Press release (3 Jun 2025)", "https://www.oecd.org/en/about/news/press-releases/2025/06/indonesia-reaches-key-milestones-in-oecd-accession-process.html")

    st.markdown("---")
    st.markdown("**Kata kunci:**")
    st.caption("Accession Roadmap • Initial Memorandum • Committee Reviews • Formal Opinions • Council decision")


# -----------------------------------------------------------------------------
# 3) HEADER
# -----------------------------------------------------------------------------
st.title("🌐 OECD dan Aksesi Indonesia ke OECD")
st.markdown("#### Snapshot proses, Roadmap (rules & guidelines), dan peta komite review")

# -----------------------------------------------------------------------------
# DATA RINGKAS (berbasis rilis & Roadmap OECD)
# -----------------------------------------------------------------------------
milestones = pd.DataFrame(
    [
        {
            "Tanggal": "2024-02-20",
            "Peristiwa": "OECD Council membuka diskusi aksesi dengan Indonesia",
            "Catatan": "Council decision untuk memulai accession discussions",
            "Sumber": "OECD press release",
            "Link": "https://www.oecd.org/en/about/news/press-releases/2024/02/oecd-makes-historic-decision-to-open-accession-discussions-with-indonesia.html",
        },
        {
            "Tanggal": "2024-03-29",
            "Peristiwa": "Accession Roadmap diadopsi oleh Council",
            "Catatan": "Roadmap jadi dokumen publik yang mengatur terms, conditions, process",
            "Sumber": "Accession Roadmap",
            "Link": "https://one.oecd.org/document/C%282024%2966/FINAL/en/pdf",
        },
        {
            "Tanggal": "2024-05-02",
            "Peristiwa": "Menteri menyambut Roadmap pada MCM 2024",
            "Catatan": "Roadmap diposisikan sebagai jangkar reform agenda menuju 2045",
            "Sumber": "OECD press release",
            "Link": "https://www.oecd.org/en/about/news/press-releases/2024/05/ministers-welcome-roadmap-for-accession-discussions-with-indonesia.html",
        },
        {
            "Tanggal": "2025-06-03",
            "Peristiwa": "Indonesia menyerahkan Initial Memorandum (IM) pada MCM 2025",
            "Catatan": "IM memulai fase teknis komprehensif; ada request join Anti-Bribery Convention",
            "Sumber": "OECD press release",
            "Link": "https://www.oecd.org/en/about/news/press-releases/2025/06/indonesia-reaches-key-milestones-in-oecd-accession-process.html",
        },
    ]
)
milestones["Tanggal"] = pd.to_datetime(milestones["Tanggal"])

policy_areas = [
    "Structural reform",
    "Open trade and investment",
    "Inclusive growth",
    "Governance (integrity & anti-corruption)",
    "Environment, biodiversity and climate",
    "Digitalisation",
    "Infrastructure (quality infrastructure)",
]

committees = pd.DataFrame(
    [
        ("Investment Committee", "Open trade and investment"),
        ("Working Party on Responsible Business Conduct", "Open trade and investment"),
        ("Working Group on Bribery in International Business Transactions", "Governance (integrity & anti-corruption)"),
        ("Corporate Governance Committee", "Governance (integrity & anti-corruption)"),
        ("Committee on Financial Markets", "Structural reform"),
        ("Insurance and Private Pensions Committee", "Structural reform"),
        ("Competition Committee", "Structural reform"),
        ("Committee on Fiscal Affairs", "Structural reform"),
        ("Environment Policy Committee", "Environment, biodiversity and climate"),
        ("Chemicals and Biotechnology Committee", "Environment, biodiversity and climate"),
        ("Public Governance Committee", "Governance (integrity & anti-corruption)"),
        ("Committee of Senior Budget Officials", "Governance (integrity & anti-corruption)"),
        ("Regulatory Policy Committee", "Structural reform"),
        ("Regional Development Policy Committee", "Inclusive growth"),
        ("Committee on Statistics and Statistical Policy", "Structural reform"),
        ("Economic and Development Review Committee", "Structural reform"),
        ("Education Policy Committee", "Inclusive growth"),
        ("Employment, Labour and Social Affairs Committee", "Inclusive growth"),
        ("Health Committee", "Inclusive growth"),
        ("Trade Committee", "Open trade and investment"),
        ("Working Party on Export Credits", "Open trade and investment"),
        ("Committee for Agriculture", "Inclusive growth"),
        ("Fisheries Committee", "Inclusive growth"),
        ("Committee for Scientific and Technological Policy", "Digitalisation"),
        ("Digital Policy Committee", "Digitalisation"),
        ("Committee on Consumer Policy", "Structural reform"),
        ("Steel Committee", "Open trade and investment"),
        ("Shipbuilding Committee", "Open trade and investment"),
    ],
    columns=["Komite", "Area Roadmap (ringkas)"],
)

# -----------------------------------------------------------------------------
# 4) TAB STRUKTUR
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    [
        "🧭 Snapshot & Milestones",
        "📜 Roadmap: Rules & Guidelines",
        "🧩 Komite Review & Area Kebijakan",
    ]
)

# =============================================================================
# TAB 1
# =============================================================================
with tab1:
    st.header("Milestone proses aksesi (ringkas)")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Council decision", "20 Feb 2024", "Start accession discussions")
    c2.metric("Roadmap adopted", "29 Mar 2024", "Terms, conditions, process")
    c3.metric("Initial Memorandum", "3 Jun 2025", "Start technical phase")
    c4.metric("Komite review", "25", "Expert committees (Roadmap)")

    st.markdown("---")

    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("Timeline visual")
        ms_plot = milestones.sort_values("Tanggal").copy()
        ms_plot["Urut"] = range(1, len(ms_plot) + 1)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ms_plot["Tanggal"],
                y=ms_plot["Urut"],
                mode="markers+text",
                text=ms_plot["Peristiwa"],
                textposition="top left",
            )
        )
        fig.update_layout(
            height=420,
            xaxis_title="Tanggal",
            yaxis_title="Urutan",
            yaxis=dict(tickmode="array", tickvals=ms_plot["Urut"], ticktext=ms_plot["Urut"]),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption("Klik link di tabel untuk membuka sumber resmi.")

    with right:
        st.subheader("Tabel milestone")
        show_cols = ["Tanggal", "Peristiwa", "Catatan", "Sumber", "Link"]
        ms_table = milestones[show_cols].copy()
        ms_table["Tanggal"] = ms_table["Tanggal"].dt.strftime("%Y-%m-%d")

        st.dataframe(
            ms_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Link": st.column_config.LinkColumn("Link sumber", display_text="buka"),
            },
        )

        with st.expander("Makna Initial Memorandum (IM) dalam proses"):
            st.markdown(
                """
IM adalah self-assessment awal yang memetakan keselarasan regulasi, kebijakan, dan praktik Indonesia dengan standar serta best practices OECD.
IM menjadi titik masuk fase teknis: komite-komite OECD mulai melakukan review berbasis IM, background report, dan dialog mendalam.
"""
            )

# =============================================================================
# TAB 2
# =============================================================================
with tab2:
    st.header("Roadmap sebagai rujukan rules & guidelines")
    st.markdown(
        """
Roadmap mendefinisikan _terms, conditions, dan process_ untuk memastikan review yang konsisten lintas area kebijakan, lalu menutupnya dengan keputusan Council.
Struktur Roadmap bisa dibaca sebagai “aturan main” dari awal proses sampai rekomendasi reform dan _formal opinions_.
"""
    )

    st.subheader("Tahapan inti (high-level steps)")
    steps = pd.DataFrame(
        [
            ("1", "Council decision", "Council memutuskan membuka accession discussions"),
            ("2", "Accession Roadmap", "Roadmap diadopsi, menjadi dokumen publik"),
            ("3", "Initial Memorandum", "Self-assessment kandidat terhadap instrumen/standar OECD"),
            ("4", "Committee reviews", "Review teknis oleh komite, dialog & rekomendasi perubahan"),
            ("5", "Formal opinions", "Komite menyampaikan evaluasi resmi ke Council"),
            ("6", "Council decision", "Council memutuskan undangan keanggotaan"),
            ("7", "Accession", "Aksesi ke OECD Convention dan penyelesaian aspek legal/formal"),
        ],
        columns=["No", "Tahap", "Inti isi"],
    )
    st.dataframe(steps, use_container_width=True, hide_index=True)

    st.markdown("---")

    colA, colB = st.columns([1, 1])

    with colA:
        st.subheader("Kewajiban keanggotaan (apa yang diuji)")
        st.markdown(
            """
Ringkasan tema kewajiban dalam Roadmap:
1. Adherensi pada nilai, rule of law, demokrasi, dan working methods OECD (peer review, konsensus).
2. Penerimaan instrumen legal OECD yang berlaku pada saat undangan keanggotaan, dengan reservasi/observasi yang disepakati.
3. Penerimaan aturan tata kelola organisasi, klasifikasi informasi, dan kontribusi finansial organisasi.
4. Pengaturan privileges and immunities agar OECD dapat berfungsi independen.
"""
        )

        with st.expander("Catatan praktis untuk baca Roadmap"):
            st.markdown(
                """
Dua fokus review komite:
- _Willingness & ability_ untuk menerapkan instrumen legal OECD pada area komite.
- Kesesuaian kebijakan/praktik dengan best practices OECD (berbasis core principles di Roadmap).

Output review:
- Letter / isu dan rekomendasi per putaran dialog.
- Formal opinion ketika komite menilai level alignment memadai.
"""
            )

    with colB:
        st.subheader("Policy areas yang dicakup (ringkas)")
        df_areas = pd.DataFrame({"Policy area": policy_areas})
        st.dataframe(df_areas, use_container_width=True, hide_index=True)

        # Visual sederhana: count area
        area_counts = pd.DataFrame({"Area": policy_areas, "Jumlah": [1] * len(policy_areas)})
        fig_area = px.bar(area_counts, x="Area", y="Jumlah", title="Cakupan area Roadmap (indikatif)")
        fig_area.update_layout(height=360, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig_area, use_container_width=True)

    st.markdown("---")
    st.subheader("Roadmap Navigator (ringkas per bagian)")
    pick = st.selectbox(
        "Pilih bagian Roadmap yang ingin ditampilkan ringkasannya",
        [
            "Shared values, vision and priorities",
            "Obligations of OECD membership",
            "Technical reviews by OECD committees",
            "Initial Memorandum (IM)",
            "Formal opinions and Council decision",
        ],
    )

    if pick == "Shared values, vision and priorities":
        st.markdown(
            """
Bagian ini menekankan “like-mindedness” dan komitmen pada working methods OECD.
Council memonitor isu-isu nilai dan prioritas sepanjang proses, bukan hanya di akhir.
"""
        )
    elif pick == "Obligations of OECD membership":
        st.markdown(
            """
Bagian ini berisi daftar kewajiban: penerimaan OECD Convention, protokol, aturan tata kelola, instrumen legal substantif, serta aspek privileges & immunities.
Poin-poin ini biasanya diterjemahkan menjadi kebutuhan penyesuaian regulasi dan tata kelola domestik.
"""
        )
    elif pick == "Technical reviews by OECD committees":
        st.markdown(
            """
Roadmap menetapkan komite-komite yang berwenang melakukan review dan mengeluarkan formal opinion.
Prosesnya mencakup pengumpulan informasi, background report Sekretariat, dialog berulang, lalu kesimpulan.
"""
        )
    elif pick == "Initial Memorandum (IM)":
        st.markdown(
            """
IM adalah baseline dokumen: peta alignment awal Indonesia terhadap standar/instrumen OECD.
IM membuka fase teknis yang lebih padat dan biasanya memicu daftar isu prioritas per komite.
"""
        )
    else:
        st.markdown(
            """
Ketika komite puas terhadap alignment, komite mengadopsi formal opinion.
Council lalu mengambil keputusan final berdasarkan kumpulan formal opinions dan dokumen pendukung proses.
"""
        )

# =============================================================================
# TAB 3
# =============================================================================
with tab3:
    st.header("Komite review dan area kebijakan")
    st.markdown(
        """
Daftar komite di bawah ini diambil dari Roadmap Indonesia.
Klasifikasi area bersifat ringkas untuk navigasi pembaca, bukan pengganti struktur formal OECD.
"""
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        q = st.text_input("Cari komite (keyword)", value="")
    with c2:
        area_filter = st.selectbox(
            "Filter area",
            ["Semua"] + sorted(committees["Area Roadmap (ringkas)"].unique().tolist()),
        )

    df = committees.copy()
    if q.strip():
        df = df[df["Komite"].str.contains(q.strip(), case=False, na=False)]
    if area_filter != "Semua":
        df = df[df["Area Roadmap (ringkas)"] == area_filter]

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("Distribusi komite per area (ringkas)")
    dist = committees.groupby("Area Roadmap (ringkas)", as_index=False).size().rename(columns={"size": "Jumlah komite"})
    fig_dist = px.bar(dist, x="Area Roadmap (ringkas)", y="Jumlah komite", title="Jumlah komite per area (ringkas)")
    fig_dist.update_layout(height=420, margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig_dist, use_container_width=True)

    with st.expander("Apa yang biasanya diminta komite selama review?"):
        st.markdown(
            """
Bentuk permintaan informasi yang sering muncul:
- Klarifikasi regulasi (kerangka hukum, turunan, implementasi).
- Evidence pelaksanaan kebijakan (data, prosedur, enforcement).
- Rencana reform (timeline, penanggung jawab, indikator hasil).
- Konsistensi dengan instrumen legal OECD dan best practices lintas negara anggota.
"""
        )

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Sumber utama: OECD Accession Process page, Indonesia Accession Roadmap (adopted 29 Mar 2024), "
    "OECD press releases (20 Feb 2024; 2 May 2024; 3 Jun 2025)."
)

