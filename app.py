import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px # Grafik için ek kütüphane

# --- GÜVENLİ AYARLAR ---
ADMIN_PASSWORD = "30052012"

# Veri Yapısı Güncellemesi
if 'ana_veritabani' not in st.session_state:
    st.session_state.ana_veritabani = pd.DataFrame() 
if 'onay_bekleyenler' not in st.session_state:
    st.session_state.onay_bekleyenler = [] 

# --- KALİTE MOTORU ---
def kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    hata_orani = (toplam_hata / G3) if G3 > 0 else 0
    temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
    t3_skor = max(temel_oran * (1 + (J3*0.03 + K3*0.05)), toplam_hata / 20) if toplam_hata > 0 else 0.0
    red_mi = (hata_orani > 0.05 or (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or t3_skor >= 5.0)
    sartli_mi = False if red_mi else (t3_skor > 1.7 or (J3 + K3) >= 6)
    
    if red_mi: return "RED", "🔴", t3_skor
    elif sartli_mi: return "SARI", "🟡", t3_skor
    else: return "UYGUN", "🟢", t3_skor

# --- UI ---
st.set_page_config(page_title="Alasar Quality Engine V6.0", layout="wide")
rol = st.sidebar.selectbox("Erişim Paneli:", ["Üretim Hattı (Operatör)", "Yönetici Analitik Paneli (Ömer Ocak)"])

# ---------------------------------------------------------
# 1. EKRAN: ÜRETİM HATTI (Vardiya ve Fotoğraf)
# ---------------------------------------------------------
if rol == "Üretim Hattı (Operatör)":
    st.header("🏭 Üretim Hattı Giriş Terminali")
    
    with st.sidebar:
        st.subheader("👤 Görevli Bilgisi")
        op_ad = st.text_input("Ad Soyad")
        op_kase = st.text_input("Kaşe No")
        vardiya = st.selectbox("Vardiya Kodu", ["V1 (08:00-16:00)", "V2 (16:00-00:00)", "V3 (00:00-08:00)"])

    with st.form("veri_giris_formu"):
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No", "LOT-")
        sevk = c2.number_input("Toplam Sevk Adeti", 1)
        kontrol = c3.number_input("Kontrol Edilen Adet", 1)
        
        st.divider()
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik) Adet", 0); k3 = h2.number_input("P2 (Majör) Adet", 0)
        l3 = h3.number_input("P3 (Minör) Adet", 0); m3 = h4.number_input("P4 (Görsel) Adet", 0)
        
        p1p = h1.number_input("P1 Risk Puanı", 1.0); p2p = h2.number_input("P2 Risk Puanı", 1.0)
        p3p = h3.number_input("P3 Risk Puanı", 1.0); p4p = h4.number_input("P4 Risk Puanı", 1.0)
        
        op_not = st.text_area("Operatör Gözlem Notları")
        submit = st.form_submit_button("SİSTEM ANALİZİNİ BAŞLAT")

    if submit:
        if not op_ad or not op_kase:
            st.error("⚠️ Operatör kimlik bilgileri eksik!")
        else:
            karar, ikon, skor = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
            st.session_state.gecici_analiz = {
                "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Operatör": op_ad, "Kaşe": op_kase, "Vardiya": vardiya,
                "Parti No": lot, "Sevk": sevk, "Kontrol": kontrol, "TRI": round(skor, 4), "Sistem": karar, "Operatör Notu": op_not
            }

    if 'gecici_analiz' in st.session_state:
        data = st.session_state.gecici_analiz
        st.divider()
        st.subheader(f"Analiz Sonucu: {data['Sistem']}")
        
        # SARI veya RED durumunda fotoğraf alanı aç
        if data['Sistem'] != "UYGUN":
            st.warning("📸 DİKKAT: Uygunsuzluk tespit edildi. Lütfen kanıt fotoğraflarını yükleyiniz.")
            f1 = st.file_uploader("1. Fotoğraf: Genel Görünüm", type=['jpg', 'png'])
            f2 = st.file_uploader("2. Fotoğraf: Hata Detayı", type=['jpg', 'png'])
            f3 = st.file_uploader("3. Fotoğraf: Parti Etiketi", type=['jpg', 'png'])
            
            if st.button("ONAYA GÖNDER"):
                if f1 and f2 and f3:
                    st.session_state.onay_bekleyenler.append(data)
                    st.info("Kayıt fotoğraflarla birlikte yöneticiye iletildi.")
                    del st.session_state.gecici_analiz
                    st.rerun()
                else:
                    st.error("⚠️ En az 3 fotoğraf yüklemeden onaya gönderemezsiniz!")
        else:
            if st.button("KAYDI TAMAMLA (YÖNETİCİ ONAYLADI, UYGUNDUR)"):
                data.update({"Yönetici Aksiyonu": "OTOMATİK ONAY", "Yönetici Notu": "-"})
                st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([data])])
                st.balloons()
                del st.session_state.gecici_analiz
                st.rerun()

