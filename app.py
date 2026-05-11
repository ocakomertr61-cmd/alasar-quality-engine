import streamlit as st

# --- ÖMER BEY'İN EXCEL FORMÜLÜ BİREBİR UYARLAMASI ---
def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3, Q3, R3, S3):
    # Toplam hatalı (I3 hücresi gibi düşünün)
    toplam_hata = J3 + K3 + L3 + M3
    
    # 1. TRI PUANI HESAPLAMA (T3 Hücresi Formülü)
    if toplam_hata == 0:
        T3 = 0.0
    else:
        # Formül: ((P3*2)+(Q3*3)+(R3*2)+(S3*2))/15
        temel_oran = ((P3 * 2) + (Q3 * 3) + (R3 * 2) + (S3 * 2)) / 15
        
        # Formül: EĞER(VE(P3<4;Q3<4;(J3+K3)<4);0;J3*0,03+K3*0,05)
        # Burada P3 ve Q3 risk puanlarını, J3 ve K3 hata adetlerini temsil eder.
        if P3 < 4 and Q3 < 4 and (J3 + K3) < 4:
            kosullu_carpan = 0
        else:
            kosullu_carpan = (J3 * 0.03) + (K3 * 0.05)
        
        # Formül: (1+(KOŞULLU + L3*0,01 + M3*0,005))
        toplam_carpan = 1 + (kosullu_carpan + (L3 * 0.01) + (M3 * 0.005))
        
        # MAK(Temel_Oran * Çarpan ; Toplam_Hata / 20)
        deger_A = temel_oran * toplam_carpan
        deger_B = toplam_hata / 20
        T3 = max(deger_A, deger_B)

    # 2. KARAR MEKANİZMASI (Filtre Durumu Formülü)
    # RED Şartları: YADA(R3>=4; S3=5; (J3+K3)>6; T3>=5; J3>=3; K3>=3; ToplamHata>(F3*0,05))
    red_mi = (
        R3 >= 4 or 
        S3 == 5 or 
        (J3 + K3) > 6 or 
        T3 >= 5 or 
        J3 >= 3 or 
        K3 >= 3 or 
        toplam_hata > (F3 * 0.05)
    )
    
    # SARI Şartları: YADA(T3>1,7; (J3+K3)>=4; P3>=1; Q3>=1; (L3+M3)>25)
    sartli_mi = (
        T3 > 1.7 or 
        (J3 + K3) >= 4 or 
        P3 >= 1 or 
        Q3 >= 1 or 
        (L3 + M3) > 25
    )

    if red_mi:
        return "SEVK EDİLEMEZ (RED)", "🔴", T3
    elif sartli_mi:
        return "ŞARTLI KABUL (ONAY GEREKLİ)", "🟡", T3
    else:
        return "UYGUN (OTOMATİK ONAY)", "🟢", T3

# --- GÖRSEL ARAYÜZ ---
st.set_page_config(page_title="Alasar Quality Engine", layout="wide")
st.title("🛡️ Alasar Quality Engine V1.3")
st.markdown("---")

# Veri Giriş Alanları
with st.sidebar:
    st.header("📋 Sevkiyat Parametreleri")
    F3 = st.number_input("Toplam Sevk Adedi (F3)", min_value=1, value=10000)
    G3 = st.number_input("Kontrol Edilen Adet (G3)", min_value=1, value=500)
    st.divider()
    st.info("Formüller Ömer Bey'in Excel tablosundan birebir aktarılmıştır.")

col_hata, col_risk = st.columns(2)

with col_hata:
    st.subheader("⚠️ Hata Adetleri")
    c1, c2 = st.columns(2)
    with c1:
        J3 = st.number_input("P1 Adet (J3)", min_value=0, step=1)
        K3 = st.number_input("P2 Adet (K3)", min_value=0, step=1)
    with c2:
        L3 = st.number_input("P3 Adet (L3)", min_value=0, step=1)
        M3 = st.number_input("P4 Adet (M3)", min_value=0, step=1)

with col_risk:
    st.subheader("🎯 Risk Puanları")
    c3, c4 = st.columns(2)
    with c3:
        P3_val = st.number_input("P1 Puanı (P3)", value=1.0)
        Q3_val = st.number_input("P2 Puanı (Q3)", value=1.0)
    with c4:
        R3_val = st.number_input("P3 Puanı (R3)", value=1.0)
        S3_val = st.number_input("P4 Puanı (S3)", value=1.0)

# Hesaplama Motoru
karar, ikon, tri_sonuc = kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3_val, Q3_val, R3_val, S3_val)

# Sonuç Paneli
st.divider()
res_col1, res_col2, res_col3 = st.columns([2, 1, 1])

with res_col1:
    st.subheader("KARAR")
    st.header(f"{ikon} {karar}")

with res_col2:
    st.subheader("TRI PUANI")
    st.metric("T3 Hücresi", f"{tri_sonuc:.4f}")

with res_col3:
    st.subheader("HATA ORANI")
    hky = ((J3+K3+L3+M3) / G3) * 100
    st.metric("HKY %", f"%{hky:.2f}")

if karar == "SEVK EDİLEMEZ (RED)":
    st.error("DİKKAT: Toplam hata sevk miktarının %5'ini geçti veya kritik limitler aşıldı!")
