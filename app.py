import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- 1. GENEL AYARLAR ---
st.set_page_config(page_title="Alaşar Kurumsal Takip", layout="wide")

DOSYA_ADI = "kurumsal_takip_veritabani.xlsx"
# KOLONLAR: Legrand_Kesinti_Tutari'ni veri yapısında tutuyoruz ama sadece manuel girişte kullanacağız
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
            for c in eksik_kolonlar: df_mevcut[c] = 0 if "Tutari" in c else "-"
            with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_mevcut.to_excel(writer, sheet_name='Veriler', index=False)

baslangic_ayarlarini_yap()

def veriyi_oku():
    return pd.read_excel(DOSYA_ADI, sheet_name='Veriler')

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

# --- 4. GİRİŞ EKRANI VE LOGİN (Öncekiyle aynı olduğu için özet geçilmiştir) ---
if not st.session_state['intro_done']:
    st.markdown('<h1 style="text-align:center; margin-top:150px; color:#2E86C1;">Hoşgeldiniz Sevgili Alaşar Ailesi</h1>', unsafe_allow_html=True)
    time.sleep(1.5); st.session_state['intro_done'] = True; st.rerun()

if st.session_state['auth_role'] is None:
    st.title("🛡️ Alaşar Kalite & Finansal Takip")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🛠️ REWORK GİRİŞİ"): st.session_state['auth_role'] = 'rework'; st.rerun()
    with c2:
        u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
        if st.button("🔍 ÖMER BEY GİRİŞİ"):
            if u == "omer" and p == "30052012": st.session_state['auth_role'] = 'omer'; st.rerun()
    with c3:
        if st.button("👑 PATRON GİRİŞİ"): st.session_state['auth_role'] = 'patron'; st.rerun()

