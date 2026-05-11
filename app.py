import streamlit as st

def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3, Q3, R3, S3):
    # I3 Hücresi (Toplam Hata)
    toplam_hatali = J3 + K3 + L3 + M3
    
    # 1. TRI PUANI HESAPLAMA (T3 Hücresi)
    if toplam_hatali == 0:
        T3 = 0.0
    else:
        # Puanlama: ((P3*2)+(Q3*3)+(R3*2)+(S3*2))/15
        temel_risk = ((P3 * 2) + (Q3 * 3) + (R3 * 2) + (S3 * 2)) / 15
        
        # EĞER(VE(P3<4;Q3<4;(J3+K3)<4);0;J3*0,03+K3*0,05)
        if P3 < 4 and Q3 < 4 and (J3 + K3) < 4:
            ek_carpan = 0
        else:
            ek_carpan = (J3 * 0.03) + (K3 * 0.05)
            
        # (1+(EK_CARPAN + L3*0,01 + M3*0,005))
        ana_carpan = 1 + (ek_carpan + (L3 * 0.01) + (M3 * 0.005))
        
        # T3 = MAK(Temel_Risk * Ana_Carpan ; Toplam_Hatali / 20)
        T3 = max(temel_risk * ana_carpan, toplam_hatali / 20)

    # 2. KARAR MEKANİZMASI (Filtre Durumu)
    # RED Koşulu: YADA(R3>=4; S3=5; (J3+K3)>6; T3>=5; J3>=3; K3>=3; I3>(F3*0,05))
    red_mi = (
        R3 >= 4 or 
        S3 == 5 or 
        (J3 + K3) > 6 or 
        T3 >= 5 or 
        J3 >= 3 or 
        K3 >= 3 or 
        toplam_hatali > (F3 * 0.05)
    )
    
    # SARI Koşulu: YADA(T3>1,7; (J3+K3)>=4; P3>=1; Q3>=1; (L3+M3)>25)
    # NOT: 0 hatada sarı yanmaması için toplam_hatali > 0 kontrolü eklendi.
    sartli_mi = (
        toplam_hatali > 0 and (
            T3 > 1.7 or 
            (J3 + K3) >= 4 or 
            P3 >= 1 or 
            Q3 >= 1 or 
            (L3 + M3) > 25
        )
    )

    if red_mi:
        return "SEVK EDİLEMEZ (RED)", "🔴", T3
    elif sartli_mi:
        return "ŞARTLI KABUL (ONAY GEREKLİ)", "🟡", T3
    else:
        return "UYGUN (OTOMATİK ONAY)", "🟢", T3

# --- ARAYÜZ (TAMAMEN EXCEL GÖRÜNÜMÜ) ---
st.set_page_config(page_title="Alasar Quality Engine V1.5", layout="wide")
st.title("🛡️ Alasar Quality Engine V1.5")

col_params, col_errors, col_risks = st.columns(3)

with col_params:
    st.subheader("📊 Sevkiyat")
    F3 = st.number_input("Toplam Sevk (F3)", value=5500)
    G3 = st.number_input("Kontrol Edilen (G3)", value=550)

with col_errors:
    st.subheader("⚠️ Hata Adetleri")
    J3 = st.number_input("P1 Adet (J3)", value=0)
    K3 = st.number_input("P2 Adet (K3)", value=0)
    L3 = st.number_input("P3 Adet (L3)", value=0)
    M3 = st.number_input("P4 Adet (M3)", value=0)

with col_risks:
    st.subheader("🎯 Risk Katsayıları")
    P3 = st.number_input("P1 Katsayı (P3)", value=0.0)
    Q3 = st.number_input("P2 Katsayı (Q3)", value=0.0)
    R3 = st.number_input("P3 Katsayı (R3)", value=0.0)
    S3 = st.number_input("P4 Katsayı (S3)", value=0.0)

karar, ikon, t3_sonuc = kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3, Q3, R3, S3)

st.divider()
st.header(f"{ikon} {karar}")
st.metric("TRI PUANI (T3)", f"{t3_sonuc:.4f}")
