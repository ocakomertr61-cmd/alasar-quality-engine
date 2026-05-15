import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Sayfa Genişlik Ayarı
st.set_page_config(page_title="Kurumsal Kayıp Zaman Motoru", layout="wide")

DOSYA_ADI = "kurumsal_takip_veritabani.xlsx"
KOLONLAR = [
    "Kayit_ID", "Şirket", "Referans_No", "pH", "Miktar", 
    "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", "Talep_Edilen_Saat",
    "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi"
]

# --- EXCEL VERİTABANI HAZIRLAMA ---
if not os.path.exists(DOSYA_ADI):
    df = pd.DataFrame(columns=KOLONLAR)
    df.to_excel(DOSYA_ADI, index=False)

def veriyi_oku():
    try:
        return pd.read_excel(DOSYA_ADI)
    except PermissionError:
        st.error(f"⚠️ HATA: '{DOSYA_ADI}' dosyası şu an Excel'de açık! Lütfen Excel programını kapatın.")
        return pd.DataFrame(columns=KOLONLAR)
    except Exception as e:
        st.error(f"Dosya okuma hatası: {e}")
        return pd.DataFrame(columns=KOLONLAR)

def veriyi_yaz(df):
    try:
        df.to_excel(DOSYA_ADI, index=False)
        return True
    except PermissionError:
        st.error(f"⚠️ KİLİTLENME HATASI: Veriler Excel'e yazılamadı çünkü dosya açık! Lütfen Excel'i kapatın.")
        return False

# --- WEB ARAYÜZÜ BAŞLIĞI ---
st.title("⏱️ Kurumsal Kayıp Zaman ve Ek İşçilik Takip Motoru")
st.markdown("Müşteri talepleri, iç üretim ve grup şirketleri ek işçilik süreç yönetim paneli.")
st.markdown("---")

# Sol Panel: Yeni Kayıt Girişi | Sağ Panel: Mevcut Veriler, Güncelleme ve Silme
sol_kol, sag_kol = st.columns([1, 2])

