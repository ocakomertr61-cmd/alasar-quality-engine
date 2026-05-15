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

# --- 4. HOŞGELDİN EKRANI ---
if not st.session_state['intro_done']:
    st.markdown("""
        <div style="text-align:center; margin-top:150px;">
            <h1 style="color:#2E86C1; font-size:60px;">Hoşgeldiniz Sevgili Alaşar Ailesi</h1>
            <p style="font-size:20px; color:#5D6D7E;">Sistem hazırlanıyor...</p>
        </div>
    """, unsafe_allow_html=True)
    st.balloons()
    time.sleep(2.5)
    st.session_state['intro_done'] = True
    st.rerun()

# --- 5. ANA GİRİŞ PANELİ ---
if st.session_state['auth_role'] is None:
    st.title("🛡️ Alaşar Kalite & Finansal Takip Sistemi")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.expander("🛠️ REWORK BİRİMİ"):
            if st.button("Rework Girişi", use_container_width=True):
                st.session_state['auth_role'] = 'rework'
                st.rerun()

    with col2:
        with st.expander("🔍 KALİTE (ÖMER BEY)"):
            u_o = st.text_input("Kullanıcı Adı", key="u_omer")
            p_o = st.text_input("Şifre", type="password", key="p_omer")
            if st.button("Ömer Bey Girişi", use_container_width=True):
                if u_o == "omer" and p_o == "30052012":
                    st.session_state['auth_role'] = 'omer'
                    st.rerun()
                else: st.error("Hatalı Giriş!")

    with col3:
        with st.expander("👑 YÖNETİCİ (PATRON)"):
            if st.button("Patron Girişi", use_container_width=True):
                st.session_state['auth_role'] = 'patron'
                st.rerun()

