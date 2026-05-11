import streamlit as st
import pandas as pd
from datetime import datetime

# --- FONKSİYONLAR ---
def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    if toplam_hata == 0:
        T3 = 0.0
    else:
        temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
        ek_ceza = (J3 * 0.03) + (K3 * 0.05) if (P3_p >= 4 or Q3_p >= 4 or (J3+K3) >= 4) else 0
        toplam_carpan = 1 + (ek_ceza + (L3 * 0.01) + (M3 * 0.005))
        T3 = max(temel_oran * toplam_carpan, toplam_hata / 20)

    red_mi = (
        (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or 
        (J3 + K3) >= 10 or R3_p >= 4 or S3_p == 5 or T3 >= 5.0 or 
        (F3 > 0 and toplam_hata > (F3 * 0.05))
    )
    
    sartli_mi = False
    if not red_mi and toplam_hata > 0:
        sartli_mi = (T3 > 1.7 or (J3 + K3) >= 6 or (L3 + M3) > 25)

    if red_mi: return "RED", "🔴", T3
    elif sartli_mi: return "SARI", "🟡", T3
    else: return "UYGUN", "🟢", T3

# --- VERİ YÖNETİMİ ---
if 'denetim_gecmisi' not in st.session_state:
    st.session_state.denetim_gecmisi = pd.DataFrame(columns=[
        "Tarih", "Parti No", "Sevk", "Kontrol", "P1", "P2", "P3", "P4", "TRI", "Karar"
    ])

# --- UI TASARIMI ---
st.set_page_config(page_title="Alasar Quality DB", layout="wide")
st.title("📊 Alasar Quality Engine V3.0 (Veri Kayıtlı)")

with st.sidebar:
    st.header("📋 Yeni Denetim Girişi")
    parti_no = st.text_input("Parti / Lot Numarası", value="LOT-001")
    f3 = st.number_input("Toplam Sevk (F3)", value=10000)
    g3 = st.number_input("Kontrol Edilen (G3)", value=500)
    st.divider()
    save_button = st.button("💾 DENETİMİ KAYDET", use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.subheader("⚠️ Hata Adetleri")
    j3, k3, l3, m3 = st.number_input("P1", 0), st.number_input("P2", 0), st.number_input("P3", 0), st.number_input("P4", 0)
with c2:
    st.subheader("🎯 Risk Puanları")
    p3, q3, r3, s3 = st.number_input("P1 Puan", 1.0), st.number_input("P2 Puan", 1.0), st.number_input("P3 Puan", 1.0), st.number_input("P4 Puan", 1.0)

# Hesaplama
karar, ikon, t3_skor = kalite_motoru_hesapla(f3, g3, j3, k3, l3, m3, p3, q3, r3, s3)

# Kaydetme Mantığı
if save_button:
    yeni_veri = {
        "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Parti No": parti_no,
        "Sevk": f3, "Kontrol": g3,
        "P1": j3, "P2": k3, "P3": l3, "P4": m3,
        "TRI": round(t3_skor, 4),
        "Karar": f"{ikon} {karar}"
    }
    st.session_state.denetim_gecmisi = pd.concat([st.session_state.denetim_gecmisi, pd.DataFrame([yeni_veri])], ignore_index=True)
    st.success(f"{parti_no} başarıyla kaydedildi!")

# --- LİSTELEME VE SİLME ---
st.divider()
st.subheader("📜 Denetim Geçmişi ve Kayıtlar")

if not st.session_state.denetim_gecmisi.empty:
    # Tabloyu Göster
    st.dataframe(st.session_state.denetim_gecmisi, use_container_width=True)
    
    # İşlemler
    col_del, col_exp = st.columns([1, 5])
    with col_del:
        if st.button("🗑️ Tümünü Temizle"):
            st.session_state.denetim_gecmisi = st.session_state.denetim_gecmisi.iloc[0:0]
            st.rerun()
    with col_exp:
        # Excel'e aktarma butonu için basit CSV indirme
        csv = st.session_state.denetim_gecmisi.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Excel/CSV Olarak İndir", csv, "denetim_gecmisi.csv", "text/csv")
else:
    st.info("Henüz kayıtlı bir denetim bulunmuyor.")
