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

# Veriyi Excel'e kaydeden ve güncelleyen ana fonksiyon
def veriyi_excele_kaydet(yeni_df, dosya):
    try:
        if not os.path.exists(dosya):
            yeni_df.to_excel(dosya, index=False, engine='openpyxl')
        else:
            mevcut_df = pd.read_excel(dosya, engine='openpyxl')
            # Eğer kayıt güncelleniyorsa (Müdür/Patron onayı gibi), eski satırı sil
            if 'Parti No' in yeni_df.columns and not mevcut_df.empty:
                mevcut_df = mevcut_df[~((mevcut_df['Parti No'] == yeni_df['Parti No'].iloc[0]) & 
                                        (mevcut_df['Tarih'] == yeni_df['Tarih'].iloc[0]))]
            
            guncel_df = pd.concat([mevcut_df, yeni_df], ignore_index=True)
            guncel_df.to_excel(dosya, index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Kayıt Hatası ({dosya}): {e}")

# Veriyi Excel'den çeken ana fonksiyon
def veriyi_excelden_yukle(dosya):
    if os.path.exists(dosya):
        return pd.read_excel(dosya, engine='openpyxl')
    return pd.DataFrame()

# Otomatik 8D Numarası Üretme
def otomatik_dof_no_uret(mevcut_8d_db):
    yil = datetime.now().strftime("%Y")
    if mevcut_8d_db.empty: return f"{yil}-DOF-001"
    try:
        son_no = int(str(mevcut_8d_db['DOF_No'].iloc[-1]).split('-')[-1])
        return f"{yil}-DOF-{son_no + 1:03d}"
    except: return f"{yil}-DOF-001"

# KALİTE HESAPLAMA MOTORU (TRI)
def kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    hata_orani = (toplam_hata / G3) if G3 > 0 else 0
    # Hassas katsayılar ile TRI skoru
    temel_oran = ((P3_p * 2.5) + (Q3_p * 1.5) + (R3_p * 0.7) + (S3_p * 0.3)) / 5
    t3_skor = max(temel_oran * (1 + (J3*0.05 + K3*0.02)), toplam_hata / 15) if toplam_hata > 0 else 0.0
    
    red_mi = (hata_orani > 0.08 or J3 >= 1 or t3_skor >= 4.0)
    sartli_mi = False if red_mi else (t3_skor > 1.5 or (J3 + K3) >= 5)
    
    if red_mi: return "RED", "🔴", t3_skor, "#FF4B4B" 
    elif sartli_mi: return "SARI", "🟡", t3_skor, "#FFD700" 
    else: return "UYGUN", "🟢", t3_skor, "#28A745" 

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Alasar Group Quality Engine V33.0", layout="wide")

if 'genel_giris' not in st.session_state: st.session_state.genel_giris = False
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None

# --- 1. PORTAL GİRİŞİ ---
if not st.session_state.genel_giris:
    st.markdown("<h1 style='text-align:center;'>🛡️ ALASAR GRUP KALİTE PORTALI</h1>", unsafe_allow_html=True)
    with st.form("portal_giris"):
        u = st.text_input("Kullanıcı Adı"); p = st.text_input("Sistem Şifresi", type="password")
        if st.form_submit_button("Giriş Yap"):
            if u == "alasar" and p == "30052012": st.session_state.genel_giris = True; st.rerun()
            else: st.error("Hatalı Giriş Bilgileri!")
    st.stop()

# --- 2. ROL SEÇİMİ ---
if st.session_state.aktif_user is None:
    st.subheader("Bölüm Doğrulaması")
    col_a, col_b = st.columns(2)
    s_sec = col_a.selectbox("Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"])
    r_sec = col_b.selectbox("Yetki Paneli:", ["Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
    ozel_p = st.text_input("Özel Şifre", type="password")
    if st.button("Paneli Aç"):
        if (r_sec == "Kalite Müdürü" and ozel_p == "30052012") or (r_sec == "Üretim-Operatör" and ozel_p == "op789") or (r_sec == "Genel Müdür" and ozel_p == "patron456"):
            st.session_state.aktif_user = {"role": r_sec, "sirket": s_sec}; st.rerun()
        else: st.error("Yetkisiz Erişim!")
    st.stop()

u_role = st.session_state.aktif_user['role']
u_sirket = st.session_state.aktif_user['sirket']
ana_db = veriyi_excelden_yukle(DB_FILE)
sikayet_db = veriyi_excelden_yukle(SIKAYET_FILE)

# --- PANEL 1: ÜRETİM OPERATÖR (TAM DETAYLI) ---
if u_role == "Üretim-Operatör":
    st.header(f"🏭 {u_sirket} - Üretim Giriş Terminali")
    
    with st.form("operatör_form_genis"):
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No (LOT)", "LOT-")
        sevk = c2.number_input("Toplam Sevk Edilecek", 1, value=5000)
        hata_ana = c3.selectbox("Baskın Hata Türü", ["Hata Yok", "Çapak", "Eksik Baskı", "Ölçü Sapması", "Yüzey Hatası", "Hammadde"])
        
        c4, c5, c6 = st.columns(3)
        op_ad = c4.text_input("Operatör Ad Soyad")
        vardiya = c5.selectbox("Vardiya No", [1, 2, 3])
        kontrol_mik = c6.number_input("Kontrol Edilen Mik.", 1, value=100)
        
        st.divider()
        st.write("🔍 **Hata Dağılımı ve Şiddet Puanlama**")
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik)", 0); p1p = h1.number_input("P1 Şiddet", value=3.0)
        k3 = h2.number_input("P2 (Majör)", 0); p2p = h2.number_input("P2 Şiddet", value=2.0)
        l3 = h3.number_input("P3 (Minör)", 0); p3p = h3.number_input("P3 Şiddet", value=1.0)
        m3 = h4.number_input("P4 (Görsel)", 0); p4p = h4.number_input("P4 Şiddet", value=0.5)
        
        st.divider()
        st.write("📸 **Üretim Kanıt Fotoğrafları**")
        f_col1, f_col2 = st.columns(2)
        f1 = f_col1.file_uploader("Genel Görünüm", type=['jpg', 'png'])
        f2 = f_col2.file_uploader("Hata Detayı", type=['jpg', 'png'])
        
        op_not = st.text_area("Operatör Notu / Teknik Açıklama")
        
        analiz_et = st.form_submit_button("SİSTEM ANALİZİNİ ÇALIŞTIR")

    if analiz_et:
        karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol_mik, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
        st.session_state.gecici_analiz = {
            "Şirket": u_sirket, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Parti No": lot, "Sevk": sevk, "Baskın Hata": hata_ana, "TRI": round(skor, 4),
            "Sistem": karar, "Renk": renk, "P1_A": j3, "P2_A": k3, "P3_A": l3, "P4_A": m3,
            "Operatör": op_ad, "Vardiya": vardiya, "Not": op_not, "Kontrol": kontrol_mik
        }

    if 'gecici_analiz' in st.session_state:
        g = st.session_state.gecici_analiz
        st.markdown(f"""<div style="background-color:{g['Renk']}; padding:30px; border-radius:15px; text-align:center; border: 4px solid white;">
                <h1 style="color:white; margin:0;">ANALİZ: {g['Sistem']} (Skor: {g['TRI']})</h1></div>""", unsafe_allow_html=True)
        
        st.warning("⚠️ Bu veriyi veritabanına göndermeyi onaylıyor musunuz?")
        onay1, onay2 = st.columns(2)
        if onay1.button("✅ EVET, KAYDI GÖNDER", use_container_width=True):
            g.update({"Yönetici Aksiyonu": "BEKLİYOR" if g['Sistem'] != "UYGUN" else "OTOMATİK ONAY"})
            veriyi_excele_kaydet(pd.DataFrame([g]), DB_FILE)
            st.markdown("<h1 style='color:#28A745; text-align:center; font-size:48px;'>✅ KAYIT BAŞARI İLE İLETİLDİ</h1>", unsafe_allow_html=True)
            del st.session_state.gecici_analiz; time.sleep(2); st.rerun()
        if onay2.button("❌ İPTAL ET", use_container_width=True):
            del st.session_state.gecici_analiz; st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ (8D + KARAR HAVUZU) ---
elif u_role == "Kalite Müdürü":
    t1, t2, t3 = st.tabs(["📊 Veri Arşivi", "🛠️ DİNAMİK 8D / DÖF", "⚖️ Karar Havuzu"])
    
    with t1:
        st.subheader(f"{u_sirket} Geçmiş Kayıtlar")
        st.dataframe(ana_db[ana_db['Şirket'] == u_sirket].iloc[::-1] if not ana_db.empty else pd.DataFrame())

    with t2:
        st.header("🏁 8D Yönetim Merkezi")
        islem = st.radio("İşlem Tipi:", ["Yeni Kayıt Aç", "Mevcut Kaydı Güncelle"], horizontal=True)
        s_8d = sikayet_db[sikayet_db['Şirket'] == u_sirket] if not sikayet_db.empty else pd.DataFrame()
        if islem == "Mevcut Kaydı Güncelle" and not s_8d.empty:
            secilen_no = st.selectbox("Güncellenecek Kayıt:", s_8d['DOF_No'].tolist())
            v = s_8d[s_8d['DOF_No'] == secilen_no].iloc[0]
        else: secilen_no = otomatik_dof_no_uret(sikayet_db); v = None

        with st.form("8d_form"):
            m_ad = st.text_input("Müşteri", value=v['Müşteri'] if v is not None else "")
            p_tanim = st.text_area("Hata Tanımı", value=v['Tanım'] if v is not None else "")
            k_neden = st.text_area("Kök Neden", value=v['Kok_Neden'] if v is not None else "")
            durum = st.selectbox("Dosya Durumu", ["Başlatıldı", "Beklemede", "Kapatıldı"], index=0 if v is None else ["Başlatıldı", "Beklemede", "Kapatıldı"].index(v['Durum']))
            if st.form_submit_button("KAYDI SİSTEME İŞLE"):
                veriyi_excele_kaydet(pd.DataFrame([{"Şirket": u_sirket, "DOF_No": secilen_no, "Müşteri": m_ad, "Tarih": datetime.now().strftime("%Y-%m-%d"), "Tanım": p_tanim, "Kok_Neden": k_neden, "Durum": durum}]), SIKAYET_FILE)
                st.success("8D Kaydı Güncellendi"); time.sleep(1); st.rerun()

    with t3:
        st.subheader("Onay Bekleyen Kritik Sevkiyatlar")
        if not ana_db.empty:
            bekleyenler = ana_db[(ana_db['Şirket'] == u_sirket) & (ana_db['Yönetici Aksiyonu'] == "BEKLİYOR")]
            if bekleyenler.empty: st.info("Şu an bekleyen kayıt yok.")
            for i, row in bekleyenler.iterrows():
                with st.expander(f"LOT: {row['Parti No']} | TRI: {row['TRI']}"):
                    st.write(f"Operatör: {row['Operatör']} | Not: {row['Not']}")
                    aks = st.selectbox("Kararınız", ["Kabul", "Şartlı Kabul", "PATRONA SEVK ET"], key=f"km_{i}")
                    m_not = st.text_input("Müdür Karar Notu", key=f"kn_{i}")
                    if st.button("KARARI UYGULA", key=f"kb_{i}"):
                        row['Yönetici Aksiyonu'] = "PATRON ONALAYI BEKLİYOR" if aks == "PATRONA SEVK ET" else aks
                        row['Mudur_Notu'] = m_not
                        veriyi_excele_kaydet(pd.DataFrame([row]), DB_FILE)
                        st.success("Karar iletildi"); time.sleep(1); st.rerun()

# --- PANEL 3: GENEL MÜDÜR (PATRON) ---
elif u_role == "Genel Müdür":
    st.header("👔 Üst Yönetim Onay Paneli")
    s_filtre = st.radio("Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"], horizontal=True)
    if not ana_db.empty:
        p_bekleyen = ana_db[(ana_db['Şirket'] == s_filtre) & (ana_db['Yönetici Aksiyonu'] == "PATRON ONALAYI BEKLİYOR")]
        if p_bekleyen.empty: st.info("Onayınızı bekleyen kritik bir sevk bulunmuyor.")
        for i, row in p_bekleyen.iterrows():
            st.error(f"KRİTİK SEVK: {row['Parti No']} | TRI: {row['TRI']}")
            st.info(f"Kalite Müdürü Notu: {row.get('Mudur_Notu', 'Belirtilmemiş')}")
            p_aks = st.radio("Nihai Karar", ["SEVK İZNİ VER", "SEVKİ DURDUR / İADE"], key=f"pa_{i}")
            p_not = st.text_input("Patron Notu", key=f"pn_{i}")
            if st.button("MÜHÜRÜ BAS", key=f"pb_{i}"):
                row['Yönetici Aksiyonu'] = f"PATRON: {p_aks}"
                row['Patron_Notu'] = p_not
                veriyi_excele_kaydet(pd.DataFrame([row]), DB_FILE)
                st.success("Karar Arşivlendi"); time.sleep(1); st.rerun()

# --- SIDEBAR & YEDEKLEME ---
st.sidebar.divider()
if st.sidebar.button("Oturumu Kapat"): st.session_state.aktif_user = None; st.rerun()
if not ana_db.empty:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer: ana_db.to_excel(writer, index=False)
    st.sidebar.download_button("📥 Tüm Veritabanını İndir", out.getvalue(), f"Alasar_Sistem_{datetime.now().strftime('%d%m%Y')}.xlsx")
