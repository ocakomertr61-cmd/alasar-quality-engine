import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Sayfa Genişlik Ayarı
st.set_page_config(page_title="Kurumsal Kayıp Zaman Motoru", layout="wide")

DOSYA_ADI = "kurumsal_takip_veritabani.xlsx"
KOLONLAR = [
    "Kayit_ID", "Şirket", "Referans_No", "Dönem_Yıl", "Dönem_Ay", "pH", "Miktar", 
    "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", "Onay_Veren", "Talep_Edilen_Saat",
    "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi"
]

# --- EXCEL VE PAROLA SİSTEMİ HAZIRLAMA ---
def baslangic_ayarlarini_yap():
    if not os.path.exists(DOSYA_ADI):
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl') as writer:
            pd.DataFrame(columns=KOLONLAR).to_excel(writer, sheet_name='Veriler', index=False)
            pd.DataFrame([{"anahtar": "admin_pass", "deger": "30052012"}]).to_excel(writer, sheet_name='Sistem', index=False)
    else:
        # Mevcut dosyada eksik sayfa veya kolon kontrolü
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            try:
                df_check = pd.read_excel(DOSYA_ADI, sheet_name='Veriler')
                for col in KOLONLAR:
                    if col not in df_check.columns: df_check[col] = "-"
                df_check.to_excel(writer, sheet_name='Veriler', index=False)
            except:
                pd.DataFrame(columns=KOLONLAR).to_excel(writer, sheet_name='Veriler', index=False)
            
            try:
                pd.read_excel(DOSYA_ADI, sheet_name='Sistem')
            except:
                pd.DataFrame([{"anahtar": "admin_pass", "deger": "30052012"}]).to_excel(writer, sheet_name='Sistem', index=False)

baslangic_ayarlarini_yap()

def veriyi_oku():
    try: return pd.read_excel(DOSYA_ADI, sheet_name='Veriler')
    except: return pd.DataFrame(columns=KOLONLAR)

def veriyi_yaz(df):
    try:
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name='Veriler', index=False)
        return True
    except Exception as e:
        st.error(f"Excel Yazma Hatası: {e}")
        return False

def parola_getir():
    df_sistem = pd.read_excel(DOSYA_ADI, sheet_name='Sistem')
    return str(df_sistem[df_sistem['anahtar'] == 'admin_pass']['deger'].values[0])

def parola_guncelle(yeni_p):
    df_sistem = pd.DataFrame([{"anahtar": "admin_pass", "deger": str(yeni_p)}])
    with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df_sistem.to_excel(writer, sheet_name='Sistem', index=False)

# --- WEB ARAYÜZÜ ---
st.title("⏱️ Kurumsal Kayıp Zaman ve Ek İşçilik Takip Motoru")

df_toplam = veriyi_oku()
toplam_saat = df_toplam["Talep_Edilen_Saat"].sum() if not df_toplam.empty else 0
c1, c2 = st.columns([3, 1])
with c2:
    st.metric(label="📊 TOPLAM TALEP EDİLEN SAAT", value=f"{toplam_saat:,.2f} Saat")

st.markdown("---")

sol_kol, sag_kol = st.columns([1, 2])