with sol_kol:
    st.subheader("📝 Yeni Talep Girişi")
    
    sirket = st.selectbox("Şirket Seçimi", ["Hakan Kalıp Plastik", "Alaşar"])
    ref_no = st.text_input("Referans No (Örn: REF-9921)")
    
    # pH (0 - 10000) ve Miktar Yan Yana
    k1, k2 = st.columns(2)
    with k1:
        ph = st.number_input("pH Değeri", min_value=0.0, max_value=10000.0, value=7.0, step=0.1)
    with k2:
        miktar = st.number_input("Miktar", min_value=1, value=1000, step=1)
        
    # Otomatik Formül Gösterimi (Miktar / pH)
    hesaplanan_saat = round(miktar / ph, 2) if ph != 0 else 0.0
    st.info(f"🧮 **Otomatik Hesaplanan Talep Saati:** {hesaplanan_saat} Saat")
    
    neden = st.text_area("Kayıp Zaman Nedeni")
    is_tanimi = st.text_area("Yapılacak İşin Tanımı")
    
    # Tarihler Yan Yana
    t1, t2 = st.columns(2)
    with t1:
        talep_tarihi = st.date_input("Talep Tarihi", datetime.now())
    with t2:
        onay_durumu_tarih = st.checkbox("Müşteri Onay Tarihi Var mı?")
        onay_tarihi = st.date_input("Müşteri Onay Tarihi", datetime.now()) if onay_durumu_tarih else "-"

    durum = st.selectbox("İlk Durum", ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"])

    if st.button("💾 Kaydı Veritabanına Ekle", use_container_width=True):
        df_mevcut = veriyi_oku()
        
        # BENZERSİZ VE OTOMATİK ARTAN ID SİSTEMİ
        if not df_mevcut.empty and "Kayit_ID" in df_mevcut.columns:
            try:
                # REQ-0001 formatındaki sayısal kısmı çekip en yükseğini bulur
                sadece_sayilar = df_mevcut["Kayit_ID"].str.replace("REQ-", "").astype(int)
                en_yuksek_id = sadece_sayilar.max()
                yeni_id = f"REQ-{(en_yuksek_id + 1):04d}"
            except:
                yeni_id = f"REQ-{(len(df_mevcut) + 1):04d}"
        else:
            yeni_id = f"REQ-0001"
        
        yeni_satir = {
            "Kayit_ID": yeni_id, "Şirket": sirket, "Referans_No": ref_no, "pH": ph, "Miktar": miktar,
            "Kayıp_Zaman_Nedeni": neden, "Yapılacak_İşin_Tanımı": is_tanimi, "Talep_Edilen_Saat": hesaplanan_saat,
            "Müşteri_Onay_Tarihi": str(onay_tarihi), "Talep_Tarihi": str(talep_tarihi), "Son_Durum": durum,
            "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        df_mevcut = pd.concat([df_mevcut, pd.DataFrame([yeni_satir])], ignore_index=True)
        if veriyi_yaz(df_mevcut):
            st.success(f"✔️ {yeni_id} başarıyla Excel'e kaydedildi!")
            st.rerun()

with sag_kol:
    st.subheader("📊 Mevcut Süreç Takip Listesi")
    df_goster = veriyi_oku()
    
    if not df_goster.empty:
        # Tabloyu geniş formatta listeleme
        st.dataframe(df_goster, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🔄 Detaylı Veri Düzenleme Paneli")
        st.markdown("<small>Düzenlemek istediğiniz kaydı seçtiğinizde tüm bilgileri aşağıya gelecektir.</small>", unsafe_allow_html=True)
        
        # Düzenlenecek Kayıt ID Seçimi
        secilen_id = st.selectbox("Düzenlenecek Kayıt ID Seçin", df_goster["Kayit_ID"].tolist())
        
        # Seçilen kaydın mevcut verilerini Excel'den yakalama
        kayit_verisi = df_goster[df_goster["Kayit_ID"] == secilen_id].iloc[0]
        
        # TÜM VERİLERİ DÜZENLEME FORMU
        with st.form(key="guncelleme_formu"):
            g_sirket = st.selectbox("Şirket", ["Hakan Kalıp Plastik", "Alaşar"], index=["Hakan Kalıp Plastik", "Alaşar"].index(kayit_verisi["Şirket"]))
            g_ref_no = st.text_input("Referans No", value=str(kayit_verisi["Referans_No"]))
            
            gk1, gk2 = st.columns(2)
            with gk1:
                g_ph = st.number_input("pH Değeri ", min_value=0.0, max_value=10000.0, value=float(kayit_verisi["pH"]), step=0.1)
            with gk2:
                g_miktar = st.number_input("Miktar ", min_value=1, value=int(kayit_verisi["Miktar"]), step=1)
            
            g_neden = st.text_area("Kayıp Zaman Nedeni", value=str(kayit_verisi["Kayıp_Zaman_Nedeni"]))
            g_is_tanimi = st.text_area("Yapılacak İşin Tanımı", value=str(kayit_verisi["Yapılacak_İşin_Tanımı"]))
            
            gt1, gt2 = st.columns(2)
            with gt1:
                g_durum = st.selectbox("Son Durum", ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"], index=["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"].index(kayit_verisi["Son_Durum"]))
            with gt2:
                g_onay_tarihi = st.text_input("Müşteri Onay Tarihi (Değiştirmek istemiyorsanız dokunmayın)", value=str(kayit_verisi["Müşteri_Onay_Tarihi"]))

            form_guncelle_butonu = st.form_submit_with_no_sidebar_navigation()
            form_guncelle_butonu = st.form_submit_button("⚙️ Tüm Değişiklikleri Hesapla ve Excel'e Kaydet", use_container_width=True)
            
            if form_guncelle_butonu:
                # Yeni değerlere göre saati otomatik yeniden hesapla
                g_hesaplanan_saat = round(g_miktar / g_ph, 2) if g_ph != 0 else 0.0
                
                # Değerleri DataFrame üzerinde güncelle
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Şirket"] = g_sirket
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Referans_No"] = g_ref_no
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "pH"] = g_ph
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Miktar"] = g_miktar
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Kayıp_Zaman_Nedeni"] = g_neden
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Yapılacak_İşin_Tanımı"] = g_is_tanimi
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Talep_Edilen_Saat"] = g_hesaplanan_saat
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Son_Durum"] = g_durum
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Müşteri_Onay_Tarihi"] = g_onay_tarihi
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Güncelleme_Tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                if veriyi_yaz(df_goster):
                    st.success(f"✔️ {secilen_id} numaralı kaydın tüm verileri başarıyla güncellendi ve yeniden hesaplandı!")
                    st.rerun()

        # --- SEÇİLİ VERİLERİ SİLME ALANI ---
        st.markdown("---")
        st.subheader("🗑️ Güvenli Veri Silme Paneli")
        silinecek_id = st.selectbox("Veritabanından Kalıcı Olarak Silinecek ID", df_goster["Kayit_ID"].tolist(), key="silme_kutusu")
        
        if st.button(f"❌ {silinecek_id} Numaralı Kaydı Tamamen Sil", use_container_width=True):
            df_yeni = df_goster[df_goster["Kayit_ID"] != silinecek_id]
            if veriyi_yaz(df_yeni):
                st.success(f"✔️ {silinecek_id} kaydı veritabanından kalıcı olarak temizlendi!")
                st.rerun()
    else:
        st.info("Henüz veritabanında kayıtlı bir takip bulunmuyor. Soldaki panelden ilk kaydı ekleyebilirsiniz.")
