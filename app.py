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
            for c in eksik_kolonlar: 
                df_mevcut[c] = 0.0 if "Tutari" in c else "-"
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
    df_genel = veriyi_oku()

    # --- ÖMER BEY PANELİ ---
    if st.session_state['auth_role'] == 'omer':
        st.header("🔍 Kalite ve Ana Tablo Yönetimi")
        
        # SAYAÇ VE FİLTRE PANELİ (ÖMER BEY)
        st.markdown("### 📊 Dönemsel Performans Göstergeleri")
        if not df_genel.empty:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                secilen_yil = st.selectbox("Yıl Filtresi", ["Tümü"] + sorted(df_genel["Dönem_Yıl"].unique().astype(str).tolist()), key="o_yil")
            with col_f2:
                secilen_ay = st.selectbox("Ay Filtresi", ["Tümü", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], key="o_ay")

            temp_df = df_genel.copy()
            if secilen_yil != "Tümü": temp_df = temp_df[temp_df["Dönem_Yıl"].astype(str) == str(secilen_yil)]
            if secilen_ay != "Tümü": temp_df = temp_df[temp_df["Dönem_Ay"] == secilen_ay]

            for c in ["Talep_Edilen_Saat", "Hakedis_Tutari", "Legrand_Kesinti_Tutari"]:
                temp_df[c] = pd.to_numeric(temp_df[c], errors='coerce').fillna(0)

            onaylanmis = temp_df[temp_df["Son_Durum"] == "Onaylandı"]
            toplam_brut = onaylanmis['Hakedis_Tutari'].sum()
            toplam_kesinti = temp_df['Legrand_Kesinti_Tutari'].sum()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Talep Saati", f"{temp_df['Talep_Edilen_Saat'].sum():,.2f}")
            m2.metric("Onaylanan Saat", f"{onaylanmis['Talep_Edilen_Saat'].sum():,.2f}")
            m3.metric("Onaylanan Tutar", f"{toplam_brut:,.0f} TL")
            m4.metric("Legrand Kesintisi", f"{toplam_kesinti:,.0f} TL", delta_color="inverse")
            m5.metric("Net Hakediş", f"{toplam_brut - toplam_kesinti:,.0f} TL")
            st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 ANA TABLO & DÜZENLEME", "✅ ONAY BEKLEYENLER", "➕ FULL MANUEL KAYIT"])
        
        with tab1:
            edited_df = st.data_editor(df_genel, use_container_width=True, hide_index=True, num_rows="dynamic")
            if st.button("💾 Tüm Değişiklikleri Kaydet"):
                veriyi_yaz(edited_df); st.success("Değişiklikler kaydedildi!"); st.rerun()

        with tab2:
            st.subheader("Onay Bekleyen Kayıtlar")
            taslaklar = df_genel[df_genel["Son_Durum"] == "Beklemede (İç Kayıt)"]
            if not taslaklar.empty:
                secilen_id = st.selectbox("İşlem Yapılacak Kayıt ID", taslaklar["Kayit_ID"].tolist())
                detay = taslaklar[taslaklar["Kayit_ID"] == secilen_id].iloc[0]
                st.write(f"**Firma:** {detay['Şirket']} | **İrsaliye:** {detay['İrsaliye_No']} | **Miktar:** {detay['Miktar']}")
                notu = st.text_area("Kalite Notu")
                c1, c2 = st.columns(2)
                if c1.button("✅ Mutabakata Gönder", use_container_width=True):
                    df_genel.loc[df_genel["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu", "Güncelleme_Tarihi"]] = ["Mutabakat Bekliyor", notu, datetime.now().strftime("%Y-%m-%d %H:%M")]
                    veriyi_yaz(df_genel); st.rerun()
                if c2.button("❌ Reddet / İptal Et", use_container_width=True):
                    df_genel.loc[df_genel["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu", "Güncelleme_Tarihi"]] = ["Kalite Reddedildi", notu, datetime.now().strftime("%Y-%m-%d %H:%M")]
                    veriyi_yaz(df_genel); st.rerun()
            else: st.info("Onay bekleyen kayıt yok.")

        with tab3:
            st.subheader("Tam Yetkili Manuel Veri Girişi")
            with st.form("full_manuel_form", clear_on_submit=True):
                # Orijinal form tasarımı (app 13'teki gibi)
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    m_sirket = st.selectbox("Şirket", ["Legrand", "Siemens", "Hakan Kalıp Plastik", "Alaşar"])
                    m_irs = st.text_input("İrsaliye No")
                    m_ref = st.text_input("Referans No")
                with col_m2:
                    m_mik = st.number_input("Miktar", min_value=1)
                    m_ph = st.number_input("pH (Hız)", value=7.0)
                    m_kesinti = st.number_input("Kesinti Tutarı", value=0.0)
                with col_m3:
                    m_yil = st.selectbox("Yıl", ["2025", "2026", "2027"], index=1)
                    m_ay = st.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], index=datetime.now().month - 1)
                    m_durum = st.selectbox("Durum", ["Onaylandı", "Mutabakat Bekliyor", "Beklemede (İç Kayıt)"])
                
                m_neden = st.text_area("İşlem Açıklaması")
                if st.form_submit_button("Sisteme Kaydet", use_container_width=True):
                    saat = round(m_mik / m_ph, 2)
                    yeni_satir = {
                        "Kayit_ID": f"MAN-{datetime.now().strftime('%d%H%M%S')}",
                        "Şirket": m_sirket, "İrsaliye_No": m_irs, "Referans_No": m_ref,
                        "Dönem_Yıl": m_yil, "Dönem_Ay": m_ay, "pH": m_ph, "Miktar": m_mik,
                        "Kayıp_Zaman_Nedeni": m_neden, "Talep_Edilen_Saat": saat,
                        "Hakedis_Tutari": saat * SAATLIK_BIRIM_FIYAT,
                        "Legrand_Kesinti_Tutari": m_kesinti, "Son_Durum": m_durum,
                        "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Veri_Kaynagi": "ÖMER BEY MANUEL"
                    }
                    veriyi_yaz(pd.concat([df_genel, pd.DataFrame([yeni_satir])], ignore_index=True))
                    st.success("Kayıt Eklendi!"); st.rerun()

    # --- PATRON PANELİ ---
    elif st.session_state['auth_role'] == 'patron':
        st.header("👑 Yönetici Finansal Özet Paneli")
        
        # PATRON İÇİN FİLTRELER (YENİ EKLENDİ)
        if not df_genel.empty:
            st.markdown("### 📊 Dönemsel Filtreleme")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_yil = st.selectbox("Yıl Seçin", ["Tümü"] + sorted(df_genel["Dönem_Yıl"].unique().astype(str).tolist()), key="p_yil")
            with col_p2:
                p_ay = st.selectbox("Ay Seçin", ["Tümü", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], key="p_ay")

            p_df = df_genel.copy()
            if p_yil != "Tümü": p_df = p_df[p_df["Dönem_Yıl"].astype(str) == str(p_yil)]
            if p_ay != "Tümü": p_df = p_df[p_df["Dönem_Ay"] == p_ay]

            for c in ["Talep_Edilen_Saat", "Hakedis_Tutari", "Legrand_Kesinti_Tutari"]:
                p_df[c] = pd.to_numeric(p_df[c], errors='coerce').fillna(0)

            p_onay = p_df[p_df["Son_Durum"] == "Onaylandı"]
            
            pm1, pm2, pm3 = st.columns(3)
            pm1.metric("Onaylı Brüt Tutar", f"{p_onay['Hakedis_Tutari'].sum():,.0f} TL")
            pm2.metric("Toplam Kesinti", f"{p_df['Legrand_Kesinti_Tutari'].sum():,.0f} TL")
            p_net = p_onay['Hakedis_Tutari'].sum() - p_df['Legrand_Kesinti_Tutari'].sum()
            pm3.metric("Net Hakediş", f"{p_net:,.0f} TL")
            
            st.markdown("---")
            st.dataframe(p_onay, use_container_width=True, hide_index=True)
        else: st.info("Kayıt bulunamadı.")

    # --- REWORK PANELİ ---
    elif st.session_state['auth_role'] == 'rework':
        st.header("🛠️ Rework Birimi Giriş Paneli")
        with st.form("rew_form", clear_on_submit=True):
            r_sirket = st.selectbox("Şirket", ["Alaşar", "Legrand", "Siemens"])
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                r_irs = st.text_input("İrsaliye No")
                r_ref = st.text_input("Referans No")
            with col_r2:
                r_mik = st.number_input("Miktar", min_value=1)
                r_ay = st.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], index=datetime.now().month - 1)
                r_yil = st.selectbox("Yıl", ["2025", "2026", "2027"], index=1)
            r_neden = st.text_area("Hata Açıklaması")
            
            if st.form_submit_button("Kaliteye Gönder", use_container_width=True):
                r_saat = round(r_mik / 7.0, 2)
                yeni_rew = {
                    "Kayit_ID": f"REW-{datetime.now().strftime('%d%H%M%S')}",
                    "Şirket": r_sirket, "İrsaliye_No": r_irs, "Referans_No": r_ref,
                    "Miktar": r_mik, "pH": 7.0, "Dönem_Ay": r_ay, "Dönem_Yıl": r_yil,
                    "Kayıp_Zaman_Nedeni": r_neden, "Talep_Edilen_Saat": r_saat,
                    "Hakedis_Tutari": r_saat * SAATLIK_BIRIM_FIYAT,
                    "Son_Durum": "Beklemede (İç Kayıt)",
                    "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Veri_Kaynagi": "REWORK BİRİMİ"
                }
                df_genel = pd.concat([df_genel, pd.DataFrame([yeni_rew])], ignore_index=True)
                veriyi_yaz(df_genel); st.success("Başarıyla iletildi!"); st.rerun()
