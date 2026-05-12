import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- 1. AYARLAR VE KULLANICI VERİTABANI ---
# Uygulama başladığında şifreleri tanımlıyoruz
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "alasar": {"pass": "30052012", "role": "Kalite Müdürü", "full_name": "Ömer Ocak"},
        "genelmudur": {"pass": "patron456", "role": "Genel Müdür", "full_name": "Genel Müdürlük"},
        "operator": {"pass": "op789", "role": "Üretim-Operatör", "full_name": "Üretim Hattı"}
    }

GENERAL_USER = "alasar"
GENERAL_PASS = "30052012"
EXCEL_FILE = "alasar_kalite_veritabani.xlsx"

st.set_page_config(page_title="Alasar Quality Engine V13", layout="wide")

# --- 2. ASIL KALİTE MOTORU (ASLA SİLİNMEYEN ÇEKİRDEK) ---
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

# --- 3. YETKİ VE OTURUM KONTROLÜ ---
if 'genel_auth' not in st.session_state: st.session_state.genel_auth = False
if 'panel_auth' not in st.session_state: st.session_state.panel_auth = None
if 'onay_listesi' not in st.session_state: st.session_state.onay_listesi = []

def excele_kaydet(veri):
    try:
        df_yeni = pd.DataFrame([veri])
        if not os.path.exists(EXCEL_FILE): df_yeni.to_excel(EXCEL_FILE, index=False)
        else:
            df_eski = pd.read_excel(EXCEL_FILE)
            pd.concat([df_eski, df_yeni], ignore_index=True).to_excel(EXCEL_FILE, index=False)
        return True
    except: return False

# --- 4. BİRİNCİ KAPI: GENEL GİRİŞ (HERKES BİLİR) ---
if not st.session_state.genel_auth:
    st.markdown("<h2 style='text-align:center;'>ALASAR QUALITY ENGINE</h2>", unsafe_allow_html=True)
    with st.form("genel_giris"):
        gu = st.text_input("Giriş Adı").strip()
        gp = st.text_input("Giriş Şifresi", type="password").strip()
        if st.form_submit_button("Sistemi Aç"):
            if gu == GENERAL_USER and gp == GENERAL_PASS:
                st.session_state.genel_auth = True
                st.rerun()
            else: st.error("Erişim reddedildi.")
    st.stop()

