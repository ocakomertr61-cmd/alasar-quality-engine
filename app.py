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
    # Hassas TRI Hesaplama (Ömer Bey'in istediği katsayılar)
    temel_oran = ((P3_p * 2.5) + (Q3_p * 1.5) + (R3_p * 0.7) + (S3_p * 0.3)) / 5
    t3_skor = max(temel_oran * (1 + (J3*0.05 + K3*0.02)), toplam_hata / 15) if toplam_hata > 0 else 0.0
    
    red_mi = (hata_orani > 0.08 or J3 >= 1 or t3_skor >= 4.0)
    sartli_mi = False if red_mi else (t3_skor > 1.5 or (J3 + K3) >= 5)
    
    if red_mi: return "RED", "🔴", t3_skor, "#FF4B4B" 
    elif sartli_mi: return "SARI", "🟡", t3_skor, "#FFD700" 
    else: return "UYGUN", "🟢", t3_skor, "#28A745" 

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Alasar Group Quality Engine V32.0", layout="wide")

if 'genel_giris' not in st.session_state: st.session_state.genel_giris = False
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None
if 'onay_bekleyenler' not in st.session_state: st.session_state.onay_bekleyenler = []

# --- 1. PORTAL GİRİŞİ ---
if not st.session_state.genel_giris:
    st.markdown("<h1 style='text-align:center;'>🛡️ ALASAR GRUP KALİTE PORTALI</h1>", unsafe_allow_html=True)
    with st.form("portal_giris"):
        u = st.text_input("Kullanıcı Adı"); p = st.text_input("Sistem Şifresi", type="password")
        if st.form_submit_button("Sisteme Giriş Yap"):
            if u == "alasar" and p == "30052012": st.session_state.genel_giris = True; st.rerun()
            else: st.error("Hatalı Giriş Bilgileri!")
    st.stop()

