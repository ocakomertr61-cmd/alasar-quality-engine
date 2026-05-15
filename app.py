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
st.divider()

# Sol Panel: Yeni Kayıt Girişi | Sağ Panel: Mevcut Veriler ve Güncelleme
sol_kol, sag_kol = st.columns([1, 2])

with sol_kol:
    st.subheader("📝 Yeni Talep Girişi")
    
    sirket = st.selectbox("Şirket Seçimi", ["Hakan Kalıp Plastik", "Alaşar"])
    ref_no = st.text_input("Referans No (Örn: REF-9921)")
    
    # pH ve Miktar Yan Yana
    k1, k2 = st.columns(2)
    with k1:
        ph = st.number_input("pH Değeri", min_value=0.1, max_value=14.0, value=7.0, step=0.1)
    with k2:
        miktar = st.number_input("Miktar", min_value=1, value=1000, step=1)
        
    # Otomatik Formül Gösterimi (Miktar / pH)
    hesaplanan_saat = round(miktar / ph, 2) if ph != 0 else 0
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
        yeni_id = f"REQ-{(len(df_mevcut) + 1):04d}"
        
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
        # Tabloyu Web Sayfasında Göster
        st.dataframe(df_goster[[
            "Kayit_ID", "Şirket", "Referans_No", "Talep_Edilen_Saat", "Son_Durum", "Güncelleme_Tarihi"
        ]], use_container_width=True, hide_index=True)
        
        st.hr()
        st.subheader("🔄 Durum Güncelleme Paneli")
        
        # Güncellenecek ID ve Yeni Durum Seçimi yan yana
        g1, g2 = st.columns(2)
        with g1:
            secilen_id = st.selectbox("Durumu Değişecek Kayıt ID", df_goster["Kayit_ID"].tolist())
        with g2:
            yeni_durum = st.selectbox("Yeni Durum Seçin", ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"])
            
        if st.button("🔄 Durumu Güncelle ve Excel'e İşle", use_container_width=True):
            df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Son_Durum"] = yeni_durum
            df_goster.loc[df_goster["Kayit_ID"] == secilen_id, "Güncelleme_Tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            if veriyi_yaz(df_goster):
                st.success(f"✔️ {secilen_id} kaydı '{yeni_durum}' olarak güncellendi!")
                st.rerun()
    else:
        st.info("Henüz veritabanında kayıtlı bir takip bulunmuyor. Soldaki panelden ilk kaydı ekleyebilirsiniz.")
