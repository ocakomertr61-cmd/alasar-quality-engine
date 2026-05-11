import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os

# --- 1. GÜVENLİK VE DOSYA AYARLARI ---
VALID_USERNAME = "alasar"
VALID_PASSWORD = "30052012"
EXCEL_FILE = "alasar_kalite_veritabani.xlsx"

# --- 2. SAYFA VE MOBİL TASARIM ---
st.set_page_config(page_title="Alasar Quality Engine", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3.5em; border-radius: 12px; font-weight: bold; }
    @media (max-width: 640px) { h1 { font-size: 22px !important; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. KALİTE MOTORU (ASIL KNOW-HOW BURADA) ---
def kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    hata_orani = (toplam_hata / G3) if G3 > 0 else 0
    temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
    t3_skor = max(temel_oran * (1 + (J3*0.03 + K3*0.05)), toplam_hata / 20) if toplam_hata > 0 else 0.0
    
    red_mi = (hata_orani > 0.05 or (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or t3_skor >= 5.0)
    sartli_mi = False if red_mi else (t3_skor > 1.7 or (J3 + K3) >= 6)
    
    if red_mi: return "RED", "🔴", t3_skor, "#FF4B4B" 
    elif sartli_mi: return "SARI", "🟡", t3_skor, "#FFD700" 
    else: return "UYGUN", "🟢", t3_skor, "#28A745" 

# --- 4. EXCEL KAYIT MEKANİZMASI ---
def excele_yaz(yeni_veri_dict):
    try:
        yeni_df = pd.DataFrame([yeni_veri_dict])
        if not os.path.isfile(EXCEL_FILE):
            yeni_df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        else:
            eski_df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
            pd.concat([eski_df, yeni_df], ignore_index=True).to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        return True
    except: return False

# --- 5. GİRİŞ KONTROLÜ (LOGIN) ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align:center;'>ALASAR QUALITY LOGIN</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Kullanıcı").strip()
        p = st.text_input("Şifre", type="password").strip()
        if st.form_submit_button("Giriş"):
            if u == VALID_USERNAME and p == VALID_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hata!")
    st.stop()

# --- 6. ANA PANEL (ESKİ PANELİN TAM HALİ) ---
else:
    st.sidebar.title(f"Hoş Geldin, {VALID_USERNAME}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.auth = False
        st.rerun()

    menu = st.sidebar.radio("İşlem Seçiniz:", ["Üretim Hattı Girişi", "Yönetici Arşivi"])

    if menu == "Üretim Hattı Girişi":
        with st.form("full_form"):
            st.subheader("📋 Kalite Veri Girişi")
            c1, c2, c3 = st.columns(3)
            op_ad = c1.text_input("Operatör")
            lot = c2.text_input("Lot No", "LOT-")
            sevk = c3.number_input("Sevk Adeti", 1, value=1000)
            kontrol = c3.number_input("Kontrol Adeti", 1, value=100)

            st.divider()
            h1, h2, h3, h4 = st.columns(4)
            j3 = h1.number_input("P1 (Kritik)", 0); p1p = h1.number_input("P1 Puan", 1.0)
            k3 = h2.number_input("P2 (Majör)", 0); p2p = h2.number_input("P2 Puan", 1.0)
            l3 = h3.number_input("P3 (Minör)", 0); p3p = h3.number_input("P3 Puan", 1.0)
            m3 = h4.number_input("P4 (Görsel)", 0); p4p = h4.number_input("P4 Puan", 1.0)
            
            if st.form_submit_button("SİSTEM ANALİZİNİ ÇALIŞTIR"):
                karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
                
                # Sonuç Paneli
                st.markdown(f"""<div style="background-color:{renk}; padding:15px; border-radius:10px; text-align:center;">
                    <h2 style="color:white;">{ikon} {karar} (TRI: {round(skor, 2)})</h2></div>""", unsafe_allow_html=True)
                
                veri = {
                    "Tarih": datetime.now().strftime("%d-%m-%Y %H:%M"), "Operatör": op_ad, 
                    "LOT": lot, "Sevk": sevk, "Kontrol": kontrol, "TRI": round(skor, 3), 
                    "Durum": karar, "P1": j3, "P2": k3, "P3": l3, "P4": m3
                }
                if excele_yaz(veri): st.success("Veriler Excel'e işlendi.")

    elif menu == "Yönetici Arşivi":
        st.subheader("📜 Tüm Kalite Kayıtları")
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            st.dataframe(df.iloc[::-1], use_container_width=True)
            with open(EXCEL_FILE, "rb") as f:
                st.download_button("Raporu İndir (.xlsx)", f, file_name=EXCEL_FILE)