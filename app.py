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
            if 'DOF_No' in yeni_df.columns and not mevcut_df.empty:
                mevcut_df = mevcut_df[~mevcut_df['DOF_No'].isin(yeni_df['DOF_No'])]
            guncel_df = pd.concat([mevcut_df, yeni_df], ignore_index=True)
            guncel_df.to_excel(dosya, index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Kayıt Hatası ({dosya}): {e}")

def veriyi_excelden_yukle(dosya):
    if os.path.exists(dosya):
        return pd.read_excel(dosya, engine='openpyxl')
    return pd.DataFrame()

def otomatik_dof_no_uret(mevcut_8d_db):
    yil = datetime.now().strftime("%Y")
    if mevcut_8d_db.empty: return f"{yil}-DOF-001"
    try:
        son_no = int(str(mevcut_8d_db['DOF_No'].iloc[-1]).split('-')[-1])
        return f"{yil}-DOF-{son_no + 1:03d}"
    except: return f"{yil}-DOF-001"

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

st.set_page_config(page_title="Alasar Quality Engine V31.0", layout="wide")

if 'genel_giris' not in st.session_state: st.session_state.genel_giris = False
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None
if 'onay_bekleyenler' not in st.session_state: st.session_state.onay_bekleyenler = []

# --- GİRİŞ VE ROL SEÇİMİ ---
if not st.session_state.genel_giris:
    st.markdown("<h1 style='text-align:center;'>🛡️ ALASAR GRUP KALİTE PORTALI</h1>", unsafe_allow_html=True)
    with st.form("portal_giris"):
        u = st.text_input("Kullanıcı Adı"); p = st.text_input("Sistem Şifresi", type="password")
        if st.form_submit_button("Giriş Yap"):
            if u == "alasar" and p == "30052012": st.session_state.genel_giris = True; st.rerun()
            else: st.error("Hatalı Giriş!")
    st.stop()

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

# --- PANEL 1: ÜRETİM OPERATÖR ---
if u_role == "Üretim-Operatör":
    st.header(f"🏭 {u_sirket} - Üretim Giriş Terminali")
    
    with st.form("operatör_form_v31"):
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No (LOT)", "LOT-")
        sevk = c2.number_input("Toplam Sevk Edilecek", 1, value=5000)
        hata_ana = c3.selectbox("Baskın Hata Türü", ["Hata Yok", "Çapak", "Eksik Baskı", "Ölçü Sapması", "Yüzey Hatası", "Hammadde Kaynaklı"])
        
        c4, c5 = st.columns(2)
        op_isim = c4.text_input("Operatör Ad Soyad")
        vardiya = c5.selectbox("Vardiya No", list(range(1, 4)))
        
        st.divider()
        st.write("🔍 **Hata Dağılımı ve Şiddet Puanlama**")
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik) Adet", 0); p1p = h1.number_input("P1 Şiddet", value=3.0)
        k3 = h2.number_input("P2 (Majör) Adet", 0); p2p = h2.number_input("P2 Şiddet", value=2.0)
        l3 = h3.number_input("P3 (Minör) Adet", 0); p3p = h3.number_input("P3 Şiddet", value=1.0)
        m3 = h4.number_input("P4 (Görsel) Adet", 0); p4p = h4.number_input("P4 Şiddet", value=0.5)
        
        st.divider()
        st.write("📸 **Ürün Kanıt Fotoğrafları (Opsiyonel)**")
        f_col1, f_col2 = st.columns(2)
        f1 = f_col1.file_uploader("Genel Görünüm", type=['jpg', 'png'])
        f2 = f_col2.file_uploader("Hata Detayı", type=['jpg', 'png'])
        
        op_not = st.text_area("Operatör Notu / Teknik Açıklama")
        
        analiz_et = st.form_submit_button("SİSTEM ANALİZİNİ ÇALIŞTIR")

    if analiz_et:
        karar, ikon, skor, renk = kalite_motoru_hesapla(100, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
        st.session_state.gecici_analiz = {
            "Şirket": u_sirket, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Parti No": lot, "Sevk": sevk, "Baskın Hata": hata_ana, "TRI": round(skor, 4),
            "Sistem": karar, "Renk": renk, "P1_A": j3, "P2_A": k3, "P3_A": l3, "P4_A": m3,
            "Operatör": op_isim, "Vardiya": vardiya, "Not": op_not
        }

    if 'gecici_analiz' in st.session_state:
        g = st.session_state.gecici_analiz
        st.markdown(f"""
            <div style="background-color:{g['Renk']}; padding:30px; border-radius:15px; text-align:center; border: 5px solid white;">
                <h1 style="color:white; margin:0;">ANALİZ SONUCU: {g['Sistem']}</h1>
                <h3 style="color:white; opacity:0.9;">Risk Skoru (TRI): {g['TRI']}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        st.warning("⚠️ **DİKKAT:** Kayıt henüz veritabanına işlenmedi. Lütfen aşağıdan onaylayın.")
        col_onay1, col_onay2 = st.columns(2)
        
        if col_onay1.button("✅ KAYDI ONAYLIYORUM VE GÖNDERİYORUM", use_container_width=True):
            g.update({"Yönetici Aksiyonu": "BEKLİYOR" if g['Sistem'] != "UYGUN" else "OTOMATİK ONAY"})
            if g['Sistem'] == "UYGUN":
                veriyi_excele_kaydet(pd.DataFrame([g]), DB_FILE)
            else:
                st.session_state.onay_bekleyenler.append(g.copy())
            
            st.markdown("<h1 style='color:#28A745; text-align:center; border:3px solid #28A745; padding:10px;'>KAYIT BAŞARI İLE İLETİLDİ</h1>", unsafe_allow_html=True)
            del st.session_state.gecici_analiz
            time.sleep(2); st.rerun()
            
        if col_onay2.button("❌ İŞLEMİ İPTAL ET / YENİDEN GİRİŞ", use_container_width=True):
            del st.session_state.gecici_analiz
            st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ ---
elif u_role == "Kalite Müdürü":
    t1, t2, t3 = st.tabs(["📊 Veri Arşivi", "🛠️ DİNAMİK 8D MODÜLÜ", "⚖️ Karar Havuzu"])
    with t1: st.dataframe(ana_db[ana_db['Şirket'] == u_sirket].iloc[::-1] if not ana_db.empty else pd.DataFrame())
    with t2:
        st.header("🏁 8D / DÖF Yönetimi")
        islem = st.radio("İşlem:", ["Yeni Kayıt", "Güncelle"], horizontal=True)
        s_8d = sikayet_db[sikayet_db['Şirket'] == u_sirket] if not sikayet_db.empty else pd.DataFrame()
        if islem == "Güncelle" and not s_8d.empty:
            sec = st.selectbox("Seç:", s_8d['DOF_No'].tolist()); v = s_8d[s_8d['DOF_No'] == sec].iloc[0]
        else: sec = otomatik_dof_no_uret(sikayet_db); v = None
        with st.form("8d_form"):
            m = st.text_input("Müşteri", value=v['Müşteri'] if v is not None else "")
            tan = st.text_area("Hata Tanımı", value=v['Tanım'] if v is not None else "")
            dur = st.selectbox("Durum", ["Başlatıldı", "Kapatıldı"], index=0 if v is None else ["Başlatıldı", "Kapatıldı"].index(v['Durum']))
            if st.form_submit_button("KAYDET"):
                veriyi_excele_kaydet(pd.DataFrame([{"Şirket": u_sirket, "DOF_No": sec, "Müşteri": m, "Tarih": datetime.now(), "Tanım": tan, "Durum": dur}]), SIKAYET_FILE)
                st.success("Güncellendi"); time.sleep(1); st.rerun()
    with t3:
        bekleyenler = [b for b in st.session_state.onay_bekleyenler if b['Şirket'] == u_sirket and not b.get("Patrona_Gitti")]
        for i, b in enumerate(bekleyenler):
            with st.expander(f"Kayıt: {b['Parti No']}"):
                aks = st.selectbox("Karar", ["Kabul", "ÜST YÖNETİCİYE SEVK"], key=f"km_{i}")
                if st.button("UYGULA", key=f"kb_{i}"):
                    if "ÜST" in aks:
                        for idx, item in enumerate(st.session_state.onay_bekleyenler):
                            if item['Parti No'] == b['Parti No']: st.session_state.onay_bekleyenler[idx]["Patrona_Gitti"] = True
                    else:
                        b.update({"Yönetici Aksiyonu": aks})
                        veriyi_excele_kaydet(pd.DataFrame([b]), DB_FILE)
                        st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['Parti No'] != b['Parti No']]
                    st.rerun()

# --- PANEL 3: PATRON ---
elif u_role == "Genel Müdür":
    s_sec = st.radio("Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"], horizontal=True)
    p_onay = [x for x in st.session_state.onay_bekleyenler if x.get("Patrona_Gitti") and x['Şirket'] == s_sec]
    for i, p in enumerate(p_onay):
        st.error(f"Kritik: {p['Parti No']} | TRI: {p['TRI']}")
        if st.button("MÜHÜRLE", key=f"pb_{i}"):
            p.update({"Yönetici Aksiyonu": "PATRON ONAYLI", "Onay_Tarihi": datetime.now()})
            veriyi_excele_kaydet(pd.DataFrame([p]), DB_FILE)
            st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['Parti No'] != p['Parti No']]
            st.rerun()

# --- YEDEKLEME ---
if not ana_db.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        ana_db.to_excel(writer, index=False, sheet_name='Uretim')
    st.sidebar.download_button("📥 Excel Yedek Al", output.getvalue(), "Alasar_Yedek.xlsx")
