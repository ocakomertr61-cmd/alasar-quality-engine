import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io 
import time
import os
from PIL import Image

# --- SİSTEM VE DOSYA AYARLARI ---
DB_FILE = "alasar_kalite_veritabani.xlsx"
SIKAYET_FILE = "kalite_8d_dof_sistemi.xlsx"

def veriyi_excele_kaydet(yeni_df, dosya):
    try:
        if not os.path.exists(dosya):
            yeni_df.to_excel(dosya, index=False, engine='openpyxl')
        else:
            mevcut_df = pd.read_excel(dosya, engine='openpyxl')
            guncel_df = pd.concat([mevcut_df, yeni_df], ignore_index=True)
            guncel_df.to_excel(dosya, index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Kayıt Hatası ({dosya}): {e}")

def veriyi_excelden_yukle(dosya):
    if os.path.exists(dosya):
        return pd.read_excel(dosya, engine='openpyxl')
    return pd.DataFrame()

# --- OTOMATİK NUMARALANDIRMA ---
def otomatik_dof_no_uret(mevcut_8d_db):
    yil = datetime.now().strftime("%Y")
    if mevcut_8d_db.empty: return f"{yil}-DOF-001"
    try:
        son_no = int(str(mevcut_8d_db['DOF_No'].iloc[-1]).split('-')[-1])
        return f"{yil}-DOF-{son_no + 1:03d}"
    except: return f"{yil}-DOF-001"

# --- 8D İSTATİSTİK PANELİ ---
def dof_istatistik_ciz(sikayet_df, sirket):
    if sikayet_df.empty:
        st.info("İstatistik için 8D verisi bulunmuyor.")
        return
    s_8d = sikayet_df[sikayet_df['Şirket'] == sirket]
    if s_8d.empty: return

    st.markdown("#### 📈 8D / DÖF Süreç Analizi")
    c1, c2 = st.columns(2)
    with c1:
        st.write("**8D Durum Dağılımı**")
        st.bar_chart(s_8d['Durum'].value_counts())
    with c2:
        st.write("**Müşteri Şikayet Yoğunluğu**")
        st.bar_chart(s_8d['Müşteri'].value_counts())

# --- KALİTE HESAPLAMA (V24 - TRI) ---
def kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    hata_orani = (toplam_hata / G3) if G3 > 0 else 0
    temel_oran = ((P3_p * 2.5) + (Q3_p * 1.5) + (R3_p * 0.7) + (S3_p * 0.3)) / 5
    t3_skor = max(temel_oran * (1 + (J3*0.05 + K3*0.02)), toplam_hata / 15) if toplam_hata > 0 else 0.0
    red_mi = (hata_orani > 0.08 or J3 >= 1 or t3_skor >= 4.0)
    sartli_mi = False if red_mi else (t3_skor > 1.5 or (J3 + K3) >= 5)
    
    if red_mi: return "RED", "🔴", t3_skor, "#FF4B4B" 
    elif sartli_mi: return "SARI", "🟡", t3_skor, "#FFD700" 
    else: return "UYGUN", "🟢", t3_skor, "#28A745" 

# --- SAYFA VE OTURUM ---
st.set_page_config(page_title="Alasar Group Quality Engine V24.0", layout="wide")

for key in ['genel_giris', 'aktif_user', 'onay_bekleyenler']:
    if key not in st.session_state:
        st.session_state[key] = [] if key == 'onay_bekleyenler' else (False if key == 'genel_giris' else None)

# --- GİRİŞ EKRANI ---
if not st.session_state.genel_giris:
    st.markdown("<h1 style='text-align:center;'>🛡️ ALASAR GRUP KALİTE PORTALI</h1>", unsafe_allow_html=True)
    with st.form("portal_giris"):
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Sistem Şifresi", type="password")
        if st.form_submit_button("Giriş Yap"):
            if u == "alasar" and p == "30052012":
                st.session_state.genel_giris = True
                st.rerun()
            else: st.error("Erişim Reddedildi.")
    st.stop()

# --- ROL VE ŞİRKET SEÇİMİ ---
if st.session_state.aktif_user is None:
    st.subheader("Bölüm ve Şirket Doğrulaması")
    col_a, col_b = st.columns(2)
    s_sec = col_a.selectbox("Çalışılan Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"])
    r_sec = col_b.selectbox("Yetki Alanı:", ["Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
    ozel_p = st.text_input("Yetki Şifresi", type="password")
    if st.button("Sistemi Aktif Et"):
        if (r_sec == "Kalite Müdürü" and ozel_p == "30052012") or \
           (r_sec == "Üretim-Operatör" and ozel_p == "op789") or \
           (r_sec == "Genel Müdür" and ozel_p == "patron456"):
            st.session_state.aktif_user = {"role": r_sec, "sirket": s_sec}
            st.rerun()
        else: st.error("Hatalı Yetki Şifresi!")
    st.stop()

u_data = st.session_state.get('aktif_user')
if not u_data: st.rerun()

u_role = u_data['role']
u_sirket = u_data['sirket']
ana_db = veriyi_excelden_yukle(DB_FILE)
sikayet_db = veriyi_excelden_yukle(SIKAYET_FILE)

# --- PANEL 1: ÜRETİM-OPERATÖR ---
if u_role == "Üretim-Operatör":
    st.header(f"🚀 {u_sirket} Üretim Giriş Paneli")
    with st.form("op_form"):
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No", "LOT-")
        sevk = c2.number_input("Sevk Miktarı", 1, value=5000)
        hata_tipi = c3.selectbox("Ana Hata", ["Hata Yok", "Çapak", "Ölçü", "Yüzey", "Hammadde"])
        
        st.divider()
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik) Adet", 0); p1p = h1.number_input("P1 Şiddet", 3.0)
        k3 = h2.number_input("P2 (Majör) Adet", 0); p2p = h2.number_input("P2 Şiddet", 2.0)
        l3 = h3.number_input("P3 (Minör) Adet", 0); p3p = h3.number_input("P3 Şiddet", 1.0)
        m3 = h4.number_input("P4 (Görsel) Adet", 0); p4p = h4.number_input("P4 Şiddet", 0.5)
        
        op_not = st.text_area("Operatör Açıklaması (Detay veriniz)")
        if st.form_submit_button("SİSTEME GÖNDER"):
            karar, ikon, skor, renk = kalite_motoru_hesapla(100, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
            kayit = {
                "Şirket": u_sirket, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Parti No": lot, "Sevk": sevk, "Baskın Hata": hata_tipi, "TRI": round(skor, 4), 
                "Sistem": karar, "P1_A": j3, "P1_S": p1p, "P2_A": k3, "P2_S": p2p, 
                "P3_A": l3, "P3_S": p3p, "P4_A": m3, "P4_S": p4p, "Not": op_not,
                "Yönetici Aksiyonu": "BEKLİYOR" if karar != "UYGUN" else "OTOMATİK ONAY"
            }
            if karar == "UYGUN": veriyi_excele_kaydet(pd.DataFrame([kayit]), DB_FILE)
            else: st.session_state.onay_bekleyenler.append(kayit)
            st.success("İşlem Başarılı."); time.sleep(1); st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ ---
elif u_role == "Kalite Müdürü":
    t1, t2, t3 = st.tabs(["📊 Analiz & Performans", "📋 Karar Bekleyenler", "🛠️ 8D / DÖF Kaydı"])
    
    with t1:
        dof_istatistik_ciz(sikayet_db, u_sirket)
        st.divider()
        st.dataframe(ana_db[ana_db['Şirket'] == u_sirket].iloc[::-1] if not ana_db.empty else pd.DataFrame())

    with t2:
        st.subheader("Onay Bekleyen Partiler")
        bekleyenler = [b for b in st.session_state.onay_bekleyenler if b['Şirket'] == u_sirket and not b.get("Patrona_Gitti", False)]
        for i, b in enumerate(bekleyenler):
            with st.expander(f"🚩 {b['Parti No']} | TRI: {b['TRI']} | Hata: {b['Baskın Hata']}"):
                # Operatör Detay Tablosu
                st.table(pd.DataFrame({
                    "Hata Sınıfı": ["P1 (Kritik)", "P2 (Majör)", "P3 (Minör)", "P4 (Görsel)"],
                    "Adet": [b['P1_A'], b['P2_A'], b['P3_A'], b['P4_A']],
                    "Şiddet": [b['P1_S'], b['P2_S'], b['P3_S'], b['P4_S']]
                }))
                st.info(f"**Operatör Notu:** {b['Not']}")
                aks = st.selectbox("Karar", ["Kabul", "Karantina", "ÜST YÖNETİCİYE SEVK", "İade"], key=f"k_aks_{i}")
                if st.button("KARARI UYGULA", key=f"k_btn_{i}"):
                    if "ÜST" in aks:
                        for idx, item in enumerate(st.session_state.onay_bekleyenler):
                            if item['Parti No'] == b['Parti No']: st.session_state.onay_bekleyenler[idx]["Patrona_Gitti"] = True
                    else:
                        b.update({"Yönetici Aksiyonu": aks})
                        veriyi_excele_kaydet(pd.DataFrame([b]), DB_FILE)
                        st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['Parti No'] != b['Parti No']]
                    st.rerun()

    with t2:
        st.header("Yeni 8D Kaydı ve Görsel Ekleme")
        with st.form("dof_v24"):
            d_no = otomatik_dof_no_uret(sikayet_db)
            m_ad = st.text_input("Müşteri")
            p_tanim = st.text_area("Hata Tanımı")
            yuklenen_dosya = st.file_uploader("Hata Görseli Yükle", type=['png', 'jpg', 'jpeg'])
            durum = st.selectbox("Durum", ["Başlatıldı", "Beklemede", "Kapatıldı"])
            if st.form_submit_button("8D SİSTEMİNE İŞLE"):
                veriyi_excele_kaydet(pd.DataFrame([{"Şirket":u_sirket,"DOF_No":d_no,"Müşteri":m_ad,"Tanım":p_tanim,"Durum":durum}]), SIKAYET_FILE)
                st.success("Kaydedildi."); st.rerun()

# --- PANEL 3: GENEL MÜDÜR (PATRON) ---
elif u_role == "Genel Müdür":
    s_sec = st.radio("Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"], horizontal=True)
    patron_onay = [x for x in st.session_state.onay_bekleyenler if x.get("Patrona_Gitti") and x['Şirket'] == s_sec]
    
    if patron_onay:
        st.error(f"🚨 KRİTİK: {len(patron_onay)} ADET SEVK ONAYI BEKLENİYOR!")
    
    dof_istatistik_ciz(sikayet_db, s_sec)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👔 Kritik Karar Paneli")
        for i, p in enumerate(patron_onay):
            with st.container():
                st.markdown(f"### Parti: {p['Parti No']} | TRI: {p['TRI']}")
                st.warning(f"Operatör Notu: {p['Not']}")
                # Detaylı Hata Matrisi
                st.write("**Hata Detayları:**")
                st.json({ "P1_Adet": p['P1_A'], "P2_Adet": p['P2_A'], "Hata_Tipi": p['Baskın Hata'] })
                p_karar = st.radio("Kararınız", ["SEVK ET", "REDDET"], key=f"p_k_{i}")
                if st.button("MÜHÜRLE", key=f"p_b_{i}"):
                    p.update({"Yönetici Aksiyonu": f"PATRON: {p_karar}"})
                    veriyi_excele_kaydet(pd.DataFrame([p]), DB_FILE)
                    st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['Parti No'] != p['Parti No']]
                    st.rerun()

    with col2:
        st.subheader("🚨 8D / DÖF Özet")
        if not sikayet_db.empty:
            st.table(sikayet_db[sikayet_db['Şirket'] == s_sec][['DOF_No', 'Müşteri', 'Durum']].tail(5))
