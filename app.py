import streamlit as st

def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    """
    Ömer Ocak - Alasar Quality Engine V2.5
    Tüm güncel limitler ve mantıksal filtreler işlenmiştir.
    """
    # I3 Hücresi: Toplam Hatalı Ürün Adedi
    toplam_hata = J3 + K3 + L3 + M3
    
    # --- 1. TRI (RISK INDEKSI - T3) HESAPLAMA ---
    if toplam_hata == 0:
        T3 = 0.0
    else:
        # Ağırlıklı Puan (Payda: 15 kuralı korunuyor)
        temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
        
        # Yoğunluk Cezası Filtresi
        if P3_p < 4 and Q3_p < 4 and (J3 + K3) < 4:
            ek_ceza = 0
        else:
            ek_ceza = (J3 * 0.03) + (K3 * 0.05)
        
        # Toplam Çarpan ve Alt Sınır Bariyeri
        toplam_carpan = 1 + (ek_ceza + (L3 * 0.01) + (M3 * 0.005))
        T3 = max(temel_oran * toplam_carpan, toplam_hata / 20)

    # --- 2. SEVK EDİLEMEZ (RED) FİLTRELERİ ---
    red_mi = (
        (J3 >= 3 and P3_p >= 3) or          # P1: Hem adet >= 3 Hem Puan >= 3 ise RED
        (K3 >= 3 and Q3_p >= 3) or          # P2: Hem adet >= 3 Hem Puan >= 3 ise RED
        (J3 + K3) >= 10 or                  # GÜNCEL: P1+P2 Toplamı >= 10 ise RED
        R3_p >= 4 or                        # P3 Puanı >= 4 (Montaj)
        S3_p == 5 or                        # P4 Puanı = 5 (Görsel)
        T3 >= 5 or                          # TRI Skoru >= 5
        (F3 > 0 and toplam_hata > (F3 * 0.05)) # Toplam hata sevk miktarının %5'inden fazlaysa
    )
    
    # --- 3. ŞARTLI KABUL (SARI) FİLTRELERİ ---
    sartli_mi = False
    if not red_mi and toplam_hata > 0:
        sartli_mi = (
            T3 > 1.7 or                     # Risk puanı eşiği (Hassasiyet)
            (J3 + K3) >= 6 or               # P1+P2 Toplamı 6-9 arası ise SARI (Esnetildi)
            (P3_p >= 3 and Q3_p >= 3 and R3_p >= 3 and S3_p >= 3 and toplam_hata >= 5) or # Yaygın Risk
            (L3 + M3) > 25                  # Çok fazla hafif hata varsa
        )

    # --- 4. KARAR MERKEZİ ---
    if red_mi:
        return "SEVK EDİLEMEZ (RED)", "🔴", T3
    elif sartli_mi:
        return "ŞARTLI KABUL (ONAY GEREKLİ)", "🟡", T3
    else:
        return "UYGUN (OTOMATİK ONAY)", "🟢", T3

# --- STREAMLIT ARAYÜZ TASARIMI ---
st.set_page_config(page_title="Alasar Quality Engine V2.5", layout="wide")
st.title("🛡️ Alasar Quality Engine V2.5")
st.markdown("---")

# Yan Panel - Genel Bilgiler
with st.sidebar:
    st.header("📋 Denetim Verileri")
    f3_input = st.number_input("Toplam Sevk Miktarı (F3)", value=10000, step=100)
    g3_input = st.number_input("Kontrol Edilen Miktar (G3)", value=500, step=10)
    st.divider()
    st.info("V2.5 Güncellemesi: P1+P2 RED sınırı 10 adede çıkarıldı. 0 hatada sarı yanma sorunu giderildi.")

# Ana Ekran - Giriş Alanları
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚠️ Hata Adetleri (J, K, L, M)")
    j3_in = st.number_input("P1 (Fonksiyonel) Adet", value=0, min_value=0)
    k3_in = st.number_input("P2 (Güvenlik) Adet", value=0, min_value=0)
    l3_in = st.number_input("P3 (Montaj) Adet", value=0, min_value=0)
    m3_in = st.number_input("P4 (Görsel) Adet", value=0, min_value=0)

with col2:
    st.subheader("🎯 Risk Puanları (P, Q, R, S)")
    p3_p_in = st.number_input("P1 Risk Puanı", value=1.0, min_value=0.0, max_value=5.0, step=1.0)
    q3_p_in = st.number_input("P2 Risk Puanı", value=1.0, min_value=0.0, max_value=5.0, step=1.0)
    r3_p_in = st.number_input("P3 Risk Puanı", value=1.0, min_value=0.0, max_value=5.0, step=1.0)
    s3_p_in = st.number_input("P4 Risk Puanı", value=1.0, min_value=0.0, max_value=5.0, step=1.0)

# Hesaplama ve Sonuç Ekranı
st.divider()
karar, ikon, t3_skoru = kalite_motoru_hesapla(f3_input, g3_input, j3_in, k3_in, l3_in, m3_in, p3_p_in, q3_p_in, r3_p_in, s3_p_in)

hky_orani = ((j3_in + k3_in + l3_in + m3_in) / g3_input * 100) if g3_input > 0 else 0

res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    st.metric("TRI (Risk Skoru)", f"{t3_skoru:.4f}")
with res_col2:
    st.metric("HKY (Hata Oranı)", f"%{hky_orani:.2f}")
with res_col3:
    st.subheader("Final Kararı")
    st.header(f"{ikon} {karar}")

# Uyarı Mesajları
if karar == "SEVK EDİLEMEZ (RED)":
    st.error("DİKKAT: Sevkiyat kritik limitleri aşmıştır. İşlemi durdurun!")
elif karar == "ŞARTLI KABUL (ONAY GEREKLİ)":
    st.warning("BİLGİ: Sistem risk tespit etti. Yönetici onayı olmadan sevk edilemez.")
else:
    st.success("ONAY: Sevkiyat kalite standartlarına uygundur.")
