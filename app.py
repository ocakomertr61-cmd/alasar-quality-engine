import streamlit as st
import pandas as pd
from datetime import datetime

# --- GÜVENLİ AYARLAR ---
ADMIN_PASSWORD = "30052012"

if 'ana_veritabani' not in st.session_state:
    st.session_state.ana_veritabani = pd.DataFrame() 
if 'onay_bekleyenler' not in st.session_state:
    st.session_state.onay_bekleyenler = [] 

# --- KALİTE MOTORU ---
def kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    hata_orani = (toplam_hata / G3) if G3 > 0 else 0
    temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
    t3_skor = max(temel_oran * (1 + (J3*0.03 + K3*0.05)), toplam_hata / 20) if toplam_hata > 0 else 0.0
    red_mi = (hata_orani > 0.05 or (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or t3_skor >= 5.0)
    sartli_mi = False if red_mi else (t3_skor > 1.7 or (J3 + K3) >= 6)
    if red_mi: return "RED", "🔴", t3_skor
    elif sartli_mi: return "SARI", "🟡", t3_skor
    else: return "UYGUN", "🟢", t3_skor

# --- UI ---
st.set_page_config(page_title="Alasar Workflow V5.6", layout="wide")
rol = st.sidebar.selectbox("Giriş Yapılan Ekran:", ["Üretim Hattı (Operatör)", "Yönetici Paneli (Ömer Ocak)"])

# ---------------------------------------------------------
# 1. EKRAN: ÜRETİM HATTI (Net Geri Bildirim)
# ---------------------------------------------------------
if rol == "Üretim Hattı (Operatör)":
    st.header("🏭 Üretim Hattı Veri Giriş Terminali")
    with st.sidebar:
        st.divider()
        op_ad = st.text_input("Ad Soyad")
        op_kase = st.text_input("Kaşe No")

    with st.container():
        c1, c2, c3 = st.columns(3)
        lot = c1.text_input("Parti No", "LOT-100")
        sevk = c2.number_input("Toplam Sevk", 1000)
        kontrol = c3.number_input("Kontrol Edilen", 100)
        h1, h2, h3, h4 = st.columns(4)
        j3 = h1.number_input("P1 Adet", 0); k3 = h2.number_input("P2 Adet", 0)
        l3 = h3.number_input("P3 Adet", 0); m3 = h4.number_input("P4 Adet", 0)
        p1p = h1.number_input("P1 Puan", 1.0); p2p = h2.number_input("P2 Puan", 1.0)
        p3p = h3.number_input("P3 Puan", 1.0); p4p = h4.number_input("P4 Puan", 1.0)
        op_not = st.text_area("Operatör Gözlem Notu")

    if st.button("🚀 VERİLERİ ANALİZ ET", use_container_width=True):
        if not op_ad or not op_kase:
            st.error("⚠️ Lütfen Ad Soyad ve Kaşe No giriniz!")
        else:
            karar, ikon, skor = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
            hky = (j3+k3+l3+m3)/kontrol if kontrol > 0 else 0
            st.session_state.gecici_analiz = {
                "Tarih": datetime.now().strftime("%d/%m %H:%M"), "Operatör": op_ad, "Kaşe": op_kase,
                "Parti No": lot, "Sevk": sevk, "Kontrol": kontrol,
                "P1_A": j3, "P1_P": p1p, "P2_A": k3, "P2_P": p2p, "P3_A": l3, "P3_P": p3p, "P4_A": m3, "P4_P": p4p,
                "TRI": round(skor, 4), "HKY": f"%{hky*100:.2f}", "Sistem": karar, "Operatör Notu": op_not if op_not else "-"
            }

    if 'gecici_analiz' in st.session_state:
        st.divider()
        data = st.session_state.gecici_analiz
        
        # Karar UYGUN ise operatöre kafa karışıklığı yaratmayacak net mesaj
        if data['Sistem'] == "UYGUN":
            st.success("✅ SİSTEM ANALİZİ: UYGUN. Herhangi bir ek onay gerekmemektedir.")
            if st.button("KAYDI TAMAMLA VE ARŞİVE GÖNDER", use_container_width=True):
                data.update({"Yönetici Aksiyonu": "OTOMATİK ONAY (YÖNETİCİ UYGUN BULDU)", "Yönetici Notu": "-"})
                st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([data])])
                st.balloons() # Başarı kutlaması
                st.success("✅ İŞLEM TAMAMLANDI: YÖNETİCİ ONAYLADI, UYGUNDUR!")
                del st.session_state.gecici_analiz
                # 3 saniye bekleyip temizlemesi için rerun eklemiyoruz ki mesajı okusunlar
        else:
            st.warning(f"⚠️ DİKKAT: Sistem Kararı {data['Sistem']}. Bu kayıt Ömer Bey'in onayına düşecektir.")
            con1, con2 = st.columns(2)
            if con1.button("✅ ONAYA GÖNDER", use_container_width=True):
                st.session_state.onay_bekleyenler.append(data)
                st.info("Kayıt yönetici paneline iletildi.")
                del st.session_state.gecici_analiz
                st.rerun()
            if con2.button("❌ İPTAL ET / DÜZELT", use_container_width=True):
                del st.session_state.gecici_analiz
                st.rerun()

