import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Sayfa Genişlik Ayarı
st.set_page_config(page_title="Kurumsal Kayıp Zaman Motoru", layout="wide")

DOSYA_ADI = "kurumsal_takip_veritabani.xlsx"
KOLONLAR = [
    "Kayit_ID", "Şirket", "Referans_No", "Dönem_Yıl", "Dönem_Ay", "pH", "Miktar", 
    "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", "Onay_Veren", "Talep_Edilen_Saat",
    "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi",
    "Yonetici_Onay_Durumu", "Hakedis_Tutari", "Legrand_Kesinti_Tutari", "Kalite_Notu"
]

SAATLIK_BIRIM_FIYAT = 491  # TL

# --- EXCEL VE SİSTEM HAZIRLAMA ---
def baslangic_ayarlarini_yap():
    if not os.path.exists(DOSYA_ADI):
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl') as writer:
            pd.DataFrame(columns=KOLONLAR).to_excel(writer, sheet_name='Veriler', index=False)
            pd.DataFrame([{"anahtar": "admin_pass", "deger": "30052012"}]).to_excel(writer, sheet_name='Sistem', index=False)
    else:
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            try:
                df_check = pd.read_excel(DOSYA_ADI, sheet_name='Veriler')
                for col in KOLONLAR:
                    if col not in df_check.columns: df_check[col] = "-"
                df_check.to_excel(writer, sheet_name='Veriler', index=False)
            except: pd.DataFrame(columns=KOLONLAR).to_excel(writer, sheet_name='Veriler', index=False)

baslangic_ayarlarini_yap()

def veriyi_oku():
    try: return pd.read_excel(DOSYA_ADI, sheet_name='Veriler')
    except: return pd.DataFrame(columns=KOLONLAR)

def veriyi_yaz(df):
    try:
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name='Veriler', index=False)
        return True
    except: return False

# --- ANA SEKME YAPISI ---
tab_rework, tab_kalite, tab_patron = st.tabs(["🛠️ REWORK GİRİŞ", "🔍 KALİTE ONAYI", "👑 PATRON PANELİ"])

