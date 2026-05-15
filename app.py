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
    st.markdown('<div style="text-align:center; margin-top:150px;"><h1 style="color:#2E86C1; font-size:60px;">Hoşgeldiniz Sevgili Alaşar Ailesi</h1></div>', unsafe_allow_html=True)
    st.balloons()
    time.sleep(2.0)
    st.session_state['intro_done'] = True
    st.rerun()

# --- 5. ANA GİRİŞ PANELİ ---
if st.session_state['auth_role'] is None:
    st.title("🛡️ Alaşar Kalite & Finansal Takip Sistemi")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🛠️ REWORK BİRİMİ GİRİŞİ", use_container_width=True):
            st.session_state['auth_role'] = 'rework'; st.rerun()
    with col2:
        u_o = st.text_input("Kullanıcı"); p_o = st.text_input("Şifre", type="password")
        if st.button("🔍 ÖMER BEY GİRİŞİ", use_container_width=True):
            if u_o == "omer" and p_o == "30052012":
                st.session_state['auth_role'] = 'omer'; st.rerun()
    with col3:
        if st.button("👑 YÖNETİCİ (PATRON) GİRİŞİ", use_container_width=True):
            st.session_state['auth_role'] = 'patron'; st.rerun()

else:
    st.sidebar.title(f"👤 {st.session_state['auth_role'].upper()}")
    st.sidebar.button("🚪 Çıkış", on_click=logout)
    df_genel = veriyi_oku()

    # --- ÖMER BEY PANELİ ---
    if st.session_state['auth_role'] == 'omer':
        st.header("🔍 Kalite ve Ana Tablo Yönetimi")
        
        if not df_genel.empty:
            c_f1, c_f2 = st.columns(2)
            s_yil = c_f1.selectbox("Yıl", ["Tümü"] + sorted(df_genel["Dönem_Yıl"].unique().astype(str).tolist()))
            s_ay = c_f2.selectbox("Ay", ["Tümü", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])

            temp_df = df_genel.copy()
            if s_yil != "Tümü": temp_df = temp_df[temp_df["Dönem_Yıl"].astype(str) == str(s_yil)]
            if s_ay != "Tümü": temp_df = temp_df[temp_df["Dönem_Ay"] == s_ay]

            for c in ["Hakedis_Tutari", "Legrand_Kesinti_Tutari"]:
                temp_df[c] = pd.to_numeric(temp_df[c], errors='coerce').fillna(0)

            onayli = temp_df[temp_df["Son_Durum"] == "Onaylandı"]
            t_brut = onayli['Hakedis_Tutari'].sum()
            t_kesinti = temp_df['Legrand_Kesinti_Tutari'].sum()

            m1, m2, m3 = st.columns(3)
            m1.metric("Onaylanan Brüt", f"{t_brut:,.0f} TL")
            m2.metric("Dönem Kesintisi", f"{t_kesinti:,.0f} TL", delta_color="inverse")
            m3.metric("Net Alacak", f"{t_brut - t_kesinti:,.0f} TL")

        tab1, tab2, tab3, tab4 = st.tabs(["📊 ANA TABLO", "✅ ONAY BEKLEYENLER", "➕ MANUEL İŞ GİRİŞİ", "📉 KESİNTİ GİRİŞİ"])
        
        with tab1:
            # Tablodan kesinti sütununu gizliyoruz
            df_viz = df_genel.drop(columns=["Legrand_Kesinti_Tutari"]) if "Legrand_Kesinti_Tutari" in df_genel.columns else df_genel
            edited = st.data_editor(df_viz, use_container_width=True, hide_index=True)
            if st.button("💾 Kaydet"):
                veriyi_yaz(pd.concat([edited, df_genel[["Legrand_Kesinti_Tutari"]]], axis=1))
                st.success("Güncellendi!"); st.rerun()

        with tab2:
            taslaklar = df_genel[df_genel["Son_Durum"] == "Beklemede (İç Kayıt)"]
            if not taslaklar.empty:
                sid = st.selectbox("Kayıt ID", taslaklar["Kayit_ID"].tolist())
                if st.button("Onayla"):
                    df_genel.loc[df_genel["Kayit_ID"] == sid, "Son_Durum"] = "Onaylandı"
                    veriyi_yaz(df_genel); st.rerun()
            else: st.info("Bekleyen iş yok.")

        with tab3:
            with st.form("m_form"):
                c1, c2 = st.columns(2)
                f_sir = c1.selectbox("Firma", ["Legrand", "Siemens", "Alaşar"])
                f_irs = c1.text_input("İrsaliye")
                f_mik = c2.number_input("Miktar", 1)
                f_ay = c2.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
                if st.form_submit_button("Ekle"):
                    saat = round(f_mik / 7.0, 2)
                    yeni = {"Kayit_ID": f"M-{datetime.now().strftime('%H%M%S')}", "Şirket": f_sir, "İrsaliye_No": f_irs, "Miktar": f_mik, "Talep_Edilen_Saat": saat, "Hakedis_Tutari": saat*SAATLIK_BIRIM_FIYAT, "Son_Durum": "Onaylandı", "Dönem_Ay": f_ay, "Dönem_Yıl": 2026, "Legrand_Kesinti_Tutari": 0}
                    veriyi_yaz(pd.concat([df_genel, pd.DataFrame([yeni])], ignore_index=True)); st.rerun()

        with tab4:
            st.subheader("⚠️ Legrand Kesintisi Tanımla")
            with st.form("k_form"):
                k_yil = st.selectbox("Kesinti Yılı", [2025, 2026, 2027], index=1)
                k_ay = st.selectbox("Kesinti Ayı", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
                k_tut = st.number_input("Kesinti Tutarı (TL)", min_value=0.0)
                if st.form_submit_button("Kesintiyi Sisteme İşle"):
                    kesinti_satiri = {"Kayit_ID": f"KES-{datetime.now().strftime('%H%M%S')}", "Şirket": "Legrand", "Yapılacak_İşin_Tanımı": "Dönemsel Kesinti", "Dönem_Yıl": k_yil, "Dönem_Ay": k_ay, "Legrand_Kesinti_Tutari": k_tut, "Son_Durum": "KESİNTİ", "Veri_Kaynagi": "ÖMER MANUEL KESİNTİ"}
                    veriyi_yaz(pd.concat([df_genel, pd.DataFrame([kesinti_satiri])], ignore_index=True)); st.success("Kesinti işlendi!"); st.rerun()

    # --- PATRON PANELİ ---
    elif st.session_state['auth_role'] == 'patron':
        st.header("👑 Yönetici Özeti")
        onayli_p = df_genel[df_genel["Son_Durum"] == "Onaylandı"]
        b_p = onayli_p["Hakedis_Tutari"].sum()
        k_p = df_genel["Legrand_Kesinti_Tutari"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Brüt Alacak", f"{b_p:,.0f} TL")
        c2.metric("Net Alacak (Kesinti Sonrası)", f"{b_p - k_p:,.0f} TL")
        st.dataframe(onayli_p[["Dönem_Ay", "Şirket", "İrsaliye_No", "Hakedis_Tutari"]], use_container_width=True)

    # --- REWORK PANELİ ---
    elif st.session_state['auth_role'] == 'rework':
        st.header("🛠️ Rework Girişi")
        with st.form("rew"):
            r_irs = st.text_input("İrsaliye"); r_mik = st.number_input("Miktar", 1)
            if st.form_submit_button("Gönder"):
                y_r = {"Kayit_ID": f"R-{datetime.now().strftime('%H%M%S')}", "İrsaliye_No": r_irs, "Miktar": r_mik, "Son_Durum": "Beklemede (İç Kayıt)", "Dönem_Ay": "Mayıs", "Dönem_Yıl": 2026, "Legrand_Kesinti_Tutari": 0}
                veriyi_yaz(pd.concat([df_genel, pd.DataFrame([y_r])], ignore_index=True)); st.success("İletildi."); st.rerun()
