import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Sayfa Genişlik Ayarı
st.set_page_config(page_title="Kurumsal Kayıp Zaman Motoru", layout="wide")

DOSYA_ADI = "kurumsal_takip_veritabani.xlsx"
# Yeni kolonlar eklendi: Dönem_Yıl, Dönem_Ay, Onay_Veren
KOLONLAR = [
    "Kayit_ID", "Şirket", "Referans_No", "Dönem_Yıl", "Dönem_Ay", "pH", "Miktar", 
    "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", "Onay_Veren", "Talep_Edilen_Saat",
    "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi"
]

# --- EXCEL VERİTABANI HAZIRLAMA ---
if not os.path.exists(DOSYA_ADI):
    df = pd.DataFrame(columns=KOLONLAR)
    df.to_excel(DOSYA_ADI, index=False)
else:
    # Eğer dosya varsa ama yeni kolonlar yoksa otomatik ekle (Veri koruma)
    df_check = pd.read_excel(DOSYA_ADI)
    for col in KOLONLAR:
        if col not in df_check.columns:
            df_check[col] = "-"
    df_check.to_excel(DOSYA_ADI, index=False)

def veriyi_oku():
    try:
        return pd.read_excel(DOSYA_ADI)
    except PermissionError:
        st.error(f"⚠️ HATA: '{DOSYA_ADI}' dosyası açık! Lütfen kapatın.")
        return pd.DataFrame(columns=KOLONLAR)
    except Exception as e:
        st.error(f"Okuma hatası: {e}")
        return pd.DataFrame(columns=KOLONLAR)

def veriyi_yaz(df):
    try:
        df.to_excel(DOSYA_ADI, index=False)
        return True
    except PermissionError:
        st.error(f"⚠️ KİLİTLENME HATASI: Excel açık!")
        return False

# --- WEB ARAYÜZÜ ---
st.title("⏱️ Kurumsal Kayıp Zaman ve Ek İşçilik Takip Motoru")

# --- SAĞ ÜST TOPLAM SAAT GÖSTERGESİ ---
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
    ref_no = st.text_input("Referans No (Örn: REF-9921)")
    
    # Yeni Alanlar: Dönem ve Onay Veren
    y1, y2 = st.columns(2)
    with y1:
        donem_yil = st.selectbox("Dönem Yılı", [str(y) for y in range(2024, 2031)], index=2) # 2026 varsayılan
    with y2:
        donem_ay = st.selectbox("Dönem Ayı", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
    
    onay_veren = st.text_input("Onay Veren İlgili (İsim Soyisim)")

    k1, k2 = st.columns(2)
    with k1:
        ph = st.number_input("pH Değeri", min_value=0.0, max_value=10000.0, value=7.0, step=0.1)
    with k2:
        miktar = st.number_input("Miktar", min_value=1, value=1000, step=1)
        
    hesaplanan_saat = round(miktar / ph, 2) if ph != 0 else 0.0
    st.info(f"🧮 **Otomatik Hesaplanan:** {hesaplanan_saat} Saat")
    
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
        if not df_mevcut.empty and "Kayit_ID" in df_mevcut.columns:
            try:
                sadece_sayilar = df_mevcut["Kayit_ID"].str.replace("REQ-", "").astype(int)
                yeni_id = f"REQ-{(sadece_sayilar.max() + 1):04d}"
            except: yeni_id = f"REQ-{(len(df_mevcut) + 1):04d}"
        else: yeni_id = "REQ-0001"
        
        yeni_satir = {
            "Kayit_ID": yeni_id, "Şirket": sirket, "Referans_No": ref_no, 
            "Dönem_Yıl": donem_yil, "Dönem_Ay": donem_ay, "pH": ph, "Miktar": miktar,
            "Kayıp_Zaman_Nedeni": neden, "Yapılacak_İşin_Tanımı": is_tanimi, 
            "Onay_Veren": onay_veren, "Talep_Edilen_Saat": hesaplanan_saat,
            "Müşteri_Onay_Tarihi": str(onay_tarihi), "Talep_Tarihi": str(talep_tarihi), 
            "Son_Durum": durum, "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        df_mevcut = pd.concat([df_mevcut, pd.DataFrame([yeni_satir])], ignore_index=True)
        if veriyi_yaz(df_mevcut):
            st.success(f"✔️ {yeni_id} eklendi!")
            st.rerun()

with sag_kol:
    st.subheader("📊 Mevcut Süreç Takip Listesi")
    df_goster = veriyi_oku()
    
    if not df_goster.empty:
        st.dataframe(df_goster, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🔄 Veri Düzenleme")
        secilen_id = st.selectbox("Düzenlenecek ID", df_goster["Kayit_ID"].tolist())
        kayit_verisi = df_goster[df_goster["Kayit_ID"] == secilen_id].iloc[0]
        
        with st.form(key="duzenleme_formu"):
            col1, col2 = st.columns(2)
            with col1:
                g_sirket = st.selectbox("Şirket", ["Hakan Kalıp Plastik", "Alaşar"], index=0 if kayit_verisi["Şirket"] == "Hakan Kalıp Plastik" else 1)
                g_yil = st.selectbox("Dönem Yıl", [str(y) for y in range(2024, 2031)], index=[str(y) for y in range(2024, 2031)].index(str(kayit_verisi["Dönem_Yıl"])))
                g_onaylayan = st.text_input("Onay Veren", value=str(kayit_verisi["Onay_Veren"]))
            with col2:
                g_ref = st.text_input("Ref No", value=str(kayit_verisi["Referans_No"]))
                g_ay = st.selectbox("Dönem Ay", ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"], index=["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"].index(str(kayit_verisi["Dönem_Ay"])))
                g_durum = st.selectbox("Durum", ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"], index=["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"].index(str(kayit_verisi["Son_Durum"])))
            
            gk1, gk2 = st.columns(2)
            with gk1: g_ph = st.number_input("pH", value=float(kayit_verisi["pH"]))
            with gk2: g_miktar = st.number_input("Miktar ", value=int(kayit_verisi["Miktar"]))
            
            submit_button = st.form_submit_button(label="⚙️ Güncelle ve Yeniden Hesapla", use_container_width=True)
            
            if submit_button:
                g_saat = round(g_miktar / g_ph, 2) if g_ph != 0 else 0.0
                df_goster.loc[df_goster["Kayit_ID"] == secilen_id, ["Şirket", "Referans_No", "Dönem_Yıl", "Dönem_Ay", "Onay_Veren", "pH", "Miktar", "Talep_Edilen_Saat", "Son_Durum", "Güncelleme_Tarihi"]] = [
                    g_sirket, g_ref, g_yil, g_ay, g_onaylayan, g_ph, g_miktar, g_saat, g_durum, datetime.now().strftime("%Y-%m-%d %H:%M")
                ]
                if veriyi_yaz(df_goster):
                    st.success("Başarıyla güncellendi!")
                    st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Kayıt Sil")
        sil_id = st.selectbox("Silinecek ID", df_goster["Kayit_ID"].tolist(), key="sil_sb")
        if st.button(f"❌ {sil_id} Kaydını Sil", use_container_width=True):
            df_yeni = df_goster[df_goster["Kayit_ID"] != sil_id]
            if veriyi_yaz(df_yeni):
                st.success("Silindi.")
                st.rerun()
    else:
        st.info("Kayıt bulunamadı.")