# --- 2. ROL VE ŞİRKET SEÇİMİ ---
if st.session_state.aktif_user is None:
    st.subheader("Bölüm Doğrulaması")
    col_a, col_b = st.columns(2)
    s_sec = col_a.selectbox("İşlem Yapılacak Şirket:", ["Alasar Grup", "Hakan Kalıp Plastik"])
    r_sec = col_b.selectbox("Yetki Paneli:", ["Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
    ozel_p = st.text_input("Panel Erişim Şifresi", type="password")
    if st.button("Seçili Paneli Başlat"):
        if (r_sec == "Kalite Müdürü" and ozel_p == "30052012") or \
           (r_sec == "Üretim-Operatör" and ozel_p == "op789") or \
           (r_sec == "Genel Müdür" and ozel_p == "patron456"):
            st.session_state.aktif_user = {"role": r_sec, "sirket": s_sec}; st.rerun()
        else: st.error("Bu panel için şifreniz hatalı!")
    st.stop()

u_role = st.session_state.aktif_user['role']
u_sirket = st.session_state.aktif_user['sirket']
ana_db = veriyi_excelden_yukle(DB_FILE)
sikayet_db = veriyi_excelden_yukle(SIKAYET_FILE)

# --- PANEL 1: ÜRETİM OPERATÖR (FULL + FOTO + ONAY) ---
if u_role == "Üretim-Operatör":
    st.header(f"🏭 {u_sirket} - Üretim Giriş Terminali")
    
    with st.form("operatör_form_final"):
        col_m1, col_m2, col_m3 = st.columns(3)
        lot = col_m1.text_input("Parti No (LOT)", "LOT-")
        sevk = col_m2.number_input("Toplam Sevk Edilecek", 1, value=5000)
        hata_ana = col_m3.selectbox("Baskın Hata Türü", ["Hata Yok", "Çapak", "Eksik Baskı", "Ölçü Sapması", "Yüzey Hatası", "Hammadde"])
        
        col_m4, col_m5, col_m6 = st.columns(3)
        op_isim = col_m4.text_input("Operatör Ad Soyad")
        vardiya = col_m5.selectbox("Vardiya No", list(range(1, 4)))
        kontrol_adet = col_m6.number_input("Kontrol Edilen Örnek Adet", 1, value=100)
        
        st.divider()
        st.write("🔍 **Hata Dağılımı ve Şiddet Puanlama**")
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik)", 0); p1p = h1.number_input("P1 Şiddet", value=3.0)
        k3 = h2.number_input("P2 (Majör)", 0); p2p = h2.number_input("P2 Şiddet", value=2.0)
        l3 = h3.number_input("P3 (Minör)", 0); p3p = h3.number_input("P3 Şiddet", value=1.0)
        m3 = h4.number_input("P4 (Görsel)", 0); p4p = h4.number_input("P4 Şiddet", value=0.5)
        
        st.divider()
        st.write("📸 **Üretim Kanıt Fotoğrafları**")
        f_col1, f_col2, f_col3 = st.columns(3)
        f1 = f_col1.file_uploader("Genel Görünüm", type=['jpg', 'png'])
        f2 = f_col2.file_uploader("Hata Detayı", type=['jpg', 'png'])
        f3 = f_col3.file_uploader("Etiket", type=['jpg', 'png'])
        
        op_not = st.text_area("Ek Notlar / Teknik Açıklamalar")
        
        submit_analiz = st.form_submit_button("VERİLERİ ANALİZ ET")

    if submit_analiz:
        karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol_adet, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
        st.session_state.gecici_analiz = {
            "Şirket": u_sirket, "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Parti No": lot, "Sevk": sevk, "Baskın Hata": hata_ana, "TRI": round(skor, 4),
            "Sistem": karar, "Renk": renk, "P1_A": j3, "P2_A": k3, "P3_A": l3, "P4_A": m3,
            "Operatör": op_isim, "Vardiya": vardiya, "Not": op_not, "Kontrol_Adet": kontrol_adet
        }

    if 'gecici_analiz' in st.session_state:
        g = st.session_state.gecici_analiz
        st.markdown(f"""
            <div style="background-color:{g['Renk']}; padding:30px; border-radius:15px; text-align:center; border: 4px solid #ffffff;">
                <h1 style="color:white; margin:0;">SİSTEM KARARI: {g['Sistem']}</h1>
                <h2 style="color:white; opacity:0.9;">Risk Skoru (TRI): {g['TRI']}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.warning("⚠️ **DİKKAT:** Bu veri henüz kaydedilmedi. Onaylıyor musunuz?")
        c_onay1, c_onay2 = st.columns(2)
        
        if c_onay1.button("✅ EVET, ONAYLIYORUM VE GÖNDER", use_container_width=True):
            g.update({"Yönetici Aksiyonu": "BEKLİYOR" if g['Sistem'] != "UYGUN" else "OTOMATİK ONAY"})
            if g['Sistem'] == "UYGUN":
                veriyi_excele_kaydet(pd.DataFrame([g]), DB_FILE)
            else:
                st.session_state.onay_bekleyenler.append(g.copy())
            
            st.markdown("<h1 style='color:#28A745; text-align:center; font-size:48px;'>✅ KAYIT BAŞARI İLE İLETİLDİ</h1>", unsafe_allow_html=True)
            del st.session_state.gecici_analiz
            time.sleep(2); st.rerun()
            
        if c_onay2.button("❌ HAYIR, İPTAL ET / DÜZELT", use_container_width=True):
            del st.session_state.gecici_analiz
            st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ (TAM DETAYLI) ---
elif u_role == "Kalite Müdürü":
    t1, t2, t3 = st.tabs(["📊 Veri Arşivi", "🛠️ DİNAMİK 8D/DÖF SİSTEMİ", "⚖️ Karar Havuzu"])
    
    with t1:
        st.subheader(f"Arşiv: {u_sirket}")
        st.dataframe(ana_db[ana_db['Şirket'] == u_sirket].iloc[::-1] if not ana_db.empty else pd.DataFrame())

    with t2:
        st.header("🏁 8D Yönetim Merkezi")
        islem = st.radio("Seçim:", ["Yeni Kayıt", "Güncelleme"], horizontal=True)
        s_8d = sikayet_db[sikayet_db['Şirket'] == u_sirket] if not sikayet_db.empty else pd.DataFrame()
        if islem == "Güncelleme" and not s_8d.empty:
            sec_no = st.selectbox("8D No:", s_8d['DOF_No'].tolist()); v = s_8d[s_8d['DOF_No'] == sec_no].iloc[0]
        else: sec_no = otomatik_dof_no_uret(sikayet_db); v = None
        
        with st.form("8d_manager"):
            mus = st.text_input("Müşteri", value=v['Müşteri'] if v is not None else "")
            tan = st.text_area("Hata Tanımı", value=v['Tanım'] if v is not None else "")
            kok = st.text_area("Kök Neden", value=v['Kok_Neden'] if v is not None else "")
            f_k = st.text_area("Kalıcı Önlem", value=v.get('K_Faaliyet', '') if v is not None else "")
            dur = st.selectbox("Durum", ["Başlatıldı", "Kapatıldı"], index=0 if v is None else ["Başlatıldı", "Kapatıldı"].index(v['Durum']))
            if st.form_submit_button("KAYDI MÜHÜRLE"):
                y_df = pd.DataFrame([{"Şirket": u_sirket, "DOF_No": sec_no, "Müşteri": mus, "Tarih": datetime.now().strftime("%Y-%m-%d"), "Tanım": tan, "Kok_Neden": kok, "K_Faaliyet": f_k, "Durum": dur}])
                veriyi_excele_kaydet(y_df, SIKAYET_FILE)
                st.success("İşlem Başarılı"); time.sleep(1); st.rerun()

    with t3:
        st.subheader("Onay Bekleyen Sevkiyatlar")
        bekleyen = [b for b in st.session_state.onay_bekleyenler if b['Şirket'] == u_sirket and not b.get("Patrona_Gitti")]
        if not bekleyen: st.info("Bekleyen kayıt bulunmuyor.")
        for i, b in enumerate(bekleyen):
            with st.expander(f"📌 {b['Parti No']} | TRI: {b['TRI']}"):
                st.table(pd.DataFrame({"Hata": ["P1","P2","P3","P4"], "Adet": [b['P1_A'], b['P2_A'], b['P3_A'], b['P4_A']]}))
                aks = st.selectbox("Karar", ["Kabul", "Şartlı Kabul", "ÜST YÖNETİCİYE GÖNDER"], key=f"km_{i}")
                n = st.text_input("Karar Notu", key=f"n_{i}")
                if st.button("UYGULA", key=f"kb_{i}"):
                    if "ÜST" in aks:
                        for idx, item in enumerate(st.session_state.onay_bekleyenler):
                            if item['Parti No'] == b['Parti No']: st.session_state.onay_bekleyenler[idx]["Patrona_Gitti"] = True; st.session_state.onay_bekleyenler[idx]["Mudur_Notu"] = n
                    else:
                        b.update({"Yönetici Aksiyonu": aks, "Mudur_Notu": n})
                        veriyi_excele_kaydet(pd.DataFrame([b]), DB_FILE)
                        st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['Parti No'] != b['Parti No']]
                    st.rerun()

# --- PANEL 3: GENEL MÜDÜR (PATRON) ---
elif u_role == "Genel Müdür":
    s_sec = st.radio("Şirket Seçin:", ["Alasar Grup", "Hakan Kalıp Plastik"], horizontal=True)
    p_onay = [x for x in st.session_state.onay_bekleyenler if x.get("Patrona_Gitti") and x['Şirket'] == s_sec]
    
    if p_onay: st.error(f"🚨 DİKKAT: Onayınızı bekleyen {len(p_onay)} kritik sevk var!")
    for i, p in enumerate(p_onay):
        st.markdown(f"### {p['Parti No']} | TRI: {p['TRI']}")
        st.info(f"Müdür Notu: {p.get('Mudur_Notu')}")
        p_aks = st.radio("Karar", ["SEVK ET", "SEVKİ DURDUR"], key=f"pa_{i}")
        if st.button("MÜHÜRLE", key=f"pb_{i}"):
            p.update({"Yönetici Aksiyonu": f"PATRON: {p_aks}", "Onay_Tarihi": datetime.now()})
            veriyi_excele_kaydet(pd.DataFrame([p]), DB_FILE)
            st.session_state.onay_bekleyenler = [x for x in st.session_state.onay_bekleyenler if x['Parti No'] != p['Parti No']]
            st.rerun()

# --- YEDEKLEME VE ÇIKIŞ ---
st.sidebar.divider()
if not ana_db.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        ana_db.to_excel(writer, index=False, sheet_name='Veri')
    st.sidebar.download_button("📥 Excel Yedek Al", output.getvalue(), "Alasar_Sistem_Yedek.xlsx")

if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.aktif_user = None
    st.rerun()
