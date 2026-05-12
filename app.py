import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- 1. KULLANICI VE YETKİ VERİTABANI ---
# Buraya istediğiniz kadar operatör ekleyebilirsiniz.
USERS = {
    "alasar": {"pass": "30052012", "role": "admin", "name": "Ömer Ocak (Müdür)"},
    "operator1": {"pass": "1234", "role": "op", "name": "Kalite Operatörü 1"},
    "operator2": {"pass": "5678", "role": "op", "name": "Kalite Operatörü 2"}
}

EXCEL_FILE = "alasar_kalite_veritabani.xlsx"

st.set_page_config(page_title="Alasar Quality Engine V10", layout="wide")

# --- 2. KALİTE MOTORU (KORUNAN ALGORİTMA) ---
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

# --- 3. OTURUM YÖNETİMİ ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'onay_listesi' not in st.session_state: st.session_state.onay_listesi = []

def excele_kaydet(veri):
    try:
        temiz = {k: v for k, v in veri.items() if not str(k).startswith('Foto_')}
        df_yeni = pd.DataFrame([temiz])
        if not os.path.exists(EXCEL_FILE):
            df_yeni.to_excel(EXCEL_FILE, index=False)
        else:
            df_eski = pd.read_excel(EXCEL_FILE)
            pd.concat([df_eski, df_yeni], ignore_index=True).to_excel(EXCEL_FILE, index=False)
        return True
    except: return False

# --- 4. GİRİŞ EKRANI (LOGIN) ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color:#28A745;'>ALASAR QUALITY LOGIN</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        u_name = st.text_input("Kullanıcı Adı").strip()
        u_pass = st.text_input("Şifre", type="password").strip()
        if st.form_submit_button("Sisteme Giriş Yap"):
            if u_name in USERS and USERS[u_name]["pass"] == u_pass:
                st.session_state.auth = True
                st.session_state.user_role = USERS[u_name]["role"]
                st.session_state.user_name = USERS[u_name]["name"]
                st.rerun()
            else:
                st.error("❌ Yetkisiz Giriş! Lütfen bilgilerinizi kontrol edin.")
    st.stop()

# --- 5. ANA PANEL (YETKİ KONTROLLÜ) ---
else:
    with st.sidebar:
        st.success(f"Oturum Açık: \n**{st.session_state.user_name}**")
        if st.button("Çıkış Yap"):
            st.session_state.auth = False
            st.rerun()
        st.divider()
        
        # YETKİYE GÖRE MENÜ GÖSTERİMİ
        if st.session_state.user_role == "admin":
            menu = st.radio("Yönetici Menüsü:", ["Hatta Veri Girişi", "⚖️ YÖNETİCİ ONAY PANELİ", "📜 GENEL ARŞİV"])
        else:
            menu = st.radio("Operatör Menüsü:", ["Hatta Veri Girişi"])
            st.warning("Diğer panellere erişim yetkiniz yoktur.")

    # --- MOD 1: VERİ GİRİŞİ (HERKES GÖREBİLİR) ---
    if menu == "Hatta Veri Girişi":
        st.header("🏭 Üretim Hattı Giriş Terminali")
        with st.form("op_form"):
            c1, c2, c3 = st.columns(3)
            op_ad = c1.text_input("Operatör / Kaşe", value=st.session_state.user_name)
            lot = c2.text_input("Parti No (LOT)", "LOT-")
            kontrol_adet = c3.number_input("Kontrol Edilen Adet", 1, value=100)
            
            st.write("### Hata Girişleri")
            h1, h2, h3, h4 = st.columns(4)
            j3 = h1.number_input("P1 (Kritik)", 0); p1p = h1.number_input("P1 Puan", 1.0)
            k3 = h2.number_input("P2 (Majör)", 0); p2p = h2.number_input("P2 Puan", 1.0)
            l3 = h3.number_input("P3 (Minör)", 0); p3p = h3.number_input("P3 Puan", 1.0)
            m3 = h4.number_input("P4 (Görsel)", 0); p4p = h4.number_input("P4 Puan", 1.0)
            
            analiz_et = st.form_submit_button("ANALİZ ET VE GÖNDER")

        if analiz_et:
            karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol_adet, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
            st.session_state.gecici = {
                "Tarih": datetime.now().strftime("%d-%m-%Y %H:%M"), "Operatör": op_ad, "LOT": lot,
                "TRI": round(skor, 3), "Karar": karar, "Renk": renk, "P1": j3, "P2": k3, "P3": l3, "P4": m3
            }

        if 'gecici' in st.session_state:
            g = st.session_state.gecici
            st.markdown(f"<div style='background-color:{g['Renk']}; padding:20px; border-radius:10px; text-align:center;'><h1 style='color:white;'>{g['Karar']} (TRI: {g['TRI']})</h1></div>", unsafe_allow_html=True)
            
            if g['Karar'] != "UYGUN":
                st.warning("⚠️ Bu kayıt yönetici onayına sunulacaktır.")
                if st.button("KAYDI ONAYA GÖNDER"):
                    st.session_state.onay_listesi.append(g)
                    st.success("Kayıt yöneticinin önüne düştü.")
                    del st.session_state.gecici
                    st.rerun()
            else:
                if st.button("UYGUN KAYDI ARŞİVLE"):
                    if excele_kaydet(g):
                        st.success("✅ Veri Excel'e işlendi.")
                        del st.session_state.gecici
                        st.rerun()

    # --- MOD 2: YÖNETİCİ ONAY PANELİ (SADECE ADMİN) ---
    elif menu == "⚖️ YÖNETİCİ ONAY PANELİ":
        st.header("⚖️ Karar Bekleyen Kritik Kayıtlar")
        if not st.session_state.onay_listesi:
            st.info("Bekleyen onay bulunmamaktadır.")
        else:
            for i, b_veri in enumerate(st.session_state.onay_listesi):
                with st.expander(f"{b_veri['LOT']} - {b_veri['Operatör']} (Durum: {b_veri['Karar']})"):
                    st.write(f"**TRI Skoru:** {b_veri['TRI']}")
                    y_karar = st.selectbox("Yönetici Nihai Kararı", ["Şartlı Kabul", "Karantina", "İade/Red"], key=f"y_k_{i}")
                    if st.button("KARARI ONAYLA VE EXCEL'E YAZ", key=f"y_b_{i}"):
                        b_veri["Final_Durum"] = y_karar
                        if excele_kaydet(b_veri):
                            st.session_state.onay_listesi.pop(i)
                            st.success("Karar başarıyla kaydedildi.")
                            st.rerun()

    # --- MOD 3: GENEL ARŞİV (SADECE ADMİN) ---
    elif menu == "📜 GENEL ARŞİV":
        st.header("📜 Alasar Kalite Veritabanı")
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            st.dataframe(df.iloc[::-1], use_container_width=True)
            with open(EXCEL_FILE, "rb") as f:
                st.download_button("Raporu İndir (.xlsx)", f, file_name=EXCEL_FILE)
        else: st.info("Henüz kayıt bulunmamaktadır.")