else:
    st.sidebar.button("🚪 Çıkış", on_click=logout)
    df_genel = veriyi_oku()

    # --- ÖMER BEY PANELİ ---
    if st.session_state['auth_role'] == 'omer':
        st.header("🔍 Kalite ve Ana Tablo Yönetimi")
        
        # SAYAÇLAR
        st.markdown("### 📊 Finansal Durum Özet")
        if not df_genel.empty:
            # Filtreler
            f1, f2 = st.columns(2)
            sel_yil = f1.selectbox("Yıl", ["Tümü"] + sorted(df_genel["Dönem_Yıl"].unique().astype(str).tolist()))
            sel_ay = f2.selectbox("Ay", ["Tümü", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
            
            temp_df = df_genel.copy()
            if sel_yil != "Tümü": temp_df = temp_df[temp_df["Dönem_Yıl"].astype(str) == str(sel_yil)]
            if sel_ay != "Tümü": temp_df = temp_df[temp_df["Dönem_Ay"] == sel_ay]
            
            for c in ["Hakedis_Tutari", "Legrand_Kesinti_Tutari"]:
                temp_df[c] = pd.to_numeric(temp_df[c], errors='coerce').fillna(0)
            
            onayli = temp_df[temp_df["Son_Durum"] == "Onaylandı"]
            top_hakedis = onayli["Hakedis_Tutari"].sum()
            top_kesinti = temp_df["Legrand_Kesinti_Tutari"].sum()
            net_alacak = top_hakedis - top_kesinti

            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Hakediş (Onaylı)", f"{top_hakedis:,.2f} TL")
            m2.metric("Toplam Legrand Kesintisi", f"{top_kesinti:,.2f} TL", delta_color="inverse")
            m3.metric("Kesinleşmiş Net Alacak", f"{net_alacak:,.2f} TL", delta="NET")
            st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📊 ANA TABLO", "✅ ONAY BEKLEYENLER", "➕ MANUEL KESİNTİ & KAYIT"])

        with tab1:
            # Ana tabloda kesinti sütununu göstermiyoruz
            gosterilecek_df = df_genel.drop(columns=["Legrand_Kesinti_Tutari"]) if "Legrand_Kesinti_Tutari" in df_genel.columns else df_genel
            st.data_editor(gosterilecek_df, use_container_width=True, hide_index=True)

        with tab2:
            st.subheader("Onay Bekleyen İşler")
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
            st.subheader("Ömer Bey - Manuel Veri & Kesinti Girişi")
            with st.form("omer_manuel"):
                c1, c2, c3 = st.columns(3)
                m_irs = c1.text_input("İrsaliye No")
                m_ref = c1.text_input("Referans No")
                m_sirket = c1.selectbox("Şirket", ["Legrand", "Siemens", "Alaşar"])
                
                m_mik = c2.number_input("Miktar", 0)
                m_ph = c2.number_input("pH (Hız)", 7.0)
                # KESİNTİ SADECE BURADA
                m_kesinti = c2.number_input("Legrand Kesinti Tutarı (TL)", 0.0)
                
                m_ay = c3.selectbox("Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
                m_yil = c3.selectbox("Yıl", ["2025", "2026"], index=1)
                m_durum = c3.selectbox("Durum", ["Onaylandı", "Beklemede (İç Kayıt)"])
                
                if st.form_submit_button("Sisteme İşle"):
                    saat = round(m_mik / m_ph, 2) if m_ph > 0 else 0
                    yeni = {
                        "Kayit_ID": f"MAN-{datetime.now().strftime('%d%H%M')}",
                        "Şirket": m_sirket, "İrsaliye_No": m_irs, "Referans_No": m_ref,
                        "Dönem_Yıl": m_yil, "Dönem_Ay": m_ay, "Miktar": m_mik, "pH": m_ph,
                        "Talep_Edilen_Saat": saat, "Hakedis_Tutari": saat * SAATLIK_BIRIM_FIYAT,
                        "Legrand_Kesinti_Tutari": m_kesinti, "Son_Durum": m_durum,
                        "Veri_Kaynagi": "ÖMER MANUEL"
                    }
                    df_genel = pd.concat([df_genel, pd.DataFrame([yeni])], ignore_index=True)
                    veriyi_yaz(df_genel); st.success("Kaydedildi!"); st.rerun()

    # --- PATRON PANELİ ---
    elif st.session_state['auth_role'] == 'patron':
        st.header("👑 Yönetici Özeti")
        # Patron sadece net sonucu ve onaylıları görür
        onayli_p = df_genel[df_genel["Son_Durum"] == "Onaylandı"]
        top_h = onayli_p["Hakedis_Tutari"].sum()
        top_k = df_genel["Legrand_Kesinti_Tutari"].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Brüt Hakediş", f"{top_h:,.2f} TL")
        c2.metric("Kesinleşmiş Net Alacak", f"{top_h - top_k:,.2f} TL")
        st.dataframe(onayli_p[["Dönem_Ay", "Şirket", "İrsaliye_No", "Hakedis_Tutari"]], use_container_width=True)

    # --- REWORK PANELİ ---
    elif st.session_state['auth_role'] == 'rework':
        st.header("🛠️ Rework Girişi")
        with st.form("rew_form"):
            # Rework formunda kesinti alanı yoktur
            r_sirket = st.selectbox("Şirket", ["Legrand", "Siemens", "Alaşar"])
            r_irs = st.text_input("İrsaliye No")
            r_ref = st.text_input("Referans No")
            r_mik = st.number_input("Miktar", 1)
            if st.form_submit_button("Kaliteye Gönder"):
                yeni_rew = {
                    "Kayit_ID": f"REW-{datetime.now().strftime('%d%H%M')}",
                    "Şirket": r_sirket, "İrsaliye_No": r_irs, "Referans_No": r_ref,
                    "Miktar": r_mik, "Son_Durum": "Beklemede (İç Kayıt)",
                    "Dönem_Ay": "Mayıs", "Dönem_Yıl": "2026", "Veri_Kaynagi": "REWORK"
                }
                df_genel = pd.concat([df_genel, pd.DataFrame([yeni_rew])], ignore_index=True)
                veriyi_yaz(df_genel); st.success("Ömer Bey'in onayına gönderildi.")
