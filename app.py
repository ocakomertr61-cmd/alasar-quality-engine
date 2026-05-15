import os
from datetime import datetime
import pandas as pd
import sys

class KurumsalKayipZamanMotoru:
    def __init__(self, dosya_adi="kurumsal_takip_veritabani.xlsx"):
        self.dosya_adi = dosya_adi
        self.gecerli_sirketler = ["Hakan Kalıp Plastik", "Alaşar"]
        self.gecerli_durumlar = ["Onaylandı", "Red Oldu", "Revize Edilerek Onaylandı", "İptal"]
        
        self.kolonlar = [
            "Kayit_ID", "Şirket", "Referans_No", "pH", "Miktar", 
            "Kayıp_Zaman_Nedeni", "Yapılacak_İşin_Tanımı", "Talep_Edilen_Saat",
            "Müşteri_Onay_Tarihi", "Talep_Tarihi", "Son_Durum", "Güncelleme_Tarihi"
        ]
        self._veritabanini_hazirla()

    def _ekrana_yaz(self, mesaj):
        """Terminal tamponunu (buffer) zorla boşaltarak yazının anında ekrana gelmesini sağlar."""
        print(mesaj)
        sys.stdout.flush()

    def _veritabanini_hazirla(self):
        """Excel dosyası yoksa güvenli bir şekilde oluşturur."""
        try:
            if not os.path.exists(self.dosya_adi):
                df = pd.DataFrame(columns=self.kolonlar)
                df.to_excel(self.dosya_adi, index=False)
                self._ekrana_yaz(f"[SİSTEM] Yeni Excel veritabanı oluşturuldu: {self.dosya_adi}")
        except Exception as e:
            self._ekrana_yaz(f"[KRİTİK HATA] Excel dosyasına erişilemiyor! Hata: {e}")

    def yeni_kayit_ekle(self, sirket, ref_no, ph, miktar, neden, is_tanimi, talep_tarihi, onay_tarihi="-", durum="Onaylandı"):
        """Sisteme yeni kayıt ekler ve Miktar/pH formülünü işletir."""
        if sirket not in self.gecerli_sirketler:
            self._ekrana_yaz(f"[HATA] Geçersiz şirket! Şunlardan biri olmalı: {self.gecerli_sirketler}")
            return False

        if durum not in self.gecerli_durumlar:
            self._ekrana_yaz(f"[HATA] Geçersiz durum! Şunlardan biri olmalı: {self.gecerli_durumlar}")
            return False

        # --- TALEP EDİLEN SAAT HESAPLAMA (Miktar / pH) ---
        try:
            sayisal_ph = float(ph)
            sayisal_miktar = float(miktar)
            talep_edilen_saat = round(sayisal_miktar / sayisal_ph, 2) if sayisal_ph != 0 else 0.0
        except (ValueError, TypeError):
            self._ekrana_yaz("[UYARI] pH veya Miktar sayısal değil! Saat 0.0 kabul edildi.")
            talep_edilen_saat = 0.0

        # --- GÜVENLİ DOSYA YAZMA ---
        try:
            df = pd.read_excel(self.dosya_adi) if os.path.exists(self.dosya_adi) else pd.DataFrame(columns=self.kolonlar)
            yeni_id = f"REQ-{(len(df) + 1):04d}"

            yeni_satir = {
                "Kayit_ID": yeni_id, "Şirket": sirket, "Referans_No": ref_no, "pH": ph, "Miktar": miktar,
                "Kayıp_Zaman_Nedeni": neden, "Yapılacak_İşin_Tanımı": is_tanimi, "Talep_Edilen_Saat": talep_edilen_saat,
                "Müşteri_Onay_Tarihi": onay_tarihi, "Talep_Tarihi": talep_tarihi, "Son_Durum": durum,
                "Güncelleme_Tarihi": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            df = pd.concat([df, pd.DataFrame([yeni_satir])], ignore_index=True)
            df.to_excel(self.dosya_adi, index=False)
            self._ekrana_yaz(f"[BAŞARILI] {yeni_id} eklendi ({sirket}). Hesaplanan Saat: {talep_edilen_saat}")
            return True
        except PermissionError:
            self._ekrana_yaz(f"[KİLİTLENME HATASI] Excel dosyası açık olduğundan yazılamadı! Lütfen kapatın.")
            return False
        except Exception as e:
            self._ekrana_yaz(f"[HATA] Dosya yazma hatası: {e}")
            return False

    def durum_guncelle(self, kayit_id, yeni_durum):
        """Kayıt durumunu günceller."""
        if yeni_durum not in self.gecerli_durumlar:
            self._ekrana_yaz(f"[HATA] Geçersiz durum: {yeni_durum}")
            return False

        try:
            df = pd.read_excel(self.dosya_adi)
            if kayit_id in df["Kayit_ID"].values:
                df.loc[df["Kayit_ID"] == kayit_id, "Son_Durum"] = yeni_durum
                df.loc[df["Kayit_ID"] == kayit_id, "Güncelleme_Tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                df.to_excel(self.dosya_adi, index=False)
                self._ekrana_yaz(f"[GÜNCELLENDİ] {kayit_id} yeni durumu: '{yeni_durum}'")
                return True
            else:
                self._ekrana_yaz(f"[HATA] {kayit_id} bulunamadı!")
                return False
        except PermissionError:
            self._ekrana_yaz(f"[KİLİTLENME HATASI] Excel açık olduğundan durum güncellenemedi!")
            return False

    def verileri_goster(self):
        try:
            return pd.read_excel(self.dosya_adi)
        except Exception:
            return pd.DataFrame()


# --- DONMAYI ÖSLEYEN PANEL ÇALIŞTIRICISI ---
if __name__ == "__main__":
    motor = KurumsalKayipZamanMotoru()

    motor._ekrana_yaz("\n==================================================")
    motor._ekrana_yaz("    KAYIP ZAMAN TAKİP MOTORU BAŞLATILIYOR...     ")
    motor._ekrana_yaz("==================================================")

    motor._ekrana_yaz("\n[1] TEST VERİLERİ YÜKLENİYOR...")
    
    # Hakan Kalıp: 1250 / 5.5 = 227.27 Saat
    motor.yeni_kayit_ekle(
        sirket="Hakan Kalıp Plastik", ref_no="REF-9921", ph="5.5", miktar=1250,
        neden="Kalıp yüzeyinde çapaklanma", is_tanimi="Ekstra çapak temizleme işlemi",
        talep_tarihi="2026-05-12", durum="Red Oldu"
    )

    # Alaşar: 500 / 7.2 = 69.44 Saat
    motor.yeni_kayit_ekle(
        sirket="Alaşar", ref_no="REF-4412", ph="7.2", miktar=500,
        neden="Müşteri revizyon talebi (Legrand)", is_tanimi="Montaj hattında parça değişimi",
        talep_tarihi="2026-05-14", onay_tarihi="2026-05-15", durum="Onaylandı"
    )

    motor._ekrana_yaz("\n[2] MEVCUT VERİ TABANI ÖZETİ:")
    tablo = motor.verileri_goster()
    if not tablo.empty:
        print(tablo[["Kayit_ID", "Şirket", "Talep_Edilen_Saat", "Son_Durum"]].to_string(index=False))
        sys.stdout.flush()

    motor._ekrana_yaz("\n[3] REQ-0001 DURUMU GÜNCELLENİYOR...")
    motor.durum_guncelle(kayit_id="REQ-0001", yeni_durum="Revize Edilerek Onaylandı")

    motor._ekrana_yaz("\n[4] GÜNCEL TABLO DURUMU:")
    tablo_son = motor.verileri_goster()
    if not tablo_son.empty:
        print(tablo_son[["Kayit_ID", "Şirket", "Talep_Edilen_Saat", "Son_Durum"]].to_string(index=False))
        sys.stdout.flush()
        
    motor._ekrana_yaz("\n==================================================")