# --- 5. İKİNCİ KAPI: PANEL SEÇİMİ VE ŞİFRESİ ---
else:
    if st.session_state.panel_auth is None:
        st.subheader("Hoş Geldiniz, Lütfen Panelinizi Seçin")
        p_secim = st.selectbox("Erişim Alanı:", ["Seçiniz...", "Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
        
        if p_secim != "Seçiniz...":
            # Panel bazlı kullanıcı anahtarı eşleme
            u_key = "operator" if p_secim == "Üretim-Operatör" else ("alasar" if p_secim == "Kalite Müdürü" else "genelmudur")
            
            p_sifre = st.text_input(f"{p_secim} Şifresi", type="password")
            if st.button("Paneli Doğrula"):
                if p_sifre == st.session_state.user_db[u_key]["pass"]:
                    st.session_state.panel_auth = u_key
                    st.rerun()
                else: st.error("Yetkisiz panel şifresi!")
        
        if st.button("Sistemden Çık"):
            st.session_state.genel_auth = False
            st.rerun()
        st.stop()

    # --- PANEL İÇİ: AYARLAR VE ÇIKIŞ ---
    current_user = st.session_state.panel_auth
    u_data = st.session_state.user_db[current_user]
    
    st.sidebar.title(f"📍 {u_data['role']}")
    st.sidebar.write(f"Kullanıcı: {u_data['full_name']}")
    
    if st.sidebar.button("Paneli Kapat"):
        st.session_state.panel_auth = None
        st.rerun()

    # Şifre Değiştirme (Teyitli)
    with st.sidebar.expander("🔑 Şifremi Değiştir"):
        e_s = st.text_input("Eski Şifre", type="password")
        y_s = st.text_input("Yeni Şifre", type="password")
        if st.button("Güncelle"):
            if e_s == u_data["pass"]:
                st.session_state.user_db[current_user]["pass"] = y_s
                st.success("Şifre güncellendi!")
                time.sleep(1); st.rerun()
            else: st.error("Mevcut şifre hatalı!")

    # --- MOD 1: ÜRETİM OPERATÖR PANELİ (TAM FONKSİYON) ---
    if u_data['role'] == "Üretim-Operatör":
        st.header("🏭 Üretim Hattı Analiz Terminali")
        with st.form("full_op_form"):
            c1, c2 = st.columns(2)
            lot = c1.text_input("LOT No", "LOT-")
            kontrol = c2.number_input("Kontrol Adeti", 1, value=100)
            
            st.write("### Hata Girişleri ve Katsayılar")
            h1, h2, h3, h4 = st.columns(4)
            j3 = h1.number_input("P1 (Kritik)", 0); p1p = h1.number_input("P1 Puan", 1.0)
            k3 = h2.number_input("P2 (Majör)", 0); p2p = h2.number_input("P2 Puan", 1.0)
            l3 = h3.number_input("P3 (Minör)", 0); p3p = h3.number_input("P3 Puan", 1.0)
            m3 = h4.number_input("P4 (Görsel)", 0); p4p = h4.number_input("P4 Puan", 1.0)
            
            if st.form_submit_button("HESAPLA VE GÖNDER"):
                karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
                st.session_state.last_res = {
                    "Tarih": datetime.now().strftime("%d-%m-%Y %H:%M"), "LOT": lot, "TRI": round(skor, 3),
                    "Karar": karar, "Renk": renk, "P1": j3, "P2": k3, "P3": l3, "P4": m3, "Operatör": u_data['full_name']
                }

        if 'last_res' in st.session_state:
            res = st.session_state.last_res
            st.markdown(f"<div style='background-color:{res['Renk']}; padding:20px; border-radius:10px; text-align:center;'><h1 style='color:white;'>{res['Karar']} (TRI: {res['TRI']})</h1></div>", unsafe_allow_html=True)
            
            if res['Karar'] == "UYGUN":
                if st.button("ARŞİVLE"):
                    if excele_kaydet(res): st.success("Excel'e yazıldı."); del st.session_state.last_res; st.rerun()
            else:
                st.warning("Bu kayıt yönetici onayına sunulacak.")
                if st.button("ONAYA GÖNDER"):
                    st.session_state.onay_listesi.append(res)
                    st.info("Kayıt Müdür paneline iletildi."); del st.session_state.last_res; st.rerun()

    # --- MOD 2: KALİTE MÜDÜRÜ (ONAY VE ARŞİV) ---
    elif u_data['role'] == "Kalite Müdürü":
        st.header("⚖️ Onay Merkezi ve Veritabanı")
        
        tab1, tab2 = st.tabs(["Bekleyen Onaylar", "Tüm Arşiv"])
        
        with tab1:
            if not st.session_state.onay_listesi: st.info("Bekleyen iş yok.")
            for i, o_veri in enumerate(st.session_state.onay_listesi):
                with st.expander(f"{o_veri['LOT']} - Analiz: {o_veri['Karar']}"):
                    st.write(f"TRI: {o_veri['TRI']} | Hatalar: {o_veri['P1']},{o_veri['P2']},{o_veri['P3']},{o_veri['P4']}")
                    f_karar = st.selectbox("Nihai Karar", ["Şartlı Kabul", "Karantina", "Red"], key=f"f_{i}")
                    if st.button("KAYDI TAMAMLA", key=f"b_{i}"):
                        o_veri["Karar"] = f_karar
                        if excele_kaydet(o_veri):
                            st.session_state.onay_listesi.pop(i)
                            st.success("Kayıt arşivlendi."); st.rerun()
        
        with tab2:
            if os.path.exists(EXCEL_FILE):
                st.dataframe(pd.read_excel(EXCEL_FILE).iloc[::-1], use_container_width=True)
                with open(EXCEL_FILE, "rb") as f: st.download_button("Excel İndir", f, file_name=EXCEL_FILE)

    # --- MOD 3: GENEL MÜDÜR (ÖZET) ---
    elif u_data['role'] == "Genel Müdür":
        st.header("📈 Genel Müdürlük Özet Raporu")
        st.info("Bu panelde sadece stratejik özetler ve grafikler yer alır.")
        # İleride buraya grafikler eklenebilir
