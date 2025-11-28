






# app.py
import streamlit as st

# ========== DEFINISI HALAMAN ==========

pages = [
    st.Page(page="pages/page1.py",  
            title="📈 Pertumbuhan Ekonomi & GDP",          
            icon="📈"),
    st.Page(page="pages/page2.py",  
            title="💰 PDB Per Kapita & Struktur Ekonomi",  
            icon="💰"),
    st.Page(page="pages/page3.py",  
            title="🔥 Inflasi & Harga Konsumen",          
            icon="🔥"),
    st.Page(page="pages/page4.py",  
            title="👷 Pengangguran & Tenaga Kerja",        
            icon="👷"),
    st.Page(page="pages/page5.py",  
            title="🌐 Perdagangan Internasional",         
            icon="🌐"),
    st.Page(page="pages/page6.py",  
            title="💼 Investasi (FDI & Kapital)",         
            icon="💼"),
    st.Page(page="pages/page7.py",  
            title="📉 Kemiskinan & Ketimpangan (GINI)",   
            icon="📉"),
    st.Page(page="pages/page8.py",  
            title="👥 Populasi & Demografi",              
            icon="👥"),
    st.Page(page="pages/page9.py",  
            title="🏥 Kesehatan & Pendidikan",            
            icon="🏥"),
    st.Page(page="pages/page10.py", 
            title="🌱 Energi & Lingkungan",               
            icon="🌱"),
]

pg = st.navigation(pages, position="sidebar", expanded=True)
pg.run()
