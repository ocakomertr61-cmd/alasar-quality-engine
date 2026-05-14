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
    try:
        if not os.path.exists(DB_FILE):
            yeni_df.to_excel(DB_FILE, index=False, engine='openpyxl')
        else:
            mevcut_df = pd.read_excel(DB_FILE, engine='openpyxl')
            guncel_df = pd.concat([mevcut_df, yeni_df], ignore_index=True)
            guncel_df.to_excel(DB_FILE, index=False, engine='openpyxl')
    except Exception as e:
        st.error(f"Excel kayıt hatası: {e}")

def veriyi_excelden_yukle():
    if os.path.exists(DB_FILE):
        return pd.read_excel(DB_FILE, engine='openpyxl')
    return pd.DataFrame()

# --- 1. GÜVENLİK VE ROL VERİTABANI ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "alasar": {"pass": "30052012", "role": "Kalite Müdürü", "full_name": "Ömer Ocak"},
        "genelmudur": {"pass": "patron456", "role": "Genel Müdür", "full_name": "Genel Müdürlük"},
        "operator": {"pass": "op789", "role": "Üretim-Operatör", "full_name": "Kalite Operatörü"}
    }

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
st.set_page_config(page_title="Alasar Quality Engine V16.7", layout="wide")

if 'genel_giris' not in st.session_state: st.session_state.genel_giris = False
if 'aktif_user' not in st.session_state: st.session_state.aktif_user = None

if not st.session_state.genel_giris:
    st.markdown("<h2 style='text-align:center;'>ALASAR SİSTEM GİRİŞİ</h2>", unsafe_allow_html=True)
    with st.form("genel_login"):
        u = st.text_input("Kullanıcı Adı").strip()
        p = st.text_input("Şifre", type="password").strip()
        if st.form_submit_button("Sisteme Gir"):
            if u == "alasar" and p == "30052012":
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

u_data = st.session_state.user_db[st.session_state.aktif_user]
st.sidebar.title(f"📍 {u_data['role']}")
st.sidebar.write(f"Kullanıcı: {u_data['full_name']}")

if st.sidebar.button("Oturumu Kapat / Geri Dön"):
    st.session_state.aktif_user = None
    st.rerun()

# --- PANEL 1: ÜRETİM-OPERATÖR ---
if u_data['role'] == "Üretim-Operatör":
    st.header("🏭 Üretim Hattı Giriş Terminali")
    placeholder = st.empty()

    with st.form("veri_giris_formu"):
        c1, c2, v_col = st.columns(3)
        lot = c1.text_input("Parti No", "LOT-")
        sevk = c2.number_input("Toplam Sevk Adeti", 1, value=1000)
        vardiya = v_col.selectbox("Vardiya No", list(range(60, 81)))
        
        c3, c4 = st.columns(2)
        kontrol = c3.number_input("Kontrol Edilen Adet", 1, value=100)
        op_ad_soyad = c4.text_input("Operatör Ad Soyad (Hatta Görevli)")
        
        st.divider()
        st.subheader("Hata Adetleri ve Risk Puanları")
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 (Kritik)", 0); p1p = h1.number_input("P1 Puan", 1.0, value=1.0)
        k3 = h2.number_input("P2 (Majör)", 0); p2p = h2.number_input("P2 Puan", 1.0, value=1.0)
        l3 = h3.number_input("P3 (Minör)", 0); p3p = h3.number_input("P3 Puan", 1.0, value=1.0)
        m3 = h4.number_input("P4 (Görsel)", 0); p4p = h4.number_input("P4 Puan", 1.0, value=1.0)
        op_not = st.text_area("Operatör Gözlem Notları")
        submit = st.form_submit_button("SİSTEM ANALİZİNİ BAŞLAT")

    if submit:
        karar, ikon, skor, renk = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
        st.session_state.gecici_analiz = {
            "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Vardiya": vardiya, "Hattaki Operatör": op_ad_soyad,
            "Sistem Operatörü": u_data['full_name'], "Parti No": lot, "Sevk": sevk, "Kontrol": kontrol, 
            "TRI": round(skor, 4), "Sistem": karar, "Renk": renk, "Not": op_not,
            "P1_A": j3, "P2_A": k3, "P3_A": l3, "P4_A": m3, "P1_P": p1p, "P2_P": p2p, "P3_P": p3p, "P4_P": p4p
        }

    if 'gecici_analiz' in st.session_state:
        data = st.session_state.gecici_analiz
        st.markdown(f"<div style='background-color:{data['Renk']}; padding:20px; border-radius:10px; text-align:center;'><h2 style='color:white;'>ÖN ANALİZ: {data['Sistem']} (TRI: {data['TRI']})</h2></div>", unsafe_allow_html=True)
        
        f1 = st.file_uploader("Genel Görünüm", type=['jpg', 'png'])
        f2 = st.file_uploader("Hata Detayı", type=['jpg', 'png'])
        f3 = st.file_uploader("Etiket", type=['jpg', 'png'])
        
        foto_yok = (f1 is None and f2 is None and f3 is None)
        if foto_yok:
            st.warning("⚠️ Kanıt dosyası (fotoğraf) yüklemediniz.")
            kanit_onay = st.checkbox("Kanıtlarınız sunulmadan iletmek istiyor musunuz?")
        else:
            kanit_onay = True

        if st.button("🚀 KAYDI GÖNDER"):
            if not kanit_onay:
                st.error("Lütfen fotoğraf yükleyin veya kanıtsız gönderim onayını işaretleyin!")
            else:
                data.update({"Yönetici Aksiyonu": "BEKLİYOR" if data['Sistem'] != "UYGUN" else "OTOMATİK ONAY"})
                if data['Sistem'] == "UYGUN":
                    veriyi_excele_kaydet(pd.DataFrame([data]))
                    st.session_state.ana_veritabani = veriyi_excelden_yukle()
                else:
                    st.session_state.onay_bekleyenler.append(data.copy())
                
                del st.session_state.gecici_analiz
                placeholder.success("✅ Kayıt başarıyla iletildi. Sistem sıfırlanıyor...")
                time.sleep(3); st.rerun()

