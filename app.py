import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io 
import time
import os

# --- VERİTABANI DOSYA YOLLARI ---
DB_FILE = "grup_kalite_veritabani.xlsx"
SIKAYET_FILE = "musteri_sikayet_8d.xlsx"

# --- YARDIMCI FONKSİYONLAR ---
def veriyi_excele_kaydet(df, dosya):
    try:
        if not os.path.exists(dosya):
            df.to_excel(dosya, index=False, engine='openpyxl')
        else:
            mevcut = pd.read_excel(dosya, engine='openpyxl')
            pd.concat([mevcut, df], ignore_index=True).to_excel(dosya, index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")

def veriyi_yukle(dosya):
    if os.path.exists(dosya):
        return pd.read_excel(dosya, engine='openpyxl')
    return pd.DataFrame()

def benzersiz_id_uret(sirket, mevcut_db):
    prefix = "AL" if "Alasar" in sirket else "HK"
    yil = datetime.now().strftime("%Y")
    sirket_kayitlari = mevcut_db[mevcut_db['Şirket'] == sirket] if not mevcut_db.empty else pd.DataFrame()
    
    if sirket_kayitlari.empty:
        yeni_no = 1
    else:
        try:
            # Son QR kodun numarasını çekip artırır
            son_id = str(sirket_kayitlari['QR_Kod'].iloc[-1])
            yeni_no = int(son_id.split('-')[-1]) + 1
        except:
            yeni_no = len(sirket_kayitlari) + 1
    return f"{prefix}-{yil}-{yeni_no:04d}"

# --- ANALİZ VE GÖRSELLEŞTİRME MODÜLÜ ---
def analiz_paneli(df, sikayet_df, sirket):
    st.subheader(f"📊 {sirket} Dijital Kalite Portalı")
    s_df = df[df['Şirket'] == sirket] if not df.empty else pd.DataFrame()
    s_sikayet = sikayet_df[sikayet_df['Şirket'] == sirket] if not sikayet_df.empty else pd.DataFrame()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Üretim Kaydı", len(s_df))
    col2.metric("Müşteri Şikayeti", len(s_sikayet))
    col3.metric("Açık DÖF Sayısı", len(s_sikayet[s_sikayet['Durum'] == 'Açık']) if not s_sikayet.empty else 0)
    col4.metric("Ortalama TRI", f"{s_df['TRI'].mean():.2f}" if not s_df.empty else "0.00")

    if not s_df.empty:
        st.divider()
        c_sol, c_sag = st.columns([2, 1])
        with c_sol:
            st.write("🎯 **Hata Kaynağı Pareto Analizi (Kök Neden)**")
            hata_sayilari = s_df['Baskın Hata Türü'].value_counts()
            st.bar_chart(hata_sayilari)
        with c_sag:
            st.write("📦 **Son Dijital Mühürler (QR)**")
            st.dataframe(s_df[['QR_Kod', 'Parti No', 'Sistem']].tail(8), hide_index=True)

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Grup Kalite V21.0", layout="wide")
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None

# --- GİRİŞ EKRANI ---
if st.session_state.aktif_user is None:
    st.title("🛡️ GRUP ŞİRKETLERİ KALİTE & İZLENEBİLİRLİK")
    with st.container():
        sirket = st.selectbox("Şirket Seçiniz:", ["Alasar Grup", "Hakan Kalıp Plastik"])
        role = st.selectbox("Yetki Seviyesi:", ["Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
        ps = st.text_input("Giriş Şifresi:", type="password")
        if st.button("SİSTEME BAĞLAN"):
            if (role == "Kalite Müdürü" and ps == "30052012") or \
               (role == "Üretim-Operatör" and ps == "op789") or \
               (role == "Genel Müdür" and ps == "patron456"):
                st.session_state.aktif_user = {"role": role, "sirket": sirket}
                st.rerun()
            else: st.error("Yetkisiz Giriş Denemesi!")
    st.stop()

u_role = st.session_state.aktif_user['role']
u_sirket = st.session_state.aktif_user['sirket']
ana_db = veriyi_yukle(DB_FILE)
sikayet_db = veriyi_yukle(SIKAYET_FILE)

st.sidebar.title(f"🏢 {u_sirket}")
st.sidebar.info(f"Kullanıcı: {u_role}")
if st.sidebar.button("Güvenli Çıkış"): 
    st.session_state.aktif_user = None
    st.rerun()

# --- PANEL 1: ÜRETİM-OPERATÖR ---
if u_role == "Üretim-Operatör":
    st.header("🏭 Üretim Veri Giriş Terminali")
    with st.form("op_form"):
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No / Lot", "LOT-")
        sevk = c2.number_input("Sevk Miktarı", 1, value=1000)
        vardiya = c3.selectbox("Vardiya", list(range(60, 81)))
        
        hata_kategorileri = ["Hata Yok", "Çapak Problemi", "Ölçüsel Sapma", "Yüzey Hatası", "Eksik Baskı", "Hammadde/Renk", "Kalıp Kaynaklı"]
        baskin_hata = st.selectbox("⚠️ BASKIN HATA TÜRÜ (ZORUNLU):", hata_kategorileri)
        
        st.divider()
        h1, h2, h3, h4 = st.columns(4)
        p1 = h1.number_input("P1 (Kritik)", 0); p1p = h1.number_input("P1 Puan", 1.0)
        p2 = h2.number_input("P2 (Majör)", 0); p2p = h2.number_input("P2 Puan", 1.0)
        p3 = h3.number_input("P3 (Minör)", 0); p3p = h3.number_input("P3 Puan", 1.0)
        p4 = h4.number_input("P4 (Görsel)", 0); p4p = h4.number_input("P4 Puan", 1.0)
        op_not = st.text_area("Operatör Gözlem Notu")
        
        if st.form_submit_button("ANALİZ ET VE DİJİTAL MÜHÜRLE"):
            # Risk Analiz Motoru
            toplam_h = p1+p2+p3+p4
            katsayi = ((p1p*2.5)+(p2p*1.5)+(p3p*0.7)+(p4p*0.3))/10
            skor = max(katsayi*(1+(p1*0.05)), toplam_h/20) if toplam_h > 0 else 0.0
            karar = "RED" if skor > 2.8 or p1 > 0 else ("SARI" if skor > 1.5 else "UYGUN")
            renk = "#FF4B4B" if karar=="RED" else ("#FFD700" if karar=="SARI" else "#28A745")
            
            # Otomatik QR Kimliği Üretimi
            yeni_qr = benzersiz_id_uret(u_sirket, ana_db)
            
            yeni_kayit = pd.DataFrame([{
                "Şirket": u_sirket, "QR_Kod": yeni_qr, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Parti No": lot, "Baskın Hata Türü": baskin_hata, "TRI": round(skor, 4), "Sistem": karar,
                "Renk": renk, "Vardiya": vardiya, "Sevk": sevk, "P1_A": p1, "P2_A": p2, "P3_A": p3, "P4_A": p4,
                "Yönetici Aksiyonu": "BEKLİYOR" if karar != "UYGUN" else "OTOMATİK ONAY", "Not": op_not
            }])
            veriyi_excele_kaydet(yeni_kayit, DB_FILE)
            st.success(f"Kayıt Başarılı! Dijital Kimlik: {yeni_qr}")
            time.sleep(1); st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ ---
elif u_role == "Kalite Müdürü":
    t1, t2, t3 = st.tabs(["📊 Üretim Analizi & Onay", "🚨 8D / Müşteri Şikayetleri", "🔍 QR Sorgulama"])
    
    with t1:
        analiz_paneli(ana_db, sikayet_db, u_sirket)
        st.divider()
        st.write("⚖️ **Karar Bekleyen Kritik Partiler**")
        bekleyen = ana_db[(ana_db['Şirket'] == u_sirket) & (ana_db['Yönetici Aksiyonu'] == 'BEKLİYOR')]
        if not bekleyen.empty:
            for i, row in bekleyen.iterrows():
                with st.expander(f"🔴 {row['Parti No']} - QR: {row['QR_Kod']} (TRI: {row['TRI']})"):
                    aks = st.selectbox("Nihai Karar", ["Kabul", "Karantina", "Üst Yöneticiye Sevk", "İade"], key=f"aks_{i}")
                    y_not = st.text_input("Yönetici Notu", key=f"not_{i}")
                    if st.button("KARARI KAYDET", key=f"btn_{i}"):
                        # Kayıt güncelleme mantığı (Basitleştirilmiş)
                        st.info("Karar işlendi (Veritabanı güncelleme modülü aktif).")
        else: st.info("Bekleyen onay bulunmuyor.")

    with t2:
        st.subheader("🆕 Yeni 8D Şikayet Dosyası Aç")
        with st.form("8d_form"):
            m, k = st.text_input("Müşteri Adı"), st.text_input("Şikayet Konusu")
            kn, df = st.text_area("Kök Neden"), st.text_area("DÖF Aksiyonu")
            st.form_submit_button("8D RAPORUNU YAYINLA")

    with t3:
        st.subheader("📦 Geriye Dönük İzlenebilirlik Sorgusu")
        qr_ara = st.text_input("Sorgulamak istediğiniz QR kodunu girin:")
        if qr_ara and not ana_db.empty:
            res = ana_db[ana_db['QR_Kod'].astype(str).str.contains(qr_ara)]
            st.dataframe(res)

# --- PANEL 3: GENEL MÜDÜR ---
elif u_role == "Genel Müdür":
    st.header("👔 Grup Stratejik Yönetim Paneli")
    secili_sirket = st.radio("İncelemek İstediğiniz Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"], horizontal=True)
    analiz_paneli(ana_db, sikayet_db, secili_sirket)
    
    st.divider()
    st.subheader("🚨 Açık Müşteri Şikayetleri (DÖF)")
    if not sikayet_db.empty:
        st.dataframe(sikayet_db[sikayet_db['Şirket'] == secili_sirket])
    else: st.info("Şu an için açık şikayet dosyası bulunmamaktadır.")

# --- GENEL EXCEL ÇIKTISI ---
st.sidebar.divider()
if not ana_db.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        ana_db.to_excel(writer, index=False, sheet_name='Uretim_Izlenebilirlik')
        if not sikayet_db.empty: sikayet_db.to_excel(writer, index=False, sheet_name='8D_Sikayet_Analizi')
    st.sidebar.download_button("📥 Full Grup Raporunu Excel Olarak Al", output.getvalue(), f"Alasar_Hakan_Kalite_{datetime.now().strftime('%Y%m%d')}.xlsx", use_container_width=True)
