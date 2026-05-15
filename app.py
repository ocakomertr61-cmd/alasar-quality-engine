import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io 
import time
import os

# --- VERİTABANI AYARLARI ---
# Mevcut dosyanızı korumak için ismini sabit tuttuk.
DB_FILE = "alasar_kalite_veritabani.xlsx"
SIKAYET_FILE = "musteri_sikayet_8d.xlsx"

def veriyi_excele_kaydet(yeni_df, dosya=DB_FILE):
    """Veriyi kalıcı olarak Excel dosyasına ekler veya oluşturur."""
    try:
        if not os.path.exists(dosya):
            yeni_df.to_excel(dosya, index=False, engine='openpyxl')
        else:
            mevcut_df = pd.read_excel(dosya, engine='openpyxl')
            guncel_df = pd.concat([mevcut_df, yeni_df], ignore_index=True)
            guncel_df.to_excel(dosya, index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Excel kayıt hatası: {e}")

def veriyi_excelden_yukle(dosya=DB_FILE):
    if os.path.exists(dosya):
        return pd.read_excel(dosya, engine='openpyxl')
    return pd.DataFrame()

# --- OTOMATİK QR KİMLİK ÜRETİCİ ---
def benzersiz_id_uret(sirket, mevcut_db):
    prefix = "AL" if "Alasar" in sirket else "HK"
    yil = datetime.now().strftime("%Y")
    s_kayitlar = mevcut_db[mevcut_db['Şirket'] == sirket] if not mevcut_db.empty and 'Şirket' in mevcut_db.columns else pd.DataFrame()
    
    if s_kayitlar.empty:
        yeni_no = 1
    else:
        try:
            # Son QR kodun numarasını çekip artırır
            son_id = str(s_kayitlar['QR_Kod'].iloc[-1])
            yeni_no = int(son_id.split('-')[-1]) + 1
        except:
            yeni_no = len(s_kayitlar) + 1
    return f"{prefix}-{yil}-{yeni_no:04d}"

# --- ANALİZ VE GRAFİK MODÜLÜ ---
def grafikleri_ciz(df, sikayet_df, sirket):
    if df.empty or 'Şirket' not in df.columns:
        st.info(f"{sirket} için henüz analiz edilecek veri mevcut değil.")
        return

    s_df = df[df['Şirket'] == sirket]
    s_sikayet = sikayet_df[sikayet_df['Şirket'] == sirket] if not sikayet_df.empty else pd.DataFrame()
    
    st.subheader(f"📊 {sirket} Performans Analizi")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Parti", len(s_df))
    m2.metric("Müşteri Şikayeti", len(s_sikayet))
    m3.metric("Açık DÖF Sayısı", len(s_sikayet[s_sikayet['Durum'] == 'Açık']) if not s_sikayet.empty else 0)
    m4.metric("Kritik (P1) Toplam", int(s_df['P1_A'].sum()) if 'P1_A' in s_df.columns else 0)

    col_l, col_r = st.columns(2)
    with col_l:
        st.write("📈 **Risk (TRI) Trendi**")
        st.line_chart(s_df['TRI'].tail(20))
    with col_r:
        st.write("🎯 **Baskın Hata Dağılımı (Pareto)**")
        if 'Baskın Hata Türü' in s_df.columns:
            st.bar_chart(s_df['Baskın Hata Türü'].value_counts())

# --- KALİTE MOTORU (TRI HESAPLAMA) ---
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

# --- SAYFA AYARLARI VE OTURUM ---
st.set_page_config(page_title="Alasar & Hakan Kalıp Quality Engine V22.0", layout="wide")

if 'genel_giris' not in st.session_state: st.session_state.genel_giris = False
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None
if 'onay_bekleyenler' not in st.session_state: st.session_state.onay_bekleyenler = []

# --- GİRİŞ EKRANI ---
if not st.session_state.genel_giris:
    st.markdown("<h2 style='text-align:center;'>🏢 GRUP KALİTE PORTALI GİRİŞİ</h2>", unsafe_allow_html=True)
    with st.form("genel_login"):
        u = st.text_input("Kullanıcı Adı").strip()
        p = st.text_input("Şifre", type="password").strip()
        if st.form_submit_button("Sisteme Gir"):
            if u == "alasar" and p == "30052012":
                st.session_state.genel_giris = True
                st.rerun()
            else: st.error("Hatalı giriş!")
    st.stop()

# --- ROL VE ŞİRKET SEÇİMİ ---
if st.session_state.aktif_user is None:
    st.subheader("Lütfen Yetki ve Şirket Seçiniz")
    c1, c2 = st.columns(2)
    sirket_sec = c1.selectbox("Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"])
    rol_sec = c2.selectbox("Panel:", ["Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
    ps = st.text_input(f"Özel Şifre", type="password")
    
    if st.button("Paneli Aç"):
        # Şifre Kontrolleri (V17.2 mantığı korunmuştur)
        if (rol_sec == "Kalite Müdürü" and ps == "30052012") or \
           (rol_sec == "Üretim-Operatör" and ps == "op789") or \
           (rol_sec == "Genel Müdür" and ps == "patron456"):
            st.session_state.aktif_user = {"role": rol_sec, "sirket": sirket_sec}
            st.rerun()
        else: st.error("Yetkisiz Şifre!")
    st.stop()

# --- GÜVENLİ VERİ ÇEKME (TypeError Engelleme) ---
user_data = st.session_state.get('aktif_user')
if not user_data:
    st.session_state.aktif_user = None
    st.rerun()

u_role = user_data['role']
u_sirket = user_data['sirket']
ana_db = veriyi_excelden_yukle(DB_FILE)
sikayet_db = veriyi_excelden_yukle(SIKAYET_FILE)

st.sidebar.title(f"📍 {u_role}")
st.sidebar.write(f"Şirket: {u_sirket}")
if st.sidebar.button("Oturumu Kapat"):
    st.session_state.aktif_user = None
    st.rerun()

# --- PANEL 1: ÜRETİM-OPERATÖR ---
if u_role == "Üretim-Operatör":
    st.header(f"🏭 {u_sirket} - Üretim Giriş Terminali")
    with st.form("veri_giris_formu"):
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No", "LOT-")
        sevk = c2.number_input("Toplam Sevk Adeti", 1, value=1000)
        vardiya = c3.selectbox("Vardiya No", list(range(60, 81)))
        
        c4, c5 = st.columns(2)
        kontrol = c4.number_input("Kontrol Edilen Adet", 1, value=100)
        baskin_hata = c5.selectbox("Baskın Hata Türü", ["Hata Yok", "Çapak", "Ölçü", "Yüzey", "Hammadde", "Kalıp"])
        
        st.divider()
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik)", 0); p1p = h1.number_input("P1 Puan", 1.0)
        k3 = h2.number_input("P2 (Majör)", 0); p2p = h2.number_input("P2 Puan", 1.0)
        l3 = h3.number_input("P3 (Minör)", 0); p3p = h3.number_input("P3 Puan", 1.0)
        m3 = h4.number_input("P4 (Görsel)", 0); p4p = h4.number_input("P4 Puan", 1.0)
        
        op_not = st.text_area("Operatör Notları")
        submit = st.form_submit_button("SİSTEM ANALİZİNİ BAŞLAT VE QR MÜHÜRLE")

    if submit:
        karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
        yeni_qr = benzersiz_id_uret(u_sirket, ana_db)
        
        data = {
            "Şirket": u_sirket, "QR_Kod": yeni_qr, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Vardiya": vardiya, "Parti No": lot, "Sevk": sevk, "Kontrol": kontrol, 
            "Baskın Hata Türü": baskin_hata, "TRI": round(skor, 4), "Sistem": karar, 
            "P1_A": j3, "P2_A": k3, "P3_A": l3, "P4_A": m3, "Not": op_not,
            "Yönetici Aksiyonu": "BEKLİYOR" if karar != "UYGUN" else "OTOMATİK ONAY"
        }
        
        if karar == "UYGUN":
            veriyi_excele_kaydet(pd.DataFrame([data]), DB_FILE)
            st.success(f"✅ UYGUN: Kayıt Arşivlendi. QR: {yeni_qr}")
        else:
            st.session_state.onay_bekleyenler.append(data)
            st.warning(f"⚠️ {karar}: Kayıt Yönetici Onayına Gönderildi. QR: {yeni_qr}")
        time.sleep(1.5)
        st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ ---
elif u_role == "Kalite Müdürü":
    tab1, tab2, tab3 = st.tabs(["📊 Performans & Analiz", "🚨 Müşteri Şikayetleri (8D)", "📜 Arşiv"])
    
    with tab1:
        grafikleri_ciz(ana_db, sikayet_db, u_sirket)
        st.divider()
        st.header("⚖️ Karar Bekleyen Kayıtlar")
        aktif_bekleyenler = [b for b in st.session_state.onay_bekleyenler if b['Şirket'] == u_sirket and not b.get("Üst Yöneticiye Sevk", False)]
        
        if not aktif_bekleyenler: st.info("Onay bekleyen kayıt bulunmuyor.")
        for i, bekleyen in enumerate(aktif_bekleyenler):
            with st.expander(f"📌 {bekleyen['Parti No']} | QR: {bekleyen['QR_Kod']} | TRI: {bekleyen['TRI']}"):
                aks = st.selectbox("Nihai Karar", ["Olduğu Gibi Kabul", "Şartlı Kabul", "Karantina", "Üst Yöneticiye Sevk (Patron)", "İade"], key=f"aks_{i}")
                y_not = st.text_input("Yönetici Notu", key=f"not_{i}")
                if st.button("KARARI UYGULA", key=f"btn_{i}"):
                    if "Üst Yönetici" in aks:
                        for idx, b in enumerate(st.session_state.onay_bekleyenler):
                            if b['QR_Kod'] == bekleyen['QR_Kod']:
                                st.session_state.onay_bekleyenler[idx]["Üst Yöneticiye Sevk"] = True
                                st.session_state.onay_bekleyenler[idx]["Kalite Müdürü Notu"] = y_not
                        st.info("Patron onayına sevk edildi.")
                    else:
                        bekleyen.update({"Yönetici Aksiyonu": aks, "Yönetici Notu": y_not})
                        veriyi_excele_kaydet(pd.DataFrame([bekleyen]), DB_FILE)
                        st.session_state.onay_bekleyenler = [b for b in st.session_state.onay_bekleyenler if b['QR_Kod'] != bekleyen['QR_Kod']]
                    st.rerun()

    with tab2:
        st.subheader("Yeni Müşteri Şikayeti / 8D Kaydı")
        with st.form("8d_form"):
            m, k, d = st.text_input("Müşteri"), st.text_input("Konu"), st.selectbox("Durum", ["Açık", "Kapatıldı"])
            if st.form_submit_button("8D KAYDET"):
                yeni_8d = pd.DataFrame([{"Şirket": u_sirket, "Tarih": datetime.now().strftime("%Y-%m-%d"), "Müşteri": m, "Konu": k, "Durum": d}])
                veriyi_excele_kaydet(yeni_8d, SIKAYET_FILE)
                st.success("Şikayet Patron ekranına düştü."); st.rerun()

    with tab3:
        st.dataframe(ana_db[ana_db['Şirket'] == u_sirket].iloc[::-1] if not ana_db.empty else pd.DataFrame())

# --- PANEL 3: GENEL MÜDÜR ---
elif u_role == "Genel Müdür":
    s_sec = st.radio("Şirket Seçin:", ["Alasar Grup", "Hakan Kalıp Plastik"], horizontal=True)
    grafikleri_ciz(ana_db, sikayet_db, s_sec)
    
    st.divider()
    st.header("👔 Kritik Onay & Şikayet Takibi")
    sevk_edilenler = [b for b in st.session_state.onay_bekleyenler if b.get("Üst Yöneticiye Sevk", False) and b['Şirket'] == s_sec]
    
    if sevk_edilenler:
        for i, sevk in enumerate(sevk_edilenler):
            st.error(f"Kritik Talep: {sevk['Parti No']} | Müdür Notu: {sevk.get('Kalite Müdürü Notu')}")
            if st.button(f"Onayla: {sevk['QR_Kod']}", key=f"p_btn_{i}"):
                sevk.update({"Yönetici Aksiyonu": "PATRON ONAYI", "Onay Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")})
                veriyi_excele_kaydet(pd.DataFrame([sevk]), DB_FILE)
                st.session_state.onay_bekleyenler = [b for b in st.session_state.onay_bekleyenler if b['QR_Kod'] != sevk['QR_Kod']]
                st.rerun()
    else: st.info("Bekleyen kritik onay yok.")

# --- İNDİRME BLOĞU ---
st.sidebar.divider()
if not ana_db.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        ana_db.to_excel(writer, index=False, sheet_name='Uretim')
        if not sikayet_db.empty: sikayet_db.to_excel(writer, index=False, sheet_name='8D_Sikayet')
    st.sidebar.download_button("📥 Excel İndir", output.getvalue(), "Grup_Kalite_Raporu.xlsx", use_container_width=True)