# --- 6. BİRİM PANELLERİ ---
else:
    st.sidebar.title(f"👤 {st.session_state['auth_role'].upper()}")
    st.sidebar.button("🚪 Sistemden Çıkış", on_click=logout)

    # --- ÖMER BEY PANELİ (KALİTE) ---
    # --- FİNANSAL FİLTRE VE SAYAÇ PANELİ (Ömer Bey ve Patron İçin Ortak) ---
    st.markdown("### 📊 Dönemsel Performans Göstergeleri")
    
    # Filtre Seçenekleri
    df_filter = veriyi_oku()
    if not df_filter.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            secilen_yil = st.selectbox("Yıl Seçin", ["Tümü"] + sorted(df_filter["Dönem_Yıl"].unique().tolist()), index=0)
        with col_f2:
            secilen_ay = st.selectbox("Ay Seçin", ["Tümü"] + ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], index=0)

        # Veriyi Filtreleme
        temp_df = df_filter.copy()
        if secilen_yil != "Tümü":
            temp_df = temp_df[temp_df["Dönem_Yıl"].astype(str) == str(secilen_yil)]
        if secilen_ay != "Tümü":
            temp_df = temp_df[temp_df["Dönem_Ay"] == secilen_ay]

        # Sayısal Dönüşümler
        temp_df["Talep_Edilen_Saat"] = pd.to_numeric(temp_df["Talep_Edilen_Saat"], errors='coerce').fillna(0)
        temp_df["Hakedis_Tutari"] = pd.to_numeric(temp_df["Hakedis_Tutari"], errors='coerce').fillna(0)
        temp_df["Legrand_Kesinti_Tutari"] = pd.to_numeric(temp_df["Legrand_Kesinti_Tutari"], errors='coerce').fillna(0)

        # Onaylanmış Veriler İçin Ayrı Hesaplama
        onaylanmis_df = temp_df[temp_df["Son_Durum"] == "Onaylandı"]

        # Sayaçlar (5'li Metrik Sistemi)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Talep Edilen Saat", f"{temp_df['Talep_Edilen_Saat'].sum():,.2f} sa")
        m2.metric("Onaylanan Saat", f"{onaylanmis_df['Talep_Edilen_Saat'].sum():,.2f} sa")
        m3.metric("Onaylanan Tutar", f"{onaylanmis_df['Hakedis_Tutari'].sum():,.2f} TL")
        m4.metric("Ek İşçilik Kesintisi", f"{temp_df['Legrand_Kesinti_Tutari'].sum():,.2f} TL", delta_color="inverse")
        
        net_tutar = onaylanmis_df['Hakedis_Tutari'].sum() - temp_df['Legrand_Kesinti_Tutari'].sum()
        m5.metric("Elde Edilen Net", f"{net_tutar:,.2f} TL", delta=f"{len(temp_df)} Kayıt")

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 ANA TABLO & DÜZENLEME", "✅ ONAY BEKLEYENLER", "➕ FULL MANUEL KAYIT"])
        
        with tab1:
            st.subheader("Tüm Verilerin Yönetimi")
            st.caption("Tablodaki herhangi bir hücreye çift tıklayarak veriyi değiştirebilirsiniz. Satır seçip Delete ile silebilirsiniz.")
            # st.data_editor sayesinde güncelleme, silme ve ekleme yapılabiliyor
            edited_df = st.data_editor(df_k, use_container_width=True, hide_index=True, num_rows="dynamic")
            if st.button("💾 Tüm Değişiklikleri Kaydet"):
                veriyi_yaz(edited_df)
                st.success("Veritabanı başarıyla güncellendi!")
                st.rerun()

        with tab2:
            st.subheader("Onay Bekleyen Kayıtlar")
            taslaklar = df_k[df_k["Son_Durum"] == "Beklemede (İç Kayıt)"]
            if not taslaklar.empty:
                secilen_id = st.selectbox("İşlem Yapılacak Kayıt", taslaklar["Kayit_ID"].tolist())
                detay = taslaklar[taslaklar["Kayit_ID"] == secilen_id].iloc[0]
                st.info(f"İrsaliye: {detay['İrsaliye_No']} | Referans: {detay['Referans_No']} | Neden: {detay['Kayıp_Zaman_Nedeni']}")
                
                notu = st.text_area("Kalite Notu")
                c1, c2 = st.columns(2)
                if c1.button("✅ Mutabakata Gönder"):
                    df_k.loc[df_k["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu"]] = ["Mutabakat Bekliyor", notu]
                    veriyi_yaz(df_k); st.rerun()
                if c2.button("❌ Reddet"):
                    df_k.loc[df_k["Kayit_ID"] == secilen_id, "Son_Durum"] = "Kalite Reddedildi"
                    veriyi_yaz(df_k); st.rerun()
            else: st.info("Şu an onay bekleyen kayıt yok.")

        with tab3:
            st.subheader("Ömer Bey - Tam Yetkili Manuel Giriş")
            with st.form("full_manuel"):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    m_sirket = st.selectbox("Şirket", ["Alaşar", "Hakan Kalıp Plastik", "Legrand", "Siemens"])
                    m_irs = st.text_input("İrsaliye No")
                    m_ref = st.text_input("Referans No")
                with col_b:
                    m_ph = st.number_input("pH (Hız)", value=7.0)
                    m_mik = st.number_input("Miktar", value=1)
                    m_kesinti = st.number_input("Legrand Kesinti Tutarı", value=0.0)
                with col_c:
                    m_durum = st.selectbox("Durum", ["Beklemede (İç Kayıt)", "Mutabakat Bekliyor", "Onaylandı"])
                    m_ay = st.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
                    m_yil = st.selectbox("Yıl", ["2025", "2026"], index=1)
                
                m_neden = st.text_area("İşlem/Hata Açıklaması")
                
                if st.form_submit_button("Sisteme Kayıt Ekle"):
                    m_saat = round(m_mik / m_ph, 2)
                    yeni_satir = {
                        "Kayit_ID": f"MAN-{len(df_k)+1:04d}", "Şirket": m_sirket, "İrsaliye_No": m_irs, "Referans_No": m_ref,
                        "Dönem_Yıl": m_yil, "Dönem_Ay": m_ay, "pH": m_ph, "Miktar": m_mik, "Kayıp_Zaman_Nedeni": m_neden,
                        "Talep_Edilen_Saat": m_saat, "Hakedis_Tutari": m_saat * SAATLIK_BIRIM_FIYAT, "Legrand_Kesinti_Tutari": m_kesinti,
                        "Son_Durum": m_durum, "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"), "Veri_Kaynagi": "ÖMER BEY MANUEL"
                    }
                    df_k = pd.concat([df_k, pd.DataFrame([yeni_satir])], ignore_index=True)
                    veriyi_yaz(df_k); st.success("Yeni kayıt eklendi!"); st.rerun()

    # --- PATRON PANELİ ---
    elif st.session_state['auth_role'] == 'patron':
       # --- FİNANSAL FİLTRE VE SAYAÇ PANELİ (Ömer Bey ve Patron İçin Ortak) ---
    st.markdown("### 📊 Dönemsel Performans Göstergeleri")
    
    # Filtre Seçenekleri
    df_filter = veriyi_oku()
    if not df_filter.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            secilen_yil = st.selectbox("Yıl Seçin", ["Tümü"] + sorted(df_filter["Dönem_Yıl"].unique().tolist()), index=0)
        with col_f2:
            secilen_ay = st.selectbox("Ay Seçin", ["Tümü"] + ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], index=0)

        # Veriyi Filtreleme
        temp_df = df_filter.copy()
        if secilen_yil != "Tümü":
            temp_df = temp_df[temp_df["Dönem_Yıl"].astype(str) == str(secilen_yil)]
        if secilen_ay != "Tümü":
            temp_df = temp_df[temp_df["Dönem_Ay"] == secilen_ay]

        # Sayısal Dönüşümler
        temp_df["Talep_Edilen_Saat"] = pd.to_numeric(temp_df["Talep_Edilen_Saat"], errors='coerce').fillna(0)
        temp_df["Hakedis_Tutari"] = pd.to_numeric(temp_df["Hakedis_Tutari"], errors='coerce').fillna(0)
        temp_df["Legrand_Kesinti_Tutari"] = pd.to_numeric(temp_df["Legrand_Kesinti_Tutari"], errors='coerce').fillna(0)

        # Onaylanmış Veriler İçin Ayrı Hesaplama
        onaylanmis_df = temp_df[temp_df["Son_Durum"] == "Onaylandı"]

        # Sayaçlar (5'li Metrik Sistemi)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Talep Edilen Saat", f"{temp_df['Talep_Edilen_Saat'].sum():,.2f} sa")
        m2.metric("Onaylanan Saat", f"{onaylanmis_df['Talep_Edilen_Saat'].sum():,.2f} sa")
        m3.metric("Onaylanan Tutar", f"{onaylanmis_df['Hakedis_Tutari'].sum():,.2f} TL")
        m4.metric("Ek İşçilik Kesintisi", f"{temp_df['Legrand_Kesinti_Tutari'].sum():,.2f} TL", delta_color="inverse")
        
        net_tutar = onaylanmis_df['Hakedis_Tutari'].sum() - temp_df['Legrand_Kesinti_Tutari'].sum()
        m5.metric("Elde Edilen Net", f"{net_tutar:,.2f} TL", delta=f"{len(temp_df)} Kayıt")

        st.markdown("---")

    # --- REWORK PANELİ ---
    elif st.session_state['auth_role'] == 'rework':
        st.header("🛠️ Rework Giriş")
        # (Aynı Rework form mantığı...)
        with st.form("rew_form"):
            r_irs = st.text_input("İrsaliye No")
            r_ref = st.text_input("Referans No")
            r_mik = st.number_input("Miktar", min_value=1)
            if st.form_submit_button("Gönder"):
                st.success("Kayıt Ömer Bey'e iletildi.")
