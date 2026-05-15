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
def veriyi_oku(): return pd.read_excel(DOSYA_ADI, sheet_name='Veriler')
def veriyi_yaz(df):
    with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name='Veriler', index=False)
    return True

# --- 3. OTURUM VE ÇIKIŞ ---
if 'auth_role' not in st.session_state: st.session_state['auth_role'] = None
if 'intro_done' not in st.session_state: st.session_state['intro_done'] = False

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

# --- 5. GİRİŞ PANELİ ---
if st.session_state['auth_role'] is None:
    st.title("🛡️ Alaşar Kalite & Finansal Takip Sistemi")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🛠️ REWORK BİRİMİ GİRİŞİ", use_container_width=True): st.session_state['auth_role'] = 'rework'; st.rerun()
    with c2:
        u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
        if st.button("🔍 ÖMER BEY GİRİŞİ", use_container_width=True):
            if u == "omer" and p == "30052012": st.session_state['auth_role'] = 'omer'; st.rerun()
    with c3:
        if st.button("👑 YÖNETİCİ (PATRON) GİRİŞİ", use_container_width=True): st.session_state['auth_role'] = 'patron'; st.rerun()

else:
    st.sidebar.title(f"👤 {st.session_state['auth_role'].upper()}")
    st.sidebar.button("🚪 Çıkış", on_click=logout)
    df_genel = veriyi_oku()

    # --- ÖMER BEY PANELİ ---
    if st.session_state['auth_role'] == 'omer':
        st.header("🔍 Kalite ve Ana Tablo Yönetimi")
        
        if not df_genel.empty:
            f1, f2 = st.columns(2)
            sel_yil = f1.selectbox("Yıl", ["Tümü"] + sorted(df_genel["Dönem_Yıl"].unique().astype(str).tolist()))
            sel_ay = f2.selectbox("Ay", ["Tümü", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])

            temp_df = df_genel.copy()
            if sel_yil != "Tümü": temp_df = temp_df[temp_df["Dönem_Yıl"].astype(str) == str(sel_yil)]
            if sel_ay != "Tümü": temp_df = temp_df[temp_df["Dönem_Ay"] == sel_ay]

            for c in ["Hakedis_Tutari", "Legrand_Kesinti_Tutari"]:
                temp_df[c] = pd.to_numeric(temp_df[c], errors='coerce').fillna(0)

            onayli = temp_df[temp_df["Son_Durum"] == "Onaylandı"]
            brut = onayli["Hakedis_Tutari"].sum()
            kesinti = temp_df["Legrand_Kesinti_Tutari"].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Brüt Hakediş", f"{brut:,.0f} TL")
            m2.metric("Toplam Kesinti", f"{kesinti:,.0f} TL", delta_color="inverse")
            m3.metric("Net Alacak", f"{brut - kesinti:,.0f} TL")

        tab1, tab2, tab3 = st.tabs(["📊 ANA TABLO", "✅ ONAY BEKLEYENLER", "➕ FULL MANUEL KAYIT"])
        
        with tab1:
            df_viz = df_genel.drop(columns=["Legrand_Kesinti_Tutari"]) if "Legrand_Kesinti_Tutari" in df_genel.columns else df_genel
            edited = st.data_editor(df_viz, use_container_width=True, hide_index=True)
            if st.button("💾 Değişiklikleri Kaydet"):
                final_df = pd.concat([edited, df_genel[["Legrand_Kesinti_Tutari"]]], axis=1)
                veriyi_yaz(final_df); st.success("Kaydedildi!")

        with tab2:
            taslaklar = df_genel[df_genel["Son_Durum"] == "Beklemede (İç Kayıt)"]
            if not taslaklar.empty:
                sid = st.selectbox("Kayıt Seç", taslaklar["Kayit_ID"].tolist())
                detay = taslaklar[taslaklar["Kayit_ID"] == sid].iloc[0]
                st.info(f"Firma: {detay['Şirket']} | İrsaliye: {detay['İrsaliye_No']} | Miktar: {detay['Miktar']}")
                if st.button("Onayla"):
                    df_genel.loc[df_genel["Kayit_ID"] == sid, "Son_Durum"] = "Onaylandı"
                    veriyi_yaz(df_genel); st.rerun()
            else: st.info("Bekleyen iş yok.")

        with tab3:
            st.subheader("Manuel Kayıt & Kesinti Girişi")
            with st.form("manual_form"):
                col_a, col_b, col_c = st.columns(3)
                m_sirket = col_a.selectbox("Şirket", ["Legrand", "Siemens", "Alaşar"])
                m_irs = col_a.text_input("İrsaliye No")
                m_mik = col_b.number_input("Miktar", 1)
                m_ph = col_b.number_input("pH (Hız)", 7.0)
                m_kesinti = col_b.number_input("Legrand Kesinti Tutarı (TL)", 0.0)
                m_ay = col_c.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
                m_yil = col_c.selectbox("Yıl", ["2025", "2026"], index=1)
                if st.form_submit_button("Sisteme Ekle"):
                    saat = round(m_mik / m_ph, 2)
                    yeni = {
                        "Kayit_ID": f"MAN-{datetime.now().strftime('%d%H%M')}",
                        "Şirket": m_sirket, "İrsaliye_No": m_irs, "Miktar": m_mik, "pH": m_ph,
                        "Talep_Edilen_Saat": saat, "Hakedis_Tutari": saat * SAATLIK_BIRIM_FIYAT,
                        "Legrand_Kesinti_Tutari": m_kesinti, "Son_Durum": "Onaylandı",
                        "Dönem_Ay": m_ay, "Dönem_Yıl": m_yil, "Veri_Kaynagi": "MANUEL"
                    }
                    df_genel = pd.concat([df_genel, pd.DataFrame([yeni])], ignore_index=True)
                    veriyi_yaz(df_genel); st.rerun()

    # --- REWORK PANELİ ---
    elif st.session_state['auth_role'] == 'rework':
        st.header("🛠️ Rework Birimi - İş Girişi")
        with st.form("rew_form"):
            r_sirket = st.selectbox("Firma", ["Alaşar", "Legrand", "Siemens"])
            r_irs = st.text_input("İrsaliye No")
            r_mik = st.number_input("Miktar", 1)
            if st.form_submit_button("Kaliteye Gönder"):
                saat = round(r_mik / 7.0, 2)
                yeni_rew = {
                    "Kayit_ID": f"REW-{datetime.now().strftime('%d%H%M')}",
                    "Şirket": r_sirket, "İrsaliye_No": r_irs, "Miktar": r_mik,
                    "Talep_Edilen_Saat": saat, "Son_Durum": "Beklemede (İç Kayıt)",
                    "Dönem_Ay": "Mayıs", "Dönem_Yıl": "2026", "Veri_Kaynagi": "REWORK"
                }
                df_genel = pd.concat([df_genel, pd.DataFrame([yeni_rew])], ignore_index=True)
                veriyi_yaz(df_genel); st.success("Onaya gönderildi."); st.rerun()

    # --- PATRON PANELİ ---
    elif st.session_state['auth_role'] == 'patron':
        st.header("👑 Yönetici Finansal Özet")
        onayli_p = df_genel[df_genel["Son_Durum"] == "Onaylandı"]
        brut_p = onayli_p["Hakedis_Tutari"].sum()
        kesinti_p = df_genel["Legrand_Kesinti_Tutari"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Brüt Hakediş", f"{brut_p:,.0f} TL")
        c2.metric("Net Alacak", f"{brut_p - kesinti_p:,.0f} TL")
        st.dataframe(onayli_p[["Dönem_Ay", "Şirket", "İrsaliye_No", "Hakedis_Tutari"]], use_container_width=True)
