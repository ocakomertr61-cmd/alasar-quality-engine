import streamlit as st
import pandas as pd
from datetime import datetime

# --- GÜVENLİ AYARLAR ---
ADMIN_PASSWORD = "30052012"
TARGET_EMAIL = "ocakomertr61@gmail.com"

# 1. VERİ HAVUZLARI
if 'ana_veritabani' not in st.session_state:
    st.session_state.ana_veritabani = pd.DataFrame() 

if 'onay_bekleyenler' not in st.session_state:
    st.session_state.onay_bekleyenler = [] 

# --- KALİTE MOTORU ---
def kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    hata_orani = (toplam_hata / G3) if G3 > 0 else 0
    temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
    # T3 Skoru hesaplama (Puanlar ve Adetler etkili)
    t3_skor = max(temel_oran * (1 + (J3*0.03 + K3*0.05)), toplam_hata / 20) if toplam_hata > 0 else 0.0

    # Kesin RED Şartları
    red_mi = (hata_orani > 0.05 or (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or t3_skor >= 5.0)
    sartli_mi = False if red_mi else (t3_skor > 1.7 or (J3 + K3) >= 6)

    if red_mi: return "RED", "🔴", t3_skor
    elif sartli_mi: return "SARI", "🟡", t3_skor
    else: return "UYGUN", "🟢", t3_skor

# --- UI ---
st.set_page_config(page_title="Alasar Workflow V5.1", layout="wide")
rol = st.sidebar.selectbox("Giriş Yapılan Ekran:", ["Üretim Hattı (Operatör)", "Yönetici Paneli (Ömer Ocak)"])

# ---------------------------------------------------------
# 1. EKRAN: ÜRETİM HATTI (Gelişmiş Geri Bildirimli)
# ---------------------------------------------------------
if rol == "Üretim Hattı (Operatör)":
    st.header("🏭 Üretim Hattı Veri Giriş ve Analiz")
    
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

    if st.button("🚀 ANALİZ ET VE SİSTEME GÖNDER", use_container_width=True):
        karar, ikon, skor = kalite_motoru_hesapla(kontrol, j3, k3, l3, m3, p1p, p2p, p3p, p4p)
        hky = (j3+k3+l3+m3)/kontrol if kontrol > 0 else 0
        
        # OPERATÖR İÇİN ANALİZ SONUÇ PANELİ
        st.divider()
        st.subheader("📊 Analiz Sonucu (Ön İzleme)")
        res1, res2, res3 = st.columns(3)
        res1.metric("TRI Skoru", f"{skor:.4f}")
        res2.metric("HKY Oranı", f"%{hky*100:.2f}")
        res3.header(f"{ikon} {karar}")

        yeni_veri = {
            "Tarih": datetime.now().strftime("%H:%M"), "Parti No": lot, "Sevk": sevk, "Kontrol": kontrol,
            "P1_A": j3, "P1_P": p1p, "P2_A": k3, "P2_P": p2p, "P3_A": l3, "P3_P": p3p, "P4_A": m3, "P4_P": p4p,
            "TRI": round(skor, 4), "HKY": f"%{hky*100:.2f}", "Sistem": karar
        }

        if karar == "UYGUN":
            yeni_veri.update({"Yönetici Aksiyonu": "OTOMATİK ONAY", "Not": "-"})
            st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([yeni_veri])])
            st.success("✅ Veri UYGUN bulundu ve Arşive kaydedildi.")
        else:
            st.session_state.onay_bekleyenler.append(yeni_veri)
            st.warning(f"⚠️ Karar {karar}: Veri yönetici onayına (Ömer Ocak) başarıyla iletildi.")

# ---------------------------------------------------------
# 2. EKRAN: YÖNETİCİ PANELİ (Önünüze düşen sayfa)
# ---------------------------------------------------------
else:
    st.header("👔 Yönetici Onay ve Karar Ekranı")
    
    if not st.session_state.onay_bekleyenler:
        st.info("Onay bekleyen denetim yok. Her şey yolunda!")
    else:
        st.subheader(f"🔔 {len(st.session_state.onay_bekleyenler)} Denetim Onayınızı Bekliyor")
        
        for i, bekleyen in enumerate(st.session_state.onay_bekleyenler):
            with st.expander(f"📌 {bekleyen['Parti No']} - Sistem Kararı: {bekleyen['Sistem']}", expanded=True):
                st.write(f"**TRI:** {bekleyen['TRI']} | **HKY:** {bekleyen['HKY']} | **P1:** {bekleyen['P1_A']} ad / {bekleyen['P1_P']} p")
                
                col_onay1, col_onay2, col_onay3 = st.columns([2, 2, 1])
                
                ops = ["Şartlı Kabulü Onayla ✅", "Kesin Reddet ❌"] if bekleyen['Sistem'] == "SARI" else \
                      ["%100 Ayıklama Yapılsın 🔍", "Karantina / Hurda 📦", "Tedarikçiye İade 🚛"]
                
                secilen_aksiyon = col_onay1.selectbox("Karar", ops, key=f"sel_{i}")
                yonetici_notu = col_onay2.text_input("Açıklama", key=f"not_{i}")
                sifre = col_onay3.text_input("Şifre", type="password", key=f"pwd_{i}")

                if st.button(f"KAYDI TAMAMLA: {bekleyen['Parti No']}", key=f"btn_{i}"):
                    if sifre == ADMIN_PASSWORD:
                        bekleyen.update({"Yönetici Aksiyonu": secilen_aksiyon, "Not": yonetici_notu})
                        st.session_state.ana_veritabani = pd.concat([st.session_state.ana_veritabani, pd.DataFrame([bekleyen])])
                        st.session_state.onay_bekleyenler.pop(i)
                        st.success("Kararınız işlendi ve arşive eklendi!")
                        st.rerun()
                    else:
                        st.error("Parola Yanlış!")

# --- GENEL ARŞİV ---
st.divider()
st.subheader("📜 Genel Denetim Arşivi")
if not st.session_state.ana_veritabani.empty:
    st.dataframe(st.session_state.ana_veritabani.iloc[::-1], use_container_width=True, hide_index=True)
