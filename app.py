import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- 1. GENEL AYARLAR ---
st.set_page_config(page_title="Alaşar Kurumsal Takip", layout="wide")

DOSYA_ADI = "kurumsal_takip_veritabani.xlsx"
KOLONLAR = [
    "Kayit_ID", "Şirket", "İrsaliye_No", "Referans_No", "Dönem_Yıl", "Dönem_Ay", "pH", "Miktar", 
    "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", "Onay_Veren", "Talep_Edilen_Saat",
    "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi",
    "Yonetici_Onay_Durumu", "Hakedis_Tutari", "Legrand_Kesinti_Tutari", "Kalite_Notu",
    "Veri_Kaynagi"
]
SAATLIK_BIRIM_FIYAT = 491

# --- 2. VERİTABANI FONKSİYONLARI ---
def baslangic_ayarlarini_yap():
    if not os.path.exists(DOSYA_ADI):
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl') as writer:
            pd.DataFrame(columns=KOLONLAR).to_excel(writer, sheet_name='Veriler', index=False)
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

# --- 3. OTURUM VE KARŞILAMA ---
if 'auth_role' not in st.session_state:
    st.session_state['auth_role'] = None
if 'intro_done' not in st.session_state:
    st.session_state['intro_done'] = False

def logout():
    st.session_state['auth_role'] = None
    st.rerun()

# --- 4. HOŞGELDİN (Intro) ---
if not st.session_state['intro_done']:
    st.markdown('<div style="text-align:center; margin-top:150px;"><h1 style="color:#2E86C1; font-size:60px;">Hoşgeldiniz Sevgili Alaşar Ailesi</h1></div>', unsafe_allow_html=True)
    st.balloons()
    time.sleep(1.5)
    st.session_state['intro_done'] = True
    st.rerun()

# --- 5. GİRİŞ PANELİ ---
if st.session_state['auth_role'] is None:
    st.title("🛡️ Alaşar Kalite & Finansal Takip")
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.expander("🛠️ REWORK BİRİMİ"):
            if st.button("Rework Girişi", key="btn_rew"): st.session_state['auth_role'] = 'rework'; st.rerun()
    with col2:
        with st.expander("🔍 KALİTE (ÖMER BEY)"):
            u_o = st.text_input("Kullanıcı", key="u_o")
            p_o = st.text_input("Şifre", type="password", key="p_o")
            if st.button("Ömer Bey Girişi"):
                if u_o == "omer" and p_o == "30052012": st.session_state['auth_role'] = 'omer'; st.rerun()
    with col3:
        with st.expander("👑 YÖNETİCİ (PATRON)"):
            if st.button("Patron Girişi", key="btn_pat"): st.session_state['auth_role'] = 'patron'; st.rerun()

