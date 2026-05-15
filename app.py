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

# Sol Panel: Yeni Kayıt Girişi | Sağ Panel: Mevcut Veriler ve Düzenleme
sol_kol, sag_kol = st.columns([1, 2])

with sol_kol:
    st.subheader("📝 Yeni Talep Girişi")
    
    sirket = st.selectbox("Şirket Seçimi", ["Hakan Kalıp Plastik", "Alaşar"])
    ref_no = st.text_input("Referans No (Örn: REF-9921)")
    
    k1, k2 = st.columns(2)
    with k1:
        ph = st.number_input("pH Değeri", min_value=0.0, max_value=10000.0, value=7.0, step=0.1)
    with k2:
        miktar = st.number_input("Miktar", min_value=1, value=1000, step=1)
        
    hesaplanan_saat = round(miktar / ph, 2) if ph != 0 else 0.0
    st.info(f"🧮 **Otomatik Hesaplanan Talep Saati:** {hesaplanan_saat} Saat")
    
    neden = st.text_area("Kayıp Zaman Nedeni")
    is_tanimi = st.text_area("Yapılacak İşin Tanımı")
    
    t1, t2 = st.columns(2)
    with t1:
        talep_tarihi = st.date_input("Talep Tarihi", datetime.now())
    with t2:
        onay_durumu_tarih = st.checkbox("Müşteri Onay Tarihi Var mı?")
        onay_tarihi = st.date_input("Müşteri Onay Tarihi", datetime.now()) if onay_durumu_tarih else "-"

    durum = st.selectbox("İlk Durum", ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"])

    if st.button("💾 Kaydı Veritabanına Ekle", use_container_width=True):
        df_mevcut = veriyi_oku()
        
        # BENZERSİZ ID SİSTEMİ
        if not df_mevcut.empty and "Kayit_ID" in df_mevcut.columns:
            try:
                sadece_sayilar = df_mevcut["Kayit_ID"].str.replace("REQ-", "").astype(int)
                yeni_id = f"REQ-{(sadece_sayilar.max() + 1):04d}"
            except:
                yeni_id = f"REQ-{(len(df_mevcut) + 1):04d}"
        else:
            yeni_id = "REQ-0001"
        
        yeni_satir = {
            "Kayit_ID": yeni_id, "Şirket": sirket, "Referans_No": ref_no, "pH": ph, "Miktar": miktar,
            "Kayıp_Zaman_Nedeni": neden, "Yapılacak_İşin_Tanımı": is_tanimi, "Talep_Edilen_Saat": hesaplanan_saat,
            "Müşteri_Onay_Tarihi": str(onay_tarihi), "Talep_Tarihi": str(talep_tarihi), "Son_Durum": durum,
            "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        df_mevcut = pd.concat([df_mevcut, pd.DataFrame([yeni_satir])], ignore_index=True)
        if veriyi_yaz(df_mevcut):
            st.success(f"✔️ {yeni_id} başarıyla eklendi!")
            st.rerun()

with sag_kol:
    st.subheader("📊 Mevcut Süreç Takip Listesi")
    df_goster = veriyi_oku()
    
    if not df_goster.empty:
        st.dataframe(df_goster, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🔄 Veri Düzenleme ve Güncelleme")
        
        secilen_id = st.selectbox("Düzenlenecek ID", df_goster["Kayit_ID"].tolist())
        kayit_verisi = df_goster[df_goster["Kayit_ID"] == secilen_id].iloc[0]
        
        # GÜNCELLEME FORMU (Hata düzeltildi)
        with st.form(key="duzenleme_formu"):
            g_sirket = st.selectbox("Şirket", ["Hakan Kalıp Plastik", "Alaşar"], index=["Hakan Kalıp Plastik", "Alaşar"].index(kayit_verisi["Şirket"]))
            g_ref_no = st.text_input("Referans No", value=str(kayit_verisi["Referans_No"]))
            
            gk1, gk2 = st.columns(2)
            with gk1:
                g_ph = st.number_input("pH Değeri ", min_value=0.0, max_value=10000.0, value=float(kayit_verisi["pH"]))
            with gk2:
                g_miktar = st.number_input("Miktar ", min_value=1, value=int(kayit_verisi["Miktar"]))
            
            g_neden = st.text_area("Neden", value=str(kayit_verisi["Kayıp_Zaman_Nedeni"]))
            g_is_tanimi = st.text_area("İş Tanımı", value=str(kayit_verisi["Yapılacak_İşin_Tanımı"]))
            
            g_durum = st.selectbox("Son Durum", ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"], index=["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"].index(kayit_verisi["Son_Durum"]))
            
            # Formun gönderilmesi için tek ve doğru buton
            submit_button = st.form_submit_button(label="⚙️ Değişiklikleri Kaydet", use_container_width=True)
            
            if submit_button:
                g_saat = round(g_miktar / g_ph, 2) if g_ph != 0 else 0.0
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, ["Şirket", "Referans_No", "pH", "Miktar", "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", "Talep_Edilen_Saat", "Son_Durum", "Güncelleme_Tarihi"]] = [
                    g_sirket, g_ref_no, g_ph, g_miktar, g_neden, g_is_tanimi, g_saat, g_durum, datetime.now().strftime("%Y-%m-%d %H:%M")
                ]
                if veriyi_yaz(df_goster):
                    st.success("Kayıt başarıyla güncellendi!")
                    st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Kayıt Sil")
        sil_id = st.selectbox("Silinecek ID", df_goster["Kayit_ID"].tolist(), key="sil_sb")
        if st.button(f"❌ {sil_id} Kaydını Sil", use_container_width=True):
            df_yeni = df_goster[df_goster["Kayit_ID"] != sil_id]
            if veriyi_yaz(df_yeni):
                st.success("Kayıt silindi.")
                st.rerun()
    else:
        st.info("Kayıt bulunamadı.")
