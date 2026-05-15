import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io 
import time
import os

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

# --- OTOMATİK NUMARALANDIRMA MOTORLARI ---
def otomatik_dof_no_uret(mevcut_8d_db):
    yil = datetime.now().strftime("%Y")
    if mevcut_8d_db.empty:
        return f"{yil}-DOF-001"
    try:
        son_no = int(str(mevcut_8d_db['DOF_No'].iloc[-1]).split('-')[-1])
        return f"{yil}-DOF-{son_no + 1:03d}"
    except:
        return f"{yil}-DOF-001"

# --- ANALİZ VE İSTATİSTİK MODÜLLERİ ---
def dof_analiz_paneli(sikayet_df, sirket):
    st.markdown(f"### 📈 {sirket} - 8D & DÖF Analitiği")
    if sikayet_df.empty:
        st.info("İstatistik için veri bulunmuyor.")
        return
    
    s_8d = sikayet_df[sikayet_df['Şirket'] == sirket]
    if s_8d.empty:
        st.info("Bu şirkete ait 8D kaydı bulunamadı.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Şikayet", len(s_8d))
    c2.metric("Açık DÖF", len(s_8d[s_8d['Durum'] != 'Kapatıldı']))
    c3.metric("Kapatılan", len(s_8d[s_8d['Durum'] == 'Kapatıldı']))

    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**DÖF Durum Dağılımı**")
        st.bar_chart(s_8d['Durum'].value_counts())
    with col_b:
        st.write("**Müşteri Bazlı Hata Dağılımı**")
        st.bar_chart(s_8d['Müşteri'].value_counts())

# --- KALİTE HESAPLAMA (TRI) ---
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

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Alasar Group Quality Engine V26.0", layout="wide")

if 'genel_giris' not in st.session_state: st.session_state.genel_giris = False
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None
if 'onay_bekleyenler' not in st.session_state: st.session_state.onay_bekleyenler = []

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
            else: st.error("Hatalı Giriş!")
    st.stop()