# --- 6. PANELLER ---
else:
    st.sidebar.title(f"👤 {st.session_state['auth_role'].upper()}")
    st.sidebar.button("🚪 Çıkış", on_click=logout)

    # --- ÖMER BEY PANELİ (GÜNCELLENEN KISIM) ---
    if st.session_state['auth_role'] == 'omer':
        st.header("🔍 Kalite ve Ana Tablo Yönetimi")
        df_k = veriyi_oku()
        
        # FİNANSAL ÖZET (PATRON PANELİNDEKİ GİBİ ÜSTTE)
        if not df_k.empty:
            df_k["Hakedis_Tutari"] = pd.to_numeric(df_k["Hakedis_Tutari"], errors='coerce').fillna(0)
            df_k["Talep_Edilen_Saat"] = pd.to_numeric(df_k["Talep_Edilen_Saat"], errors='coerce').fillna(0)
            df_k["Legrand_Kesinti_Tutari"] = pd.to_numeric(df_k["Legrand_Kesinti_Tutari"], errors='coerce').fillna(0)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Kayıtlı Saat", f"{df_k['Talep_Edilen_Saat'].sum():,.2f} sa")
            m2.metric("Brüt Hakediş", f"{df_k['Hakedis_Tutari'].sum():,.2f} TL")
            m3.metric("Net Hakediş", f"{(df_k['Hakedis_Tutari'].sum() - df_k['Legrand_Kesinti_Tutari'].sum()):,.2f} TL")
            st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 ANA TABLO & DÜZENLEME", "✅ ONAY BEKLEYENLER", "➕ MANUEL KAYIT (FULL)"])

        with tab1:
            st.subheader("Veritabanı Düzenleme ve Silme")
            st.caption("Tablodaki herhangi bir hücreye çift tıklayarak güncelleyebilir, satır seçip 'Delete' ile silebilirsiniz.")
            # Gelişmiş Düzenleme Tablosu
            edited_df = st.data_editor(df_k, use_container_width=True, hide_index=True, num_rows="dynamic")
            if st.button("💾 Değişiklikleri Kaydet"):
                if veriyi_yaz(edited_df):
                    st.success("Veritabanı başarıyla güncellendi!"); st.rerun()

        with tab2:
            taslaklar = df_k[df_k["Son_Durum"] == "Beklemede (İç Kayıt)"]
            if not taslaklar.empty:
                secilen_id = st.selectbox("İşlem Yapılacak Kayıt", taslaklar["Kayit_ID"].tolist())
                detay = taslaklar[taslaklar["Kayit_ID"] == secilen_id].iloc[0]
                st.info(f"İrsaliye: {detay['İrsaliye_No']} | Referans: {detay['Referans_No']} | Saat: {detay['Talep_Edilen_Saat']}")
                
                notu = st.text_area("Kalite Notu Ekle")
                c1, c2 = st.columns(2)
                if c1.button("✅ MUTABAKATA GÖNDER"):
                    df_k.loc[df_k["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu"]] = ["Mutabakat Bekliyor", notu]
                    veriyi_yaz(df_k); st.rerun()
                if c2.button("❌ REDDET"):
                    df_k.loc[df_k["Kayit_ID"] == secilen_id, "Son_Durum"] = "Kalite Reddedildi"
                    veriyi_yaz(df_k); st.rerun()
            else: st.info("Bekleyen kayıt yok.")

        with tab3:
            st.subheader("Ömer Bey - Detaylı Manuel Kayıt Girişi")
            with st.form("manuel_form_full"):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    m_sirket = st.selectbox("Şirket", ["Alaşar", "Hakan Kalıp Plastik", "Legrand", "Siemens"])
                    m_irs = st.text_input("İrsaliye No")
                    m_ref = st.text_input("Referans No")
                    m_yil = st.selectbox("Yıl", ["2025", "2026"], index=1)
                with col_b:
                    m_ph = st.number_input("pH (Hız)", min_value=0.1, value=7.0)
                    m_mik = st.number_input("Miktar", min_value=1, value=1)
                    m_kesinti = st.number_input("Legrand Kesinti Tutarı", value=0.0)
                    m_ay = st.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
                with col_c:
                    m_durum = st.selectbox("Başlangıç Durumu", ["Beklemede (İç Kayıt)", "Mutabakat Bekliyor", "Onaylandı"])
                    m_onay_tar = st.text_input("Müşteri Onay Tarihi (Örn: 15.05.2026)")
                    m_neden = st.text_area("İşlem Nedeni")
                
                if st.form_submit_button("Sisteme Full Kayıt Olarak Ekle"):
                    m_saat = round(m_mik / m_ph, 2)
                    yeni_row = {
                        "Kayit_ID": f"MAN-{len(df_k)+1:04d}", "Şirket": m_sirket, "İrsaliye_No": m_irs, "Referans_No": m_ref,
                        "Dönem_Yıl": m_yil, "Dönem_Ay": m_ay, "pH": m_ph, "Miktar": m_mik, "Kayıp_Zaman_Nedeni": m_neden,
                        "Talep_Edilen_Saat": m_saat, "Hakedis_Tutari": m_saat * SAATLIK_BIRIM_FIYAT, "Legrand_Kesinti_Tutari": m_kesinti,
                        "Son_Durum": m_durum, "Müşteri_Onay_Tarihi": m_onay_tar, "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Veri_Kaynagi": "MANUEL (ÖMER BEY)"
                    }
                    df_k = pd.concat([df_k, pd.DataFrame([yeni_row])], ignore_index=True)
                    veriyi_yaz(df_k); st.success("Kayıt eklendi!"); st.rerun()

    # --- PATRON PANELİ ---
    elif st.session_state['auth_role'] == 'patron':
        st.header("👑 Kesinleşmiş Finansal Raporlar")
        df_p = veriyi_oku()
        kesin = df_p[df_p["Son_Durum"] == "Onaylandı"].copy()
        if not kesin.empty:
            st.metric("Toplam Hakediş (Net)", f"{(pd.to_numeric(kesin['Hakedis_Tutari']).sum() - pd.to_numeric(kesin['Legrand_Kesinti_Tutari']).sum()):,.2f} TL")
            st.dataframe(kesin, use_container_width=True)
        else: st.warning("Onaylı kayıt bulunamadı.")import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- 1. GENEL AYARLAR ---