# --- PANEL 2: KALİTE MÜDÜRÜ ---
elif u_data['role'] == "Kalite Müdürü":
    st.header("⚖️ Karar Bekleyen Kayıtlar")
    bekleyenler = st.session_state.onay_bekleyenler
    
    # Sevk edilmemişleri filtrele
    aktif_bekleyenler = [b for b in bekleyenler if not b.get("Üst Yöneticiye Sevk", False)]
    
    if not aktif_bekleyenler:
        st.info("Onay bekleyen kayıt bulunmuyor.")

    for i, bekleyen in enumerate(aktif_bekleyenler):
        with st.expander(f"📌 {bekleyen['Parti No']} | TRI: {bekleyen['TRI']} | Vardiya: {bekleyen['Vardiya']}"):
            st.write(f"**Operatör:** {bekleyen['Hattaki Operatör']} | **Sistem Kararı:** {bekleyen['Sistem']}")
            st.table(pd.DataFrame({"Hata": ["P1","P2","P3","P4"], "Adet": [bekleyen['P1_A'], bekleyen['P2_A'], bekleyen['P3_A'], bekleyen['P4_A']]}))
            
            aks = st.selectbox("Nihai Karar", [
                "Olduğu Gibi Kabul", 
                "%100 Ayıklama Sonrası Şartlı Kabul", 
                "Karantinaya Alınız ve Bekletiniz", 
                "Üst Yöneticiye Sevk (Patron Onayı)", 
                "Müşteriye İade Edelim", 
                "Tedarikçiye İade Edelim"
            ], key=f"aks_{i}")
            
            y_not = st.text_input("Yönetici Notu", key=f"not_{i}")
            
            if st.button("KARARI UYGULA", key=f"btn_{i}"):
                if aks == "Üst Yöneticiye Sevk (Patron Onayı)":
                    # Kaydı güncelle ve listede "sevk edildi" olarak işaretle
                    for idx, b in enumerate(st.session_state.onay_bekleyenler):
                        if b['Parti No'] == bekleyen['Parti No'] and b['Tarih'] == bekleyen['Tarih']:
                            st.session_state.onay_bekleyenler[idx]["Üst Yöneticiye Sevk"] = True
                            st.session_state.onay_bekleyenler[idx]["Kalite Müdürü Notu"] = y_not
                            st.session_state.onay_bekleyenler[idx]["Yönetici Aksiyonu"] = "ÜST YÖNETİCİYE SEVK EDİLDİ"
                    st.info("Kayıt Genel Müdür onayına sevk edildi.")
                else:
                    bekleyen.update({"Yönetici Aksiyonu": aks, "Yönetici Notu": y_not})
                    veriyi_excele_kaydet(pd.DataFrame([bekleyen]))
                    # Listeden sil
                    st.session_state.onay_bekleyenler = [b for b in st.session_state.onay_bekleyenler if not (b['Parti No'] == bekleyen['Parti No'] and b['Tarih'] == bekleyen['Tarih'])]
                    st.session_state.ana_veritabani = veriyi_excelden_yukle()
                time.sleep(1); st.rerun()

    st.divider()
    st.subheader("📜 Arşiv (Excel Veritabanı)")
    st.dataframe(st.session_state.ana_veritabani.iloc[::-1])

