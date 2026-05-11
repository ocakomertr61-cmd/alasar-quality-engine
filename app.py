import streamlit as st

# --- ÖMER BEY'İN EXCEL FORMÜLÜNE GÖRE KALİTE MOTORU ---
def kalite_motoru_hesapla(g3, j3, k3, l3, m3, p3, q3, r3, s3):
    # g3: Kontrol Adedi, j3-m3: Hata Adetleri, p3-s3: Risk Puanları
    toplam_hatali = j3 + k3 + l3 + m3
    
    # 1. TRI PUANI HESAPLAMA (T3 Hücresi Formülü)
    if toplam_hatali == 0:
        t3 = 0.0
    else:
        # Formülün ilk kısmı: Ağırlıklı ortalamanın 15'e bölümü
        temel_risk = ((p3 * 2) + (q3 * 3) + (r3 * 2) + (s3 * 2)) / 15
        
        # Formülün çarpan kısmı (EĞER(VE(P3<4;Q3<4;(J3+K3)<4);0;...))
        if p3 < 4 and q3 < 4 and (j3 + k3) < 4:
            carpan_ici = 0
        else:
            carpan_ici = (j3 * 0.03) + (k3 * 0.05)
            
        carpan = 1 + (carpan_ici + (l3 * 0.01) + (m3 * 0.005))
        
        # MAK Fonksiyonu: İki değerden büyük olanı seçer
        deger1 = temel_risk * carpan
        deger2 = toplam_hatali / 20
        t3 = max(deger1, deger2)

    # 2. KARAR MEKANİZMASI (Filtre Durumu Formülü)
    h3 = (toplam_hatali / g3) * 100 if g3 > 0 else 0 # HKY
    
    # SEVK EDİLEMEZ (RED) Koşulları
    red_mi = (
        r3 >= 4 or 
        s3 == 5 or 
        (j3 + k3) > 6 or 
        t3 >= 5 or 
        j3 >= 3 or 
        k3 >= 3 or 
        toplam_hatali > (g3 * 0.05)
    )
    
    # ŞARTLI KABUL Koşulları
    sartli_mi = (
        t3 > 1.7 or 
        (j3 + k3) >= 4 or 
        p3 >= 1 or 
        q3 >= 1 or 
        (l3 + m3) > 25
    )

    if red_mi:
        return "SEVK EDİLEMEZ (RED)", "🔴", t3, h3
    elif sartli_mi:
        return "ŞARTLI KABUL (ONAY GEREKLİ)", "🟡", t3, h3
    else:
        return "UYGUN (OTOMATİK ONAY)", "🟢", t3, h3

# --- STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="Alasar Quality Engine", layout="wide")
st.title("🛡️ Alasar Quality Engine V1.0")
st.sidebar.info("Ömer Bey'in Excel Formülleriyle Güncellenmiştir.")

col_main, col_res = st.columns([2, 1])

with col_main:
    st.subheader("📦 Sevkiyat Verileri")
    g3 = st.number_input("Kontrol Edilen Toplam Adet (G3)", min_value=1, value=500)
    
    st.subheader("⚠️ Hata Adetleri")
    c1, c2, c3, c4 = st.columns(4)
    with c1: j3 = st.number_input("P1 (Kritik) Adet (J3)", min_value=0, step=1)
    with c2: k3 = st.number_input("P2 (Majör) Adet (K3)", min_value=0, step=1)
    with c3: l3 = st.number_input("P3 (Minör) Adet (L3)", min_value=0, step=1)
    with c4: m3 = st.number_input("P4 (Hafif) Adet (M3)", min_value=0, step=1)

    st.subheader("🎯 Hata Risk Puanları")
    r1, r2, r3, r4 = st.columns(4)
    with r1: p3 = st.number_input("P1 Risk Puanı (P3)", value=1.0)
    with r2: q3 = st.number_input("P2 Risk Puanı (Q3)", value=1.0)
    with r3: r3_val = st.number_input("P3 Risk Puanı (R3)", value=1.0)
    with r4: s3 = st.number_input("P4 Risk Puanı (S3)", value=1.0)

karar, ikon, tri, hky = kalite_motoru_hesapla(g3, j3, k3, l3, m3, p3, q3, r3_val, s3)

with col_res:
    st.subheader("📊 Analiz Sonucu")
    st.header(f"{ikon} {karar}")
    st.write("---")
    st.metric("TRI (Risk İndeksi)", f"{tri:.3f}")
    st.metric("HKY (Hata Oranı)", f"%{hky:.2f}")
    
    if red_mi := (karar == "SEVK EDİLEMEZ (RED)"):
        st.error("DİKKAT: Kritik sınırlar aşıldı!")
