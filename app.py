import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. GENEL AYARLAR ---
st.set_page_config(page_title="Kurumsal Kayıp Zaman Motoru", layout="wide")

DOSYA_ADI = "kurumsal_takip_veritabani.xlsx"
KOLONLAR = [
    "Kayit_ID", "Şirket", "Referans_No", "Dönem_Yıl", "Dönem_Ay", "pH", "Miktar", 
    "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", "Onay_Veren", "Talep_Edilen_Saat",
    "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi",
    "Yonetici_Onay_Durumu", "Hakedis_Tutari", "Legrand_Kesinti_Tutari", "Kalite_Notu"
]
SAATLIK_BIRIM_FIYAT = 491

# --- 2. VERİTABANI FONKSİYONLARI ---
def baslangic_ayarlarini_yap():
    if not os.path.exists(DOSYA_ADI):
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl') as writer:
            pd.DataFrame(columns=KOLONLAR).to_excel(writer, sheet_name='Veriler', index=False)
            pd.DataFrame([{"anahtar": "admin_pass", "deger": "30052012"}]).to_excel(writer, sheet_name='Sistem', index=False)
    else:
        # Mevcut dosya varsa kolon kontrolü yap, silmeden güncelle
        df_mevcut = pd.read_excel(DOSYA_ADI, sheet_name='Veriler')
        eksik_kolonlar = [c for c in KOLONLAR if c not in df_mevcut.columns]
        if eksik_kolonlar:
            for c in eksik_kolonlar: df_mevcut[c] = "-"
            with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_mevcut.to_excel(writer, sheet_name='Veriler', index=False)

baslangic_ayarlarini_yap()

def veriyi_oku():
    return pd.read_excel(DOSYA_ADI, sheet_name='Veriler')

def veriyi_yaz(df):
    with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name='Veriler', index=False)
    return True

# --- 3. OTURUM YÖNETİMİ ---
if 'auth_role' not in st.session_state:
    st.session_state['auth_role'] = None # 'omer' veya 'patron'

def logout():
    st.session_state['auth_role'] = None
    st.rerun()

# --- 4. ARAYÜZ (SEKMELER) ---
tab_rework, tab_kalite, tab_patron = st.tabs(["🛠️ REWORK BİRİMİ", "🔍 KALİTE ONAYI (ÖMER)", "👑 PATRON PANELİ"])

