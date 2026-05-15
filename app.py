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
    "Veri_Kaynagi" # Yeni Kolon: Verinin nereden geldiğini anlamak için
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

# --- 3. OTURUM VE KARŞILAMA YÖNETİMİ ---
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
            <h1 style="color:#2E86C1; font-size:60px; animation: pulse 2s infinite;">
                Hoşgeldiniz Sevgili Alaşar Ailesi
            </h1>
            <p style="font-size:20px; color:#5D6D7E;">Sistem hazırlanıyor...</p>
        </div>
        <style>
            @keyframes pulse {
                0% { transform: scale(0.95); opacity: 0.7; }
                50% { transform: scale(1); opacity: 1; }
                100% { transform: scale(0.95); opacity: 0.7; }
            }
        </style>
    """, unsafe_allow_html=True)
    st.balloons()
    time.sleep(3.5)
    st.session_state['intro_done'] = True
    st.rerun()

# --- 5. ANA GİRİŞ PANELİ ---
if st.session_state['auth_role'] is None:
    st.title("🛡️ Alaşar Kalite & Finansal Takip Sistemi")
    st.info("Lütfen işlem yapmak istediğiniz birimi seçerek giriş yapınız.")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.expander("🛠️ REWORK BİRİMİ"):
            u_r = st.text_input("Kullanıcı Adı", key="u_rew")
            p_r = st.text_input("Şifre", type="password", key="p_rew")
            if st.button("Rework Girişi"):
                if u_r == "rework-2" and p_r == "alasar1234":
                    st.session_state['auth_role'] = 'rework'
                    st.rerun()
                else: st.error("Hatalı Giriş!")

    with col2:
        with st.expander("🔍 KALİTE (ÖMER BEY)"):
            u_o = st.text_input("Kullanıcı Adı", key="u_omer")
            p_o = st.text_input("Şifre", type="password", key="p_omer")
            if st.button("Ömer Bey Girişi"):
                if u_o == "omer" and p_o == "30052012":
                    st.session_state['auth_role'] = 'omer'
                    st.rerun()
                else: st.error("Hatalı Giriş!")

    with col3:
        with st.expander("👑 YÖNETİCİ (PATRON)"):
            u_p = st.text_input("Kullanıcı Adı", key="u_pat")
            p_p = st.text_input("Şifre", type="password", key="p_pat")
            if st.button("Patron Girişi"):
                if u_p == "patron" and p_p == "alasar1234":
                    st.session_state['auth_role'] = 'patron'
                    st.rerun()
                else: st.error("Yetkisiz Giriş!")

# --- 6. BİRİM PANELLERİ ---
else:
    st.sidebar.title(f"👤 {st.session_state['auth_role'].upper()}")
    st.sidebar.button("🚪 Sistemden Çıkış", on_click=logout)

    # --- REWORK PANELİ ---
    if st.session_state['auth_role'] == 'rework':
        st.header("🛠️ Rework Birimi Giriş Ekranı")
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

            if st.form_submit_button("💾 Kaydet ve Ömer Bey'e Gönder"):
                df = veriyi_oku()
                saat = round(miktar / ph, 2)
                mask = (df["İrsaliye_No"].astype(str) == str(irsaliye)) | (df["Referans_No"].astype(str) == str(ref))
                
                if mask.any():
                    df.loc[mask, ["pH", "Miktar", "Talep_Edilen_Saat", "Hakedis_Tutari", "Kayıp_Zaman_Nedeni", "Son_Durum", "Güncelleme_Tarihi", "Veri_Kaynagi"]] = [
                        ph, miktar, saat, saat * SAATLIK_BIRIM_FIYAT, tamir_aciklama, "Beklemede (İç Kayıt)", datetime.now().strftime("%Y-%m-%d %H:%M"), "REWORK"
                    ]
                    st.info("Mevcut kayıt güncellendi.")
                else:
                    yeni_satir = {
                        "Kayit_ID": f"RWK-{len(df)+1:04d}", "İrsaliye_No": irsaliye, "Referans_No": ref, "Dönem_Yıl": yil, "Dönem_Ay": ay,
                        "pH": ph, "Miktar": miktar, "Kayıp_Zaman_Nedeni": tamir_aciklama, "Yapılacak_İşin_Tanımı": "Rework İşlemi",
                        "Talep_Edilen_Saat": saat, "Hakedis_Tutari": saat * SAATLIK_BIRIM_FIYAT, "Son_Durum": "Beklemede (İç Kayıt)", 
                        "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"), "Veri_Kaynagi": "REWORK"
                    }
                    df = pd.concat([df, pd.DataFrame([yeni_satir])], ignore_index=True)
                    st.success("Yeni kayıt oluşturuldu.")
                veriyi_yaz(df)

    # --- ÖMER BEY PANELİ (KALİTE) ---
    elif st.session_state['auth_role'] == 'omer':
        st.header("🔍 Kalite ve Ana Tablo Yönetimi")
        tab1, tab2, tab3 = st.tabs(["📊 ANA TABLO", "✅ ONAY BEKLEYENLER", "➕ MANUEL KAYIT"])
        
        df_k = veriyi_oku()
        
        with tab1:
            st.subheader("Müşteri Kayıp Zaman Takip Ana Tablosu")
            # Kaynağa göre renklendirme veya etiketleme görünür olacak
            st.dataframe(df_k, use_container_width=True, hide_index=True)
            
        with tab2:
            taslaklar = df_k[df_k["Son_Durum"] == "Beklemede (İç Kayıt)"]
            if not taslaklar.empty:
                st.subheader("Onay Bekleyen Kayıtlar")
                secilen_id = st.selectbox("Detayını Görmek ve İşlem Yapmak İçin Seçin", taslaklar["Kayit_ID"].tolist())
                
                # SEÇİLEN KAYDIN DETAYLARI (Ömer Bey'in görebilmesi için)
                detay = taslaklar[taslaklar["Kayit_ID"] == secilen_id].iloc[0]
                
                # Detay Görünümü Kartı
                st.markdown(f"""
                <div style="background-color:#F0F2F6; padding:20px; border-radius:10px; border-left: 5px solid #2E86C1;">
                    <h4>📋 Kayıt Detayları ({detay['Veri_Kaynagi']})</h4>
                    <div style="display: flex; justify-content: space-between;">
                        <p><b>İrsaliye No:</b> {detay['İrsaliye_No']}</p>
                        <p><b>Referans No:</b> {detay['Referans_No']}</p>
                        <p><b>Dönem:</b> {detay['Dönem_Ay']} {detay['Dönem_Yıl']}</p>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <p><b>pH (Hız):</b> {detay['pH']}</p>
                        <p><b>Miktar:</b> {detay['Miktar']}</p>
                        <p><b>Hesaplanan Saat:</b> {detay['Talep_Edilen_Saat']}</p>
                    </div>
                    <p><b>Hata/İşlem Nedeni:</b> {detay['Kayıp_Zaman_Nedeni']}</p>
                </div>
                """, unsafe_allow_html=True)

                notu = st.text_area("Özel Kalite/Mutabakat Notunuz", placeholder="Buraya eklemek istediğiniz notu yazın...")
                
                c1, c2 = st.columns(2)
                if c1.button("✅ MUTABAKATA GÖNDER", use_container_width=True):
                    df_k.loc[df_k["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu"]] = ["Mutabakat Bekliyor", notu]
                    veriyi_yaz(df_k); st.rerun()
                if c2.button("❌ KAYDI REDDET / SİL", use_container_width=True):
                    df_k.loc[df_k["Kayit_ID"] == secilen_id, "Son_Durum"] = "Kalite Reddedildi"
                    veriyi_yaz(df_k); st.rerun()
            else:
                st.info("Şu an onay bekleyen bir kayıt bulunmuyor.")
            
            st.markdown("---")
            st.subheader("📢 Mutabık Kalınanlar (Yönetici Onayına Hazır)")
            mutabakat = df_k[df_k["Son_Durum"] == "Mutabakat Bekliyor"]
            st.dataframe(mutabakat, use_container_width=True)
            if not mutabakat.empty:
                if st.button("TÜMÜNÜ KESİNLEŞTİR VE PATRONA GÖNDER", type="primary", use_container_width=True):
                    df_k.loc[df_k["Son_Durum"] == "Mutabakat Bekliyor", "Son_Durum"] = "Onaylandı"
                    veriyi_yaz(df_k); st.success("Rapor başarıyla kesinleşti."); st.rerun()

        with tab3:
            st.subheader("Ömer Bey - Manuel Kayıt Girişi")
            with st.form("manuel_form"):
                mc1, mc2 = st.columns(2)
                with mc1:
                    m_irs = st.text_input("İrsaliye No")
                    m_ref = st.text_input("Referans No")
                    m_neden = st.text_area("İşlem/Kayıp Zaman Nedeni")
                with mc2:
                    m_ph = st.number_input("pH (Hız)", min_value=0.1, value=7.0)
                    m_mik = st.number_input("Miktar", min_value=1, value=1)
                    m_sirket = st.selectbox("Şirket", ["Alaşar", "Hakan Kalıp Plastik"])
                
                if st.form_submit_button("Sisteme Manuel Ekle"):
