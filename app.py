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
tab_rework, tab_kalite, tab_patron = st.tabs(["🛠️ REWORK BİRİMİ", "🔍 KALİTE ONAYI & MUTABAKAT", "👑 PATRON PANELİ"])

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
                "Son_Durum": "Beklemede (İç Kayıt)", "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            if veriyi_yaz(pd.concat([df, pd.DataFrame([yeni_satir])], ignore_index=True)):
                st.success("Kayıt Ömer Bey'in inceleme listesine eklendi."); st.rerun()

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
        st.success("Hoşgeldiniz Ömer Bey")
        
        df_k = veriyi_oku()
        
        # 1. BÖLÜM: KESİNLEŞMEMİŞ (İÇ) KAYITLAR
        st.markdown("### 📋 1. Taslak ve İnceleme Listesi (Kesinleşmemiş)")
        taslaklar = df_k[df_k["Son_Durum"] == "Beklemede (İç Kayıt)"]
        st.dataframe(taslaklar, use_container_width=True)
        
        if not taslaklar.empty:
            st.markdown("#### ⚡ Kayıt Yönetimi")
            secilen_id = st.selectbox("İşlem Seçin", taslaklar["Kayit_ID"].tolist(), key="k_sec")
            detay = taslaklar[taslaklar["Kayit_ID"] == secilen_id].iloc[0]
            notu = st.text_area("Kalite Notu (Opsiyonel)", key="not_k")
            
            c1, c2 = st.columns(2)
            if c1.button("✅ MUTABAKAT LİSTESİNE AL", use_container_width=True):
                # Bu buton veriyi "İnceleme Bekliyor"dan "Mutabakat Bekliyor"a çeker
                df_k.loc[df_k["Kayit_ID"] == secilen_id, ["Son_Durum", "Kalite_Notu"]] = ["Mutabakat Bekliyor", notu]
                veriyi_yaz(df_k); st.rerun()
            
            if c2.button("❌ KAYDI REDDET/SİL", use_container_width=True):
                df_k.loc[df_k["Kayit_ID"] == secilen_id, "Son_Durum"] = "Kalite Reddedildi"
                veriyi_yaz(df_k); st.rerun()

        st.markdown("---")
        
        # 2. BÖLÜM: MUTABAKAT VE RAPORLAMA
        st.markdown("### 📊 2. Mutabık Kalınan Kayıtlar (Yöneticiye Raporlanacak)")
        mutabakat_listesi = df_k[df_k["Son_Durum"] == "Mutabakat Bekliyor"]
        st.dataframe(mutabakat_listesi, use_container_width=True)
        
        if not mutabakat_listesi.empty:
            st.warning(f"Şu an mutabık kalınmış {len(mutabakat_listesi)} adet kayıt var.")
            if st.button("📢 YÖNETİCİYE RAPORU GÖNDER (KESİNLEŞTİR)", use_container_width=True, type="primary"):
                # TÜM mutabakat bekleyenleri "Onaylandı (Kesin)" yapar. Patron sadece bunları görür.
                df_k.loc[df_k["Son_Durum"] == "Mutabakat Bekliyor", "Son_Durum"] = "Onaylandı"
                veriyi_yaz(df_k)
                st.success("Rapor kesinleşti ve Yönetici paneline gönderildi!"); st.rerun()

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
        st.success("Kesinleşmiş Finansal Rapor (Müşteri Onaylı)")
        
        df_p = veriyi_oku()
        # Patron SADECE Ömer Bey'in "Raporu Gönder" dediği "Onaylandı" verileri görür
        kesin_liste = df_p[df_p["Son_Durum"] == "Onaylandı"]
        
        if not kesin_liste.empty:
            brut = kesin_liste["Hakedis_Tutari"].sum()
            kesinti = kesin_liste["Legrand_Kesinti_Tutari"].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Kesinleşmiş Saat", f"{kesin_liste['Talep_Edilen_Saat'].sum():,.2f}")
            m2.metric("Brüt Hakediş", f"{brut:,.2f} TL")
            m3.metric("Net Hakediş", f"{(brut - kesinti):,.2f} TL")
            
            st.write("### 📋 Kesinleşmiş İşlemler")
            st.dataframe(kesin_liste, use_container_width=True, hide_index=True)
        else:
            st.info("Ömer Bey tarafından henüz kesinleşmiş bir rapor gönderilmedi.")