st.set_page_config(page_title="Alaşar Kurumsal Takip", layout="wide")

DOSYA_ADI = "kurumsal_takip_veritabani.xlsx"
KOLONLAR = [
    "Kayit_ID", "Şirket", "İrsaliye_No", "Referans_No", "Dönem_Yıl", "Dönem_Ay", "pH", "Miktar", 
    "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", "Onay_Veren", "Talep_Edilen_Saat",
    "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi",
    "Yonetici_Onay_Durumu", "Hakedis_Tutari", "Legrand_Kesinti_Tutari", "Kalite_Notu",
    "Veri_Kaynagi"
]
SAATLIK_BIRIM_FIYAT = 491

# --- 2. VERİTABANI FONKSİYONLARI ---
def baslangic_ayarlarini_yap():
    if not os.path.exists(DOSYA_ADI):
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl') as writer:
            pd.DataFrame(columns=KOLONLAR).to_excel(writer, sheet_name='Veriler', index=False)
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

# --- 3. OTURUM VE KARŞILAMA ---
if 'auth_role' not in st.session_state:
    st.session_state['auth_role'] = None
if 'intro_done' not in st.session_state:
    st.session_state['intro_done'] = False

def logout():
    st.session_state['auth_role'] = None
    st.rerun()

# --- 4. HOŞGELDİN (Intro) ---
if not st.session_state['intro_done']:
    st.markdown('<div style="text-align:center; margin-top:150px;"><h1 style="color:#2E86C1; font-size:60px;">Hoşgeldiniz Sevgili Alaşar Ailesi</h1></div>', unsafe_allow_html=True)
    st.balloons()
    time.sleep(1.5)
    st.session_state['intro_done'] = True
    st.rerun()

# --- 5. GİRİŞ PANELİ ---
if st.session_state['auth_role'] is None:
    st.title("🛡️ Alaşar Kalite & Finansal Takip")
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.expander("🛠️ REWORK BİRİMİ"):
            if st.button("Rework Girişi", key="btn_rew"): st.session_state['auth_role'] = 'rework'; st.rerun()
    with col2:
        with st.expander("🔍 KALİTE (ÖMER BEY)"):
            u_o = st.text_input("Kullanıcı", key="u_o")
            p_o = st.text_input("Şifre", type="password", key="p_o")
            if st.button("Ömer Bey Girişi"):
                if u_o == "omer" and p_o == "30052012": st.session_state['auth_role'] = 'omer'; st.rerun()
    with col3:
        with st.expander("👑 YÖNETİCİ (PATRON)"):
            if st.button("Patron Girişi", key="btn_pat"): st.session_state['auth_role'] = 'patron'; st.rerun()

