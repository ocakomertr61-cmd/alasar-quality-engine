import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io 
import time
import os

# --- 1. GÜVENLİK VE ROL VERİTABANI ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "alasar": {"pass": "30052012", "role": "Kalite Müdürü", "full_name": "Ömer Ocak"},
        "genelmudur": {"pass": "patron456", "role": "Genel Müdür", "full_name": "Genel Müdürlük"},
        "operator": {"pass": "op789", "role": "Üretim-Operatör", "full_name": "Hatta Görevli Operatör"}
    }

GENERAL_USER = "alasar"
GENERAL_PASS = "30052012"
EXCEL_FILE = "alasar_kalite_veritabani.xlsx"

# --- 2. SAYFA AYARLARI ---
st.set_page_config(page_title="Alasar Quality Engine V14", layout="wide")

# --- 3. KALİTE MOTORU (V6.7 ÇEKİRDEK) ---
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

# --- 4. OTURUM YÖNETİMİ ---
if 'genel_auth' not in st.session_state: st.session_state.genel_auth = False
if 'panel_auth' not in st.session_state: st.session_state.panel_auth = None
if 'onay_bekleyenler' not in st.session_state: st.session_state.onay_bekleyenler = [] 
if 'ana_veritabani' not in st.session_state: st.session_state.ana_veritabani = pd.DataFrame()

# --- 5. BİRİNCİ KAPI: GENEL SİTE GİRİŞİ ---
if not st.session_state.genel_auth:
    st.markdown("<h2 style='text-align:center;'>ALASAR QUALITY ENGINE</h2>", unsafe_allow_html=True)
    with st.form("genel_login"):
        u = st.text_input("Giriş Adı").strip()
        p = st.text_input("Giriş Şifresi", type="password").strip()
        if st.form_submit_button("Sistemi Aç"):
            if u == GENERAL_USER and p == GENERAL_PASS:
                st.session_state.genel_auth = True
                st.rerun()
            else: st.error("Geçersiz giriş bilgileri.")
    st.stop()

# --- 6. İKİNCİ KAPI: PANEL SEÇİMİ VE YETKİ ---
else:
    if st.session_state.panel_auth is None:
        st.subheader("Lütfen Erişim Alanınızı Seçiniz")
        p_secim = st.selectbox("Panel:", ["Seçiniz...", "Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
        
        if p_secim != "Seçiniz...":
            u_key = "operator" if p_secim == "Üretim-Operatör" else ("alasar" if p_secim == "Kalite Müdürü" else "genelmudur")
            p_sifre = st.text_input(f"{p_secim} Şifresi", type="password")
            if st.button("Doğrula ve Gir"):
                if p_sifre == st.session_state.user_db[u_key]["pass"]:
                    st.session_state.panel_auth = u_key
                    st.rerun()
                else: st.error("Bu panele giriş yetkiniz bulunmamaktadır.")
        
        if st.button("Sistemden Çıkış"):
            st.session_state.genel_auth = False
            st.rerun()
        st.stop()

    # --- PANEL İÇİ YÖNETİM ---
    user_key = st.session_state.panel_auth
    u_info = st.session_state.user_db[user_key]
    
    st.sidebar.title(f"📍 {u_info['role']}")
    st.sidebar.write(f"Kullanıcı: {u_info['full_name']}")
    
    if st.sidebar.button("Geri Dön / Paneli Kapat"):
        st.session_state.panel_auth = None
        st.rerun()

    # Şifre Değiştirme (Kişiye Özel)
    with st.sidebar.expander("🔑 Şifremi Değiştir"):
        e_s = st.text_input("Mevcut Şifre", type="password")
        y_s = st.text_input("Yeni Şifre", type="password")
        if st.button("Şifreyi Güncelle"):
            if e_s == u_info["pass"]:
                st.session_state.user_db[user_key]["pass"] = y_s
                st.success("Şifre güncellendi!"); time.sleep(1); st.rerun()
            else: st.error("Mevcut şifre yanlış!")

    # --- MOD 1: ÜRETİM OPERATÖR PANELİ (V6.7 TAM HALİ) ---
    if u_info['role'] == "Üretim-Operatör":
        st.header("🏭 Üretim Hattı Giriş Terminali")
        with st.form("veri_giris_formu"):
            c1, c2, c3 = st.columns(3)
            lot = c1.text_input("Parti No", "LOT-")
            sevk = c2.number_input("Toplam Sevk Adeti", 1, value=1000)
            kontrol = c3.number_input("Kontrol Edilen Adet", 1, value=100)
            
            st.divider()
            st.subheader("Hata Adetleri ve Risk Puanları")
            h1, h2, h3, h4 = st.columns(4)
            j3 = h1.number_input("P1 (Kritik) Adet", 0); p1p = h1.number_input("P1 Puan", 1.0)
            k3 = h2.number_input("P2 (Majör) Adet", 0); p2p = h2.number_input("P2 Puan", 1.0)
            l3 = h3.number_input("P3 (Minör) Adet", 0); p3p = h3.number_input("P3 Puan", 1.0)
            m3 = h4.number_input("P4 (Görsel) Adet", 0); p4p = h4.number_input("P4 Puan", 1.0)
            
            if st.form_submit_button("SİSTEM ANALİZİNİ BAŞLAT"):
                karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
                st.session_state.gecici = {
                    "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "LOT": lot, "Sevk": sevk, "Kontrol": kontrol,
                    "TRI": round(skor, 4), "Sistem": karar, "Renk": renk, "P1": j3, "P2": k3, "P3": l3, "P4": m3
                }

        if 'gecici' in st.session_state:
            g = st.session_state.gecici
            st.markdown(f"<div style='background-color:{g['Renk']}; padding:20px; border-radius:10px; text-align:center;'><h1 style='color:white;'>KARAR: {g['Sistem']} (TRI: {g['TRI']})</h1></div>", unsafe_allow_html=True)
            
            if g['Sistem'] != "UYGUN":
                st.warning("📸 Lütfen 3 kanıt fotoğrafı yükleyin.")
                f1 = st.file_uploader("Genel", type=['jpg', 'png'], key="f1")
                f2 = st.file_uploader("Detay", type=['jpg', 'png'], key="f2")
                f3 = st.file_uploader("Etiket", type=['jpg', 'png'], key="f3")
                if st.button("KAYDI YÖNETİCİYE GÖNDER"):
                    if f1 and f2 and f3:
                        g.update({"Foto_1": f1.read(), "Foto_2": f2.read(), "Foto_3": f3.read(), "Durum": "ONAY BEKLİYOR"})
                        st.session_state.onay_bekleyenler.append(g)
                        st.success("Kayıt Ömer Bey'e iletildi."); del st.session_state.gecici; time.sleep(1.5); st.rerun()
                    else: st.error("Fotoğraflar eksik!")
            else:
                if st.button("UYGUN KAYDI ARŞİVLE"):
                    st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([g])])
                    st.success("Kayıt arşive eklendi."); del st.session_state.gecici; time.sleep(1.5); st.rerun()
