import streamlit as st
import pandas as pd
from datetime import datetime

# --- YÖNETİCİ PAROLASI ---
ADMIN_PASSWORD = "1234"  # Burayı dilediğiniz bir şifre ile değiştirebilirsiniz

# --- 1. KALİTE MOTORU HESAPLAMA ---
def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    hata_orani = (toplam_hata / G3) if G3 > 0 else 0
    
    if toplam_hata == 0:
        T3 = 0.0
    else:
        temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
        ek_ceza = (J3 * 0.03) + (K3 * 0.05) if (P3_p >= 4 or Q3_p >= 4 or (J3+K3) >= 4) else 0
        toplam_carpan = 1 + (ek_ceza + (L3 * 0.01) + (M3 * 0.005))
        T3 = max(temel_oran * toplam_carpan, toplam_hata / 20)

    # RED (🔴) ŞARTLARI
    red_mi = (
        hata_orani > 0.05 or (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or 
        (J3 + K3) >= 10 or R3_p >= 4 or S3_p == 5 or T3 >= 5.0
    )
    
    # SARI (🟡) ŞARTLARI
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

# --- 2. VERİ YÖNETİMİ ---
if 'denetim_gecmisi' not in st.session_state:
    st.session_state.denetim_gecmisi = pd.DataFrame(columns=[
        "Tarih", "Parti No", "Sevk", "Kontrol", 
        "P1_A", "P1_P", "P2_A", "P2_P", "P3_A", "P3_P", "P4_A", "P4_P", 
        "TRI", "HKY", "Sistem Kararı", "Yönetici Kararı"
    ])

# --- 3. UI TASARIMI ---
st.set_page_config(page_title="Alasar Quality DB V3.6", layout="wide")
st.title("🛡️ Alasar Quality Engine V3.6 (Güvenli Onay)")

with st.sidebar:
    st.header("📋 Denetim Bilgileri")
    parti_no = st.text_input("Parti / Lot Numarası", value="LOT-001")
    f3 = st.number_input("Toplam Sevk (F3)", value=10000)
    g3 = st.number_input("Kontrol Edilen (G3)", value=500)

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
hky_sonuc = ((j3+k3+l3+m3)/g3*100) if g3 > 0 else 0

st.divider()
res1, res2, res3 = st.columns(3)
res1.metric("TRI (Risk Skoru)", f"{t3_skor:.4f}")
res2.metric("HKY (Hata Oranı)", f"%{hky_sonuc:.2f}")
res3.header(f"{ikon} {karar}")

# --- GÜVENLİ ONAY PANELİ ---
final_karar_notu = "OTOMATİK ONAY"
can_save = True

if karar == "SARI":
    st.warning(f"🔐 YÖNETİCİ ONAYI GEREKLİ: {parti_no}")
    pwd_input = st.text_input("Onay Parolası Giriniz", type="password")
    
    o1, o2 = st.columns(2)
    if o1.button("✅ ŞARTLI KABULÜ ONAYLA"):
        if pwd_input == ADMIN_PASSWORD:
            st.session_state.auth_status = "YÖNETİCİ ONAYLADI"
            st.success("Parola Doğru! Onaylandı.")
        else: st.error("Hatalı Parola!")
    
    if o2.button("❌ ŞARTLI KABULÜ REDDET"):
        if pwd_input == ADMIN_PASSWORD:
            st.session_state.auth_status = "YÖNETİCİ REDDETTİ"
            st.error("Parola Doğru! Reddedildi.")
        else: st.error("Hatalı Parola!")

    if 'auth_status' not in st.session_state:
        can_save = False
    else: final_karar_notu = st.session_state.auth_status

elif karar == "RED":
    final_karar_notu = "SİSTEM REDDETTİ"
    if hky_sonuc > 5: st.error("❌ HATA ORANI %5'İ GEÇTİ!")

# --- KAYDETME (Puanlar ve Adetler Dahil) ---
if st.button("💾 DENETİMİ LİSTEYE KAYDET", use_container_width=True, disabled=not can_save):
    yeni_veri = {
        "Tarih": datetime.now().strftime("%H:%M:%S"),
        "Parti No": parti_no, "Sevk": f3, "Kontrol": g3,
        "P1_A": j3, "P1_P": p3, "P2_A": k3, "P2_P": q3,
        "P3_A": l3, "P3_P": r3, "P4_A": m3, "P4_P": s3,
        "TRI": round(t3_skor, 4), "HKY": f"%{hky_sonuc:.2f}",
        "Sistem Kararı": f"{ikon} {karar}",
        "Yönetici Kararı": final_karar_notu
    }
    st.session_state.denetim_gecmisi = pd.concat([st.session_state.denetim_gecmisi, pd.DataFrame([yeni_veri])], ignore_index=True)
    if 'auth_status' in st.session_state: del st.session_state.auth_status
    st.toast("Detaylı kayıt eklendi!")

# --- LİSTELEME ---
st.subheader("📜 Detaylı Denetim ve Onay Geçmişi")
st.dataframe(st.session_state.denetim_gecmisi.iloc[::-1], use_container_width=True, hide_index=True)

csv = st.session_state.denetim_gecmisi.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 Excel İndir", csv, "alasar_final_rapor.csv", "text/csv")
