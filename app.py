import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os
import io

# --- GÜVENLİK AYARLARI ---
VALID_USERNAME = "alasar"
VALID_PASSWORD = "30052012"
EXCEL_FILE = "alasar_kalite_veritabani.xlsx"

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Alasar Quality Engine", layout="wide")

# --- KALİTE MOTORU (KNOW-HOW ALGORİTMASI) ---
def kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    hata_orani = (toplam_hata / G3) if G3 > 0 else 0
    # Sizin özel TRI katsayılarınız
    temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
    t3_skor = max(temel_oran * (1 + (J3*0.03 + K3*0.05)), toplam_hata / 20) if toplam_hata > 0 else 0.0
    
    # Karar Mantığı
    red_mi = (hata_orani > 0.05 or (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or t3_skor >= 5.0)
    sartli_mi = False if red_mi else (t3_skor > 1.7 or (J3 + K3) >= 6)
    
    if red_mi: return "RED", "🔴", t3_skor, "#FF4B4B" 
    elif sartli_mi: return "SARI", "🟡", t3_skor, "#FFD700" 
    else: return "UYGUN", "🟢", t3_skor, "#28A745" 

# --- MOBİL CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3.5em; border-radius: 12px; font-weight: bold; }
    .stNumberInput input { font-size: 18px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- OTURUM VE EXCEL YÖNETİMİ ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def excele_yaz(yeni_veri_dict):
    try:
        temiz_veri = {k: v for k, v in yeni_veri_dict.items() if not str(k).startswith('Foto_')}
        yeni_df = pd.DataFrame([temiz_veri])
        if not os.path.isfile(EXCEL_FILE):
            yeni_df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        else:
            eski_df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
            pd.concat([eski_df, yeni_df], ignore_index=True).to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        return True
    except Exception as e:
        st.error(f"Excel hatası: {e}"); return False

# --- GİRİŞ KONTROLÜ ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align:center;'>ALASAR QUALITY ENGINE</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş Yap"):
            if u == VALID_USERNAME and p == VALID_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Hatalı Giriş!")
    st.stop()

# --- ANA PANEL ---
else:
    top_c1, top_c2 = st.columns([9, 1])
    top_c1.title("🏭 Alasar Kalite Terminali")
    if top_c2.button("Çıkış"):
        st.session_state.authenticated = False
        st.rerun()

    menu = st.sidebar.radio("Menü:", ["Veri Girişi", "Yönetici Paneli"])

    if menu == "Veri Girişi":
        with st.form("main_form"):
            c1, c2, c3 = st.columns(3)
            op = c1.text_input("Operatör Adı")
            lot = c2.text_input("LOT No", "LOT-")
            kontrol = c3.number_input("Kontrol Adeti", 1, value=100)
            
            st.write("### Hata Girişi")
            h1, h2, h3, h4 = st.columns(4)
            j3 = h1.number_input("P1 Adet", 0); p1p = h1.number_input("P1 Puan", 1.0)
            k3 = h2.number_input("P2 Adet", 0); p2p = h2.number_input("P2 Puan", 1.0)
            l3 = h3.number_input("P3 Adet", 0); p3p = h3.number_input("P3 Puan", 1.0)
            m3 = h4.number_input("P4 Adet", 0); p4p = h4.number_input("P4 Puan", 1.0)
            
            if st.form_submit_button("ANALİZ ET VE GÖNDER"):
                karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
                veriler = {
                    "Tarih": datetime.now().strftime("%d-%m-%Y %H:%M"), "Operatör": op, "LOT": lot,
                    "TRI": round(skor, 3), "Karar": karar, "P1": j3, "P2": k3, "P3": l3, "P4": m3
                }
                if excele_yaz(veriler):
                    st.markdown(f"<h2 style='color:{renk}; text-align:center;'>{ikon} Karar: {karar} (TRI: {round(skor, 2)})</h2>", unsafe_allow_html=True)
                    st.success("Kayıt Excel'e işlendi.")
                    time.sleep(2)
                    st.rerun()

    elif menu == "Yönetici Paneli":
        st.subheader("📊 Kayıtlı Veriler")
        if os.path.exists(EXCEL_FILE):
            st.dataframe(pd.read_excel(EXCEL_FILE).iloc[::-1], use_container_width=True)