# ---------------------------------------------------------
# 2. EKRAN: YÖNETİCİ PANELİ (Giriş Kilidi)
# ---------------------------------------------------------
else:
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.error("🚫 YETKİ ALANINIZ DIŞINDA!")
        admin_pwd = st.text_input("Yönetici Parolası:", type="password")
        if st.button("GİRİŞ YAP"):
            if admin_pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
            else: st.error("Hatalı Parola!")
        st.stop()

    if st.sidebar.button("OTURUMU KAPAT"):
        st.session_state.admin_logged_in = False
        st.rerun()

    st.header("👔 Yönetici Onay ve Karar Ekranı")
    if not st.session_state.onay_bekleyenler:
        st.info("Onay bekleyen kayıt yok.")
    else:
        for i, bekleyen in enumerate(st.session_state.onay_bekleyenler):
            with st.expander(f"📌 PARTİ: {bekleyen['Parti No']} | Operatör: {bekleyen['Operatör']} | {bekleyen['Sistem']}", expanded=True):
                st.table(pd.DataFrame({
                    "Kategori": ["P1 (Kritik)", "P2 (Majör)", "P3 (Minör)", "P4 (Görsel)"],
                    "Hata Adeti": [bekleyen['P1_A'], bekleyen['P2_A'], bekleyen['P3_A'], bekleyen['P4_A']],
                    "Risk Puanı": [bekleyen['P1_P'], bekleyen['P2_P'], bekleyen['P3_P'], bekleyen['P4_P']]
                }))
                st.info(f"📝 **Operatör Notu:** {bekleyen['Operatör Notu']}")
                
                # Hızlı Onay Butonu
                if st.button(f"⚡ SİSTEMİN '{bekleyen['Sistem']}' KARARINI DİREKT ONAYLA", key=f"q_{i}"):
                    bekleyen.update({"Yönetici Aksiyonu": f"YÖNETİCİ ONAYLADI, UYGUNDUR ({bekleyen['Sistem']})", "Yönetici Notu": "Hızlı Onay"})
                    st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([bekleyen])])
                    st.session_state.onay_bekleyenler.pop(i)
                    st.rerun()

                st.write("Veya manuel aksiyon seçin:")
                c1, c2 = st.columns([2, 2])
                secilen = c1.selectbox("Aksiyon", ["Şartlı Kabul ✅", "Kesin Red ❌", "%100 Ayıklama 🔍", "Karantina 📦", "İade 🚛"], key=f"s_{i}")
                y_notu = c2.text_input("Yönetici Notu", key=f"n_{i}")
                if st.button(f"KARARI KAYDET: {bekleyen['Parti No']}", key=f"b_{i}"):
                    bekleyen.update({"Yönetici Aksiyonu": secilen, "Yönetici Notu": y_notu if y_notu else "-"})
                    st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([bekleyen])])
                    st.session_state.onay_bekleyenler.pop(i)
                    st.rerun()

    st.divider()
    st.subheader("📜 Genel Kalite Denetim Arşivi")
    st.dataframe(st.session_state.ana_veritabani.iloc[::-1], use_container_width=True, hide_index=True)
