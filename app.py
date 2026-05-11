import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. KALİTE MOTORU HESAPLAMA (V2.5 Kuralları) ---
def kalite_motoru_hesapla(F3, G3, J3, K3, L3, M3, P3_p, Q3_p, R3_p, S3_p):
    toplam_hata = J3 + K3 + L3 + M3
    if toplam_hata == 0:
        T3 = 0.0
    else:
        # Ağırlıklı Temel Oran (Payda: 15)
        temel_oran = ((P3_p * 2) + (Q3_p * 3) + (R3_p * 2) + (S3_p * 2)) / 15
        
        # Yoğunluk Cezası
        if P3_p < 4 and Q3_p < 4 and (J3 + K3) < 4:
            ek_ceza = 0
        else:
            ek_ceza = (J3 * 0.03) + (K3 * 0.05)
        
        toplam_carpan = 1 + (ek_ceza + (L3 * 0.01) + (M3 * 0.005))
        T3 = max(temel_oran * toplam_carpan, toplam_hata / 20)

    # RED FİLTRELERİ
    red_mi = (
        (J3 >= 3 and P3_p >= 3) or (K3 >= 3 and Q3_p >= 3) or 
        (J3 + K3) >= 10 or R3_p >= 4 or S3_p == 5 or T3 >= 5.0 or 
        (F3 > 0 and toplam_hata > (F3 * 0.05))
    )
    
    # SARI FİLTRELERİ
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

# --- 2. VERİ YÖNETİMİ (Session State) ---
if 'denetim_gecmisi' not in st.session_state:
    st.session_state.denetim_gecmisi = pd.DataFrame(columns=[
        "Tarih", "Parti No", "Sevk", "Kontrol", "P1", "P2", "P3", "P4", "TRI", "Karar"
    ])

# --- 3. UI TASARIMI ---
st.set_page_config(page_title="Alasar Quality DB V3.1", layout="wide")
st.title("📊 Alasar Quality Engine V3.1 (Kayıt + Analiz)")

with st.sidebar:
    st.header("📋 Denetim Bilgileri")
    parti_no = st.text_input("Parti / Lot Numarası", value="LOT-001")
    f3 = st.number_input("Toplam Sevk (F3)", value=10000)
    g3 = st.number_input("Kontrol Edilen (G3)", value=500)
    st.divider()
    save_button = st.button("💾 DENETİMİ LİSTEYE EKLE", use_container_width=True)

# Giriş Alanları
col1, col2 = st.columns(2)
with col1:
    st.subheader("⚠️ Hata Adetleri")
    j3 = st.number_input("P1 (Fonksiyonel) Adet", value=0, min_value=0)
    k3 = st.number_input("P2 (Güvenlik) Adet", value=0, min_value=0)
    l3 = st.number_input("P3 (Montaj) Adet", value=0, min_value=0)
    m3 = st.number_input("P4 (Görsel) Adet", value=0, min_value=0)

with col2:
    st.subheader("🎯 Risk Puanları")
    p3 = st.number_input("P1 Puan", value=1.0, min_value=0.0, max_value=5.0)
    q3 = st.number_input("P2 Puan", value=1.0, min_value=0.0, max_value=5.0)
    r3 = st.number_input("P3 Puan", value=1.0, min_value=0.0, max_value=5.0)
    s3 = st.number_input("P4 Puan", value=1.0, min_value=0.0, max_value=5.0)

# --- HESAPLAMA VE CANLI SONUÇ EKRANI ---
karar, ikon, t3_skor = kalite_motoru_hesapla(f3, g3, j3, k3, l3, m3, p3, q3, r3, s3)
hky = ((j3+k3+l3+m3)/g3*100) if g3 > 0 else 0

st.divider()
# Burada TRI ve KARAR'ı görünür kılıyoruz:
res1, res2, res3 = st.columns(3)
with res1:
    st.metric("TRI (Risk Skoru)", f"{t3_skor:.4f}")
with res2:
    st.metric("HKY (Hata Oranı)", f"%{hky:.2f}")
with res3:
    st.subheader("Anlık Karar")
    st.header(f"{ikon} {karar}")

# --- KAYIT MANTIĞI ---
if save_button:
    yeni_veri = {
        "Tarih": datetime.now().strftime("%H:%M:%S"),
        "Parti No": parti_no,
        "Sevk": f3, "Kontrol": g3,
        "P1": j3, "P2": k3, "P3": l3, "P4": m3,
        "TRI": round(t3_skor, 4),
        "Karar": f"{ikon} {karar}"
    }
    st.session_state.denetim_gecmisi = pd.concat([st.session_state.denetim_gecmisi, pd.DataFrame([yeni_veri])], ignore_index=True)
    st.toast(f"{parti_no} listeye eklendi!", icon="💾")

# --- LİSTELEME VE YÖNETİM ---
st.divider()
st.subheader("📜 Denetim Geçmişi")

if not st.session_state.denetim_gecmisi.empty:
    # Tabloyu göster (En son kayıt en üstte görünsün diye ters çeviriyoruz)
    st.table(st.session_state.denetim_gecmisi.iloc[::-1])
    
    c_del, c_exp = st.columns([1, 4])
    with c_del:
        if st.button("🗑️ Tümünü Sil"):
            st.session_state.denetim_gecmisi = st.session_state.denetim_gecmisi.iloc[0:0]
            st.rerun()
    with c_exp:
        csv = st.session_state.denetim_gecmisi.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Excel/CSV Olarak İndir", csv, "kalite_denetim.csv", "text/csv")
else:
    st.info("Henüz kayıtlı veri yok.")
