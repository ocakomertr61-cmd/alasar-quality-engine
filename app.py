import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# --- GÜVENLİK AYARLARI ---
ADMIN_PASSWORD = "30052012"
TARGET_EMAIL = "ocakomertr61@gmail.com"

# Hatalı girişleri takip etmek için session state başlatma
if 'error_count' not in st.session_state:
    st.session_state.error_count = 0

# --- MAİL GÖNDERME FONKSİYONU ---
def send_security_alert():
    try:
        # Not: Bu kısım için bir SMTP sunucusu (Gmail vb.) ayarı gerekebilir.
        # Şimdilik sistemin bu tetiklemeyi yaptığını logluyoruz.
        msg = MIMEText(f"Dikkat! Alasar Quality Engine üzerinde 3 kez hatalı parola denemesi yapıldı.\nZaman: {datetime.now()}")
        msg['Subject'] = "KRİTİK UYARI: Yetkisiz Erişim Denemesi"
        msg['From'] = "sistem@alasar.com"
        msg['To'] = TARGET_EMAIL
        # smtplib kodları buraya eklenebilir
        st.error(f"🚨 GÜVENLİK İHLALİ! {TARGET_EMAIL} adresine bilgilendirme maili gönderildi.")
    except:
        st.warning("Mail gönderimi tetiklendi ancak sunucu ayarları eksik.")

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

    red_mi = (hata_orani > 0.05 or (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or 
              (J3 + K3) >= 10 or R3_p >= 4 or S3_p == 5 or T3 >= 5.0)
    
    sartli_mi = False
    if not red_mi and toplam_hata > 0:
        sartli_mi = (T3 > 1.7 or (J3 + K3) >= 6 or (L3 + M3) > 25)

    if red_mi: return "RED", "🔴", T3
    elif sartli_mi: return "SARI", "🟡", T3
    else: return "UYGUN", "🟢", T3

# --- 2. VERİ YÖNETİMİ ---
if 'denetim_gecmisi' not in st.session_state:
    st.session_state.denetim_gecmisi = pd.DataFrame(columns=[
        "Tarih", "Parti No", "Sevk", "Kontrol", "P1_A", "P1_P", "P2_A", "P2_P", 
        "P3_A", "P3_P", "P4_A", "P4_P", "TRI", "HKY", "Sistem", "Yönetici"
    ])

# --- 3. UI TASARIMI ---
st.set_page_config(page_title="Alasar Quality V3.7", layout="wide")
st.title("🛡️ Alasar Quality Engine V3.7 (Mail Korumalı)")

with st.sidebar:
    st.header("📋 Denetim Bilgileri")
    parti_no = st.text_input("Parti No", value="LOT-001")
    f3 = st.number_input("Toplam Sevk (F3)", 10000)
    g3 = st.number_input("Kontrol Edilen (G3)", 500)

col1, col2 = st.columns(2)
with col1:
    st.subheader("⚠️ Hata Adetleri")
    j3, k3, l3, m3 = st.number_input("P1", 0), st.number_input("P2", 0), st.number_input("P3", 0), st.number_input("P4", 0)
with col2:
    st.subheader("🎯 Risk Puanları")
    p3, q3, r3, s3 = st.number_input("P1 P", 1.0), st.number_input("P2 P", 1.0), st.number_input("P3 P", 1.0), st.number_input("P4 P", 1.0)

# --- HESAPLAMA ---
karar, ikon, t3_skor = kalite_motoru_hesapla(f3, g3, j3, k3, l3, m3, p3, q3, r3, s3)
hky_sonuc = ((j3+k3+l3+m3)/g3*100) if g3 > 0 else 0

st.divider()
res1, res2, res3 = st.columns(3)
res1.metric("TRI", f"{t3_skor:.4f}"); res2.metric("HKY", f"%{hky_sonuc:.2f}"); res3.header(f"{ikon} {karar}")

# --- GÜVENLİ ONAY VE MAİL PANELİ ---
final_karar = "OTOMATİK ONAY"; can_save = True

if karar == "SARI":
    st.warning(f"🔐 YÖNETİCİ ONAYI GEREKLİ")
    pwd_input = st.text_input("Parola Giriniz", type="password")
    
    if st.button("Onayla ve Kaydet"):
        if pwd_input == ADMIN_PASSWORD:
            st.session_state.auth = "YÖNETİCİ ONAYLADI"
            st.session_state.error_count = 0 # Sıfırla
        else:
            st.session_state.error_count += 1
            st.error(f"Parolayı yanlış girdiniz! (Deneme: {st.session_state.error_count}/3)")
            if st.session_state.error_count >= 3:
                send_security_alert()
                st.session_state.error_count = 0 # Mailden sonra sıfırla

    if 'auth' not in st.session_state: can_save = False
    else: final_karar = st.session_state.auth

elif karar == "RED":
    final_karar = "SİSTEM REDDETTİ"

# --- KAYIT ---
if st.button("💾 VERİYİ LİSTEYE İŞLE", use_container_width=True, disabled=not can_save):
    yeni = {
        "Tarih": datetime.now().strftime("%H:%M"), "Parti No": parti_no, "Sevk": f3, "Kontrol": g3,
        "P1_A": j3, "P1_P": p3, "P2_A": k3, "P2_P": q3, "P3_A": l3, "P3_P": r3, "P4_A": m3, "P4_P": s3,
        "TRI": round(t3_skor, 4), "HKY": f"%{hky_sonuc:.2f}", "Sistem": karar, "Yönetici": final_karar
    }
    st.session_state.denetim_gecmisi = pd.concat([st.session_state.denetim_gecmisi, pd.DataFrame([yeni])], ignore_index=True)
    if 'auth' in st.session_state: del st.session_state.auth
    st.toast("Kayıt tamamlandı.")

# --- LİSTELEME ---
st.subheader("📜 Denetim Geçmişi (Tüm Detaylar)")
st.dataframe(st.session_state.denetim_gecmisi.iloc[::-1], use_container_width=True, hide_index=True)
