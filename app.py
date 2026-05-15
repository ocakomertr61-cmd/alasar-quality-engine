import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. GENEL AYARLAR ---
st.set_page_config(page_title="Kurumsal Kayıp Zaman Motoru", layout="wide")

DOSYA_ADI = "kurumsal_takip_veritabani.xlsx"
# Ana tablo yapısını koruyoruz (İrsaliye No eklendi)
KOLONLAR = [
    "Kayit_ID", "Şirket", "İrsaliye_No", "Referans_No", "Dönem_Yıl", "Dönem_Ay", "pH", "Miktar", 
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
    st.session_state['auth_role'] = None

def logout():
    st.session_state['auth_role'] = None
    st.rerun()

# --- 4. ARAYÜZ (SEKMELER) ---
tab_ana_tablo, tab_rework, tab_kalite, tab_patron = st.tabs(["📊 ANA TABLO", "🛠️ REWORK GİRİŞİ", "🔍 KALİTE & MUTABAKAT", "👑 PATRON PANELİ"])

# --- TAB 0: ANA TABLO (Senin Takip Ettiğin Liste) ---
with tab_ana_tablo:
    st.subheader("📊 Müşteri Kayıp Zaman Takip Ana Tablosu")
    df_ana = veriyi_oku()
    st.dataframe(df_ana, use_container_width=True, hide_index=True)

# --- TAB 1: REWORK ---
with tab_rework:
    st.subheader("🛠️ Rework Birimi Veri İşleme")
    with st.form("rework_form"):
        c1, c2 = st.columns(2)
        with c1:
            irsaliye = st.text_input("İrsaliye No")
            ref = st.text_input("Referans No")
            tamir_aciklama = st.text_area("Tamir Açıklaması")
        with c2:
            ph = st.number_input("pH (Hız)", min_value=0.1, value=7.0)
            miktar = st.number_input("Miktar", min_value=1, value=1)
            yil = st.selectbox("Yıl", ["2024", "2025", "2026"], index=2)
            ay = st.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])

        if st.form_submit_button("💾 Ana Tabloya İşle / Eşleştir"):
            df = veriyi_oku()
            saat = round(miktar / ph, 2)
            
            # Eşleştirme Mantığı: İrsaliye veya Referans No var mı?
            mask = (df["İrsaliye_No"].astype(str) == str(irsaliye)) | (df["Referans_No"].astype(str) == str(ref))
            
            if mask.any():
                # Mevcut kaydı güncelle
                df.loc[mask, ["pH", "Miktar", "Talep_Edilen_Saat", "Hakedis_Tutari", "Kayıp_Zaman_Nedeni", "Son_Durum", "Güncelleme_Tarihi"]] = [
                    ph, miktar, saat, saat * SAATLIK_BIRIM_FIYAT, tamir_aciklama, "Beklemede (İç Kayıt)", datetime.now().strftime("%Y-%m-%d %H:%M")
                ]
                st.info("Mevcut kayıt bulundu ve güncellendi.")
            else:
                # Yeni kayıt aç
                yeni_satir = {
                    "Kayit_ID": f"RWK-{len(df)+1:04d}", "İrsaliye_No": irsaliye, "Referans_No": ref, "Dönem_Yıl": yil, "Dönem_Ay": ay,
                    "pH": ph, "Miktar": miktar, "Kayıp_Zaman_Nedeni": tamir_aciklama, "Yapılacak_İşin_Tanımı": "Rework İşlemi",
                    "Talep_Edilen_Saat": saat, "Hakedis_Tutari": saat * SAATLIK_BIRIM_FIYAT, "Son_Durum": "Beklemede (İç Kayıt)", 
                    "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                df = pd.concat([df, pd.DataFrame([yeni_satir])], ignore_index=True)
                st.success("Yeni kayıt ana tabloya eklendi.")
            
            veriyi_yaz(df)
            st.rerun()

# --- TAB 2: KALİTE (ÖMER) ---
with tab_kalite:
    if st.session_state['auth_role'] != 'omer':
        st.subheader("🔍 Ömer Bey Girişi")
        u = st.text_input("Kullanıcı Adı", key="u_omer")
        p = st.text_input("Şifre", type="password", key="p_omer")
        if st.button("Giriş Yap", key="btn_omer"):
            if u == "omer" and p == "30052012":
                st.session_state['auth_role'] = 'omer'
                st.rerun()
            else: st.error("Hatalı Giriş!")
    else:
        st.sidebar.button("🚪 Ömer Bey (Çıkış)", on_click=logout)
        df_k = veriyi_oku()
        
        st.markdown("### 📋 1. Taslak / İç Kayıtlar (Eşleşen Veriler)")
        taslaklar = df_k[df_k["Son_Durum"] == "Beklemede (İç Kayıt)"]
        st.dataframe(taslaklar, use_container_width=True)
        
        if not taslaklar.empty:
            secilen_id = st.selectbox("İşlem Seçin", taslaklar["Kayit_ID"].tolist(), key="k_sec")
            notu = st.text_area("Kalite Notu / İnceleme Notu")
            
            c1, c2 = st.columns(2)
            if c1.button("✅ MUTABAKATA HAZIR", use_container_width=True):
                df_k.loc[df_k["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu"]] = ["Mutabakat Bekliyor", notu]
                veriyi_yaz(df_k); st.rerun()
            if c2.button("❌ REDDET", use_container_width=True):
                df_k.loc[df_k["Kayit_ID"] == secilen_id, "Son_Durum"] = "Kalite Reddedildi"
                veriyi_yaz(df_k); st.rerun()

        st.markdown("---")
        st.markdown("### 📊 2. Raporu Gönder (Müşteri ile Kesinleşmiş)")
        mutabakat = df_k[df_k["Son_Durum"] == "Mutabakat Bekliyor"]
        st.dataframe(mutabakat, use_container_width=True)
        
        if not mutabakat.empty:
            if st.button("📢 RAPORU YÖNETİCİYE GÖNDER", use_container_width=True, type="primary"):
                df_k.loc[df_k["Son_Durum"] == "Mutabakat Bekliyor", "Son_Durum"] = "Onaylandı"
                veriyi_yaz(df_k); st.success("Kesinleşmiş rapor iletildi!"); st.rerun()

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
        df_p = veriyi_oku()
        kesin_liste = df_p[df_p["Son_Durum"] == "Onaylandı"]
        
        if not kesin_liste.empty:
            brut = kesin_liste["Hakedis_Tutari"].sum()
            kesinti = kesin_liste["Legrand_Kesinti_Tutari"].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Onaylı Saat", f"{kesin_liste['Talep_Edilen_Saat'].sum():,.2f}")
            m2.metric("Brüt Hakediş", f"{brut:,.2f} TL")
            m3.metric("Net Hakediş", f"{(brut - kesinti):,.2f} TL")
            st.dataframe(kesin_liste, use_container_width=True, hide_index=True)
        else: st.info("Henüz kesinleşmiş rapor yok.")
