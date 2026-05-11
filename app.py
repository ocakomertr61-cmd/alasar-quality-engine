import streamlit as st

# --- ÖMER BEY'İN EXCEL FORMÜLÜ BİREBİR UYARLAMASI ---
def kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3, Q3, R3, S3):
    # J3+K3+L3+M3 = Toplam Hata Adedi
    toplam_hata = J3 + K3 + L3 + M3
    
    # 1. TRI PUANI HESAPLAMA (Excel T3 Hücresi)
    if toplam_hata == 0:
        T3 = 0.0
    else:
        # Formülün ilk kısmı: ((P3*2)+(Q3*3)+(R3*2)+(S3*2))/15
        temel_oran = ((P3 * 2) + (Q3 * 3) + (R3 * 2) + (S3 * 2)) / 15
        
        # Formülün içindeki EĞER(VE(P3<4;Q3<4;(J3+K3)<4);0;J3*0,03+K3*0,05) kısmı
        if P3 < 4 and Q3 < 4 and (J3 + K3) < 4:
            kosullu_carpan = 0
        else:
            kosullu_carpan = (J3 * 0.03) + (K3 * 0.05)
        
        # Toplam çarpan yapısı: (1+(KOŞULLU + L3*0,01 + M3*0,005))
        toplam_carpan = 1 + (kosullu_carpan + (L3 * 0.01) + (M3 * 0.005))
        
        # MAK fonksiyonu: MAK(Temel_Oran * Çarpan ; Toplam_Hata / 20)
        deger_A = temel_oran * toplam_carpan
        deger_B = toplam_hata / 20
        T3 = max(deger_A, deger_B)

    # 2. KARAR MEKANİZMASI (Filtre Durumu)
    # RED Koşulu: YADA(R3>=4; S3=5; (J3+K3)>6; T3>=5; J3>=3; K3>=3; ToplamHata>(G3*0,05))
    red_mi = (
        R3 >= 4 or 
        S3 == 5 or 
        (J3 + K3) > 6 or 
        T3 >= 5 or 
        J3 >= 3 or 
        K3 >= 3 or 
        toplam_hata > (G3 * 0.05)
    )
    
    # SARI Koşulu: YADA(T3>1,7; (J3+K3)>=4; P3>=1; Q3>=1; (L3+M3)>25)
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
st.title("🛡️ Alasar Quality Engine V1.1")

# Sidebar - Hücre Adresleri ile Tanımlama
st.sidebar.header("Excel Hücre Değerleri")
G3 = st.sidebar.number_input("Toplam Kontrol Adedi (G3)", value=500)

st.subheader("⚠️ Hata Adetleri (Hücre J, K, L, M)")
col1, col2, col3, col4 = st.columns(4)
with col1: J3 = st.number_input("P1 Hata Adedi (J3)", value=0, step=1)
with col2: K3 = st.number_input("P2 Hata Adedi (K3)", value=0, step=1)
with col3: L3 = st.number_input("P3 Hata Adedi (L3)", value=0, step=1)
with col4: M3 = st.number_input("P4 Hata Adedi (M3)", value=0, step=1)

st.subheader("🎯 Risk Puanları (Hücre P, Q, R, S)")
col5, col6, col7, col8 = st.columns(4)
with col5: P3_val = st.number_input("P1 Risk Puanı (P3)", value=1.0)
with col6: Q3_val = st.number_input("P2 Risk Puanı (Q3)", value=1.0)
with col7: R3_val = st.number_input("P3 Risk Puanı (R3)", value=1.0)
with col8: S3_val = st.number_input("P4 Risk Puanı (S3)", value=1.0)

# Hesaplama
karar, ikon, tri_sonuc = kalite_motoru_hesapla(G3, J3, K3, L3, M3, P3_val, Q3_val, R3_val, S3_val)

# Sonuç Ekranı
st.divider()
c_res1, c_res2 = st.columns(2)
with c_res1:
    st.header(f"{ikon} {karar}")
with c_res2:
    st.metric("Hesaplanan TRI (T3)", f"{tri_sonuc:.4f}")

hky = ( (J3+K3+L3+M3) / G3) * 100
st.info(f"Mevcut Hata Oranı (HKY): %{hky:.2f}")
