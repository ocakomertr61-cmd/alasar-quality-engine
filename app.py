import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. KALİTE MOTORU HESAPLAMA ---
def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
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

    red_mi = (
        (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or 
        (J3 + K3) >= 10 or R3_p >= 4 or S3_p == 5 or T3 >= 5.0 or 
        (F3 > 0 and toplam_hata > (F3 * 0.05))
    )
    
    sartli_mi = False
    if not red_mi and toplam_hata > 0:
        sartli_mi = (
            T3 > 1.7 or (J3 + K3) >= 6 or (L3 + M3) > 25 or
            (P3_p >= 3 and Q3_p >= 3 and R3_p >= 3 and S3_p >= 3 and 
             J3 >= 3 and K3 >= 3 and L3 >= 3 and M3 >= 3)
        )

    if red_mi: return "RED", "🔴", T3
    elif sartli_mi: return "SARI", "🟡", T3
    else: return "UYGUN", "🟢", T3

# --- 2. VERİ YÖNETİMİ (Sütunlar Temizlendi) ---
if 'denetim_gecmisi' not in st.session_state:
    st.session_state.denetim_gecmisi = pd.DataFrame(columns=[
        "Tarih", "Parti No", "Sevk", "Kontrol", 
        "P1_Adet", "P1_Puan", "P2_Adet", "P2_Puan", 
        "P3_Adet", "P3_Puan", "P4_Adet", "P4_Puan", 
        "TRI", "Karar"
    ])

# --- 3. UI TASARIMI ---
st.set_page_config(page_title="Alasar Quality DB V3.3", layout="wide")
st.title("🛡️ Alasar Quality Engine V3.3 (Temiz Kayıt)")

with st.sidebar:
    st.header("📋 Denetim Girişi")
    parti_no = st.text_input("Parti / Lot Numarası", value="LOT-001")
    f3 = st.number_input("Toplam Sevk (F3)", value=10000)
    g3 = st.number_input("Kontrol Edilen (G3)", value=500)
    st.divider()
    if st.button("💾 DENETİMİ KAYDET", use_container_width=True):
        # Hesaplamayı burada tekrar yapıp kaydediyoruz
        res_karar, res_ikon, res_t3 = kalite_motoru_hesapla(f3, g3, 0, 0, 0, 0, 1.0, 1.0, 1.0, 1.0) # Dummy call for logic
        # Gerçek değerleri UI'dan alıyoruz (aşağıdaki değişkenler)
        yeni_veri = {
            "Tarih": datetime.now().strftime("%H:%M:%S"),
            "Parti No": parti_no,
            "Sevk": f3, "Kontrol": g3,
            "P1_Adet": st.session_state.j3_val, "P1_Puan": st.session_state.p3_val,
            "P2_Adet": st.session_state.k3_val, "P2_Puan": st.session_state.q3_val,
            "P3_Adet": st.session_state.l3_val, "P3_Puan": st.session_state.r3_val,
            "P4_Adet": st.session_state.m3_val, "P4_Puan": st.session_state.s3_val,
            "TRI": round(st.session_state.current_t3, 4),
            "Karar": f"{st.session_state.current_ikon} {st.session_state.current_karar}"
        }
        st.session_state.denetim_gecmisi = pd.concat([st.session_state.denetim_gecmisi, pd.DataFrame([yeni_veri])], ignore_index=True)
        st.toast("Kayıt Başarılı!", icon="✅")

col1, col2 = st.columns(2)
with col1:
    st.subheader("⚠️ Hata Adetleri")
    j3 = st.number_input("P1 Adet", value=0, key="j3_val")
    k3 = st.number_input("P2 Adet", value=0, key="k3_val")
    l3 = st.number_input("P3 Adet", value=0, key="l3_val")
    m3 = st.number_input("P4 Adet", value=0, key="m3_val")

with col2:
    st.subheader("🎯 Risk Puanları")
    p3 = st.number_input("P1 Puan", value=1.0, key="p3_val")
    q3 = st.number_input("P2 Puan", value=1.0, key="q3_val")
    r3 = st.number_input("P3 Puan", value=1.0, key="r3_val")
    s3 = st.number_input("P4 Puan", value=1.0, key="s3_val")

# --- HESAPLAMA VE DURUM SAKLAMA ---
karar, ikon, t3_skor = kalite_motoru_hesapla(f3, g3, j3, k3, l3, m3, p3, q3, r3, s3)
st.session_state.current_karar = karar
st.session_state.current_ikon = ikon
st.session_state.current_t3 = t3_skor

st.divider()
res1, res2, res3 = st.columns(3)
res1.metric("TRI (Risk Skoru)", f"{t3_skor:.4f}")
res2.metric("HKY (Hata Oranı)", f"%{((j3+k3+l3+m3)/g3*100) if g3 > 0 else 0:.2f}")
res3.header(f"{ikon} {karar}")

# --- LİSTELEME ---
st.subheader("📜 Denetim Geçmişi")
if not st.session_state.denetim_gecmisi.empty:
    st.dataframe(st.session_state.denetim_gecmisi.iloc[::-1], use_container_width=True, hide_index=True)
    
    c_del, c_exp = st.columns([1, 4])
    with c_del:
        if st.button("🗑️ Temizle"):
            st.session_state.denetim_gecmisi = st.session_state.denetim_gecmisi.iloc[0:0]
            st.rerun()
    with c_exp:
        csv = st.session_state.denetim_gecmisi.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Excel İndir", csv, "denetim_raporu.csv", "text/csv")
else:
    st.info("Kayıtlı veri yok.")
