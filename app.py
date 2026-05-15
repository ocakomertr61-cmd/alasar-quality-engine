import os
from datetime import datetime
import pandas as pd

class KurumsalKayipZamanMotoru:
    def __init__(self, dosya_adi="kurumsal_takip_veritabani.xlsx"):
        self.dosya_adi = dosya_adi
        # İzin verilen geçerli seçim listeleri (Validasyon için)
        self.gecerli_sirketler = ["Hakan Kalıp Plastik", "Alaşar"]
        self.gecerli_durumlar = ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"]
        
        self.kolonlar = [
            "Kayit_ID", "Şirket", "Referans_No", "pH", "Miktar", 
            "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", 
            "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi"
        ]
        self._veritabanini_hazirla()

    def _veritabanini_hazirla(self):
        """Excel dosyası yoksa şablonu oluşturur."""
        if not os.path.exists(self.dosya_adi):
            df = pd.DataFrame(columns=self.kolonlar)
            df.to_excel(self.dosya_adi, index=False)
            print(f"[SİSTEM] Excel veritabanı oluşturuldu: {self.dosya_adi}")

    def yeni_kayit_ekle(self, sirket, ref_no, ph, miktar, neden, is_tanimi, talep_tarihi, onay_tarihi="-", durum="Onaylandı"):
        """Sisteme yeni bir takip kaydı ekler ve otomatik ID üretir."""
        
        # Şirket kontrolü
        if sirket not in self.gecerli_sirketler:
            print(f"[HATA] Geçersiz şirket! Şunlardan biri olmalı: {self.gecerli_sirketler}")
            return False

        # Durum kontrolü
        if durum not in self.gecerli_durumlar:
            print(f"[HATA] Geçersiz durum! Şunlardan biri olmalı: {self.gecerli_durumlar}")
            return False

        df = pd.read_excel(self.dosya_adi)

        # Otomatik Benzersiz ID Üretimi (Örn: REQ-0001)
        yeni_id = f"REQ-{(len(df) + 1):04d}"

        yeni_satir = {
            "Kayit_ID": yeni_id,
            "Şirket": sirket,
            "Referans_No": ref_no,
            "pH": ph,
            "Miktar": miktar,
            "Kayıp_Zaman_Nedeni": neden,
            "Yapılacak_İşin_Tanımı": is_tanimi,
            "Müşteri_Onay_Tarihi": onay_tarihi,
            "Talep_Tarihi": talep_tarihi,
            "Son_Durum": durum,
            "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        df = pd.concat([df, pd.DataFrame([yeni_satir])], ignore_index=True)
        df.to_excel(self.dosya_adi, index=False)
        print(f"[BAŞARILI] {yeni_id} kimliği ile yeni kayıt oluşturuldu ({sirket}).")
        return True

    def durum_guncelle(self, kayit_id, yeni_durum):
        """Mevcut bir kaydın son durumunu günceller ve Excel'i yeniler."""
        if yeni_durum not in self.gecerli_durumlar:
            print(f"[HATA] Geçersiz durum! Şunlardan biri olmalı: {self.gecerli_durumlar}")
            return False

        df = pd.read_excel(self.dosya_adi)

        # İlgili ID'ye sahip satırı bul
        if kayit_id in df["Kayit_ID"].values:
            # Durumu ve güncelleme zamanını değiştir
            df.loc[df["Kayit_ID"] == kayit_id, "Son_Durum"] = yeni_durum
            df.loc[df["Kayit_ID"] == kayit_id, "Güncelleme_Tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            df.to_excel(self.dosya_adi, index=False)
            print(f"[GÜNCELLENDİ] {kayit_id} numaralı kaydın durumu '{yeni_durum}' olarak değiştirildi.")
            return True
        else:
            print(f"[HATA] {kayit_id} bulunamadı!")
            return False

    def verileri_goster(self):
        """Mevcut tüm tabloyu ekrana basar."""
        return pd.read_excel(self.dosya_adi)


# --- SİSTEMİ ÇALIŞTIRMA VE TEST SENARYOLARI ---

motor = KurumsalKayipZamanMotoru()

print("\n--- 1. ADIM: YENİ KAYITLARIN EKLENMESİ ---")

# Kayıt 1: Hakan Kalıp Plastik için ek işçilik/proses talebi
motor.yeni_kayit_ekle(
    sirket="Hakan Kalıp Plastik",
    ref_no="REF-9921",
    ph="5.5",
    miktar=1250,
    neden="Kalıp yüzeyinde çapaklanma ve rivet deliği kayması",
    is_tanimi="Ekstra çapak temizleme ve rivet deliklerinin genişletilmesi",
    talep_tarihi="2026-05-12",
    durum="Red Oldu"  # İlk başta red gelmiş olsun
)

# Kayıt 2: Alaşar için ek işçilik talebi
motor.yeni_kayit_ekle(
    sirket="Alaşar",
    ref_no="REF-4412",
    ph="7.2",
    miktar=500,
    neden="Müşteri revizyon talebi (Legrand parça değişimi)",
    is_tanimi="Montaj hattında buton basmama sorunu çözümü ve parça değişimi",
    talep_tarihi="2026-05-14",
    onay_tarihi="2026-05-15",
    durum="Onaylandı"
)

print("\n--- 2. ADIM: MEVCUT VERİ DURUMU ---")
print(motor.verileri_goster()[["Kayit_ID", "Şirket", "Son_Durum", "Güncelleme_Tarihi"]])

print("\n--- 3. ADIM: GÜNCELLEME MOTORUNUN ÇALIŞTIRILMASI ---")
# REQ-0001 ID'li kaydın durumu revize edilerek onaylandı olarak değişiyor
motor.durum_guncelle(kayit_id="REQ-0001", yeni_durum="Revize Edilerek Onaylandı")

print("\n--- 4. ADIM: GÜNCELLEME SONRASI DURUM ---")
print(motor.verileri_goster()[["Kayit_ID", "Şirket", "Son_Durum", "Güncelleme_Tarihi"]])
