import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io 
import time
import os

# --- EXCEL VERİTABANI AYARI ---
DB_FILE = "alasar_kalite_veritabani.xlsx"

def veriyi_excele_kaydet(yeni_df):
    """Veriyi kalıcı olarak Excel dosyasına ekler veya oluşturur."""
    if not os.path.exists(DB_FILE):
        yeni_df.to_excel(DB_FILE, index=False)
    else:
        mevcut_df = pd.read_excel(DB_FILE)
        guncel_df = pd.concat([mevcut_df, yeni_df], ignore_index=True)
        guncel_df.to_excel(DB_FILE, index=False)

def veriyi_excelden_yukle():
    """Uygulama başında Excel'deki verileri session_state'e çeker."""
    if os.path.exists(DB_FILE):
        return pd.read_excel(DB_FILE)
    return pd.DataFrame()

# --- 1. GÜVENLİK VE ROL VERİTABANI ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "alasar": {"pass": "30052012", "role": "Kalite Müdürü", "full_name": "Ömer Ocak"},
        "genelmudur": {"pass": "patron456", "role": "Genel Müdür", "full_name": "Genel Müdürlük"},
        "operator": {"pass": "op789", "role": "Üretim-Operatör", "full_name": "Kalite Operatörü"}
    }

GENERAL_USER = "alasar"
GENERAL_PASS = "30052012"

# --- 2. VERİTABANI BAŞLATMA ---
if 'ana_veritabani' not in st.session_state:
    st.session_state.ana_veritabani = veriyi_excelden_yukle()
if 'onay_bekleyenler' not in st.session_state:
    st.session_state.onay_bekleyenler = [] 

# --- 3. KALİTE MOTORU ---
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

# --- 4. OTURUM AYARLARI ---
st.set_page_config(page_title="Alasar Quality Engine V16.5", layout="wide")

if 'genel_giris' not in st.session_state: st.session_state.genel_giris = False
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None

if not st.session_state.genel_giris:
    st.markdown("<h2 style='text-align:center;'>ALASAR SİSTEM GİRİŞİ</h2>", unsafe_allow_html=True)
    with st.form("genel_login"):
        u = st.text_input("Kullanıcı Adı").strip()
        p = st.text_input("Şifre", type="password").strip()
        if st.form_submit_button("Sisteme Gir"):
            if u == GENERAL_USER and p == GENERAL_PASS:
                st.session_state.genel_giris = True
                st.rerun()
            else: st.error("Hatalı giriş!")
    st.stop()

if st.session_state.aktif_user is None:
    st.subheader("Lütfen Yetki Alanınızı Seçiniz")
    secim = st.selectbox("Panel:", ["Seçiniz...", "Üretim-Operatör", "Kalite Müdürü", "Genel Müdür"])
    if secim != "Seçiniz...":
        u_key = "operator" if secim == "Üretim-Operatör" else ("alasar" if secim == "Kalite Müdürü" else "genelmudur")
        ps = st.text_input(f"{secim} Özel Şifresi", type="password")
        if st.button("Paneli Aç"):
            if ps == st.session_state.user_db[u_key]["pass"]:
                st.session_state.aktif_user = u_key
                st.rerun()
            else: st.error("Yetkisiz Şifre!")
    st.stop()

# --- ANALİTİK PANEL FONKSİYONU ---
def analitik_panel_goster(df, baslik):
    st.subheader(baslik)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Parti", len(df))
    m2.metric("Ortalama TRI", round(df['TRI'].mean(), 2) if not df.empty else 0)
    uyg_orani = (len(df[df['Yönetici Aksiyonu'].str.contains("Kabul|OTOMATİK", na=False)]) / len(df) * 100) if not df.empty else 0
    m3.metric("Uygunluk Oranı", f"%{round(uyg_orani, 1)}")
    m4.metric("Toplam P1 Hatası", int(df['P1_A'].sum()) if not df.empty else 0)
    
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Karar Dağılımı")
        st.bar_chart(df['Yönetici Aksiyonu'].value_counts())
    with g2:
        st.subheader("Risk Dağılımı")
        st.pie_chart(df['Sistem'].value_counts()) if hasattr(st, "pie_chart") else st.write(df['Sistem'].value_counts())