# --- PANEL 3: GENEL MÜDÜR ---
elif u_data['role'] == "Genel Müdür":
    st.header("👔 Üst Yönetim (Patron) Onay Paneli")
    sevk_edilenler = [b for b in st.session_state.onay_bekleyenler if b.get("Üst Yöneticiye Sevk", False)]
    
    if not sevk_edilenler:
        st.info("Şu an onayınızı bekleyen kritik bir sevk bulunmuyor.")
    
    for i, sevk in enumerate(sevk_edilenler):
        with st.container():
            st.markdown(f"""
            <div style="border:2px solid #FF4B4B; padding:20px; border-radius:10px; background-color:#FFF5F5;">
                <h3 style="color:#FF4B4B;">⚠️ DİKKAT: KRİTİK ONAY BEKLEYEN PARTİ</h3>
                <b>Parti No:</b> {sevk['Parti No']} | <b>Vardiya:</b> {sevk['Vardiya']}<br>
                <b>Kalite Müdürü Notu:</b> {sevk.get('Kalite Müdürü Notu', 'Not belirtilmemiş')}<br>
                <b>TRI Skoru:</b> {sevk['TRI']} | <b>Sistem Kararı:</b> {sevk['Sistem']}
            </div>
            """, unsafe_allow_html=True)
            
            st.table(pd.DataFrame({"Hata Sınıfı": ["P1","P2","P3","P4"], "Adet": [sevk['P1_A'], sevk['P2_A'], sevk['P3_A'], sevk['P4_A']]}))
            
            p_aks = st.radio("Kararınız nedir?", ["Onayla (Kabul)", "Şartlı Onay", "Reddet (İade)"], key=f"p_aks_{i}", horizontal=True)
            p_not = st.text_area("Patron Karar Notu (Zorunlu)", key=f"p_not_{i}", placeholder="Karar gerekçenizi buraya yazınız...")
            
            c_p1, c_p2 = st.columns(2)
            if c_p1.button("✅ KARARI KAYDET VE ARŞİVLE", key=f"p_save_{i}"):
                if not p_not:
                    st.warning("Lütfen kararın altına bir not ekleyiniz!")
                else:
                    final_status = f"PATRON ONAYI: {p_aks}"
                    sevk.update({
                        "Yönetici Aksiyonu": final_status, 
                        "Patron Notu": p_not,
                        "Onay Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    # Fotoğraf bilgilerini excel'e taşımadan önce temizle (isteğe bağlı)
                    veriyi_excele_kaydet(pd.DataFrame([sevk]))
                    
                    # Bekleyenler listesinden tamamen temizle
                    st.session_state.onay_bekleyenler = [b for b in st.session_state.onay_bekleyenler if not (b['Parti No'] == sevk['Parti No'] and b['Tarih'] == sevk['Tarih'])]
                    
                    st.session_state.ana_veritabani = veriyi_excelden_yukle()
                    st.success("Karar başarıyla kaydedildi."); time.sleep(2); st.rerun()
            st.divider()
    
    st.subheader("📊 Fabrika Genel Performans Arşivi")
    st.dataframe(st.session_state.ana_veritabani.iloc[::-1])