# --- TAB 1: REWORK ---
with tab_rework:
    st.subheader("🛠️ Yeni Tamir/Rework Girişi")
    with st.form("rework_form"):
        c1, c2 = st.columns(2)
        with c1:
            sirket = st.selectbox("Şirket", ["Hakan Kalıp Plastik", "Alaşar"])
            ref = st.text_input("Referans / Parti No")
            yil = st.selectbox("Yıl", ["2024", "2025", "2026"], index=2)
            ay = st.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
        with c2:
            ph = st.number_input("pH (Hız)", min_value=0.1, value=7.0)
            miktar = st.number_input("Miktar", min_value=1, value=100)
            kesinti = st.number_input("Legrand Kesinti (TL)", value=0.0)
            neden = st.text_area("Hata Nedeni")
        
        if st.form_submit_button("🚀 Kalite Onayına Gönder"):
            df = veriyi_oku()
            saat = round(miktar / ph, 2)
            yeni_satir = {
                "Kayit_ID": f"RWK-{len(df)+1:04d}", "Şirket": sirket, "Referans_No": ref, "Dönem_Yıl": yil, "Dönem_Ay": ay,
                "pH": ph, "Miktar": miktar, "Kayıp_Zaman_Nedeni": neden, "Yapılacak_İşin_Tanımı": "Rework İşlemi",
                "Talep_Edilen_Saat": saat, "Hakedis_Tutari": saat * SAATLIK_BIRIM_FIYAT, "Legrand_Kesinti_Tutari": kesinti,
                "Son_Durum": "Kalite Onayı Bekliyor", "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            if veriyi_yaz(pd.concat([df, pd.DataFrame([yeni_satir])], ignore_index=True)):
                st.success("Kayıt başarıyla Kalite'ye iletildi."); st.rerun()

    st.markdown("---")
    st.write("### ⚠️ Reddedilen İşlemler (Revize Gerekli)")
    df_all = veriyi_oku()
    st.dataframe(df_all[df_all["Son_Durum"] == "Kalite Reddedildi"], use_container_width=True)

# --- TAB 2: KALİTE (ÖMER) ---
with tab_kalite:
    if st.session_state['auth_role'] != 'omer':
        st.subheader("🔍 Ömer Bey, Lütfen Giriş Yapın")
        u = st.text_input("Kullanıcı Adı", key="u_omer")
        p = st.text_input("Şifre", type="password", key="p_omer")
        if st.button("Giriş Yap", key="btn_omer"):
            if u == "omer" and p == "30052012":
                st.session_state['auth_role'] = 'omer'
                st.rerun()
            else: st.error("Hatalı Giriş!")
    else:
        st.sidebar.button("🚪 Ömer Bey (Çıkış)", on_click=logout)
        st.success("Hoşgeldiniz Ömer Bey. Onayınızı bekleyen işler aşağıdadır:")
        
        df_k = veriyi_oku()
        bekleyenler = df_k[df_k["Son_Durum"] == "Kalite Onayı Bekliyor"]
        
        if not bekleyenler.empty:
            secilen_id = st.selectbox("İşlem Seçin", bekleyenler["Kayit_ID"].tolist())
            detay = bekleyenler[bekleyenler["Kayit_ID"] == secilen_id].iloc[0]
            
            st.info(f"**Ref:** {detay['Referans_No']} | **Miktar:** {detay['Miktar']} | **Saat:** {detay['Talep_Edilen_Saat']}")
            notu = st.text_area("Kalite Notu / Red Gerekçesi")
            
            col_on, col_red = st.columns(2)
            if col_on.button("✅ ONAYLA", use_container_width=True):
                df_k.loc[df_k["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu"]] = ["Onaylandı", notu]
                veriyi_yaz(df_k); st.success("Onaylandı!"); st.rerun()
            if col_red.button("❌ REDDET", use_container_width=True):
                df_k.loc[df_k["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu"]] = ["Kalite Reddedildi", notu]
                veriyi_yaz(df_k); st.error("Rework birimine iade edildi!"); st.rerun()
        else: st.info("Onay bekleyen yeni kayıt yok.")

# --- TAB 3: PATRON ---
with tab_patron:
    if st.session_state['auth_role'] != 'patron':
        st.subheader("👑 Yönetici Girişi")
        u = st.text_input("Kullanıcı Adı", key="u_pat")
        p = st.text_input("Şifre", type="password", key="p_pat")
        if st.button("Sisteme Giriş", key="btn_pat"):
            if u == "patron" and p == "alasar1234":
                st.session_state['auth_role'] = 'patron'
                st.rerun()
            else: st.error("Yetkisiz Giriş!")
    else:
        st.sidebar.button("🚪 Patron (Çıkış)", on_click=logout)
        st.success("Güncel Finansal Durum")
        
        df_p = veriyi_oku()
        onayli = df_p[df_p["Son_Durum"] == "Onaylandı"]
        
        if not onayli.empty:
            brut = onayli["Hakedis_Tutari"].sum()
            kesinti = onayli["Legrand_Kesinti_Tutari"].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Onaylı Saat", f"{onayli['Talep_Edilen_Saat'].sum():,.2f}")
            m2.metric("Brüt Hakediş", f"{brut:,.2f} TL")
            m3.metric("Net Hakediş", f"{(brut - kesinti):,.2f} TL", delta=f"-{kesinti:,.2f} Kesinti")
            
            st.write("### 📋 Tüm Onaylı Liste")
            st.dataframe(onayli, use_container_width=True, hide_index=True)
            
            with st.expander("🛠️ Gelişmiş Ayarlar"):
                if st.button("⚠️ TÜM VERİLERİ SIFIRLA"):
                    if veriyi_yaz(pd.DataFrame(columns=KOLONLAR)): 
                        st.success("Sistem temizlendi."); st.rerun()
        else: st.info("Henüz onaylanmış nihai bir hakediş verisi yok.")