# ---------------------------------------------------------
# 2. EKRAN: YÖNETİCİ ANALİTİK (İstatistikler ve Grafikler)
# ---------------------------------------------------------
else:
    if not st.session_state.get('admin_logged_in'):
        st.error("🔒 YÖNETİCİ GİRİŞİ GEREKLİ")
        pwd = st.text_input("Parola", type="password")
        if st.button("Giriş"):
            if pwd == ADMIN_PASSWORD: st.session_state.admin_logged_in = True; st.rerun()
        st.stop()

    st.header("📊 Alasar Stratejik Kalite Analitiği")
    
    # --- ÜST ÖZET METRİKLER ---
    if not st.session_state.ana_veritabani.empty:
        df = st.session_state.ana_veritabani
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Parti", len(df))
        m2.metric("Ortalama TRI", round(df['TRI'].mean(), 2))
        m3.metric("Uygunluk Oranı", f"%{len(df[df['Sistem']=='UYGUN'])/len(df)*100:.1f}")
        m4.metric("Karantina/Red", len(df[df['Yönetici Aksiyonu'].str.contains('Red|Karantina', na=False)]))

        # --- GRAFİKLER ---
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("📈 SPC: TRI Skor Trendi")
            fig_line = px.line(df, x="Tarih", y="TRI", title="Süreç Stabilizasyon Grafiği", markers=True)
            fig_line.add_hline(y=5.0, line_dash="dash", line_color="red", annotation_text="KRİTİK EŞİK")
            st.plotly_chart(fig_line, use_container_width=True)

        with g2:
            st.subheader("🍩 Karar Dağılım Analizi")
            fig_pie = px.pie(df, names="Yönetici Aksiyonu", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- ONAY BEKLEYENLER ---
    st.divider()
    st.subheader("📥 Onay Bekleyen Kritik Kayıtlar")
    if not st.session_state.onay_bekleyenler:
        st.info("Onay bekleyen kayıt yok.")
    else:
        for i, bekleyen in enumerate(st.session_state.onay_bekleyenler):
            with st.expander(f"⚠️ {bekleyen['Parti No']} - {bekleyen['Operatör']} ({bekleyen['Vardiya']})", expanded=True):
                st.write(f"**Sistem Kararı:** {bekleyen['Sistem']} | **TRI:** {bekleyen['TRI']}")
                st.write(f"**Operatör Notu:** {bekleyen['Operatör Notu']}")
                st.write("🖼️ *Kanıt fotoğrafları ekte sunulmuştur (Simüle Edildi)*")
                
                c_onay1, c_onay2 = st.columns(2)
                aks = c_onay1.selectbox("Karar", ["Şartlı Kabul ✅", "Kesin Red ❌", "Karantina 📦", "İade 🚛"], key=f"v6s_{i}")
                y_not = c_onay2.text_input("Yönetici Notu", key=f"v6n_{i}")
                
                if st.button("KARARI SİSTEME İŞLE", key=f"v6b_{i}"):
                    bekleyen.update({"Yönetici Aksiyonu": aks, "Yönetici Notu": y_not})
                    st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([bekleyen])])
                    st.session_state.onay_bekleyenler.pop(i)
                    st.rerun()

# --- ARŞİV (HERKESE AÇIK) ---
st.divider()
st.subheader("📜 Genel Denetim Arşivi")
if not st.session_state.ana_veritabani.empty:
    st.dataframe(st.session_state.ana_veritabani.iloc[::-1], use_container_width=True, hide_index=True)