with sol_kol:
    st.subheader("📝 Yeni Talep Girişi")
    sirket = st.selectbox("Şirket Seçimi", ["Hakan Kalıp Plastik", "Alaşar"])
    ref_no = st.text_input("Referans No")
    y1, y2 = st.columns(2)
    with y1: donem_yil = st.selectbox("Dönem Yılı", [str(y) for y in range(2024, 2031)], index=2)
    with y2: donem_ay = st.selectbox("Dönem Ayı", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
    onay_veren = st.text_input("Onay Veren İlgili")
    k1, k2 = st.columns(2)
    with k1: ph = st.number_input("pH Değeri", min_value=0.0, max_value=10000.0, value=7.0, step=0.1)
    with k2: miktar = st.number_input("Miktar", min_value=1, value=1000, step=1)
    hesaplanan_saat = round(miktar / ph, 2) if ph != 0 else 0.0
    st.info(f"🧮 **Hesaplanan:** {hesaplanan_saat} Saat")
    neden = st.text_area("Kayıp Zaman Nedeni")
    is_tanimi = st.text_area("Yapılacak İşin Tanımı")
    talep_tarihi = st.date_input("Talep Tarihi", datetime.now())
    durum = st.selectbox("İlk Durum", ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"])

    if st.button("💾 Kaydı Veritabanına Ekle", use_container_width=True):
        df_mevcut = veriyi_oku()
        if not df_mevcut.empty:
            try:
                sadece_sayilar = df_mevcut["Kayit_ID"].str.replace("REQ-", "").astype(int)
                yeni_id = f"REQ-{(sadece_sayilar.max() + 1):04d}"
            except: yeni_id = f"REQ-{(len(df_mevcut) + 1):04d}"
        else: yeni_id = "REQ-0001"
        
        yeni_satir = {
            "Kayit_ID": yeni_id, "Şirket": sirket, "Referans_No": ref_no, "Dönem_Yıl": donem_yil, "Dönem_Ay": donem_ay, 
            "pH": ph, "Miktar": miktar, "Kayıp_Zaman_Nedeni": neden, "Yapılacak_İşin_Tanımı": is_tanimi, 
            "Onay_Veren": onay_veren, "Talep_Edilen_Saat": hesaplanan_saat, "Müşteri_Onay_Tarihi": "-", 
            "Talep_Tarihi": str(talep_tarihi), "Son_Durum": durum, "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        df_mevcut = pd.concat([df_mevcut, pd.DataFrame([yeni_satir])], ignore_index=True)
        if veriyi_yaz(df_mevcut):
            st.success(f"✔️ {yeni_id} eklendi!"); st.rerun()

with sag_kol:
    st.subheader("📊 Mevcut Süreç Takip Listesi")
    df_goster = veriyi_oku()
    if not df_goster.empty:
        st.dataframe(df_goster, use_container_width=True, hide_index=True)
        st.markdown("---")
        st.subheader("🔄 Veri Düzenleme")
        secilen_id = st.selectbox("Düzenlenecek ID", df_goster["Kayit_ID"].tolist())
        kv = df_goster[df_goster["Kayit_ID"] == secilen_id].iloc[0]
        yillar = [str(y) for y in range(2024, 2031)]; aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]; durumlar = ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"]
        idx_yil = yillar.index(str(kv["Dönem_Yıl"])) if str(kv["Dönem_Yıl"]) in yillar else 2
        idx_ay = aylar.index(str(kv["Dönem_Ay"])) if str(kv["Dönem_Ay"]) in aylar else 0
        idx_durum = durumlar.index(str(kv["Son_Durum"])) if str(kv["Son_Durum"]) in durumlar else 0

        with st.form(key="duzenleme_formu"):
            col1, col2 = st.columns(2)
            with col1:
                g_sirket = st.selectbox("Şirket", ["Hakan Kalıp Plastik", "Alaşar"], index=0 if kv["Şirket"] == "Hakan Kalıp Plastik" else 1)
                g_yil = st.selectbox("Dönem Yıl", yillar, index=idx_yil)
                g_onaylayan = st.text_input("Onay Veren", value=str(kv["Onay_Veren"]))
            with col2:
                g_ref = st.text_input("Ref No", value=str(kv["Referans_No"]))
                g_ay = st.selectbox("Dönem Ay", aylar, index=idx_ay)
                g_durum = st.selectbox("Durum", durumlar, index=idx_durum)
            gk1, gk2 = st.columns(2)
            with gk1: g_ph = st.number_input("pH", value=float(kv["pH"]) if pd.notnull(kv["pH"]) else 7.0)
            with gk2: g_miktar = st.number_input("Miktar ", value=int(kv["Miktar"]) if pd.notnull(kv["Miktar"]) else 1000)
            if st.form_submit_button(label="⚙️ Güncelle", use_container_width=True):
                g_saat = round(g_miktar / g_ph, 2) if g_ph != 0 else 0.0
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, ["Şirket", "Referans_No", "Dönem_Yıl", "Dönem_Ay", "Onay_Veren", "pH", "Miktar", "Talep_Edilen_Saat", "Son_Durum", "Güncelleme_Tarihi"]] = [g_sirket, g_ref, g_yil, g_ay, g_onaylayan, g_ph, g_miktar, g_saat, g_durum, datetime.now().strftime("%Y-%m-%d %H:%M")]
                if veriyi_yaz(df_goster): st.success("Güncellendi!"); st.rerun()

        st.markdown("---")
        # TEKİL SİLME
        sil_id = st.selectbox("Silinecek ID", df_goster["Kayit_ID"].tolist(), key="sil_sb")
        if st.button(f"❌ {sil_id} Kaydını Sil", use_container_width=True):
            df_yeni = df_goster[df_goster["Kayit_ID"] != sil_id]
            if veriyi_yaz(df_yeni): st.success("Silindi."); st.rerun()
    else:
        st.info("Kayıt yok.")

# --- EN SONA EKLENEN YÖNETİCİ PANELİ ---
st.markdown("---")
expander = st.expander("🛡️ Yönetici ve Güvenlik Paneli")
with expander:
    tab1, tab2 = st.tabs(["🔥 Toplu Veri Silme", "🔑 Parola Değiştirme"])
    
    with tab1:
        st.warning("Bu alandaki işlemler tüm veritabanını kalıcı olarak siler.")
        p_giris = st.text_input("İşlem için Yönetici Parolası", type="password", key="p_sil")
        if st.button("Tüm Verileri Temizle", use_container_width=True):
            if p_giris == parola_getir():
                st.session_state['silme_onayi'] = True
            else:
                st.error("Hatalı Parola!")
        
        if st.session_state.get('silme_onayi', False):
            st.error("⚠️ EMİN MİSİNİZ? Bu işlem geri alınamaz.")
            c_onay1, c_onay2 = st.columns(2)
            if c_onay1.button("EVET, HER ŞEYİ SİL"):
                if veriyi_yaz(pd.DataFrame(columns=KOLONLAR)):
                    st.session_state['silme_onayi'] = False
                    st.success("Veritabanı sıfırlandı."); st.rerun()
            if c_onay2.button("HAYIR, İPTAL ET"):
                st.session_state['silme_onayi'] = False
                st.rerun()

    with tab2:
        st.subheader("Parola Güncelleme")
        eski_p = st.text_input("Mevcut Parola", type="password")
        yeni_p = st.text_input("Yeni Parola", type="password")
        yeni_p_tekrar = st.text_input("Yeni Parola Tekrar", type="password")
        
        if st.button("Parolayı Güncelle", use_container_width=True):
            if eski_p != parola_getir():
                st.error("Mevcut parola hatalı!")
            elif yeni_p != yeni_p_tekrar:
                st.error("Yeni parolalar eşleşmiyor!")
            elif len(yeni_p) < 4:
                st.error("Yeni parola çok kısa!")
            else:
                parola_guncelle(yeni_p)
                st.success("Parola başarıyla değiştirildi.")
