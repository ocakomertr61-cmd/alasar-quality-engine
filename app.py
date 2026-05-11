import streamlit as st

def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3, Q3, R3, S3):
    toplam_hata = J3 + K3 + L3 + M3
    
    if toplam_hata == 0:
        T3 = 0.0
    else:
        temel_oran = ((P3 * 2) + (Q3 * 3) + (R3 * 2) + (S3 * 2)) / 15
        if P3 < 4 and Q3 < 4 and (J3 + K3) < 4:
            kosullu_carpan = 0
        else:
            kosullu_carpan = (J3 * 0.03) + (K3 * 0.05)
        toplam_carpan = 1 + (kosullu_carpan + (L3 * 0.01) + (M3 * 0.005))
        deger_A = temel_oran * toplam_carpan
        deger_B = toplam_hata / 20
        T3 = max(deger_A, deger_B)

    # RED Koşulu
    red_mi = (
        R3 >= 4 or 
        S3 == 5 or 
        (J3 + K3) > 6 or 
        T3 >= 5 or 
        J3 >= 3 or 
        K3 >= 3 or 
        toplam_hata > (F3 * 0.05)
    )
    
    # SARI Koşulu (DÜZELTİLDİ: Sadece hata varsa puanı kontrol eder)
    sartli_mi = (
        T3 > 1.7 or 
        (J3 + K3) >= 4 or 
        (J3 > 0 and P3 >= 1) or 
        (K3 > 0 and Q3 >= 1) or 
        (L3 + M3) > 25
    )

    if red_mi:
        return "SEVK EDİLEMEZ (RED)", "🔴", T3
    elif sartli_mi:
        return "ŞARTLI KABUL (ONAY GEREKLİ)", "🟡", T3
    else:
        return "UYGUN (OTOMATİK ONAY)", "🟢", T3

# --- ARAYÜZ ---
st.set_page_config(page_title="Alasar Quality Engine", layout="wide")
st.title("🛡️ Alasar Quality Engine V1.4")

with st.sidebar:
    st.header("📋 Sevkiyat Parametreleri")
    F3 = st.number_input("Toplam Sevk Adedi (F3)", min_value=1, value=10000)
    G3 = st.number_input("Kontrol Edilen Adet (G3)", min_value=1, value=500)

col_hata, col_risk = st.columns(2)
with col_hata:
    st.subheader("⚠️ Hata Adetleri")
    J3 = st.number_input("P1 Adet (J3)", min_value=0, step=1)
    K3 = st.number_input("P2 Adet (K3)", min_value=0, step=1)
    L3 = st.number_input("P3 Adet (L3)", min_value=0, step=1)
    M3 = st.number_input("P4 Adet (M3)", min_value=0, step=1)

with col_risk:
    st.subheader("🎯 Risk Puanları")
    P3_val = st.number_input("P1 Puanı (P3)", value=1.0)
    Q3_val = st.number_input("P2 Puanı (Q3)", value=1.0)
    R3_val = st.number_input("P3 Puanı (R3)", value=1.0)
    S3_val = st.number_input("P4 Puanı (S3)", value=1.0)

karar, ikon, tri_sonuc = kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3_val, Q3_val, R3_val, S3_val)

st.divider()
st.header(f"{ikon} {karar}")
st.metric("TRI (T3)", f"{tri_sonuc:.4f}")
