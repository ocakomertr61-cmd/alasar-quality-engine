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
def benzersiz_qr_uret(sirket, mevcut_db):
    prefix = "AL" if "Alasar" in sirket else "HK"
    yil = datetime.now().strftime("%Y")
    s_kayitlar = mevcut_db[mevcut_db['Şirket'] == sirket] if not mevcut_db.empty and 'Şirket' in mevcut_db.columns else pd.DataFrame()
    yeni_no = (int(str(s_kayitlar['QR_Kod'].iloc[-1]).split('-')[-1]) + 1) if not s_kayitlar.empty else 1
    return f"{prefix}-{yil}-{yeni_no:04d}"

def otomatik_dof_no_uret(mevcut_8d_db):
    yil = datetime.now().strftime("%Y")
    if mevcut_8d_db.empty:
        return f"{yil}-DOF-001"
    else:
        try:
            son_no = int(str(mevcut_8d_db['DOF_No'].iloc[-1]).split('-')[-1])
            return f"{yil}-DOF-{son_no + 1:03d}"
        except:
            return f"{yil}-DOF-001"

# --- ANALİZ MODÜLÜ ---
def grafikleri_ciz(df, sikayet_df, sirket):
    st.subheader(f"📊 {sirket} Genel Performans")
    if df.empty or 'Şirket' not in df.columns:
        st.info("Henüz üretim verisi yok.")
        return
    s_df = df[df['Şirket'] == sirket]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Parti", len(s_df))
    m2.metric("Ortalama TRI", f"{s_df['TRI'].mean():.2f}" if not s_df.empty else "0.00")
    
    s_8d = sikayet_df[sikayet_df['Şirket'] == sirket] if not sikayet_df.empty else pd.DataFrame()
    m3.metric("Aktif DÖF", len(s_8d[s_8d['Durum'] != 'Kapatıldı']) if not s_8d.empty else 0)
    m4.metric("Kritik Hata (P1)", int(s_df['P1_A'].sum()) if 'P1_A' in s_df.columns else 0)

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

# --- SAYFA VE OTURUM ---
st.set_page_config(page_title="Alasar Group Quality Engine V23.0", layout="wide")

# Session State Güvenlik Duvarı
for key in ['genel_giris', 'aktif_user', 'onay_bekleyenler']:
    if key not in st.session_state:
        if key == 'onay_bekleyenler': st.session_state[key] = []
        elif key == 'genel_giris': st.session_state[key] = False
        else: st.session_state[key] = None

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

# --- VERİ ÇEKME VE KONTROL ---
u_data = st.session_state.get('aktif_user')
if not u_data: st.rerun() # TypeError koruması

u_role = u_data['role']
u_sirket = u_data['sirket']
ana_db = veriyi_excelden_yukle(DB_FILE)
sikayet_db = veriyi_excelden_yukle(SIKAYET_FILE)

st.sidebar.header(f"👤 {u_role}")
st.sidebar.info(f"Şirket: {u_sirket}")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.aktif_user = None
    st.rerun()

# --- PANEL 1: ÜRETİM-OPERATÖR ---
if u_role == "Üretim-Operatör":
    st.header(f"🚀 {u_sirket} Üretim Terminali")
    with st.form("op_veri_form"):
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No / Batch", "LOT-")
        sevk = c2.number_input("Sevk Miktarı", 1, value=5000)
        vardiya = c3.selectbox("Vardiya", list(range(60, 81)))
        
        c4, c5 = st.columns(2)
        kontrol = c4.number_input("Örneklem Adedi", 1, value=100)
        hata_tipi = c5.selectbox("Ana Hata Türü", ["Hata Yok", "Çapak", "Eksik Baskı", "Ölçüsel Sapma", "Yüzey Deformasyonu", "Hammadde Problemi"])
        
        st.divider()
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik)", 0); p1p = h1.number_input("P1 Ağırlık", 3.0)
        k3 = h2.number_input("P2 (Majör)", 0); p2p = h2.number_input("P2 Ağırlık", 2.0)
        l3 = h3.number_input("P3 (Minör)", 0); p3p = h3.number_input("P3 Ağırlık", 1.0)
        m3 = h4.number_input("P4 (Görsel)", 0); p4p = h4.number_input("P4 Ağırlık", 0.5)
        
        op_not = st.text_area("Gözlem ve Notlar")
        if st.form_submit_button("ANALİZİ TAMAMLA VE QR ÜRET"):
            karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
            qr = benzersiz_qr_uret(u_sirket, ana_db)
            
            kayit = {
                "Şirket": u_sirket, "QR_Kod": qr, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Vardiya": vardiya, "Parti No": lot, "Sevk": sevk, "Kontrol": kontrol, 
                "Baskın Hata": hata_tipi, "TRI": round(skor, 4), "Sistem": karar, 
                "P1_A": j3, "P2_A": k3, "P3_A": l3, "P4_A": m3, "Not": op_not,
                "Yönetici Aksiyonu": "BEKLİYOR" if karar != "UYGUN" else "OTOMATİK ONAY"
            }
            
            if karar == "UYGUN":
                veriyi_excele_kaydet(pd.DataFrame([kayit]), DB_FILE)
                st.success(f"Kayıt Onaylandı. QR: {qr}")
            else:
                st.session_state.onay_bekleyenler.append(kayit)
                st.warning(f"Kayıt {karar} statüsünde. Yöneticiye iletildi. QR: {qr}")
            time.sleep(1); st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ ---
