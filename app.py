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
        
        # SAYAÇ VE FİLTRE PANELİ
        st.markdown("### 📊 Dönemsel Performans Göstergeleri")
        if not df_genel.empty:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                secilen_yil = st.selectbox("Yıl Seçin", ["Tümü"] + sorted(df_genel["Dönem_Yıl"].unique().astype(str).tolist()), index=0)
            with col_f2:
                secilen_ay = st.selectbox("Ay Seçin", ["Tümü", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], index=0)

            temp_df = df_genel.copy()
            if secilen_yil != "Tümü": temp_df = temp_df[temp_df["Dönem_Yıl"].astype(str) == str(secilen_yil)]
            if secilen_ay != "Tümü": temp_df = temp_df[temp_df["Dönem_Ay"] == secilen_ay]

            for c in ["Talep_Edilen_Saat", "Hakedis_Tutari", "Legrand_Kesinti_Tutari"]:
                temp_df[c] = pd.to_numeric(temp_df[c], errors='coerce').fillna(0)

            onaylanmis = temp_df[temp_df["Son_Durum"] == "Onaylandı"]
            
            # --- HESAPLAMA MANTIĞI ---
            toplam_brut = onaylanmis['Hakedis_Tutari'].sum()
            toplam_kesinti = temp_df['Legrand_Kesinti_Tutari'].sum()
            net_alacak = toplam_brut - toplam_kesinti

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Talep Saati", f"{temp_df['Talep_Edilen_Saat'].sum():,.2f}")
            m2.metric("Onaylanan Saat", f"{onaylanmis['Talep_Edilen_Saat'].sum():,.2f}")
            m3.metric("Onaylanan Tutar", f"{toplam_brut:,.0f} TL")
            m4.metric("Dönem Kesintisi", f"{toplam_kesinti:,.0f} TL", delta_color="inverse")
            m5.metric("Net Hakediş", f"{net_alacak:,.0f} TL")
            st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs(["📊 ANA TABLO", "✅ ONAY BEKLEYENLER", "➕ MANUEL İŞ GİRİŞİ", "📉 LEGRAND KESİNTİ GİRİŞİ"])
        
        with tab1:
            # Tablodan kesinti sütununu çıkarıyoruz
            df_viz = df_genel.drop(columns=["Legrand_Kesinti_Tutari"]) if "Legrand_Kesinti_Tutari" in df_genel.columns else df_genel
            edited_df = st.data_editor(df_viz, use_container_width=True, hide_index=True, num_rows="dynamic")
            if st.button("💾 Tüm Değişiklikleri Kaydet"):
                final_to_save = pd.concat([edited_df, df_genel[["Legrand_Kesinti_Tutari"]]], axis=1)
                veriyi_yaz(final_to_save); st.success("Kaydedildi!"); st.rerun()

        with tab2:
            st.subheader("Onay Bekleyen Kayıtlar")
            taslaklar = df_genel[df_genel["Son_Durum"] == "Beklemede (İç Kayıt)"]
            if not taslaklar.empty:
                secilen_id = st.selectbox("İşlem Yapılacak Kayıt ID", taslaklar["Kayit_ID"].tolist())
                detay = taslaklar[taslaklar["Kayit_ID"] == secilen_id].iloc[0]
                st.info(f"Firma: {detay['Şirket']} | İrsaliye: {detay['İrsaliye_No']} | Miktar: {detay['Miktar']}")
                notu = st.text_area("Kalite Notu")
                c1, c2 = st.columns(2)
                if c1.button("✅ Onayla", use_container_width=True):
                    df_genel.loc[df_genel["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu", "Güncelleme_Tarihi"]] = ["Onaylandı", notu, datetime.now().strftime("%Y-%m-%d %H:%M")]
                    veriyi_yaz(df_genel); st.rerun()
                if c2.button("❌ Reddet", use_container_width=True):
                    df_genel.loc[df_genel["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu", "Güncelleme_Tarihi"]] = ["Reddedildi", notu, datetime.now().strftime("%Y-%m-%d %H:%M")]
                    veriyi_yaz(df_genel); st.rerun()
            else: st.info("Bekleyen iş yok.")

        with tab3:
            st.subheader("Manuel İş Kaydı")
            with st.form("m_form"):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    m_sirket = st.selectbox("Şirket", ["Legrand", "Siemens", "Alaşar"])
                    m_irs = st.text_input("İrsaliye No")
                    m_ref = st.text_input("Referans")
                with col_m2:
                    m_mik = st.number_input("Miktar", 1)
                    m_ay = st.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
                    m_yil = st.selectbox("Yıl", ["2025", "2026", "2027"], index=1)
                if st.form_submit_button("Sisteme Ekle"):
                    saat = round(m_mik / 7.0, 2)
                    yeni = {"Kayit_ID": f"MAN-{datetime.now().strftime('%H%M%S')}", "Şirket": m_sirket, "İrsaliye_No": m_irs, "Referans_No": m_ref, "Miktar": m_mik, "Talep_Edilen_Saat": saat, "Hakedis_Tutari": saat*SAATLIK_BIRIM_FIYAT, "Dönem_Ay": m_ay, "Dönem_Yıl": m_yil, "Son_Durum": "Onaylandı", "Legrand_Kesinti_Tutari": 0}
                    veriyi_yaz(pd.concat([df_genel, pd.DataFrame([yeni])], ignore_index=True)); st.rerun()

        with tab4:
            st.subheader("⚠️ Dönemsel Legrand Kesintisi Girişi")
            st.markdown("Buradan girdiğiniz tutarlar, seçilen ayın toplam hakedişinden düşülecektir.")
            with st.form("kesinti_form"):
                k_yil = st.selectbox("Kesinti Yılı", ["2025", "2026", "2027"], index=1)
                k_ay = st.selectbox("Kesinti Ayı", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
                k_tutar = st.number_input("Kesinti Tutarı (TL)", min_value=0.0, step=100.0)
                if st.form_submit_button("Kesintiyi Onayla ve Kaydet"):
                    kesinti_verisi = {
                        "Kayit_ID": f"KES-{datetime.now().strftime('%H%M%S')}",
                        "Şirket": "Legrand",
                        "Dönem_Yıl": k_yil,
                        "Dönem_Ay": k_ay,
                        "Legrand_Kesinti_Tutari": k_tutar,
                        "Yapılacak_İşin_Tanımı": "Dönemsel Kesinti Uygulaması",
                        "Son_Durum": "KESİNTİ_KAYDI",
                        "Veri_Kaynagi": "ÖMER BEY MANUEL KESİNTİ"
                    }
                    veriyi_yaz(pd.concat([df_genel, pd.DataFrame([kesinti_verisi])], ignore_index=True))
                    st.success(f"{k_ay} {k_yil} dönemi için {k_tutar} TL kesinti kaydedildi!"); st.rerun()

    # --- PATRON PANELİ ---
    elif st.session_state['auth_role'] == 'patron':
        st.header("👑 Yönetici Finansal Özet")
        if not df_genel.empty:
            onayli = df_genel[df_genel["Son_Durum"] == "Onaylandı"]
            brut = onayli["Hakedis_Tutari"].sum()
            kesinti = df_genel["Legrand_Kesinti_Tutari"].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("Brüt Hakediş", f"{brut:,.0f} TL")
            c2.metric("Toplam Kesinti", f"{kesinti:,.0f} TL")
            c3.metric("Net Ödenecek", f"{brut - kesinti:,.0f} TL")
            st.dataframe(onayli, use_container_width=True)

    # --- REWORK PANELİ ---
    elif st.session_state['auth_role'] == 'rework':
        st.header("🛠️ Rework Girişi")
        with st.form("rew_form"):
            r_irs = st.text_input("İrsaliye No"); r_mik = st.number_input("Miktar", 1)
            if st.form_submit_button("Kaliteye Gönder"):
                y_r = {"Kayit_ID": f"REW-{datetime.now().strftime('%H%M%S')}", "İrsaliye_No": r_irs, "Miktar": r_mik, "Son_Durum": "Beklemede (İç Kayıt)", "Dönem_Ay": "Mayıs", "Dönem_Yıl": "2026", "Legrand_Kesinti_Tutari": 0}
                veriyi_yaz(pd.concat([df_genel, pd.DataFrame([y_r])], ignore_index=True)); st.success("İletildi."); st.rerun()
