import streamlit as st

# --- KALİTE MOTORU MANTIĞI ---
def kalite_motoru_hesapla(adet_toplam, p1_n, p2_n, p3_n, p4_n, p1_p, p2_p, p3_p, p4_p):
    total_hata = p1_n + p2_n + p3_n + p4_n
    if total_hata > 0:
        tri_puani = (p1_n * p1_p + p2_n * p2_p + p3_n * p3_p + p4_n * p4_p) / total_hata
    else:
        tri_puani = 0

    hata_orani = (total_hata / adet_toplam) * 100

    red_mi = (
        (p1_n + p2_n) > 6 or        
        p1_n >= 3 or                
        p2_n >= 3 or                
        total_hata > (adet_toplam * 0.05)
    )

    sartli_mi = (
        tri_puani > 1.7 or          
        (p1_n + p2_n) >= 4 or       
        (p3_n + p4_n) > 25          
    )

    if red_mi:
        return "SEVK EDİLEMEZ (RED)", "🔴", tri_puani, hata_orani
    elif sartli_mi:
        return "ŞARTLI KABUL (ONAY GEREKLİ)", "🟡", tri_puani, hata_orani
    else:
        return "UYGUN (OTOMATİK ONAY)", "🟢", tri_puani, hata_orani

# --- ARAYÜZ ---
st.set_page_config(page_title="Alasar Quality Engine", layout="wide")
st.title("🛡️ Alasar Quality Engine V1.0")
st.sidebar.info("Ömer Bey'in 11 Yıllık Denetçi Tecrübesiyle Programlanmıştır.")

col_main, col_res = st.columns([2, 1])

with col_main:
    st.subheader("📦 Sevkiyat Verileri")
    adet = st.number_input("Kontrol Edilen Toplam Adet", min_value=1, value=550)
    st.subheader("⚠️ Hata Girişleri")
    c1, c2, c3, c4 = st.columns(4)
    with c1: p1_n = st.number_input("P1 (Kritik) Adet", min_value=0, step=1)
    with c2: p2_n = st.number_input("P2 (Majör) Adet", min_value=0, step=1)
    with c3: p3_n = st.number_input("P3 (Minör) Adet", min_value=0, step=1)
    with c4: p4_n = st.number_input("P4 (Hafif) Adet", min_value=0, step=1)
    
    p1_p, p2_p, p3_p, p4_p = 5, 3, 2, 1 # Standart Şiddet Puanları

karar, ikon, tri, oran = kalite_motoru_hesapla(adet, p1_n, p2_n, p3_n, p4_n, p1_p, p2_p, p3_p, p4_p)

with col_res:
    st.subheader("📊 Analiz Sonucu")
    st.header(f"{ikon} {karar}")
    st.metric("TRI (Risk İndeksi)", f"{tri:.2f}")
    st.metric("HKY (Hata Oranı)", f"%{oran:.2f}")