elif u_role == "Kalite Müdürü":
    t1, t2, t3 = st.tabs(["📊 Sistem Analizi", "🛠️ 8D & DÖF Yönetimi", "📋 Karar Havuzu"])
    
    with t1:
        grafikleri_ciz(ana_db, sikayet_db, u_sirket)
        st.divider()
        st.subheader("Arşiv Kayıtları")
        st.dataframe(ana_db[ana_db['Şirket'] == u_sirket].iloc[::-1] if not ana_db.empty else pd.DataFrame())

    with t2:
        st.header("🏁 Yeni 8D / DÖF Süreci Başlat")
        with st.form("dof_form"):
            d_no = otomatik_dof_no_uret(sikayet_db)
            st.write(f"**Atanan DÖF NO:** {d_no}")
            
            col1, col2 = st.columns(2)
            m_ad = col1.text_input("Müşteri Adı")
            s_tarih = col2.date_input("Şikayet Tarihi")
            
            p_tanim = st.text_area("Problemin Tanımı")
            kok_neden = st.text_area("Kök Neden Analizi")
            
            st.divider()
            f1, f2 = st.columns(2)
            f_secilen = f1.text_area("Seçilen Faaliyetler")
            f_kalici = f2.text_area("Uygulanan Kalıcı Faaliyetler")
            f_onleyici = st.text_area("Önleyici Faaliyetler")
            
            st.divider()
            b1, b2 = st.columns(2)
            durum = b1.selectbox("8D Durumu", ["Başlatıldı", "Beklemede", "Kapatıldı"])
            k_tarih = b2.text_input("Kapatılma Tarihi (Kapandıysa)", "---")
            
            if st.form_submit_button("DÖF KAYDINI ONAYLA"):
                yeni_8d = pd.DataFrame([{
                    "Şirket": u_sirket, "DOF_No": d_no, "Müşteri": m_ad, "Tarih": s_tarih,
                    "Tanım": p_tanim, "Kök_Neden": kok_neden, "S_Faaliyet": f_secilen,
                    "K_Faaliyet": f_kalici, "O_Faaliyet": f_onleyici, "Durum": durum, "Kapanis": k_tarih
                }])
                veriyi_excele_kaydet(yeni_8d, SIKAYET_FILE)
                st.success(f"{d_no} başarıyla sisteme işlendi."); time.sleep(1); st.rerun()

    with t3:
        st.subheader("Onay Bekleyen Üretim Partileri")
        bekleyenler = [b for b in st.session_state.onay_bekleyenler if b['Şirket'] == u_sirket and not b.get("Patrona_Gitti", False)]
        if not bekleyenler: st.info("Bekleyen iş yok.")
        for i, b in enumerate(bekleyenler):
            with st.expander(f"Kayıt: {b['Parti No']} | TRI: {b['TRI']}"):
                aks = st.selectbox("Nihai Karar", ["Kabul", "Şartlı Kabul", "Karantina", "ÜST YÖNETİCİYE SEVK (PATRON)", "İmha/İade"], key=f"k_aks_{i}")
                n = st.text_input("Yönetici Notu", key=f"k_not_{i}")
                if st.button("KARARI İŞLE", key=f"k_btn_{i}"):
                    if "ÜST YÖNETİCİ" in aks:
                        for idx, item in enumerate(st.session_state.onay_bekleyenler):
                            if item['QR_Kod'] == b['QR_Kod']:
                                st.session_state.onay_bekleyenler[idx]["Patrona_Gitti"] = True
                                st.session_state.onay_bekleyenler[idx]["Mudur_Notu"] = n
                        st.warning("Dosya Patron onayına gönderildi.")
                    else:
                        b.update({"Yönetici Aksiyonu": aks, "Yönetici Notu": n})
                        veriyi_excele_kaydet(pd.DataFrame([b]), DB_FILE)
                        st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['QR_Kod'] != b['QR_Kod']]
                    st.rerun()