# --- 1. REWORK BÖLÜMÜ ---
with tab_rework:
    st.subheader("Tamir Edilen Ürün Veri Girişi")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            r_sirket = st.selectbox("Şirket", ["Hakan Kalıp Plastik", "Alaşar"], key="rew_sirket")
            r_ref = st.text_input("Referans / Parti No", key="rew_ref")
            r_yil = st.selectbox("Yıl", ["2024", "2025", "2026"], index=2)
            r_ay = st.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
        with col2:
            r_ph = st.number_input("pH (Tamir Hızı)", min_value=0.1, value=7.0)
            r_miktar = st.number_input("Tamir Edilen Miktar", min_value=1, value=100)
            r_kesinti = st.number_input("Legrand Kesinti (Varsa)", value=0.0)
            r_neden = st.text_area("Hata / Tamir Nedeni")
        
        if st.button("🚀 Veriyi Kalite Onayına Gönder", use_container_width=True):
            df_r = veriyi_oku()
            saat = round(r_miktar / r_ph, 2)
            yeni_satir = {
                "Kayit_ID": f"RWK-{len(df_r)+1:04d}", "Şirket": r_sirket, "Referans_No": r_ref, "Dönem_Yıl": r_yil, "Dönem_Ay": r_ay,
                "pH": r_ph, "Miktar": r_miktar, "Kayıp_Zaman_Nedeni": r_neden, "Yapılacak_İşin_Tanımı": "Rework/Tamir İşlemi",
                "Talep_Edilen_Saat": saat, "Hakedis_Tutari": saat * SAATLIK_BIRIM_FIYAT, "Legrand_Kesinti_Tutari": r_kesinti,
                "Son_Durum": "Kalite Onayı Bekliyor", "Yonetici_Onay_Durumu": "Beklemede", "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            if veriyi_yaz(pd.concat([df_r, pd.DataFrame([yeni_satir])], ignore_index=True)):
                st.success("Veri Kalite Yöneticisine gönderildi!"); st.rerun()

    # Reddedilenleri Göster
    st.markdown("### ⚠️ Reddedilen / Revize Bekleyenler")
    df_red = veriyi_oku()
    reddedilenler = df_red[df_red["Son_Durum"] == "Kalite Reddedildi"]
    if not reddedilenler.empty:
        st.warning("Aşağıdaki kayıtlar kalite tarafından reddedilmiştir. Lütfen düzenleyip tekrar gönderin.")
        st.dataframe(reddedilenler[["Kayit_ID", "Referans_No", "Kalite_Notu", "Güncelleme_Tarihi"]], use_container_width=True)

# --- 2. KALİTE YÖNETİCİSİ ---
with tab_kalite:
    st.subheader("🔍 Kalite Kontrol ve Onay Paneli")
    k_user = st.text_input("Kalite Kullanıcı Adı", key="k_u")
    k_pass = st.text_input("Kalite Şifre", type="password", key="k_p")
    
    if k_user == "kalite" and k_pass == "alasar_quality":
        df_k = veriyi_oku()
        onay_bekleyen = df_k[df_k["Son_Durum"] == "Kalite Onayı Bekliyor"]
        
        if not onay_bekleyen.empty:
            st.write(f"Şu an **{len(onay_bekleyen)}** adet onay bekleyen rework işlemi var.")
            secilen_rwk = st.selectbox("İncelemek için ID Seçin", onay_bekleyen["Kayit_ID"].tolist())
            detay = onay_bekleyen[onay_bekleyen["Kayit_ID"] == secilen_rwk].iloc[0]
            
            st.info(f"**Referans:** {detay['Referans_No']} | **Miktar:** {detay['Miktar']} | **Saat:** {detay['Talep_Edilen_Saat']}")
            k_notu = st.text_area("Kalite Notu / Red Nedeni", key="k_not")
            
            c1, c2 = st.columns(2)
            if c1.button("✅ ONAYLA (Nihai Tabloya Yaz)", use_container_width=True):
                df_k.loc[df_k["Kayit_ID"] == secilen_rwk, ["Son_Durum", "Kalite_Notu", "Yonetici_Onay_Durumu"]] = ["Onaylandı", k_notu, "Yöneticiye Gönderildi"]
                veriyi_yaz(df_k); st.success("Onaylandı!"); st.rerun()
            
            if c2.button("❌ REDDET (Rework'e Geri Gönder)", use_container_width=True):
                df_k.loc[df_k["Kayit_ID"] == secilen_rwk, ["Son_Durum", "Kalite_Notu"]] = ["Kalite Reddedildi", k_notu]
                veriyi_yaz(df_k); st.error("Reddedildi!"); st.rerun()
        else: st.info("Onay bekleyen kayıt bulunamadı.")

# --- 3. PATRON PANELİ ---
with tab_patron:
    st.subheader("👑 Üst Yönetim Finansal Takip")
    p_user = st.text_input("Yönetici Adı", key="p_u")
    p_pass = st.text_input("Şifre", type="password", key="p_p")
    
    if p_user == "patron" and p_pass == "alasar1234":
        df_p = veriyi_oku()
        # Patron sadece Kalite Onayından geçmiş "Nihai" verileri görür
        nihai_veriler = df_p[df_p["Son_Durum"] == "Onaylandı"]
        
        if not nihai_veriler.empty:
            hakedis = nihai_veriler["Hakedis_Tutari"].sum()
            kesinti = nihai_veriler["Legrand_Kesinti_Tutari"].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Onaylı Saat", f"{nihai_veriler['Talep_Edilen_Saat'].sum():,.2f}")
            m2.metric("Brüt Hakediş (TL)", f"{hakedis:,.2f} TL")
            m3.metric("Net Hakediş (TL)", f"{(hakedis - kesinti):,.2f} TL", delta=f"-{kesinti:,.2f} Kesinti")
            
            st.markdown("### 📋 Onaylı İşlemler Listesi")
            st.dataframe(nihai_veriler, use_container_width=True)
        else: st.info("Henüz onaylanmış nihai bir veri bulunmuyor.")