u_data = st.session_state.user_db[st.session_state.aktif_user]
st.sidebar.title(f"📍 {u_data['role']}")
st.sidebar.write(f"Hoş Geldiniz: {u_data['full_name']}")

if st.sidebar.button("Oturumu Kapat / Geri Dön"):
    st.session_state.aktif_user = None
    st.rerun()

# --- PANEL 1: ÜRETİM-OPERATÖR ---
if u_data['role'] == "Üretim-Operatör":
    st.header("🏭 Üretim Hattı Giriş Terminali")
    
    placeholder = st.empty() # Başarı mesajı için dinamik yer tutucu

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
        karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
        st.session_state.gecici_analiz = {
            "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Operatör": u_data['full_name'], "Parti No": lot,
            "Sevk": sevk, "Kontrol": kontrol, "TRI": round(skor, 4), "Sistem": karar, "Renk": renk, "Not": op_not,
            "P1_A": j3, "P2_A": k3, "P3_A": l3, "P4_A": m3, "P1_P": p1p, "P2_P": p2p, "P3_P": p3p, "P4_P": p4p
        }

    if 'gecici_analiz' in st.session_state:
        data = st.session_state.gecici_analiz
        st.markdown(f"<div style='background-color:{data['Renk']}; padding:25px; border-radius:15px; text-align:center; margin-top:15px; border: 2px solid white;'><h1 style='color:white; font-size: 40px;'>ÖN ANALİZ: {data['Sistem']} (TRI: {data['TRI']})</h1></div>", unsafe_allow_html=True)
        
        st.subheader("🛡️ Gönderim Onayı ve Kanıtlar")
        col_onay1, col_onay2 = st.columns([2, 1])
        
        with col_onay1:
            if data['Sistem'] != "UYGUN":
                st.warning("⚠️ Kritik risk tespit edildi. Lütfen 3 adet fotoğraf yükleyiniz.")
                f1 = st.file_uploader("Genel Görünüm", type=['jpg', 'png'], key="f1")
                f2 = st.file_uploader("Hata Detayı", type=['jpg', 'png'], key="f2")
                f3 = st.file_uploader("Etiket", type=['jpg', 'png'], key="f3")
            else:
                st.info("Parti uygun görünüyor. Fotoğraf yüklemek opsiyoneldir.")
                f1 = f2 = f3 = None
            onay_box = st.checkbox("Girdiğim verilerin doğruluğunu onaylıyorum. (UYGUNDUR)", key="final_check")
        
        with col_onay2:
            st.write("### İşlem Seçiniz")
            btn_gonder = st.button("🚀 KAYDI YÖNETİCİYE GÖNDER", use_container_width=True)
            if btn_gonder:
                if not onay_box:
                    st.error("Lütfen 'Uygundur Onaylıyorum' kutucuğunu işaretleyin!")
                elif data['Sistem'] != "UYGUN" and (not f1 or not f2 or not f3):
                    st.error("RED veya SARI kararlarda 3 fotoğraf yüklemek zorunludur!")
                else:
                    # Kayıt İşlemi
                    if f1: data.update({"Foto_1": "VAR", "Foto_2": "VAR", "Foto_3": "VAR"}) # Excel'e fotoğraf binary gömülmez (Hız için)
                    data.update({"Yönetici Aksiyonu": "BEKLİYOR" if data['Sistem'] != "UYGUN" else "OTOMATİK ONAY"})
                    
                    if data['Sistem'] == "UYGUN":
                        veriyi_excele_kaydet(pd.DataFrame([data]))
                        st.session_state.ana_veritabani = veriyi_excelden_yukle()
                    else:
                        st.session_state.onay_bekleyenler.append(data.copy())
                    
                    # EKRANA DEV BAŞARI MESAJINI BAS
                    del st.session_state.gecici_analiz
                    placeholder.markdown("""
                        <div style="background-color:#28A745; border: 5px solid #1e7e34; padding:60px; border-radius:25px; text-align:center; margin-bottom:30px; box-shadow: 0px 10px 20px rgba(0,0,0,0.2); position:relative; z-index:999;">
                            <h1 style="color:white; font-size: 55px; font-weight: bold;">✅ KAYDINIZ BAŞARIYLA GÖNDERİLMİŞTİR.</h1>
                            <h2 style="color:#f8f9fa; font-size: 30px;">Veritabanına işlendi. Sistem 6 saniye içinde sıfırlanacaktır...</h2>
                        </div>
                    """, unsafe_allow_html=True)
                    time.sleep(6)
                    st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ ---