# --- 6. PANELLER ---
else:
    st.sidebar.title(f"👤 {st.session_state['auth_role'].upper()}")
    st.sidebar.button("🚪 Çıkış", on_click=logout)

    # --- ÖMER BEY PANELİ (GÜNCELLENEN KISIM) ---
    if st.session_state['auth_role'] == 'omer':
        st.header("🔍 Kalite ve Ana Tablo Yönetimi")
        df_k = veriyi_oku()
        
        # FİNANSAL ÖZET (PATRON PANELİNDEKİ GİBİ ÜSTTE)
        if not df_k.empty:
            df_k["Hakedis_Tutari"] = pd.to_numeric(df_k["Hakedis_Tutari"], errors='coerce').fillna(0)
            df_k["Talep_Edilen_Saat"] = pd.to_numeric(df_k["Talep_Edilen_Saat"], errors='coerce').fillna(0)
            df_k["Legrand_Kesinti_Tutari"] = pd.to_numeric(df_k["Legrand_Kesinti_Tutari"], errors='coerce').fillna(0)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Kayıtlı Saat", f"{df_k['Talep_Edilen_Saat'].sum():,.2f} sa")
            m2.metric("Brüt Hakediş", f"{df_k['Hakedis_Tutari'].sum():,.2f} TL")
            m3.metric("Net Hakediş", f"{(df_k['Hakedis_Tutari'].sum() - df_k['Legrand_Kesinti_Tutari'].sum()):,.2f} TL")
            st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 ANA TABLO & DÜZENLEME", "✅ ONAY BEKLEYENLER", "➕ MANUEL KAYIT (FULL)"])

        with tab1:
            st.subheader("Veritabanı Düzenleme ve Silme")
            st.caption("Tablodaki herhangi bir hücreye çift tıklayarak güncelleyebilir, satır seçip 'Delete' ile silebilirsiniz.")
            # Gelişmiş Düzenleme Tablosu
            edited_df = st.data_editor(df_k, use_container_width=True, hide_index=True, num_rows="dynamic")
            if st.button("💾 Değişiklikleri Kaydet"):
                if veriyi_yaz(edited_df):
                    st.success("Veritabanı başarıyla güncellendi!"); st.rerun()

        with tab2:
            taslaklar = df_k[df_k["Son_Durum"] == "Beklemede (İç Kayıt)"]
            if not taslaklar.empty:
                secilen_id = st.selectbox("İşlem Yapılacak Kayıt", taslaklar["Kayit_ID"].tolist())
                detay = taslaklar[taslaklar["Kayit_ID"] == secilen_id].iloc[0]
                st.info(f"İrsaliye: {detay['İrsaliye_No']} | Referans: {detay['Referans_No']} | Saat: {detay['Talep_Edilen_Saat']}")
                
                notu = st.text_area("Kalite Notu Ekle")
                c1, c2 = st.columns(2)
                if c1.button("✅ MUTABAKATA GÖNDER"):
                    df_k.loc[df_k["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu"]] = ["Mutabakat Bekliyor", notu]
                    veriyi_yaz(df_k); st.rerun()
                if c2.button("❌ REDDET"):
                    df_k.loc[df_k["Kayit_ID"] == secilen_id, "Son_Durum"] = "Kalite Reddedildi"
                    veriyi_yaz(df_k); st.rerun()
            else: st.info("Bekleyen kayıt yok.")

        with tab3:
            st.subheader("Ömer Bey - Detaylı Manuel Kayıt Girişi")
            with st.form("manuel_form_full"):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    m_sirket = st.selectbox("Şirket", ["Alaşar", "Hakan Kalıp Plastik", "Legrand", "Siemens"])
                    m_irs = st.text_input("İrsaliye No")
                    m_ref = st.text_input("Referans No")
                    m_yil = st.selectbox("Yıl", ["2025", "2026"], index=1)
                with col_b:
                    m_ph = st.number_input("pH (Hız)", min_value=0.1, value=7.0)
                    m_mik = st.number_input("Miktar", min_value=1, value=1)
                    m_kesinti = st.number_input("Legrand Kesinti Tutarı", value=0.0)
                    m_ay = st.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
                with col_c:
                    m_durum = st.selectbox("Başlangıç Durumu", ["Beklemede (İç Kayıt)", "Mutabakat Bekliyor", "Onaylandı"])
                    m_onay_tar = st.text_input("Müşteri Onay Tarihi (Örn: 15.05.2026)")
                    m_neden = st.text_area("İşlem Nedeni")
                
                if st.form_submit_button("Sisteme Full Kayıt Olarak Ekle"):
                    m_saat = round(m_mik / m_ph, 2)
                    yeni_row = {
                        "Kayit_ID": f"MAN-{len(df_k)+1:04d}", "Şirket": m_sirket, "İrsaliye_No": m_irs, "Referans_No": m_ref,
                        "Dönem_Yıl": m_yil, "Dönem_Ay": m_ay, "pH": m_ph, "Miktar": m_mik, "Kayıp_Zaman_Nedeni": m_neden,
                        "Talep_Edilen_Saat": m_saat, "Hakedis_Tutari": m_saat * SAATLIK_BIRIM_FIYAT, "Legrand_Kesinti_Tutari": m_kesinti,
                        "Son_Durum": m_durum, "Müşteri_Onay_Tarihi": m_onay_tar, "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Veri_Kaynagi": "MANUEL (ÖMER BEY)"
                    }
                    df_k = pd.concat([df_k, pd.DataFrame([yeni_row])], ignore_index=True)
                    veriyi_yaz(df_k); st.success("Kayıt eklendi!"); st.rerun()

    # --- PATRON PANELİ ---
    elif st.session_state['auth_role'] == 'patron':
        st.header("👑 Kesinleşmiş Finansal Raporlar")
        df_p = veriyi_oku()
        kesin = df_p[df_p["Son_Durum"] == "Onaylandı"].copy()
        if not kesin.empty:
            st.metric("Toplam Hakediş (Net)", f"{(pd.to_numeric(kesin['Hakedis_Tutari']).sum() - pd.to_numeric(kesin['Legrand_Kesinti_Tutari']).sum()):,.2f} TL")
            st.dataframe(kesin, use_container_width=True)
        else: st.warning("Onaylı kayıt bulunamadı.")
