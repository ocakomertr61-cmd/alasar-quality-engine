import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. SİSTEM AYARLARI VE KULLANICI VERİTABANI ---
# Başlangıç şifreleri (Kullanıcı ilk girişte bunları kullanır)
if 'user_creds' not in st.session_state:
    st.session_state.user_creds = {
        "alasar": {"pass": "30052012", "role": "Kalite Müdürü"},
        "genelmudur": {"pass": "patron456", "role": "Genel Müdür"},
        "operator": {"pass": "op789", "role": "Üretim-Operatör"}
    }

GENERAL_USER = "alasar"
GENERAL_PASS = "30052012"
EXCEL_FILE = "alasar_kalite_veritabani.xlsx"

st.set_page_config(page_title="Alasar Quality Engine V12", layout="wide")

# --- 2. KALİTE MOTORU (ASIL HESAPLAMA) ---
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

# --- 3. OTURUM DURUMLARI ---
if 'genel_giris' not in st.session_state: st.session_state.genel_giris = False
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None

# --- 4. BİRİNCİ KAPI: GENEL GİRİŞ ---
if not st.session_state.genel_giris:
    st.markdown("<h2 style='text-align:center;'>ALASAR QUALITY ENGINE</h2>", unsafe_allow_html=True)
    with st.form("genel_login"):
        u = st.text_input("Genel Kullanıcı Adı").strip()
        p = st.text_input("Genel Şifre", type="password").strip()
        if st.form_submit_button("Sisteme Giriş"):
            if u == GENERAL_USER and p == GENERAL_PASS:
                st.session_state.genel_giris = True
                st.rerun()
            else: st.error("Genel erişim reddedildi!")
    st.stop()

# --- 5. İKİNCİ KAPI: PANEL VE KİŞİSEL ŞİFRE ---
else:
    if st.session_state.aktif_user is None:
        st.subheader("Lütfen Yetki Alanınızı Seçiniz")
        secim = st.selectbox("Panel Seçin:", ["Seçiniz...", "Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
        
        if secim != "Seçiniz...":
            # Panel ismine göre kullanıcı adını eşleştiriyoruz
            u_key = "operator" if secim == "Üretim-Operatör" else ("alasar" if secim == "Kalite Müdürü" else "genelmudur")
            
            sifre_onay = st.text_input(f"{secim} Şifresi", type="password")
            if st.button("Paneli Aç"):
                if sifre_onay == st.session_state.user_creds[u_key]["pass"]:
                    st.session_state.aktif_user = u_key
                    st.rerun()
                else:
                    st.error("Hatalı Panel Şifresi!")
        
        if st.button("Sistemden Çıkış Yap"):
            st.session_state.genel_giris = False
            st.rerun()
        st.stop()

    # --- PANEL İÇİ: AYARLAR VE ŞİFRE DEĞİŞTİRME ---
    user_info = st.session_state.user_creds[st.session_state.aktif_user]
    st.sidebar.title(f"📍 {user_info['role']}")
    st.sidebar.write(f"Kullanıcı: {st.session_state.aktif_user}")
    
    if st.sidebar.button("Paneli Kapat / Geri Dön"):
        st.session_state.aktif_user = None
        st.rerun()

    # --- ŞİFRE DEĞİŞTİRME MODÜLÜ (SIDEBAR) ---
    with st.sidebar.expander("🔑 Şifremi Değiştir"):
        eski_sifre = st.text_input("Mevcut Şifre", type="password")
        yeni_sifre = st.text_input("Yeni Şifre", type="password")
        if st.button("Şifreyi Güncelle"):
            if eski_sifre == user_info["pass"]:
                st.session_state.user_creds[st.session_state.aktif_user]["pass"] = yeni_sifre
                st.success("Şifreniz başarıyla değiştirildi!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Mevcut şifre yanlış!")

    # --- PANEL İÇERİKLERİ (YETKİYE GÖRE) ---
    if user_info['role'] == "Üretim-Operatör":
        st.header("🏭 Üretim Hattı Veri Girişi")
        # Operatör Formu (TRI Motoru Buraya Bağlı)
        with st.form("op_form"):
            lot = st.text_input("LOT No")
            kontrol = st.number_input("Kontrol Adet", value=100)
            j3 = st.number_input("P1 Hatası", 0)
            if st.form_submit_button("Analiz Et"):
                # Burada kalite_motoru_hesapla fonksiyonu çalışacak
                st.info("Analiz yapıldı.")

    elif user_info['role'] == "Kalite Müdürü":
        st.header("⚖️ Onay ve Denetim Paneli")
        st.write("Sadece Müdür yetkisiyle görünen alan.")
        # Excel Tablosu ve Onay Butonları Buraya Gelecek

    elif user_info['role'] == "Genel Müdür":
        st.header("📈 Genel Performans Dashboard")
        st.write("Sadece Patron yetkisiyle görünen grafik alanı.")
