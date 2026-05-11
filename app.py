import streamlit as st

def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3_puan, Q3_puan, R3_puan, S3_puan):
    toplam_hata = J3 + K3 + L3 + M3
    
    # --- 1. TRI (RISK INDEKSI) HESAPLAMA ---
    if toplam_hata == 0:
        T3 = 0.0
    else:
        temel_oran = ((P3_puan * 2) + (Q3_puan * 3) + (R3_puan * 2) + (S3_puan * 2)) / 15
        if P3_puan < 4 and Q3_puan < 4 and (J3 + K3) < 4:
            ek_ceza = 0
        else:
            ek_ceza = (J3 * 0.03) + (K3 * 0.05)
        
        toplam_carpan = 1 + (ek_ceza + (L3 * 0.01) + (M3 * 0.005))
        T3 = max(temel_oran * toplam_carpan, toplam_hata / 20)

    # --- 2. SEVK EDİLEMEZ (RED) FİLTRELERİ ---
    red_mi = (
        J3 >= 3 or                          # P1 tek başına 3 ve üzeri
        K3 >= 3 or                          # P2 tek başına 3 ve üzeri
        (J3 + K3) >= 6 or                   # Kritik Toplam 6 ve üzeri
        R3_puan >= 4 or                     
        S3_puan == 5 or                     
        T3 >= 5 or                          
        toplam_hata > (F3 * 0.05)           
    )
    
    # --- 3. ŞARTLI KABUL (SARI) FİLTRELERİ (GÜNCELLENDİ) ---
    sartli_mi = False
    if not red_mi and toplam_hata > 0:
        sartli_mi = (
            T3 > 1.7 or                     
            (J3 + K3) >= 4 or               
            (J3 >= 3 and P3_puan >= 3) or    # YENİ: P1 hem adet >= 3 hem puan >= 3 ise SARI
            (K3 >= 3 and Q3_puan >= 3) or    # YENİ: P2 hem adet >= 3 hem puan >= 3 ise SARI
            (L3 + M3) > 25                  
        )

    # --- 4. SONUÇ ---
    if red_mi:
        return "SEVK EDİLEMEZ (RED)", "🔴", T3
    elif sartli_mi:
        return "ŞARTLI KABUL (ONAY GEREKLİ)", "🟡", T3
    else:
        return "UYGUN (OTOMATİK ONAY)", "🟢", T3

# --- KULLANICI ARAYÜZÜ ---
st.set_page_config(page_title="Alasar Quality Engine V2.0", layout="wide")
st.title("🛡️ Alasar Quality Engine V2.0")

col_params, col_errors, col_risks = st.columns(3)

with col_params:
    st.subheader("📊 Sevkiyat")
    f3_val = st.number_input("Toplam Sevk (F3)", value=10000)
    g3_val = st.number_input("Kontrol Edilen (G3)", value=500)

with col_errors:
    st.subheader("⚠️ Hata Adetleri")
    j3_val = st.number_input("P1 Adet (J3)", value=0)
    k3_val = st.number_input("P2 Adet (K3)", value=0)
    l3_val = st.number_input("P3 Adet (L3)", value=0)
    m3_val = st.number_input("P4 Adet (M3)", value=0)

with col_risks:
    st.subheader("🎯 Risk Puanları")
    p3_p = st.number_input("P1 Puan (P3)", value=0.0)
    q3_p = st.number_input("P2 Puan (Q3)", value=0.0)
    r3_p = st.number_input("P3 Puan (R3)", value=0.0)
    s3_p = st.number_input("P4 Puan (S3)", value=0.0)

karar, ikon, t3_degeri = kalite_motoru_hesapla(f3_val, g3_val, j3_val, k3_val, l3_val, m3_val, p3_p, q3_p, r3_p, s3_p)

st.divider()
st.header(f"{ikon} {karar}")
st.metric("TRI (T3)", f"{t3_degeri:.4f}")
