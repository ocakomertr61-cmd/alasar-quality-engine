import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
import time

# --- 1. AYARLAR VE GÜVENLİK ---
VALID_USER = "alasar"
VALID_PASS = "30052012"
EXCEL_FILE = "alasar_kalite_veritabani.xlsx"

st.set_page_config(page_title="Alasar Quality Engine V9", layout="wide")

# --- 2. ASIL KALİTE MOTORU (TÜM DETAYLARIYLA) ---
def kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    hata_orani = (toplam_hata / G3) if G3 > 0 else 0
    # Hassas TRI Puanlama Mantığı
    temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
    t3_skor = max(temel_oran * (1 + (J3*0.03 + K3*0.05)), toplam_hata / 20) if toplam_hata > 0 else 0.0
    
    # Karar Algoritması
    red_mi = (hata_orani > 0.05 or (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or t3_skor >= 5.0)
    sartli_mi = False if red_mi else (t3_skor > 1.7 or (J3 + K3) >= 6)
    
    if red_mi: return "RED", "🔴", t3_skor, "#FF4B4B" 
    elif sartli_mi: return "SARI", "🟡", t3_skor, "#FFD700" 
    else: return "UYGUN", "🟢", t3_skor, "#28A745" 

# --- 3. EXCEL VE OTURUM YÖNETİMİ ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'onay_listesi' not in st.session_state: st.session_state.onay_listesi = []

def excele_kaydet(veri):
    try:
        # Fotoğrafları Excel'e yazmıyoruz (dosyayı bozmasın diye)
        temiz = {k: v for k, v in veri.items() if not str(k).startswith('Foto_')}
        df_yeni = pd.DataFrame([temiz])
        if not os.path.exists(EXCEL_FILE):
            df_yeni.to_excel(EXCEL_FILE, index=False)
        else:
            df_eski = pd.read_excel(EXCEL_FILE)
            pd.concat([df_eski, df_yeni], ignore_index=True).to_excel(EXCEL_FILE, index=False)
        return True
    except: return False

# --- 4. GİRİŞ EKRANI ---
if not st.session_state.auth:
    st.markdown("<h2 style='text-align:center;'>ALASAR QUALITY ENGINE LOGIN</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Kullanıcı Adı").strip()
        p = st.text_input("Şifre", type="password").strip()
        if st.form_submit_button("Sisteme Giriş"):
            if u == VALID_USER and p == VALID_PASS:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Hatalı bilgiler!")
    st.stop()

# --- 5. ANA PANEL ---
else:
    with st.sidebar:
        st.write(f"👤 **{VALID_USER.upper()}**")
        if st.button("Güvenli Çıkış"):
            st.session_state.auth = False
            st.rerun()
        st.divider()
        mod = st.radio("Menü Seçimi:", ["Hatta Veri Girişi", "Yönetici Onay Paneli", "Genel Arşiv"])

    # --- MOD 1: VERİ GİRİŞİ (OPERATÖR) ---
    if mod == "Hatta Veri Girişi":
        st.header("🏭 Üretim Hattı Giriş Terminali")
        with st.form("op_form"):
            c1, c2, c3 = st.columns(3)
            op_ad = c1.text_input("Ad Soyad / Kaşe")
            lot = c2.text_input("Parti No (LOT)", "LOT-")
            kontrol_adet = c3.number_input("Kontrol Edilen Adet", 1, value=100)
            
            st.write("### Hata ve Risk Girişleri")
            h1, h2, h3, h4 = st.columns(4)
            j3 = h1.number_input("P1 (Kritik) Adet", 0); p1p = h1.number_input("P1 Puan", 1.0)
            k3 = h2.number_input("P2 (Majör) Adet", 0); p2p = h2.number_input("P2 Puan", 1.0)
            l3 = h3.number_input("P3 (Minör) Adet", 0); p3p = h3.number_input("P3 Puan", 1.0)
            m3 = h4.number_input("P4 (Görsel) Adet", 0); p4p = h4.number_input("P4 Puan", 1.0)
            
            notlar = st.text_area("Operatör Notu")
            analiz_et = st.form_submit_button("SİSTEM ANALİZİNİ ÇALIŞTIR")

        if analiz_et:
            karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol_adet, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
            st.session_state.gecici = {
                "Tarih": datetime.now().strftime("%d-%m-%Y %H:%M"), "Operatör": op_ad, "LOT": lot,
                "Kontrol": kontrol_adet, "TRI": round(skor, 3), "Karar": karar, "Renk": renk, "Not": notlar,
                "P1": j3, "P2": k3, "P3": l3, "P4": m3
            }

        if 'gecici' in st.session_state:
            g = st.session_state.gecici
            st.markdown(f"<div style='background-color:{g['Renk']}; padding:20px; border-radius:10px; text-align:center;'><h1 style='color:white;'>{g['Karar']} (TRI: {g['TRI']})</h1></div>", unsafe_allow_html=True)
            
            if g['Karar'] != "UYGUN":
                st.warning("📸 Lütfen Uygunsuzluk Fotoğraflarını Ekleyin!")
                f1 = st.file_uploader("Fotoğraf 1", type=['jpg','png'])
                if st.button("KAYDI YÖNETİCİYE GÖNDER"):
                    g["Yönetici Durumu"] = "BEKLİYOR"
                    st.session_state.onay_listesi.append(g)
                    st.success("Kayıt yönetici onayına düştü.")
                    del st.session_state.gecici
                    st.rerun()
            else:
                if st.button("KAYDI TAMAMLA VE EXCEL'E İŞLE"):
                    g["Yönetici Durumu"] = "OTOMATİK ONAY"
                    if excele_kaydet(g):
                        st.success("✅ Veri başarıyla arşivlendi.")
                        del st.session_state.gecici
                        st.rerun()

    # --- MOD 2: YÖNETİCİ ONAY ---
    elif mod == "Yönetici Onay Paneli":
        st.header("⚖️ Karar Bekleyen Kayıtlar")
        for i, b_veri in enumerate(st.session_state.onay_listesi):
            with st.expander(f"{b_veri['LOT']} - {b_veri['Operatör']} ({b_veri['Karar']})"):
                st.write(f"**TRI Skoru:** {b_veri['TRI']} | **Hatalar:** P1:{b_veri['P1']}, P2:{b_veri['P2']}, P3:{b_veri['P3']}, P4:{b_veri['P4']}")
                y_karar = st.selectbox("Yönetici Kararı", ["Şartlı Kabul", "Karantina", "Hurda / Red"], key=f"y_k_{i}")
                y_not = st.text_input("Yönetici Notu", key=f"y_n_{i}")
                if st.button("ONAYLA VE ARŞİVLE", key=f"y_b_{i}"):
                    b_veri["Yönetici Durumu"] = y_karar
                    b_veri["Yönetici Notu"] = y_not
                    if excele_kaydet(b_veri):
                        st.session_state.onay_listesi.pop(i)
                        st.success("Excel güncellendi.")
                        st.rerun()

    # --- MOD 3: GENEL ARŞİV ---
    elif mod == "Genel Arşiv":
        st.header("📜 Alasar Kalite Veritabanı")
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            st.dataframe(df.iloc[::-1], use_container_width=True)
            with open(EXCEL_FILE, "rb") as f:
                st.download_button("Excel Dosyasını İndir", f, file_name=EXCEL_FILE)
        else: st.info("Henüz kayıt bulunmamaktadır.")