elif u_data['role'] == "Kalite Müdürü":
    if not st.session_state.ana_veritabani.empty:
        analitik_panel_goster(st.session_state.ana_veritabani, "📊 Güncel Kalite Performansı (Özet)")
        st.divider()

    st.header("⚖️ Onay Bekleyen Kritik Kayıtlar")
    if not st.session_state.onay_bekleyenler: st.info("Şu an bekleyen bir kayıt yok.")
    
    for i, bekleyen in enumerate(st.session_state.onay_bekleyenler):
        with st.expander(f"📌 {bekleyen['Parti No']} | TRI: {bekleyen['TRI']} | Operatör: {bekleyen['Operatör']}"):
            detay_data = {
                "Hata Sınıfı": ["P1 (Kritik)", "P2 (Majör)", "P3 (Minör)", "P4 (Görsel)"],
                "Hata Adedi": [bekleyen['P1_A'], bekleyen['P2_A'], bekleyen['P3_A'], bekleyen['P4_A']],
                "Risk Puanı (Ağırlık)": [bekleyen['P1_P'], bekleyen['P2_P'], bekleyen['P3_P'], bekleyen['P4_P']]
            }
            st.table(pd.DataFrame(detay_data))
            st.divider()
            c_a1, c_a2 = st.columns(2)
            aks = c_a1.selectbox("Nihai Aksiyon", ["Olduğu Gibi Kabul (Sapma) ✅", "%100 Ayıklama 🔍", "İade 🚛", "Karantina 🔒"], key=f"aks_m_{i}")
            y_not = c_a2.text_input("Yönetici Notu", key=f"not_m_{i}")
            if st.button("KARARI ONAYLA VE EXCEL'E YAZ", key=f"save_m_{i}"):
                bekleyen.update({"Yönetici Aksiyonu": aks, "Yönetici Notu": y_not})
                save_data = {k: v for k, v in bekleyen.items() if not k.startswith("Foto_")}
                veriyi_excele_kaydet(pd.DataFrame([save_data]))
                st.session_state.ana_veritabani = veriyi_excelden_yukle()
                st.session_state.onay_bekleyenler.pop(i)
                st.success("Kalıcı olarak Excel'e kaydedildi."); time.sleep(1); st.rerun()

    st.divider()
    st.subheader("📜 Excel Veritabanı Arşiv Listesi")
    st.dataframe(st.session_state.ana_veritabani.iloc[::-1], use_container_width=True)

# --- PANEL 3: GENEL MÜDÜR ---
elif u_data['role'] == "Genel Müdür":
    st.header("📈 Kalite Stratejik Analitik Paneli")
    if not st.session_state.ana_veritabani.empty:
        analitik_panel_goster(st.session_state.ana_veritabani, "Fabrika Genel Durum")
        st.divider()
        st.subheader("📊 Performans Arşivi (Excel'den Gelen)")
        st.dataframe(st.session_state.ana_veritabani.iloc[::-1], use_container_width=True)
    else:
        st.info("Henüz analiz edilmiş veri bulunmuyor.")
