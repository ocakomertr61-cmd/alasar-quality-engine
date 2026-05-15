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
    "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi",
    "Yonetici_Onay_Durumu", "Hakedis_Tutari", "Legrand_Kesinti_Tutari"
]

SAATLIK_BIRIM_FIYAT = 491  # TL

# --- EXCEL VE SİSTEM HAZIRLAMA ---
def baslangic_ayarlarini_yap():
    if not os.path.exists(DOSYA_ADI):
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl') as writer:
            pd.DataFrame(columns=KOLONLAR).to_excel(writer, sheet_name='Veriler', index=False)
            pd.DataFrame([{"anahtar": "admin_pass", "deger": "30052012"}]).to_excel(writer, sheet_name='Sistem', index=False)
    else:
        with pd.ExcelWriter(DOSYA_ADI, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            try:
                df_check = pd.read_excel(DOSYA_ADI, sheet_name='Veriler')
                for col in KOLONLAR:
                    if col not in df_check.columns: 
                        if col == "Yonetici_Onay_Durumu": df_check[col] = "Beklemede"
                        elif "Tutari" in col: df_check[col] = 0.0
                        else: df_check[col] = "-"
                df_check.to_excel(writer, sheet_name='Veriler', index=False)
            except:
                pd.DataFrame(columns=KOLONLAR).to_excel(writer, sheet_name='Veriler', index=False)
            
            try: pd.read_excel(DOSYA_ADI, sheet_name='Sistem')
            except: pd.DataFrame([{"anahtar": "admin_pass", "deger": "30052012"}]).to_excel(writer, sheet_name='Sistem', index=False)

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
        st.error(f"Excel Yazma Hatası: {e}"); return False

def parola_getir():
    df_sistem = pd.read_excel(DOSYA_ADI, sheet_name='Sistem')
    return str(df_sistem[df_sistem['anahtar'] == 'admin_pass']['deger'].values[0])

# --- ANA ARAYÜZ ---
st.title("⏱️ Kurumsal Kayıp Zaman ve Ek İşçilik Takip Motoru")

df_ana = veriyi_oku()
toplam_saat = df_ana["Talep_Edilen_Saat"].sum() if not df_ana.empty else 0
c1, c2 = st.columns([3, 1])
with c2:
    st.metric(label="📊 GENEL TOPLAM SAAT", value=f"{toplam_saat:,.2f} Saat")

st.markdown("---")

# --- KULLANICI GİRİŞİ (SOL PANEL) VE TABLO (SAĞ PANEL) ---
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
    with k1: ph = st.number_input("pH Değeri", min_value=0.01, value=7.0, step=0.1)
    with k2: miktar = st.number_input("Miktar", min_value=1, value=1000, step=1)
    
    hesaplanan_saat = round(miktar / ph, 2)
    hakedis = round(hesaplanan_saat * SAATLIK_BIRIM_FIYAT, 2)
    st.info(f"🧮 Saat: {hesaplanan_saat} | Hakediş: {hakedis:,.2f} TL")
    
    legrand_kesinti = st.number_input("Legrand Kesinti Tutarı (TL)", min_value=0.0, value=0.0)
    neden = st.text_area("Kayıp Zaman Nedeni")
    is_tanimi = st.text_area("Yapılacak İşin Tanımı")
    talep_tarihi = st.date_input("Talep Tarihi", datetime.now())
    durum = st.selectbox("İlk Durum", ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"])

    if st.button("💾 Kaydı Ekle ve Yöneticiye Gönder", use_container_width=True):
        df_mevcut = veriyi_oku()
        yeni_id = f"REQ-{(len(df_mevcut) + 1):04d}"
        yeni_satir = {
            "Kayit_ID": yeni_id, "Şirket": sirket, "Referans_No": ref_no, "Dönem_Yıl": donem_yil, "Dönem_Ay": donem_ay, 
            "pH": ph, "Miktar": miktar, "Kayıp_Zaman_Nedeni": neden, "Yapılacak_İşin_Tanımı": is_tanimi, 
            "Onay_Veren": onay_veren, "Talep_Edilen_Saat": hesaplanan_saat, "Müşteri_Onay_Tarihi": "-", 
            "Talep_Tarihi": str(talep_tarihi), "Son_Durum": durum, "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Yonetici_Onay_Durumu": "Yöneticiye Gönderildi", "Hakedis_Tutari": hakedis, "Legrand_Kesinti_Tutari": legrand_kesinti
        }
        df_mevcut = pd.concat([df_mevcut, pd.DataFrame([yeni_satir])], ignore_index=True)
        if veriyi_yaz(df_mevcut): st.success(f"✔️ {yeni_id} Yöneticiye İletildi!"); st.rerun()

with sag_kol:
    st.subheader("📊 Mevcut Süreç Takip Listesi")
    if not df_ana.empty:
        st.dataframe(df_ana, use_container_width=True, hide_index=True)
    else: st.info("Kayıt yok.")

# --- 👑 YÖNETİCİ (PATRON) ÖZEL EKRANI ---
st.markdown("---")
with st.expander("👑 YÖNETİCİ GİRİŞİ (PATRON PANELI)"):
    u_name = st.text_input("Kullanıcı Adı")
    u_pass = st.text_input("Yönetici Şifresi", type="password")
    
    if u_name == "patron" and u_pass == "alasar1234":
        st.success("Hoşgeldiniz Sayın Yönetici. Finansal özet aşağıdadır:")
        
        # Sadece Yöneticiye Gönderilenleri Filtrele
        df_yonetici = df_ana[df_ana["Yonetici_Onay_Durumu"] == "Yöneticiye Gönderildi"]
        
        if not df_yonetici.empty:
            # Finansal Özet Kartları
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Toplam Talep (Saat)", f"{df_yonetici['Talep_Edilen_Saat'].sum():,.2f}")
            m2.metric("Toplam Onaylanan (Saat)", f"{df_yonetici[df_yonetici['Son_Durum']=='Onaylandı']['Talep_Edilen_Saat'].sum():,.2f}")
            m3.metric("Toplam Hakediş (TL)", f"{df_yonetici['Hakedis_Tutari'].sum():,.2f} TL")
            m4.metric("Legrand Kesinti (TL)", f"{df_yonetici['Legrand_Kesinti_Tutari'].sum():,.2f} TL")
            
            st.write("### Onay Bekleyen Rapor Detayı")
            st.table(df_yonetici[["Kayit_ID", "Şirket", "Referans_No", "Talep_Edilen_Saat", "Hakedis_Tutari", "Legrand_Kesinti_Tutari", "Son_Durum"]])
            
            if st.button("Tümünü Onayla ve Arşivle"):
                df_ana.loc[df_ana["Yonetici_Onay_Durumu"] == "Yöneticiye Gönderildi", "Yonetici_Onay_Durumu"] = "Onaylandı"
                if veriyi_yaz(df_ana): st.success("Tüm raporlar onaylandı."); st.rerun()
        else:
            st.info("Şu an onay bekleyen yeni bir rapor bulunmamaktadır.")
    elif u_name != "":
        st.error("Kullanıcı adı veya şifre hatalı!")

# --- GÜVENLİK VE AYARLAR ---
st.markdown("---")
with st.expander("🛡️ Sistem Güvenlik Ayarları"):
    tab1, tab2 = st.tabs(["🔥 Veri Sıfırlama", "🔑 Parola Değiştirme"])
    with tab1:
        p_sil = st.text_input("Yönetici Parolası (Silme)", type="password")
        if st.button("TÜM VERİLERİ SİL"):
            if p_sil == parola_getir():
                if veriyi_yaz(pd.DataFrame(columns=KOLONLAR)): st.success("Sistem sıfırlandı."); st.rerun()
            else: st.error("Parola Yanlış!")
