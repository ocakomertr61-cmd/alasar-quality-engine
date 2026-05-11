import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io 

# --- GRAFİK KÜTÜPHANESİ KONTROLÜ ---
TRY_PLOTLY = True
try:
    import plotly.express as px
except ImportError:
    TRY_PLOTLY = False

# --- GÜVENLİ AYARLAR ---
ADMIN_PASSWORD = "30052012"

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

# --- UI SETTINGS ---
st.set_page_config(page_title="Alasar Quality Engine V6.3", layout="wide")
rol = st.sidebar.selectbox("Erişim Paneli:", ["Üretim Hattı (Operatör)", "Yönetici Analitik Paneli (Ömer Ocak)"])

# ---------------------------------------------------------
# 1. EKRAN: ÜRETİM HATTI
# ---------------------------------------------------------
if rol == "Üretim Hattı (Operatör)":
    st.header("🏭 Üretim Hattı Giriş Terminali")
    
    with st.sidebar:
        st.subheader("👤 Görevli Bilgisi")
        op_ad = st.text_input("Ad Soyad")
        op_kase = st.text_input("Kaşe No")
        # Seçenek yerine serbest rakam girişi (66, 67, 68 gibi)
        vardiya_no = st.number_input("Vardiya Kodu (Sayısal)", min_value=1, value=66, step=1)

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
        if not op_ad or not op_kase or lot == "LOT-":
            st.error("⚠️ Lütfen bilgileri eksiksiz doldurun!")
        else:
            karar, ikon, skor = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
            st.session_state.gecici_analiz = {
                "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Operatör": op_ad, "Kaşe": op_kase, "Vardiya": str(vardiya_no),
                "Parti No": lot, "Sevk": sevk, "Kontrol": kontrol, 
                "P1_A": j3, "P1_P": p1p, "P2_A": k3, "P2_P": p2p, "P3_A": l3, "P3_P": p3p, "P4_A": m3, "P4_P": p4p,
                "TRI": round(skor, 4), "Sistem": karar, "Operatör Notu": op_not
            }

    # Operatör ekranında TRI ve KARAR bilgilerini göster
    if 'gecici_analiz' in st.session_state:
        data = st.session_state.gecici_analiz
        st.divider()
        
        # BİLGİ PANELİ (Operatörün görmesi gerekenler)
        col_res1, col_res2 = st.columns(2)
        col_res1.success(f"### SİSTEM KARARI: {data['Sistem']}")
        col_res2.info(f"### TRI PUANI: {data['TRI']}")

        if data['Sistem'] != "UYGUN":
            st.warning("📸 UYGUNSUZLUK TESPİT EDİLDİ! Lütfen 3 adet kanıt fotoğrafı yükleyin.")
            f_c1, f_c2, f_c3 = st.columns(3)
            f1 = f_c1.file_uploader("Genel Görünüm", type=['jpg', 'png'], key="op_f1")
            f2 = f_c2.file_uploader("Hata Detayı", type=['jpg', 'png'], key="op_f2")
            f3 = f_c3.file_uploader("Etiket", type=['jpg', 'png'], key="op_f3")
            
            if st.button("KAYDI YÖNETİCİ ONAYINA GÖNDER"):
                if f1 and f2 and f3:
                    data.update({"Foto_1": f1.read(), "Foto_2": f2.read(), "Foto_3": f3.read(), "Yönetici Aksiyonu": "BEKLİYOR", "Yönetici Notu": "-"})
                    st.session_state.onay_bekleyenler.append(data)
                    st.info("Kayıt iletildi. Ömer Bey'in onayı bekleniyor.")
                    del st.session_state.gecici_analiz
                    st.rerun()
                else:
                    st.error("⚠️ Fotoğraflar eksik!")
        else:
            if st.button("KAYDI TAMAMLA (YÖNETİCİ ONAYLADI, UYGUNDUR)"):
                data.update({"Yönetici Aksiyonu": "OTOMATİK ONAY", "Yönetici Notu": "-"})
                st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([data])])
                st.balloons()
                del st.session_state.gecici_analiz
                st.rerun()

# ---------------------------------------------------------
# 2. EKRAN: YÖNETİCİ ANALİTİK
# ---------------------------------------------------------
else:
    if not st.session_state.get('admin_logged_in'):
        st.error("🔒 YÖNETİCİ GİRİŞİ GEREKLİ")
        pwd = st.text_input("Parola", type="password")
        if st.button("Giriş"):
            if pwd == ADMIN_PASSWORD: st.session_state.admin_logged_in = True; st.rerun()
        st.stop()

    st.header("📊 Alasar Stratejik Kalite Analitiği")
    
    if not st.session_state.ana_veritabani.empty:
        df = st.session_state.ana_veritabani
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Parti", len(df))
        m2.metric("Ortalama TRI", f"{df['TRI'].mean():.2f}")
        m3.metric("Uygunluk Oranı", f"%{(len(df[df['Sistem']=='UYGUN'])/len(df)*100):.1f}")
        
        if TRY_PLOTLY:
            st.divider()
            g1, g2 = st.columns(2)
            with g1:
                fig_line = px.line(df, x="Tarih", y="TRI", markers=True, title="SPC: TRI Skor Trendi")
                st.plotly_chart(fig_line, use_container_width=True)
            with g2:
                fig_pie = px.pie(df, names="Yönetici Aksiyonu", title="Aksiyon Dağılımı")
                st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    st.subheader(f"📥 Onay Bekleyen {len(st.session_state.onay_bekleyenler)} Kayıt")
    
    for i, bekleyen in enumerate(st.session_state.onay_bekleyenler):
        with st.expander(f"⚠️ {bekleyen['Parti No']} | Vardiya: {bekleyen['Vardiya']}", expanded=True):
            st.write(f"**Operatör:** {bekleyen['Operatör']} | **Sistem:** {bekleyen['Sistem']} | **TRI:** {bekleyen['TRI']}")
            
            # FOTOĞRAF GÖRÜNTÜLEME
            st.divider()
            img_c1, img_c2, img_c3 = st.columns(3)
            if 'Foto_1' in bekleyen: img_c1.image(io.BytesIO(bekleyen['Foto_1']), caption="Genel", use_container_width=True)
            if 'Foto_2' in bekleyen: img_c2.image(io.BytesIO(bekleyen['Foto_2']), caption="Detay", use_container_width=True)
            if 'Foto_3' in bekleyen: img_c3.image(io.BytesIO(bekleyen['Foto_3']), caption="Etiket", use_container_width=True)
            
            st.divider()
            c_a1, c_a2 = st.columns(2)
            aks = c_a1.selectbox("Karar", ["Şartlı Kabul ✅", "Kesin Red ❌", "Karantina 📦", "İade 🚛"], key=f"v63s_{i}")
            y_not = c_a2.text_input("Yönetici Notu", key=f"v63n_{i}")
            
            if st.button("KARARI KAYDET", key=f"v63b_{i}"):
                bekleyen.update({"Yönetici Aksiyonu": aks, "Yönetici Notu": y_not})
                # Arşive geçerken fotoğrafları sil (hafıza koruma)
                save_data = bekleyen.copy()
                for f in ['Foto_1', 'Foto_2', 'Foto_3']: save_data.pop(f, None)
                st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([save_data])])
                st.session_state.onay_bekleyenler.pop(i)
                st.rerun()

# --- ARŞİV (HERKESE AÇIK) ---
if st.session_state.get('admin_logged_in'):
    st.divider()
    st.subheader("📜 Genel Arşiv")
    st.dataframe(st.session_state.ana_veritabani.iloc[::-1], use_container_width=True, hide_index=True)