# --- PANEL 3: GENEL MÜDÜR (PATRON) ---
elif u_role == "Genel Müdür":
    s_sec = st.radio("İzlenecek Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"], horizontal=True)
    
    # KRİTİK UYARI PANELİ (DİNAMİK)
    patron_onay_listesi = [x for x in st.session_state.onay_bekleyenler if x.get("Patrona_Gitti") and x['Şirket'] == s_sec]
    
    if patron_onay_listesi:
        st.markdown(f"""
            <div style="background-color:#FF4B4B; padding:30px; border-radius:15px; border: 5px solid white; text-align:center; animation: pulse 2s infinite;">
                <h1 style="color:white; margin:0;">🚨 DİKKAT: KRİTİK ONAY BEKLEYEN {len(patron_onay_listesi)} KAYIT VAR!</h1>
                <p style="color:white; font-size:20px;">Lütfen aşağıdan sevk kararlarını veriniz.</p>
            </div>
            <style>
            @keyframes pulse {{ 0% {{opacity: 1;}} 50% {{opacity: 0.5;}} 100% {{opacity: 1;}} }}
            </style>
        """, unsafe_allow_html=True)

    grafikleri_ciz(ana_db, sikayet_db, s_sec)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.header("👔 Patron Onay Ekranı")
        if not patron_onay_listesi: st.info("Onay bekleyen kritik sevk bulunmuyor.")
        for i, p_onay in enumerate(patron_onay_listesi):
            with st.container():
                st.markdown(f"### 📦 Parti: {p_onay['Parti No']} (TRI: {p_onay['TRI']})")
                st.write(f"**Kalite Müdürü Notu:** {p_onay.get('Mudur_Notu', 'Belirtilmemiş')}")
                p_karar = st.radio("Kararınız:", ["SEVK ET", "ŞARTLI SEVK", "DURDUR/İADE"], key=f"p_kar_{i}")
                p_gerekce = st.text_input("Karar Gerekçesi", key=f"p_ger_{i}")
                if st.button("KARARI MÜHÜRLE", key=f"p_müh_{i}"):
                    p_onay.update({"Yönetici Aksiyonu": f"PATRON: {p_karar}", "Patron_Notu": p_gerekce, "Onay_Tarihi": datetime.now()})
                    veriyi_excele_kaydet(pd.DataFrame([p_onay]), DB_FILE)
                    st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['QR_Kod'] != p_onay['QR_Kod']]
                    st.success("Karar sisteme işlendi."); time.sleep(1); st.rerun()
            st.divider()

    with col_r:
        st.header("🚨 DÖF / 8D Özet Takibi")
        if not sikayet_db.empty:
            s_8d = sikayet_db[sikayet_db['Şirket'] == s_sec]
            for idx, row in s_8d.tail(5).iterrows():
                renk = "orange" if row['Durum'] != "Kapatıldı" else "green"
                st.markdown(f"""
                <div style="border-left: 5px solid {renk}; padding-left:10px; margin-bottom:10px; background:#f0f2f6; padding:10px;">
                    <b>{row['DOF_No']} - {row['Müşteri']}</b><br>
                    Konu: {row['Tanım'][:50]}...<br>
                    Durum: <span style="color:{renk}; font-weight:bold;">{row['Durum']}</span>
                </div>
                """, unsafe_allow_html=True)
        else: st.write("Şikayet kaydı bulunmuyor.")

# --- GENEL RAPORLAMA ---
st.sidebar.divider()
if not ana_db.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        ana_db.to_excel(writer, index=False, sheet_name='Uretim_Verileri')
        if not sikayet_db.empty: sikayet_db.to_excel(writer, index=False, sheet_name='8D_DOF_Arsivi')
    st.sidebar.download_button("📥 Full Veritabanı (Excel)", output.getvalue(), "Grup_Kalite_Full.xlsx", use_container_width=True)
