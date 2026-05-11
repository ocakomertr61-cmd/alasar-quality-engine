import streamlit as st

def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    
    # --- 1. TRI (RISK INDEKSI) HESAPLAMA (Payda: 15) ---
    if toplam_hata == 0:
        T3 = 0.0
    else:
        temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
        if P3_p < 4 and Q3_p < 4 and (J3 + K3) < 4:
            ek_ceza = 0
        else:
            ek_ceza = (J3 * 0.03) + (K3 * 0.05)
        toplam_carpan = 1 + (ek_ceza + (L3 * 0.01) + (M3 * 0.005))
        T3 = max(temel_oran * toplam_carpan, toplam_hata / 20)

    # --- 2. SEVK EDİLEMEZ (RED) FİLTRELERİ (GÜNCELLENDİ) ---
    red_mi = (
        (J3 >= 3 and P3_p >= 3) or          # P1: Hem adet >= 3 Hem Puan >= 3 ise RED
        (K3 >= 3 and Q3_p >= 3) or          # P2: Hem adet >= 3 Hem Puan >= 3 ise RED
        (J3 + K3) >= 10 or                  # GÜNCEL: P1+P2 Toplamı >= 10 ise RED
        R3_p >= 4 or                        # P3 Puanı >= 4
        S3_p == 5 or                        # P4 Puanı = 5
        T3 >= 5 or                          # TRI >= 5
        toplam_hata > (F3 * 0.05)           # Toplam hata > %5 sevk
    )
    
    # --- 3. ŞARTLI KABUL (SARI) FİLTRELERİ ---
    sartli_mi = False
    if not red_mi and toplam_hata > 0:
        sartli_mi = (
            T3 > 1.7 or                     
            (J3 + K3) >= 4 or               
            (J3 >= 3 or K3 >= 3) or         # Adet 3 olsa bile puan düşükse SARI'da kalır
            (L3 + M3) > 25                  
        )

    # --- 4. SONUÇ ---
    if red_mi:
        return "SEVK EDİLEMEZ (RED)", "🔴", T3
    elif sartli_mi:
        return "ŞARTLI KABUL (ONAY GEREKLİ)", "🟡", T3
    else:
        return "UYGUN (OTOMATİK ONAY)", "🟢", T3

# --- STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="Alasar Quality Engine V2.3", layout="wide")
st.title("🛡️ Alasar Quality Engine V2.3")

with st.sidebar:
    st.header("📋 Sevkiyat Parametreleri")
    f3 = st.number_input("Toplam Sevk (F3)", value=10000)
    g3 = st.number_input("Kontrol Edilen (G3)", value=500)
    st.info("RED Sınırı (P1+P2) >= 10 olarak güncellendi.")

c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("⚠️ Hata Adetleri")
    j3 = st.number_input("P1 Adet (J3)", value=0)
    k3 = st.number_input("P2 Adet (K3)", value=0)
    l3 = st.number_input("P3 Adet (L3)", value=0)
    m3 = st.number_input("P4 Adet (M3)", value=0)
with c2:
    st.subheader("🎯 Risk Puanları")
    p3 = st.number_input("P1 Puan (P3)", value=0.0)
    q3 = st.number_input("P2 Puan (Q3)", value=0.0)
    r3 = st.number_input("P3 Puan (R3)", value=0.0)
    s3 = st.number_input("P4 Puan (S3)", value=0.0)

karar, ikon, t3_d = kalite_motoru_hesapla(f3, g3, j3, k3, l3, m3, p3, q3, r3, s3)

with c3:
    st.subheader("🏁 Karar")
    st.header(f"{ikon} {karar}")
    st.metric("TRI (T3) Puanı", f"{t3_d:.4f}")
