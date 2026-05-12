import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io 
import time

# --- 1. GÜVENLİK VE ROL VERİTABANI (SİLİNMEZ) ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "alasar": {"pass": "30052012", "role": "Kalite Müdürü", "full_name": "Ömer Ocak"},
        "genelmudur": {"pass": "patron456", "role": "Genel Müdür", "full_name": "Genel Müdürlük"},
        "operator": {"pass": "op789", "role": "Üretim-Operatör", "full_name": "Kalite Operatörü"}
    }

GENERAL_USER = "alasar"
GENERAL_PASS = "30052012"

# --- 2. VERİTABANI BAŞLATMA ---
if 'ana_veritabani' not in st.session_state:
    st.session_state.ana_veritabani = pd.DataFrame() 
if 'onay_bekleyenler' not in st.session_state:
    st.session_state.onay_bekleyenler = [] 

# --- 3. KALİTE MOTORU (ORİJİNAL V6.7 KATSAYILARI) ---
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

# --- 4. OTURUM VE PANEL KONTROLÜ ---
st.set_page_config(page_title="Alasar Quality Engine V16", layout="wide")

if 'genel_giris' not in st.session_state: st.session_state.genel_giris = False
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None

# A - GENEL GİRİŞ
if not st.session_state.genel_giris:
    st.markdown("<h2 style='text-align:center;'>ALASAR SİSTEM GİRİŞİ</h2>", unsafe_allow_html=True)
    with st.form("genel_login"):
        u = st.text_input("Kullanıcı Adı").strip()
        p = st.text_input("Şifre", type="password").strip()
        if st.form_submit_button("Sisteme Gir"):
            if u == GENERAL_USER and p == GENERAL_PASS:
                st.session_state.genel_giris = True
                st.rerun()
            else: st.error("Hatalı giriş!")
    st.stop()

# B - PANEL SEÇİMİ
if st.session_state.aktif_user is None:
    st.subheader("Lütfen Yetki Alanınızı Seçiniz")
    secim = st.selectbox("Panel:", ["Seçiniz...", "Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
    if secim != "Seçiniz...":
        u_key = "operator" if secim == "Üretim-Operatör" else ("alasar" if secim == "Kalite Müdürü" else "genelmudur")
        ps = st.text_input(f"{secim} Özel Şifresi", type="password")
        if st.button("Paneli Aç"):
            if ps == st.session_state.user_db[u_key]["pass"]:
                st.session_state.aktif_user = u_key
                st.rerun()
            else: st.error("Yetkisiz Şifre!")
    st.stop()

u_data = st.session_state.user_db[st.session_state.aktif_user]
st.sidebar.title(f"📍 {u_data['role']}")
st.sidebar.write(f"Hoş Geldiniz: {u_data['full_name']}")

if st.sidebar.button("Oturumu Kapat / Geri Dön"):
    st.session_state.aktif_user = None
    st.rerun()

# --- PANEL 1: ÜRETİM HATTI ---
if u_data['role'] == "Üretim-Operatör":
    st.header("🏭 Üretim Hattı Giriş Terminali")
    with st.form("veri_giris_formu"):
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No", "LOT-")
        sevk = c2.number_input("Toplam Sevk Adeti", 1, value=1000)
        kontrol = c3.number_input("Kontrol Edilen Adet", 1, value=100)
        st.divider()
        st.subheader("Hata Adetleri ve Risk Puanları")
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik) Adet", 0); p1p = h1.number_input("P1 Puan", 1.0, value=1.0)
        k3 = h2.number_input("P2 (Majör) Adet", 0); p2p = h2.number_input("P2 Puan", 1.0, value=1.0)
        l3 = h3.number_input("P3 (Minör) Adet", 0); p3p = h3.number_input("P3 Puan", 1.0, value=1.0)
        m3 = h4.number_input("P4 (Görsel) Adet", 0); p4p = h4.number_input("P4 Puan", 1.0, value=1.0)
        op_not = st.text_area("Operatör Gözlem Notları")
        submit = st.form_submit_button("SİSTEM ANALİZİNİ BAŞLAT")

    if submit:
        karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
        st.session_state.gecici_analiz = {
            "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Operatör": u_data['full_name'], "Parti No": lot,
            "Sevk": sevk, "Kontrol": kontrol, "TRI": round(skor, 4), "Sistem": karar, "Renk": renk, "Not": op_not,
            "P1_A": j3, "P2_A": k3, "P3_A": l3, "P4_A": m3, "P1_P": p1p, "P2_P": p2p, "P3_P": p3p, "P4_P": p4p
        }

    if 'gecici_analiz' in st.session_state:
        data = st.session_state.gecici_analiz
        st.markdown(f"<div style='background-color:{data['Renk']}; padding:20px; border-radius:10px; text-align:center;'><h1 style='color:white;'>KARAR: {data['Sistem']} (TRI: {data['TRI']})</h1></div>", unsafe_allow_html=True)
        if data['Sistem'] != "UYGUN":
            st.warning("📸 Lütfen 3 kanıt fotoğrafı yükleyin.")
            f1 = st.file_uploader("Genel Görünüm", type=['jpg', 'png'], key="f1")
            f2 = st.file_uploader("Hata Detayı", type=['jpg', 'png'], key="f2")
            f3 = st.file_uploader("Etiket", type=['jpg', 'png'], key="f3")
            if st.button("KAYDI YÖNETİCİYE GÖNDER"):
                if f1 and f2 and f3:
                    data.update({"Foto_1": f1.read(), "Foto_2": f2.read(), "Foto_3": f3.read(), "Yönetici Aksiyonu": "BEKLİYOR"})
                    st.session_state.onay_bekleyenler.append(data)
                    st.success("✅ Kayıt iletildi."); del st.session_state.gecici_analiz; time.sleep(1.5); st.rerun()
                else: st.error("Fotoğraflar eksik!")
        else:
            if st.button("KAYDI TAMAMLA (UYGUN)"):
                data.update({"Yönetici Aksiyonu": "OTOMATİK ONAY"})
                st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([data])])
                st.success("✅ arşivlendi."); del st.session_state.gecici_analiz; time.sleep(1.5); st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ (GELİŞMİŞ KARARLAR) ---