# --- ROL SEÇİMİ ---
if st.session_state.aktif_user is None:
    st.subheader("Bölüm Doğrulaması")
    col_a, col_b = st.columns(2)
    s_sec = col_a.selectbox("Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"])
    r_sec = col_b.selectbox("Yetki Paneli:", ["Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
    ozel_p = st.text_input("Özel Şifre", type="password")
    if st.button("Paneli Aç"):
        if (r_sec == "Kalite Müdürü" and ozel_p == "30052012") or \
           (r_sec == "Üretim-Operatör" and ozel_p == "op789") or \
           (r_sec == "Genel Müdür" and ozel_p == "patron456"):
            st.session_state.aktif_user = {"role": r_sec, "sirket": s_sec}
            st.rerun()
        else: st.error("Yetkisiz Erişim!")
    st.stop()

u_role = st.session_state.aktif_user['role']
u_sirket = st.session_state.aktif_user['sirket']
ana_db = veriyi_excelden_yukle(DB_FILE)
sikayet_db = veriyi_excelden_yukle(SIKAYET_FILE)

st.sidebar.header(f"👤 {u_role}")
st.sidebar.info(f"Şirket: {u_sirket}")
if st.sidebar.button("Oturumu Kapat"):
    st.session_state.aktif_user = None
    st.rerun()

# --- PANEL 1: ÜRETİM OPERATÖR ---
if u_role == "Üretim-Operatör":
    st.header(f"🏭 {u_sirket} - Üretim Giriş Terminali")
    with st.form("operatör_form"):
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No", "LOT-")
        sevk = c2.number_input("Toplam Sevk", 1, value=5000)
        hata_ana = c3.selectbox("Baskın Hata", ["Hata Yok", "Çapak", "Ölçü", "Eksik Baskı", "Yüzey", "Hammadde"])
        
        st.divider()
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik) Adet", 0); p1p = h1.number_input("P1 Şiddet", 3.0)
        k3 = h2.number_input("P2 (Majör) Adet", 0); p2p = h2.number_input("P2 Şiddet", 2.0)
        l3 = h3.number_input("P3 (Minör) Adet", 0); p3p = h3.number_input("P3 Şiddet", 1.0)
        m3 = h4.number_input("P4 (Görsel) Adet", 0); p4p = h4.number_input("P4 Şiddet", 0.5)
        
        op_not = st.text_area("Operatör Notu / Açıklama")
        if st.form_submit_button("ANALİZE GÖNDER"):
            karar, ikon, skor, renk = kalite_motoru_hesapla(100, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
            data = {
                "Şirket": u_sirket, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Parti No": lot, "Sevk": sevk, "Baskın Hata": hata_ana, "TRI": round(skor, 4),
                "Sistem": karar, "P1_A": j3, "P1_S": p1p, "P2_A": k3, "P2_S": p2p,
                "P3_A": l3, "P3_S": p3p, "P4_A": m3, "P4_S": p4p, "Not": op_not,
                "Yönetici Aksiyonu": "BEKLİYOR" if karar != "UYGUN" else "OTOMATİK ONAY"
            }
            if karar == "UYGUN": veriyi_excele_kaydet(pd.DataFrame([data]), DB_FILE)
            else: st.session_state.onay_bekleyenler.append(data)
            st.success("Veri sisteme iletildi."); time.sleep(1); st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ ---
elif u_role == "Kalite Müdürü":
    t1, t2, t3 = st.tabs(["📊 Analizler", "🛠️ 8D / DÖF MODÜLÜ", "⚖️ Karar Bekleyenler"])
    
    with t1:
        dof_analiz_paneli(sikayet_db, u_sirket)
        st.divider()
        st.write("**Üretim Arşivi**")
        st.dataframe(ana_db[ana_db['Şirket'] == u_sirket].iloc[::-1] if not ana_db.empty else pd.DataFrame())

    with t2:
        st.header("🏁 8D / DÖF Kaydı ve Arşivi")
        with st.form("full_8d_form"):
            d_no = otomatik_dof_no_uret(sikayet_db)
            st.info(f"Yeni Kayıt No: {d_no}")
            c1, c2 = st.columns(2); m_ad = c1.text_input("Müşteri Adı"); s_tarih = c2.date_input("Tespit Tarihi")
            p_tanim = st.text_area("1. Problemin Tanımı"); hata_gorsel = st.file_uploader("2. Görsel Yükle", type=['jpg','png','pdf'])
            kok_neden = st.text_area("3. Kök Neden Analizi")
            f1, f2, f3 = st.columns(3); f_secilen = f1.text_area("4. Seçilen Faaliyet"); f_kalici = f2.text_area("5. Kalıcı Faaliyet"); f_onleyici = f3.text_area("6. Önleyici Faaliyet")
            b1, b2 = st.columns(2); durum = b1.selectbox("7. Durum", ["Başlatıldı", "Beklemede", "Kapatıldı"]); k_tarih = b2.text_input("8. Kapatılma Tarihi", "---")
            
            if st.form_submit_button("8D RAPORUNU KAYDET"):
                y_8d = pd.DataFrame([{"Şirket": u_sirket, "DOF_No": d_no, "Müşteri": m_ad, "Tarih": s_tarih, "Tanım": p_tanim, "Kok_Neden": kok_neden, "S_Faaliyet": f_secilen, "K_Faaliyet": f_kalici, "O_Faaliyet": f_onleyici, "Durum": durum, "Kapanis": k_tarih}])
                veriyi_excele_kaydet(y_8d, SIKAYET_FILE); st.success(f"{d_no} kaydedildi."); st.rerun()
        
        st.divider()
        st.subheader("📋 8D / DÖF Kayıt Tablosu (Excel Arşivi)")
        if not sikayet_db.empty:
            s_8d_tablo = sikayet_db[sikayet_db['Şirket'] == u_sirket]
            st.dataframe(s_8d_tablo.iloc[::-1])
        else: st.info("Henüz 8D kaydı bulunmuyor.")

    with t3:
        st.subheader("Karar Havuzu")
        bekleyenler = [b for b in st.session_state.onay_bekleyenler if b['Şirket'] == u_sirket and not b.get("Patrona_Gitti", False)]
        for i, b in enumerate(bekleyenler):
            with st.expander(f"Kayıt: {b['Parti No']} | TRI: {b['TRI']}"):
                st.table(pd.DataFrame({"Kritik (P1)": [b['P1_A']], "Majör (P2)": [b['P2_A']], "Minör (P3)": [b['P3_A']], "Görsel (P4)": [b['P4_A']]}))
                st.info(f"Op. Notu: {b['Not']}")
                aks = st.selectbox("Nihai Karar", ["Kabul", "Şartlı Kabul", "Karantina", "ÜST YÖNETİCİYE SEVK (PATRON)", "İade"], key=f"km_{i}")
                n = st.text_input("Karar Notu", key=f"kn_{i}")
                if st.button("UYGULA", key=f"kb_{i}"):
                    if "ÜST YÖNETİCİ" in aks:
                        for idx, item in enumerate(st.session_state.onay_bekleyenler):
                            if item['Parti No'] == b['Parti No']:
                                st.session_state.onay_bekleyenler[idx]["Patrona_Gitti"] = True
                                st.session_state.onay_bekleyenler[idx]["Mudur_Notu"] = n
                    else:
                        b.update({"Yönetici Aksiyonu": aks, "Mudur_Notu": n})
                        veriyi_excele_kaydet(pd.DataFrame([b]), DB_FILE)
                        st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['Parti No'] != b['Parti No']]
                    st.rerun()

# --- PANEL 3: GENEL MÜDÜR (PATRON) ---
elif u_role == "Genel Müdür":
    s_sec = st.radio("Şirket Seçimi:", ["Alasar Grup", "Hakan Kalıp Plastik"], horizontal=True)
    patron_onay = [x for x in st.session_state.onay_bekleyenler if x.get("Patrona_Gitti") and x['Şirket'] == s_sec]
    
    if patron_onay:
        st.markdown(f'<div style="background-color:#FF4B4B; padding:20px; border-radius:10px; text-align:center;"><h2 style="color:white;">🚨 ACİL ONAY BEKLEYEN {len(patron_onay)} SEVK!</h2></div>', unsafe_allow_html=True)
    
    dof_analiz_paneli(sikayet_db, s_sec)
    st.divider()
    
    col1, col2 = st.columns([2,1])
    with col1:
        st.subheader("👔 Kritik Sevk Onayları")
        for i, p in enumerate(patron_onay):
            with st.container():
                st.markdown(f"### Parti: {p['Parti No']} | TRI: {p['TRI']}")
                st.warning(f"Kalite Müdürü Notu: {p.get('Mudur_Notu')}")
                st.table(pd.DataFrame({"P1": [p['P1_A']], "P2": [p['P2_A']], "Hata": [p['Baskın Hata']]}))
                p_aks = st.radio("Karar", ["SEVK İZNİ VER", "ŞARTLI SEVK", "SEVKİ DURDUR"], key=f"pa_{i}")
                p_not = st.text_input("Patron Notu", key=f"pn_{i}")
                if st.button("MÜHÜRLE", key=f"pb_{i}"):
                    p.update({"Yönetici Aksiyonu": f"PATRON: {p_aks}", "Patron_Notu": p_not, "Onay_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    veriyi_excele_kaydet(pd.DataFrame([p]), DB_FILE)
                    st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['Parti No'] != p['Parti No']]
                    st.rerun()
            st.divider()

    with col2:
        st.subheader("🚨 Son 8D / DÖF Durumları")
        if not sikayet_db.empty:
            st.dataframe(sikayet_db[sikayet_db['Şirket'] == s_sec][['DOF_No', 'Müşteri', 'Durum']].tail(10))

    st.divider()
    st.subheader("📜 Genel Müdür (Patron) Karar Geçmişi")
    if not ana_db.empty:
        # Sadece Patronun karar verdiği satırları filtrele
        p_gecmis = ana_db[(ana_db['Şirket'] == s_sec) & (ana_db['Yönetici Aksiyonu'].str.contains("PATRON", na=False))]
        if not p_gecmis.empty:
            st.dataframe(p_gecmis[['Tarih', 'Parti No', 'TRI', 'Baskın Hata', 'Yönetici Aksiyonu', 'Patron_Notu']].iloc[::-1])
        else: st.info("Henüz mühürlediğiniz bir kayıt bulunmuyor.")

# --- İNDİRME ---
st.sidebar.divider()
if not ana_db.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        ana_db.to_excel(writer, index=False, sheet_name='Uretim')
        if not sikayet_db.empty: sikayet_db.to_excel(writer, index=False, sheet_name='8D_DOF')
    st.sidebar.download_button("📥 Excel Yedek Al", output.getvalue(), "Kalite_Sistem_Yedek.xlsx")
