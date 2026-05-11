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
        ek_ceza = (J3 * 0.03) + (K3 * 0.05) if (P3_p >= 4 or Q3_p >= 4 or (J3+K3) >= 4) else 0
        toplam_carpan = 1 + (ek_ceza + (L3 * 0.01) + (M3 * 0.005))
        T3 = max(temel_oran * toplam_carpan, toplam_hata / 20)

    red_mi = ( (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or (J3 + K3) >= 10 or 
               R3_p >= 4 or S3_p == 5 or T3 >= 5.0 or (F3 > 0 and toplam_hata > (F3 * 0.05)) )
    
    sartli_mi = False
    if not red_mi and toplam_hata > 0:
        sartli_mi = ( T3 > 1.7 or (J3 + K3) >= 6 or (L3 + M3) > 25 or
                     (P3_p >= 3 and Q3_p >= 3 and R3_p >= 3 and S3_p >= 3 and 
                      J3 >= 3 and K3 >= 3 and L3 >= 3 and M3 >= 3) )

    if red_mi: return "RED", "🔴", T3
    elif sartli_mi: return "SARI", "🟡", T3
    else: return "UYGUN", "🟢", T3

# --- 2. VERİ YÖNETİMİ ---
if 'denetim_gecmisi' not in st.session_state:
    st.session_state.denetim_gecmisi = pd.DataFrame(columns=[
        "Tarih", "Parti No", "Sevk", "Kontrol", "TRI", "Sistem Kararı", "Yönetici Kararı"
    ])

# --- 3. UI TASARIMI ---
st.set_page_config(page_title="Alasar Quality DB V3.4", layout="wide")
st.title("🛡️ Alasar Quality Engine V3.4 (Onay Mekanizması)")

with st.sidebar:
    st.header("📋 Denetim Girişi")
    parti_no = st.text_input("Parti / Lot Numarası", value="LOT-001")
    f3 = st.number_input("Toplam Sevk (F3)", value=10000)
    g3 = st.number_input("Kontrol Edilen (G3)", value=500)
    st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("⚠️ Hata Adetleri")
    j3 = st.number_input("P1 Adet", 0); k3 = st.number_input("P2 Adet", 0)
    l3 = st.number_input("P3 Adet", 0); m3 = st.number_input("P4 Adet", 0)
with col2:
    st.subheader("🎯 Risk Puanları")
    p3 = st.number_input("P1 Puan", 1.0); q3 = st.number_input("P2 Puan", 1.0)
    r3 = st.number_input("P3 Puan", 1.0); s3 = st.number_input("P4 Puan", 1.0)

# --- HESAPLAMA ---
karar, ikon, t3_skor = kalite_motoru_hesapla(f3, g3, j3, k3, l3, m3, p3, q3, r3, s3)
st.divider()

# --- BİLDİRİM VE ONAY PANELİ ---
final_karar_notu = "OTOMATİK ONAY"
can_save = True

if karar == "SARI":
    st.warning(f"⚠️ BİLDİRİM: {parti_no} Nolu Parti ŞARTLI KABUL Sınırında! Lütfen Karar Verin.")
    onay_col1, onay_col2 = st.columns(2)
    with onay_col1:
        if st.button("✅ ŞARTLI KABULÜ ONAYLA", use_container_width=True):
            st.session_state.admin_decision = "YÖNETİCİ ONAYLADI"
            st.success("Karar: ONAYLANDI")
    with onay_col2:
        if st.button("❌ ŞARTLI KABULÜ REDDET", use_container_width=True):
            st.session_state.admin_decision = "YÖNETİCİ REDDETTİ"
            st.error("Karar: REDDEDİLDİ")
    
    if 'admin_decision' not in st.session_state:
        st.info("Kayıt için onay veya red seçmelisiniz.")
        can_save = False
    else:
        final_karar_notu = st.session_state.admin_decision
elif karar == "RED":
    final_karar_notu = "SİSTEM REDDETTİ"
    st.error("🚫 BU PARTİ SEVK EDİLEMEZ!")

# --- KAYDET BUTONU ---
if st.button("💾 DENETİMİ LİSTEYE KAYDET", use_container_width=True, disabled=not can_save):
    yeni_veri = {
        "Tarih": datetime.now().strftime("%H:%M:%S"),
        "Parti No": parti_no, "Sevk": f3, "Kontrol": g3,
        "TRI": round(t3_skor, 4),
        "Sistem Kararı": f"{ikon} {karar}",
        "Yönetici Kararı": final_karar_notu
    }
    st.session_state.denetim_gecmisi = pd.concat([st.session_state.denetim_gecmisi, pd.DataFrame([yeni_veri])], ignore_index=True)
    if 'admin_decision' in st.session_state: del st.session_state.admin_decision # Sıfırlama
    st.toast("Kayıt Listeye Eklendi!")

# --- LİSTELEME ---
st.subheader("📜 Denetim ve Onay Geçmişi")
st.dataframe(st.session_state.denetim_gecmisi.iloc[::-1], use_container_width=True, hide_index=True)

csv = st.session_state.denetim_gecmisi.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 Raporu Excel Olarak İndir", csv, "kalite_onay_raporu.csv", "text/csv")