elif u_data['role'] == "Kalite Müdürü":
    st.header("⚖️ Onay Bekleyen Kritik Kayıtlar")
    if not st.session_state.onay_bekleyenler: st.info("Şu an bekleyen bir kayıt yok.")
    for i, bekleyen in enumerate(st.session_state.onay_bekleyenler):
        with st.expander(f"📌 {bekleyen['Parti No']} | TRI: {bekleyen['TRI']}"):
            st.table(pd.DataFrame({"Hata": ["P1","P2","P3","P4"], "Adet": [bekleyen['P1_A'], bekleyen['P2_A'], bekleyen['P3_A'], bekleyen['P4_A']]}))
            img_c1, img_c2, img_c3 = st.columns(3)
            if 'Foto_1' in bekleyen: img_c1.image(io.BytesIO(bekleyen['Foto_1']), caption="Genel")
            if 'Foto_2' in bekleyen: img_c2.image(io.BytesIO(bekleyen['Foto_2']), caption="Hata")
            if 'Foto_3' in bekleyen: img_c3.image(io.BytesIO(bekleyen['Foto_3']), caption="Etiket")
            
            st.divider()
            c_a1, c_a2 = st.columns(2)
            # İSTEDİĞİNİZ KARAR SEÇENEKLERİ
            aks = c_a1.selectbox("Nihai Aksiyon", [
                "Olduğu Gibi Kabul (Sapma) ✅", 
                "%100 Ayıklama Yapılsın 🔍", 
                "Palette Rastlantısal Kontrol (Her Kasa Min 10 Adet) 📦", 
                "Tedarikçiye İade (Parti Reddi) 🚛", 
                "Karantinaya Al Beklet 🔒"
            ], key=f"aks_{i}")
            y_not = c_a2.text_input("Yönetici Notu", key=f"not_{i}")
            if st.button("KARARI ONAYLA VE ARŞİVLE", key=f"save_{i}"):
                bekleyen.update({"Yönetici Aksiyonu": aks, "Yönetici Notu": y_not})
                save_data = {k: v for k, v in bekleyen.items() if not k.startswith("Foto_")}
                st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([save_data])])
                st.session_state.onay_bekleyenler.pop(i)
                st.success("Karar sisteme işlendi."); time.sleep(1); st.rerun()

    st.divider()
    st.subheader("📜 Genel Arşiv (Detaylı Liste)")
    st.dataframe(st.session_state.ana_veritabani.iloc[::-1], use_container_width=True)

# --- PANEL 3: GENEL MÜDÜR (STRATEJİK ÖZET) ---
elif u_data['role'] == "Genel Müdür":
    st.header("📈 Kalite Stratejik Analitik Paneli")
    if not st.session_state.ana_veritabani.empty:
        df = st.session_state.ana_veritabani
        
        # 1. Kısım: Üst Metrikler
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Kontrol Edilen Parti", len(df))
        m2.metric("Ortalama TRI Risk Puanı", round(df['TRI'].mean(), 2))
        uygunluk_orani = (len(df[df['Yönetici Aksiyonu'].str.contains("Kabul|OTOMATİK", na=False)]) / len(df)) * 100
        m3.metric("Genel Uygunluk Oranı", f"%{round(uygunluk_orani, 1)}")
        m4.metric("Kritik Hata (P1) Toplamı", int(df['P1_A'].sum()))
        
        st.divider()
        
        # 2. Kısım: Aksiyon Dağılımı ve İstatistikler
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Karar Dağılım Grafiği")
            aks_counts = df['Yönetici Aksiyonu'].value_counts()
            st.bar_chart(aks_counts)
            
        with g2:
            st.subheader("Risk Dağılımı (Sistem Kararları)")
            sistem_counts = df['Sistem'].value_counts()
            st.pie_chart(sistem_counts) if hasattr(st, "pie_chart") else st.write(sistem_counts)

        st.divider()
        st.subheader("📊 Performans Arşivi")
        # Genel Müdür sadece özet sütunları görsün
        ozet_df = df[["Tarih", "Parti No", "TRI", "Sistem", "Yönetici Aksiyonu", "Yönetici Notu"]]
        st.dataframe(ozet_df.iloc[::-1], use_container_width=True)
    else:
        st.info("Henüz analiz edilmiş veri bulunmuyor.")
