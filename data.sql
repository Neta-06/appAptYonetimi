-- --------------------------------------------------------
-- Sunucu:                       127.0.0.1
-- Sunucu sürümü:                8.4.3 - MySQL Community Server - GPL
-- Sunucu İşletim Sistemi:       Win64
-- HeidiSQL Sürüm:               12.8.0.6908
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- appapartman için veritabanı yapısı dökülüyor
CREATE DATABASE IF NOT EXISTS `appapartman` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `appapartman`;

-- appapartman.aidat: ~11 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `aidat` (`aidat_no`, `site_no`, `daire_no`, `aidat_tipi_no`, `donem_yil`, `donem_ay`, `tutar`, `odenen_tutar`, `son_odeme_tarihi`, `durum`, `otomatik_islendi_mi`, `olusturma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 1, 1, 1, 2026, 9, 1500.00, 1500.00, '2026-09-30', 'ODENDI', 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(2, 1, 2, 1, 2026, 9, 1800.00, 0.00, '2026-09-30', 'BEKLIYOR', 1, '2026-09-27 16:08:57', '2026-09-27 23:34:09'),
	(3, 1, 3, 1, 2026, 9, 1500.00, 1500.00, '2026-09-30', 'ODENDI', 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(4, 1, 4, 1, 2026, 9, 1500.00, 0.00, '2026-09-30', 'BEKLIYOR', 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(5, 2, 5, 1, 2026, 9, 2000.00, 0.00, '2026-09-30', 'BEKLIYOR', 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(6, 2, 6, 1, 2026, 9, 2000.00, 0.00, '2026-09-30', 'GECIKMIS', 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(7, 1, 1, 1, 2026, 8, 1500.00, 1500.00, '2026-08-30', 'ODENDI', 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(8, 1, 1, 1, 2027, 1, 1500.00, 0.00, '2027-01-31', 'BEKLIYOR', 1, '2026-09-27 23:25:09', '2026-09-27 23:25:09'),
	(9, 1, 2, 1, 2027, 1, 1800.00, 0.00, '2027-01-31', 'BEKLIYOR', 1, '2026-09-27 23:25:09', '2026-09-27 23:25:09'),
	(10, 1, 3, 1, 2027, 1, 1500.00, 0.00, '2027-01-31', 'BEKLIYOR', 1, '2026-09-27 23:25:09', '2026-09-27 23:25:09'),
	(11, 1, 4, 1, 2027, 1, 1500.00, 0.00, '2027-01-31', 'BEKLIYOR', 1, '2026-09-27 23:25:09', '2026-09-27 23:25:09');

-- appapartman.aidat_tipi: ~6 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `aidat_tipi` (`tip_no`, `ad`, `aciklama`, `periyodik_mi`) VALUES
	(1, 'NORMAL_AIDAT', 'Aylik normal aidat', 1),
	(2, 'DEMIRBAS_KATILIM', 'Demirbas katilim payi', 0),
	(3, 'EK_HIZMET', 'Otopark/spor salonu vb.', 1),
	(4, 'AVANS', 'Pesin odenen aidat', 0),
	(5, 'SU_FATURA', 'Sayac bazli su', 1),
	(6, 'DOGALGAZ_FATURA', 'Sayac bazli dogalgaz', 1);

-- appapartman.alembic_version: ~0 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `alembic_version` (`version_num`) VALUES
	('0001_baseline');

-- appapartman.anahtar_teslim: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `anahtar_teslim` (`teslim_no`, `daire_no`, `anahtar_tipi`, `adet`, `teslim_edilen_kullanici_no`, `teslim_tarihi`, `iade_tarihi`, `aciklama`) VALUES
	(1, 1, 'DAIRE', 2, 4, '2026-09-27 16:08:57', NULL, '2 adet daire anahtari teslim edildi'),
	(2, 1, 'BINA_GIRIS', 1, 4, '2026-09-27 16:08:57', NULL, 'Ortak giris anahtari'),
	(3, 3, 'DAIRE', 1, 5, '2026-09-27 16:08:57', NULL, 'Kiralayan tarafindan teslim');

-- appapartman.anket: ~0 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `anket` (`anket_no`, `site_no`, `soru`, `aciklama`, `baslangic_tarihi`, `bitis_tarihi`, `olusturan_no`, `aktif_mi`) VALUES
	(1, 1, 'Bahceye oyun parki yapalim mi?', 'Tahmini maliyet aidattan karsilanacak.', '2026-09-10 09:00:00', '2026-09-30 23:59:59', 1, 1);

-- appapartman.anket_oyu: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `anket_oyu` (`oy_no`, `secenek_no`, `kullanici_no`, `oy_tarihi`) VALUES
	(1, 1, 4, '2026-09-27 16:08:57'),
	(2, 1, 5, '2026-09-27 16:08:57');

-- appapartman.anket_oy_hakki: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `anket_oy_hakki` (`hak_no`, `anket_no`, `kullanici_no`, `oy_kullandi_mi`) VALUES
	(1, 1, 4, 1),
	(2, 1, 5, 1),
	(3, 1, 6, 0);

-- appapartman.anket_secenegi: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `anket_secenegi` (`secenek_no`, `anket_no`, `secenek_metni`) VALUES
	(1, 1, 'EVET'),
	(2, 1, 'HAYIR'),
	(3, 1, 'KARARSIZIM');

-- appapartman.arac: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `arac` (`arac_no`, `site_no`, `daire_no`, `plaka`, `marka`, `model`, `renk`, `otopark_yer_no`, `aktif_mi`) VALUES
	(1, 1, 1, '34ABC123', 'Toyota', 'Corolla', 'Beyaz', 1, 1),
	(2, 1, 3, '34XYZ789', 'Honda', 'Civic', 'Siyah', 2, 1),
	(3, 2, 5, '06DEF456', 'Ford', 'Focus', 'Gri', 5, 1);

-- appapartman.audit_log: ~49 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `audit_log` (`log_no`, `kullanici_no`, `site_no`, `tablo_adi`, `kayit_id`, `islem_tipi`, `eski_deger`, `yeni_deger`, `ip_adresi`, `user_agent`, `islem_tarihi`) VALUES
	(16, NULL, NULL, 'kullanici', '25', 'INSERT', 'null', '{"ad": "AuthFlow", "soyad": "Test", "e_posta": "auth.flow@example.com", "aktif_mi": true, "firma_no": null, "sifre_hash": "$argon2id$v=19$m=65536,t=3,p=4$8eFTK9u3ujReAKEcNqomaA$0q5cetX79bpa95pqyR/sBp/GYsLusWJbT+IjeSBFZ4o", "kullanici_no": null, "mfa_aktif_mi": false, "tc_kimlik_hash": null, "telefon_sifreli": null, "hesap_kilitli_mi": false, "olusturma_tarihi": null, "son_giris_tarihi": null, "tc_kimlik_sifreli": null, "guncellenme_tarihi": null, "mfa_secret_sifreli": null, "kilit_acilma_tarihi": null, "basarisiz_giris_sayisi": 0, "sifre_degistirme_tarihi": null, "sifre_hatirlatma_zorunlu": null}', NULL, NULL, '2026-09-27 18:17:49'),
	(17, NULL, NULL, 'kvkk_onay', '19', 'INSERT', 'null', '{"onay_no": null, "metin_no": 1, "ip_adresi": "<binary 4 byte>", "onay_tipi": "AYDINLATMA", "onay_tarihi": "2026-09-27T18:17:48.696342", "kullanici_no": 25, "onaylandi_mi": true}', NULL, NULL, '2026-09-27 18:17:49'),
	(18, NULL, NULL, 'kullanici', '25', 'UPDATE', '{"son_giris_tarihi": null}', '{"son_giris_tarihi": "2026-09-27T18:17:48.922772"}', NULL, NULL, '2026-09-27 18:17:50'),
	(19, NULL, NULL, 'kullanici_site', '10', 'INSERT', 'null', '{"rol_no": 1, "site_no": 1, "aktif_mi": true, "kayit_no": null, "bitis_tarihi": null, "kullanici_no": 11, "baslangic_tarihi": "2026-09-27", "olusturma_tarihi": null, "guncellenme_tarihi": null}', NULL, NULL, '2026-09-27 18:30:47'),
	(20, NULL, NULL, 'kullanici_site', '11', 'INSERT', 'null', '{"rol_no": 1, "site_no": 2, "aktif_mi": true, "kayit_no": null, "bitis_tarihi": null, "kullanici_no": 11, "baslangic_tarihi": "2026-09-27", "olusturma_tarihi": null, "guncellenme_tarihi": null}', NULL, NULL, '2026-09-27 18:30:47'),
	(21, NULL, NULL, 'kullanici_site', '12', 'INSERT', 'null', '{"rol_no": 1, "site_no": 1, "aktif_mi": true, "kayit_no": null, "bitis_tarihi": null, "kullanici_no": 11, "baslangic_tarihi": "2026-09-27", "olusturma_tarihi": null, "guncellenme_tarihi": null}', NULL, NULL, '2026-09-27 18:47:38'),
	(22, NULL, NULL, 'kullanici_site', '13', 'INSERT', 'null', '{"rol_no": 1, "site_no": 2, "aktif_mi": true, "kayit_no": null, "bitis_tarihi": null, "kullanici_no": 11, "baslangic_tarihi": "2026-09-27", "olusturma_tarihi": null, "guncellenme_tarihi": null}', NULL, NULL, '2026-09-27 18:47:38'),
	(23, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"hesap_kilitli_mi": true, "son_giris_tarihi": "2026-09-27T16:12:51", "kilit_acilma_tarihi": "2026-09-27T16:45:41", "basarisiz_giris_sayisi": 5}', '{"hesap_kilitli_mi": false, "son_giris_tarihi": "2026-09-27T18:49:52.304070", "kilit_acilma_tarihi": null, "basarisiz_giris_sayisi": 0}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:49:52'),
	(24, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T18:49:52"}', '{"son_giris_tarihi": "2026-09-27T18:51:47.842780"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:51:48'),
	(25, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T18:51:48"}', '{"son_giris_tarihi": "2026-09-27T18:52:32.286261"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:52:32'),
	(26, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T18:52:32"}', '{"son_giris_tarihi": "2026-09-27T18:56:37.560113"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:56:38'),
	(27, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T18:56:38"}', '{"son_giris_tarihi": "2026-09-27T18:56:52.268903"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:56:52'),
	(28, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T18:56:52"}', '{"son_giris_tarihi": "2026-09-27T19:40:33.401965"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 19:40:34'),
	(29, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T19:40:33"}', '{"son_giris_tarihi": "2026-09-27T20:22:07.342605"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:22:07'),
	(30, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T20:22:07"}', '{"son_giris_tarihi": "2026-09-27T20:23:50.441415"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:23:50'),
	(31, 11, 1, 'odeme', '4', 'INSERT', 'null', '{"site_no": 1, "aciklama": "Test tahsilat - aidat 2", "odeme_no": null, "dekont_no": "HB-TEST-001", "onay_tarihi": "2026-09-27T20:23:52.739940", "referans_no": null, "odeme_tarihi": "2026-09-27T20:23:52.739934", "olusturan_no": 11, "onaylayan_no": 11, "toplam_tutar": "1800.00", "onay_durum_no": 1, "odeme_kanali_no": 1, "olusturma_tarihi": null, "guncellenme_tarihi": null}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:23:53'),
	(32, 11, 1, 'aidat', '2', 'UPDATE', '{"durum": "BEKLIYOR", "odenen_tutar": "0.00"}', '{"durum": "ODENDI", "odenen_tutar": "1800.00"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:23:53'),
	(33, 11, 1, 'odeme', '4', 'UPDATE', '{"aciklama": "Test tahsilat - aidat 2", "onay_durum_no": 1}', '{"aciklama": "Test tahsilat - aidat 2 | IPTAL: Yanlis girilen tutar", "onay_durum_no": 3}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:24:26'),
	(34, 11, 1, 'aidat', '8', 'INSERT', 'null', '{"durum": "BEKLIYOR", "tutar": "1500.00", "site_no": 1, "aidat_no": null, "daire_no": 1, "donem_ay": 1, "donem_yil": 2027, "odenen_tutar": "0.00", "aidat_tipi_no": 1, "olusturma_tarihi": null, "son_odeme_tarihi": "2027-01-31", "guncellenme_tarihi": null, "otomatik_islendi_mi": true}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:25:10'),
	(35, 11, 1, 'aidat', '9', 'INSERT', 'null', '{"durum": "BEKLIYOR", "tutar": "1800.00", "site_no": 1, "aidat_no": null, "daire_no": 2, "donem_ay": 1, "donem_yil": 2027, "odenen_tutar": "0.00", "aidat_tipi_no": 1, "olusturma_tarihi": null, "son_odeme_tarihi": "2027-01-31", "guncellenme_tarihi": null, "otomatik_islendi_mi": true}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:25:10'),
	(36, 11, 1, 'aidat', '10', 'INSERT', 'null', '{"durum": "BEKLIYOR", "tutar": "1500.00", "site_no": 1, "aidat_no": null, "daire_no": 3, "donem_ay": 1, "donem_yil": 2027, "odenen_tutar": "0.00", "aidat_tipi_no": 1, "olusturma_tarihi": null, "son_odeme_tarihi": "2027-01-31", "guncellenme_tarihi": null, "otomatik_islendi_mi": true}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:25:10'),
	(37, 11, 1, 'aidat', '11', 'INSERT', 'null', '{"durum": "BEKLIYOR", "tutar": "1500.00", "site_no": 1, "aidat_no": null, "daire_no": 4, "donem_ay": 1, "donem_yil": 2027, "odenen_tutar": "0.00", "aidat_tipi_no": 1, "olusturma_tarihi": null, "son_odeme_tarihi": "2027-01-31", "guncellenme_tarihi": null, "otomatik_islendi_mi": true}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:25:10'),
	(38, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T20:23:50"}', '{"son_giris_tarihi": "2026-09-27T20:27:47.998860"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:27:48'),
	(39, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T20:27:48"}', '{"son_giris_tarihi": "2026-09-27T20:30:31.066690"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:30:31'),
	(40, NULL, NULL, 'aidat', '2', 'UPDATE', '{"durum": "ODENDI", "odenen_tutar": "1800.00"}', '{"durum": "BEKLIYOR", "odenen_tutar": "0.00"}', NULL, NULL, '2026-09-27 20:32:11'),
	(41, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T20:30:31"}', '{"son_giris_tarihi": "2026-09-27T20:34:07.669364"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:34:08'),
	(42, 11, 1, 'odeme', '5', 'INSERT', 'null', '{"site_no": 1, "aciklama": null, "odeme_no": null, "dekont_no": "HB-FIX-001", "onay_tarihi": "2026-09-27T20:34:08.670731", "referans_no": null, "odeme_tarihi": "2026-09-27T20:34:08.670720", "olusturan_no": 11, "onaylayan_no": 11, "toplam_tutar": "1800.00", "onay_durum_no": 1, "odeme_kanali_no": 1, "olusturma_tarihi": null, "guncellenme_tarihi": null}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:34:09'),
	(43, 11, 1, 'odeme_detay', '4', 'INSERT', 'null', '{"tutar": "1800.00", "aciklama": null, "aidat_no": 2, "detay_no": null, "gider_no": null, "odeme_no": null}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:34:09'),
	(44, 11, 1, 'aidat', '2', 'UPDATE', '{"durum": "BEKLIYOR", "odenen_tutar": "0.00"}', '{"durum": "ODENDI", "odenen_tutar": "1800.00"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:34:09'),
	(45, 11, 1, 'aidat', '2', 'UPDATE', '{"durum": "ODENDI", "odenen_tutar": "1800.00"}', '{"durum": "BEKLIYOR", "odenen_tutar": "0.00"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:34:10'),
	(46, 11, 1, 'odeme', '5', 'UPDATE', '{"aciklama": null, "onay_durum_no": 1}', '{"aciklama": " | IPTAL: Test iptal", "onay_durum_no": 3}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:34:10'),
	(47, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T20:34:08"}', '{"son_giris_tarihi": "2026-09-27T20:58:08.193397"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:58:08'),
	(48, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T20:58:08"}', '{"son_giris_tarihi": "2026-09-27T20:59:16.523539"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:59:17'),
	(49, 11, 1, 'gider', '5', 'INSERT', 'null', '{"tutar": "1500.00", "cari_no": 1, "site_no": 1, "aciklama": "Test gideri - HTTP", "belge_no": "FTR-TEST-001", "gider_no": null, "kalem_no": 4, "kdv_tutar": "270.00", "kaydeden_no": 11, "gider_tarihi": "2026-10-01", "olusturma_tarihi": null, "guncellenme_tarihi": null}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:59:17'),
	(50, 11, 1, 'cari_hareket', '5', 'INSERT', 'null', '{"tutar": "1770.00", "cari_no": 1, "aciklama": "Gider: Elektrik Faturasi", "belge_no": "FTR-TEST-001", "gider_no": 5, "odeme_no": null, "hareket_no": null, "olusturan_no": 11, "islem_tipi_no": 1, "hareket_tarihi": "2026-09-27", "olusturma_tarihi": null}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:59:17'),
	(51, 11, 1, 'gider', '5', 'UPDATE', '{"tutar": "1500.00", "aciklama": "Test gideri - HTTP"}', '{"tutar": "2000.00", "aciklama": "Guncellendi - HTTP test"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:00:23'),
	(52, 11, 1, 'gider', '5', 'DELETE', '{"tutar": "2000.00", "cari_no": 1, "site_no": 1, "aciklama": "Guncellendi - HTTP test", "belge_no": "FTR-TEST-001", "gider_no": 5, "kalem_no": 4, "kdv_tutar": "270.00", "kaydeden_no": 11, "gider_tarihi": "2026-10-01", "olusturma_tarihi": "2026-09-27T23:59:17", "guncellenme_tarihi": "2026-09-28T00:00:23"}', 'null', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:00:44'),
	(53, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T20:59:17"}', '{"son_giris_tarihi": "2026-09-27T21:02:02.655036"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:02:03'),
	(54, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T21:02:03"}', '{"son_giris_tarihi": "2026-09-27T21:03:28.061032"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:03:28'),
	(55, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T21:03:28"}', '{"son_giris_tarihi": "2026-09-27T21:03:56.552812"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:03:57'),
	(56, 11, 1, 'gelir', '4', 'INSERT', 'null', '{"tutar": "800.00", "kaynak": "Otopark Kira Geliri", "site_no": 1, "aciklama": "Ekim otopark", "gelir_no": null, "kaydeden_no": 11, "gelir_tarihi": "2026-10-05", "olusturma_tarihi": null}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:04:45'),
	(57, 11, 1, 'gelir', '4', 'UPDATE', '{"tutar": "800.00", "aciklama": "Ekim otopark"}', '{"tutar": "1000.00", "aciklama": "Guncellendi"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:04:47'),
	(58, 11, 1, 'gelir', '4', 'DELETE', '{"tutar": "1000.00", "kaynak": "Otopark Kira Geliri", "site_no": 1, "aciklama": "Guncellendi", "gelir_no": 4, "kaydeden_no": 11, "gelir_tarihi": "2026-10-05", "olusturma_tarihi": "2026-09-28T00:04:44"}', 'null', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:04:47'),
	(59, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T21:03:57"}', '{"son_giris_tarihi": "2026-09-27T21:06:14.877108"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:06:15'),
	(60, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T21:06:15"}', '{"son_giris_tarihi": "2026-09-27T21:06:29.279134"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:06:29'),
	(61, 11, 1, 'gelir', '5', 'INSERT', 'null', '{"tutar": "800.00", "kaynak": "Otopark Kira Geliri", "site_no": 1, "aciklama": "Ekim otopark", "gelir_no": null, "kaydeden_no": 11, "gelir_tarihi": "2026-10-05", "olusturma_tarihi": null}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:06:58'),
	(62, 11, 1, 'gelir', '5', 'UPDATE', '{"tutar": "800.00", "aciklama": "Ekim otopark"}', '{"tutar": "1000.00", "aciklama": "Guncellendi"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:06:59'),
	(63, 11, 1, 'gelir', '5', 'DELETE', '{"tutar": "1000.00", "kaynak": "Otopark Kira Geliri", "site_no": 1, "aciklama": "Guncellendi", "gelir_no": 5, "kaydeden_no": 11, "gelir_tarihi": "2026-10-05", "olusturma_tarihi": "2026-09-28T00:06:58"}', 'null', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:07:02'),
	(64, NULL, NULL, 'kullanici', '11', 'UPDATE', '{"son_giris_tarihi": "2026-09-27T21:06:29"}', '{"son_giris_tarihi": "2026-09-27T21:14:21.876172"}', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:14:22');

-- appapartman.banka_hareketi: ~4 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `banka_hareketi` (`hareket_no`, `hesap_no`, `hareket_tarihi`, `aciklama`, `tutar`, `bakiye`, `karsi_hesap`, `karsi_iban`, `eslesti_mi`, `olusturma_tarihi`) VALUES
	(1, 1, '2026-09-05', 'A Blok 1 Daire - Eylul Aidat', 1500.00, 1500.00, 'Ayse Sahin', NULL, 1, '2026-09-27 16:08:57'),
	(2, 1, '2026-09-08', 'B Blok 1 Daire - Eylul Aidat', 1500.00, 3000.00, 'Fatma Celik', NULL, 1, '2026-09-27 16:08:57'),
	(3, 1, '2026-09-10', 'Asansor Teknik Ltd. odeme', -2500.00, 500.00, 'Asansor Teknik', NULL, 1, '2026-09-27 16:08:57'),
	(4, 2, '2026-09-10', '1. Kat 1 Daire - Eylul Aidat', 2000.00, 2000.00, 'Mustafa Toprak', NULL, 0, '2026-09-27 16:08:57');

-- appapartman.banka_hesabi: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `banka_hesabi` (`hesap_no`, `site_no`, `banka_adi`, `sube_adi`, `iban_sifreli`, `iban_hash`, `hesap_sahibi`, `para_birimi`, `aktif_mi`, `olusturma_tarihi`) VALUES
	(1, 1, 'Ziraat Bankasi', 'Kadikoy Subesi', _binary 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, '672133eb15b7f9a4f79af64c08213e4856ed543e827838937d531bfab04fdc2e', 'Gul Sitesi Yonetimi', 'TRY', 1, '2026-09-27 16:08:57'),
	(2, 2, 'Is Bankasi', 'Cankaya Subesi', _binary 0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb, '72e44ef0e0e12c950266e255ed42b8864853f00e14cc6abc6eebf1d34593dc09', 'Yildiz Apartmani Yonetimi', 'TRY', 1, '2026-09-27 16:08:57');

-- appapartman.banka_odeme_eslesme: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `banka_odeme_eslesme` (`eslesme_no`, `hareket_no`, `odeme_no`, `eslesme_tarihi`) VALUES
	(1, 1, 1, '2026-09-27 16:08:57'),
	(2, 2, 2, '2026-09-27 16:08:57');

-- appapartman.belge: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `belge` (`belge_no`, `site_no`, `belge_adi`, `kategori`, `guncel_versiyon`, `yukleyen_no`, `olusturma_tarihi`) VALUES
	(1, 1, 'Asansor Bakim Sozlesmesi 2026', 'SOZLESME', 1, 2, '2026-09-27 16:08:57'),
	(2, 2, 'Guvenlik Sozlesmesi 2026', 'SOZLESME', 1, 2, '2026-09-27 16:08:57');

-- appapartman.belge_versiyon: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `belge_versiyon` (`versiyon_no`, `belge_no`, `versiyon`, `dosya_yolu`, `dosya_boyut`, `mime_type`, `sha256_hash`, `yukleyen_no`, `yukleme_tarihi`) VALUES
	(1, 1, 1, '/belgeler/gul/asansor-sozlesme-2026.pdf', NULL, 'application/pdf', NULL, 2, '2026-09-27 16:08:57'),
	(2, 2, 1, '/belgeler/yildiz/guvenlik-sozlesme-2026.pdf', NULL, 'application/pdf', NULL, 2, '2026-09-27 16:08:57');

-- appapartman.bildirim: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `bildirim` (`bildirim_no`, `site_no`, `gonderen_no`, `hedef_no`, `tip_no`, `sablon_no`, `konu`, `icerik`, `gonderim_tarihi`) VALUES
	(1, 1, 1, 1, 3, 2, 'Su Kesintisi', '25 Eylul 09:00-15:00 su kesintisi olacaktir.', '2026-09-27 16:08:57'),
	(2, 2, 1, 1, 2, 1, 'Aidat Hatirlatma', 'Eylul aidatlarinizin son odeme tarihi 30 Eylul dur.', '2026-09-27 16:08:57');

-- appapartman.bildirim_alici: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `bildirim_alici` (`alici_no`, `bildirim_no`, `kullanici_no`, `kanal_no`, `durum_no`, `gonderim_zamani`, `teslim_zamani`, `hata_mesaji`, `deneme_sayisi`) VALUES
	(1, 1, 4, 1, 3, '2026-09-23 09:00:00', '2026-09-23 09:00:05', NULL, 0),
	(2, 1, 5, 1, 3, '2026-09-23 09:00:00', '2026-09-23 09:00:07', NULL, 0),
	(3, 2, 6, 2, 3, '2026-09-25 10:00:00', '2026-09-25 10:00:02', NULL, 0);

-- appapartman.bildirim_durum: ~4 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `bildirim_durum` (`durum_no`, `ad`) VALUES
	(4, 'BASARISIZ'),
	(1, 'BEKLIYOR'),
	(2, 'GONDERILDI'),
	(3, 'TESLIM_EDILDI');

-- appapartman.bildirim_hedef: ~5 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `bildirim_hedef` (`hedef_no`, `ad`) VALUES
	(2, 'BELIRLI_DAIRE'),
	(5, 'BELIRLI_KULLANICI'),
	(4, 'PERSONEL'),
	(1, 'TUM_SAKINLER'),
	(3, 'YONETIM');

-- appapartman.bildirim_kanal_ayar: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `bildirim_kanal_ayar` (`ayar_no`, `site_no`, `kanal_no`, `saglayici`, `yapilandirma`, `aktif_mi`) VALUES
	(1, 1, 1, 'NetGSM', '{"kullanici": "gulsitesi", "sifre_sifreli": "***"}', 1),
	(2, 1, 2, 'SMTP', '{"host": "smtp.gmail.com", "port": 587, "kullanici": "info@gulsitesi.com"}', 1);

-- appapartman.bildirim_sablon: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `bildirim_sablon` (`sablon_no`, `kod`, `baslik`, `icerik`, `kanal_no`, `aktif_mi`) VALUES
	(1, 'AIDAT_HATIRLATMA', 'Aidat Hatirlatma', 'Sayin {{ad}} {{soyad}}, {{donem}} donemi aidatinizin son odeme tarihi {{son_tarih}} dir.', 2, 1),
	(2, 'SU_KESINTI', 'Su Kesintisi', 'Sayin sakin, {{tarih}} tarihinde {{baslangic}}-{{bitis}} arasi su kesintisi olacaktir.', 1, 1);

-- appapartman.bildirim_tipi: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `bildirim_tipi` (`tip_no`, `ad`) VALUES
	(2, 'E_POSTA'),
	(3, 'PUSH'),
	(1, 'SMS');

-- appapartman.blok: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `blok` (`blok_no`, `site_no`, `blok_adi`, `kat_sayisi`, `olusturma_tarihi`) VALUES
	(1, 1, 'A Blok', 4, '2026-09-27 16:08:57'),
	(2, 1, 'B Blok', 4, '2026-09-27 16:08:57'),
	(3, 2, 'Tek Blok', 6, '2026-09-27 16:08:57');

-- appapartman.cari_hareket: ~4 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `cari_hareket` (`hareket_no`, `cari_no`, `hareket_tarihi`, `islem_tipi_no`, `tutar`, `aciklama`, `belge_no`, `gider_no`, `odeme_no`, `olusturan_no`, `olusturma_tarihi`) VALUES
	(1, 1, '2026-09-01', 1, 2500.00, 'Eylul asansor bakimi', 'FTR-1001', NULL, NULL, 2, '2026-09-27 16:08:57'),
	(2, 1, '2026-09-10', 2, 2500.00, 'Odeme yapildi', 'BK-1001', NULL, NULL, 2, '2026-09-27 16:08:57'),
	(3, 2, '2026-09-01', 1, 6000.00, 'Eylul temizlik hizmeti', 'FTR-1002', NULL, NULL, 2, '2026-09-27 16:08:57'),
	(4, 3, '2026-09-01', 1, 8000.00, 'Eylul guvenlik hizmeti', 'FTR-2001', NULL, NULL, 2, '2026-09-27 16:08:57');

-- appapartman.cari_hesap: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `cari_hesap` (`cari_no`, `site_no`, `unvan`, `vergi_no`, `telefon`, `e_posta`, `adres`, `iban`, `aktif_mi`, `olusturma_tarihi`) VALUES
	(1, 1, 'Asansor Teknik Ltd.', '1111111111', '02165550001', NULL, NULL, NULL, 1, '2026-09-27 16:08:57'),
	(2, 1, 'Temizlik Hizmetleri A.S.', '2222222222', '02165550002', NULL, NULL, NULL, 1, '2026-09-27 16:08:57'),
	(3, 2, 'Guvenlik Sistemleri A.S.', '3333333333', '03125550003', NULL, NULL, NULL, 1, '2026-09-27 16:08:57');

-- appapartman.cari_islem_tipi: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `cari_islem_tipi` (`tip_no`, `ad`) VALUES
	(2, 'ALACAK'),
	(1, 'BORC');

-- appapartman.daire: ~6 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `daire` (`daire_no`, `site_no`, `blok_no`, `daire_numarasi`, `kat`, `daire_tipi_no`, `brut_metrekare`, `ozel_aidat`, `doluluk_no`, `kullanim_no`, `olusturma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 1, 1, '1', 0, 3, 85.00, NULL, 1, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(2, 1, 1, '2', 0, 4, 110.00, 1800.00, 1, 2, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(3, 1, 2, '1', 0, 3, 85.00, NULL, 1, 2, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(4, 1, 2, '5', 1, 4, 115.00, NULL, 2, 3, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(5, 2, 3, '1', 0, 3, 90.00, NULL, 1, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(6, 2, 3, '3', 1, 5, 140.00, NULL, 1, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57');

-- appapartman.daire_doluluk: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `daire_doluluk` (`doluluk_no`, `ad`) VALUES
	(2, 'BOS'),
	(1, 'DOLU');

-- appapartman.daire_kullanim: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `daire_kullanim` (`kullanim_no`, `ad`) VALUES
	(3, 'BOS'),
	(2, 'KIRACI'),
	(1, 'MALIK_OTURUYOR');

-- appapartman.daire_sakin: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `daire_sakin` (`kayit_no`, `daire_no`, `kullanici_no`, `mulk_sahibi_mi`, `giris_tarihi`, `cikis_tarihi`, `olusturma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 1, 4, 1, '2025-02-01', NULL, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(2, 3, 5, 0, '2025-03-01', NULL, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(3, 5, 6, 1, '2025-02-01', NULL, '2026-09-27 16:08:57', '2026-09-27 16:08:57');

-- appapartman.daire_sayaci: ~5 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `daire_sayaci` (`daire_sayac_no`, `daire_no`, `sayac_turu_no`, `seri_no`, `montaj_tarihi`, `sokulme_tarihi`, `ilk_deger`, `aktif_mi`) VALUES
	(1, 1, 1, 'SS-0001', '2025-01-01', NULL, 100.00, 1),
	(2, 2, 1, 'SS-0002', '2025-01-01', NULL, 180.00, 1),
	(3, 3, 1, 'SS-0003', '2025-01-01', NULL, 80.00, 1),
	(4, 5, 1, 'SS-0004', '2025-01-01', NULL, 140.00, 1),
	(5, 6, 1, 'SS-0005', '2025-01-01', NULL, 300.00, 1);

-- appapartman.daire_tipi: ~6 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `daire_tipi` (`tip_no`, `ad`) VALUES
	(1, '1+0'),
	(2, '1+1'),
	(3, '2+1'),
	(4, '3+1'),
	(5, '4+1'),
	(6, 'DUBLEKS');

-- appapartman.demirbas: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `demirbas` (`demirbas_no`, `site_no`, `ad`, `kategori`, `adet`, `alis_fiyati`, `alis_tarihi`, `bulundugu_yer`, `durum`) VALUES
	(1, 1, 'Asansor', 'TASIMA', 2, 800000.00, '2020-05-01', 'Bloklar', 'CALISIYOR'),
	(2, 2, 'Jenerator', 'ENERJI', 1, 350000.00, '2021-01-15', 'Bodrum', 'CALISIYOR');

-- appapartman.demirbas_hareket: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `demirbas_hareket` (`hareket_no`, `demirbas_no`, `hareket_tipi`, `kullanici_no`, `tarih`, `aciklama`, `maliyet`) VALUES
	(1, 1, 'BAKIM', 3, '2026-09-27 16:08:57', 'Aylik periyodik bakim', 2500.00),
	(2, 1, 'ZIMBET', 3, '2026-09-27 16:08:57', 'Mehmet Demir sorumlulugunda', NULL);

-- appapartman.duyuru: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `duyuru` (`duyuru_no`, `site_no`, `baslik`, `icerik`, `onem_derecesi`, `yayin_tarihi`, `bitis_tarihi`, `yayinlayan_no`) VALUES
	(1, 1, 'Su Kesintisi', '25 Eylul 09:00-15:00 ana hat bakimi nedeniyle su kesintisi olacaktir.', 'ACIL', '2026-09-27 16:08:57', '2026-09-25', 1),
	(2, 2, 'Asansor Bakimi', 'Asansor periyodik bakimi 22 Eylul yapilacaktir.', 'ONEMLI', '2026-09-27 16:08:57', '2026-09-22', 1);

-- appapartman.duyuru_okuma: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `duyuru_okuma` (`okuma_no`, `duyuru_no`, `kullanici_no`, `okuma_tarihi`) VALUES
	(1, 1, 4, '2026-09-27 16:08:57'),
	(2, 1, 5, '2026-09-27 16:08:57'),
	(3, 2, 6, '2026-09-27 16:08:57');

-- appapartman.gelir: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `gelir` (`gelir_no`, `site_no`, `kaynak`, `tutar`, `gelir_tarihi`, `aciklama`, `kaydeden_no`, `olusturma_tarihi`) VALUES
	(1, 1, 'Aidat Tahsilati', 3000.00, '2026-09-08', 'Eylul aidati tahsilatlari', 2, '2026-09-27 16:08:57'),
	(2, 1, 'Kira Geliri', 1500.00, '2026-09-01', 'Kapici dairesi kirasi', 2, '2026-09-27 16:08:57'),
	(3, 2, 'Aidat Tahsilati', 2000.00, '2026-09-10', 'Eylul aidati tahsilati', 2, '2026-09-27 16:08:57');

-- appapartman.gider: ~5 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `gider` (`gider_no`, `site_no`, `kalem_no`, `cari_no`, `tutar`, `kdv_tutar`, `gider_tarihi`, `belge_no`, `aciklama`, `kaydeden_no`, `olusturma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 1, 1, 1, 2500.00, 0.00, '2026-09-01', 'FTR-1001', 'Eylul asansor bakimi', 2, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(2, 1, 2, 2, 6000.00, 0.00, '2026-09-01', 'FTR-1002', 'Eylul temizlik', 2, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(3, 1, 4, NULL, 3200.00, 0.00, '2026-09-05', 'FTR-1003', 'Ortak alan elektrik', 2, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(4, 2, 3, 3, 8000.00, 0.00, '2026-09-01', 'FTR-2001', 'Eylul guvenlik', 2, '2026-09-27 16:08:57', '2026-09-27 16:08:57');

-- appapartman.gider_kalemi: ~6 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `gider_kalemi` (`kalem_no`, `kalem_adi`, `kategori_no`) VALUES
	(1, 'Asansor Periyodik Bakimi', 1),
	(6, 'Dogalgaz Faturasi', 8),
	(4, 'Elektrik Faturasi', 6),
	(3, 'Ozel Guvenlik Hizmeti', 3),
	(2, 'Site Temizlik Hizmeti', 2),
	(5, 'Su Faturasi', 7);

-- appapartman.gider_kategori: ~11 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `gider_kategori` (`kategori_no`, `ad`) VALUES
	(1, 'ASANSOR'),
	(4, 'BAKIM'),
	(11, 'DIGER'),
	(8, 'DOGALGAZ'),
	(6, 'ENERJI'),
	(3, 'GUVENLIK'),
	(5, 'ONARIM'),
	(10, 'PERSONEL'),
	(9, 'PEYZAJ'),
	(7, 'SU'),
	(2, 'TEMIZLIK');

-- appapartman.icra_takip: ~0 rows (yaklaşık) tablosu için veriler indiriliyor

-- appapartman.is_durum: ~5 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `is_durum` (`durum_no`, `ad`, `kapanis_mi`) VALUES
	(1, 'ACIK', 0),
	(2, 'ATANDI', 0),
	(3, 'UZERINDE_CALISIYOR', 0),
	(4, 'TAMAMLANDI', 1),
	(5, 'IPTAL', 1);

-- appapartman.is_emri: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `is_emri` (`is_no`, `site_no`, `daire_no`, `acan_no`, `atanan_no`, `baslik`, `aciklama`, `oncelik_no`, `durum_no`, `olusturma_tarihi`, `termin_tarihi`, `tamamlanma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 1, 1, 1, 3, 'Balkon Suyu Sizintisi', 'Daire 1 balkon drenaj kontrolu.', 1, 4, '2026-09-27 16:08:57', '2026-09-10 18:00:00', NULL, '2026-09-27 16:08:57'),
	(2, 1, NULL, 1, 3, 'Bahce Sulama Arizasi', 'Sulama vanasi degisimi.', 3, 3, '2026-09-27 16:08:57', '2026-09-20 18:00:00', NULL, '2026-09-27 16:08:57'),
	(3, 2, 6, 1, 3, 'Klozet Rezervuar Arizasi', 'Rezervuar ic takim degisimi.', 2, 2, '2026-09-27 16:08:57', '2026-09-18 18:00:00', NULL, '2026-09-27 16:08:57');

-- appapartman.is_emri_guncelleme: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `is_emri_guncelleme` (`guncelleme_no`, `is_no`, `yazan_no`, `durum_no`, `notlar`, `guncelleme_tarihi`) VALUES
	(1, 1, 3, 3, 'Drenaj borusu degistiriliyor.', '2026-09-27 16:08:57'),
	(2, 1, 3, 4, 'Test edildi, sorun cozuldu.', '2026-09-27 16:08:57'),
	(3, 3, 3, 2, 'Malzeme temin edilecek.', '2026-09-27 16:08:57');

-- appapartman.is_emri_malzeme: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `is_emri_malzeme` (`malzeme_no`, `is_no`, `ad`, `adet`, `birim`, `birim_fiyat`) VALUES
	(1, 1, 'PVC Boru 50mm', 2.50, 'm', 80.00),
	(2, 1, 'Drenaj Izgarasi', 1.00, 'adet', 250.00);

-- appapartman.is_oncelik: ~4 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `is_oncelik` (`oncelik_no`, `ad`, `siralama`) VALUES
	(1, 'ACIL', 1),
	(2, 'YUKSEK', 2),
	(3, 'ORTA', 3),
	(4, 'DUSUK', 4);

-- appapartman.kargo_kaydi: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `kargo_kaydi` (`kargo_no`, `site_no`, `daire_no`, `kargo_firmasi`, `takip_no`, `gelis_tarihi`, `teslim_tarihi`, `teslim_alan_kullanici_no`, `durum`) VALUES
	(1, 1, 1, 'Yurtici Kargo', 'YK-2026-99001', '2026-09-27 16:08:57', NULL, NULL, 'BEKLIYOR'),
	(2, 1, 3, 'Aras Kargo', 'AR-2026-55002', '2026-09-27 16:08:57', NULL, NULL, 'TESLIM_EDILDI');

-- appapartman.kullanici: ~15 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `kullanici` (`kullanici_no`, `firma_no`, `ad`, `soyad`, `tc_kimlik_sifreli`, `tc_kimlik_hash`, `telefon_sifreli`, `e_posta`, `sifre_hash`, `sifre_degistirme_tarihi`, `sifre_hatirlatma_zorunlu`, `mfa_aktif_mi`, `mfa_secret_sifreli`, `son_giris_tarihi`, `basarisiz_giris_sayisi`, `hesap_kilitli_mi`, `kilit_acilma_tarihi`, `aktif_mi`, `olusturma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 1, 'Ahmet', 'Yilmaz', NULL, NULL, NULL, 'ahmet@ornekyonetim.com', '$argon2id$v=19$m=65536,t=3,p=4$ornekhash1', NULL, 0, 1, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(2, 1, 'Zeynep', 'Kaya', NULL, NULL, NULL, 'zeynep@ornekyonetim.com', '$argon2id$v=19$m=65536,t=3,p=4$ornekhash2', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(3, 1, 'Mehmet', 'Demir', NULL, NULL, NULL, 'mehmet@ornekyonetim.com', '$argon2id$v=19$m=65536,t=3,p=4$ornekhash3', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(4, NULL, 'Ayse', 'Sahin', NULL, NULL, NULL, 'ayse.sahin@mail.com', '$argon2id$v=19$m=65536,t=3,p=4$ornekhash4', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(5, NULL, 'Fatma', 'Celik', NULL, NULL, NULL, 'fatma.celik@mail.com', '$argon2id$v=19$m=65536,t=3,p=4$ornekhash5', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(6, NULL, 'Mustafa', 'Toprak', NULL, NULL, NULL, 'mustafa.toprak@mail.com', '$argon2id$v=19$m=65536,t=3,p=4$ornekhash6', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(7, NULL, 'Test', 'Kullanici', NULL, NULL, _binary 0x19e1c768810255be63f407dfa74df95b41794efc10d3d6d3564f0c7bc6cd68ca40ce535748ee46, 'test.user@example.com', '$argon2id$v=19$m=65536,t=3,p=4$eRBXMR/pGL1V7BxGVa5NPg$6giBJTfeRBUC+cSf/HOaGXAN/9lTpddJx5QwCvReTSM', NULL, 0, 0, NULL, '2026-09-27 15:23:38', 0, 0, NULL, 1, '2026-09-27 18:23:37', '2026-09-27 18:23:37'),
	(8, NULL, 'Ahmet', 'Test', NULL, NULL, NULL, 'ahmet.test@example.com', '$argon2id$v=19$m=65536,t=3,p=4$IPtZyGNaxFqh4B+ZfAU7BA$zdcyCWGlhfho9ChrBoccx+VsIy+5Ygiej94HC6VaIp0', NULL, 0, 0, NULL, '2026-09-27 15:46:28', 0, 0, NULL, 1, '2026-09-27 18:42:17', '2026-09-27 18:46:27'),
	(9, NULL, 'Test2', 'User2', NULL, NULL, NULL, 'test2@example.com', '$argon2id$v=19$m=65536,t=3,p=4$heC2wnzamvtmieF4iD0yrQ$s01luuNwjdcVXkmA/uKxSVMNd0OJ7B5DRz5HqI6ESH8', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 18:47:20', '2026-09-27 18:47:20'),
	(10, NULL, 'Yeni', 'Kullanici', NULL, NULL, NULL, 'yeni.kullanici@example.com', '$argon2id$v=19$m=65536,t=3,p=4$k6U6w61CzrUx2wZKb5pRMA$H50W1gcU4cDeUP7ar8pDqB3GY6uXmf/PUf/VGe8wb6c', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 18:47:49', '2026-09-27 18:47:49'),
	(11, NULL, 'Test', 'Kullanici', NULL, NULL, NULL, 'test.kullanici@example.com', '$argon2id$v=19$m=65536,t=3,p=4$icoihXb+N7i6BIbbYCBe9A$F+65R+HqhsMFlo+T6F2p7OGAtGvTH5O1GERIbVmydJE', NULL, 0, 0, NULL, '2026-09-27 21:14:22', 0, 0, NULL, 1, '2026-09-27 18:49:29', '2026-09-28 00:14:21'),
	(12, NULL, 'AuditTest', 'Kullanici', NULL, NULL, NULL, 'audit.test2@example.com', '$argon2id$v=19$m=65536,t=3,p=4$qJOL2XPg9ghXoFbmc0bDPA$OBElNQ3Bjb7IWRTR1rHr3Wyq8KMvX+E+Q1ZdzB+ZwKI', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 19:52:12', '2026-09-27 19:52:12'),
	(13, NULL, 'TestAudit', 'Kullanici', NULL, NULL, NULL, 'test.audit.final@example.com', '$argon2id$v=19$m=65536,t=3,p=4$555/WLoLzxz/gWafZ88OHA$AZ6rwMpI/fTMk0GCqb7e6SS7SfSwnzTi0HOigslyN9g', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 19:56:23', '2026-09-27 19:56:23'),
	(14, NULL, 'YeniAudit', 'Test', NULL, NULL, NULL, 'yeni.audit@example.com', '$argon2id$v=19$m=65536,t=3,p=4$Sj/h7HnVBFMkRlUYlAwQyg$d+4nPatlxgw0lWxI48ADuk3xGoXsqXqwRWFJzBS5nSQ', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 20:29:08', '2026-09-27 20:29:08'),
	(15, NULL, 'TestFinal', 'Audit', NULL, NULL, NULL, 'final.audit2@example.com', '$argon2id$v=19$m=65536,t=3,p=4$fsMLYKUM0cXyKGndxywBvA$WE6c2zDD/NfCe1cu8evrL21gY2akRJNKo67tyowWQvA', NULL, 0, 0, NULL, NULL, 0, 0, NULL, 1, '2026-09-27 20:46:11', '2026-09-27 20:46:11');

-- appapartman.kullanici_mfa_yedek_kod: ~0 rows (yaklaşık) tablosu için veriler indiriliyor

-- appapartman.kullanici_site: ~11 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `kullanici_site` (`kayit_no`, `kullanici_no`, `site_no`, `rol_no`, `baslangic_tarihi`, `bitis_tarihi`, `aktif_mi`, `olusturma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 1, 1, 1, '2025-01-01', NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(2, 1, 2, 1, '2025-01-01', NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(3, 2, 1, 2, '2025-01-01', NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(4, 2, 2, 2, '2025-06-01', NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(5, 3, 1, 4, '2025-01-01', NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(6, 3, 2, 4, '2025-06-01', NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(7, 4, 1, 3, '2025-02-01', NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(8, 5, 1, 3, '2025-03-01', NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(9, 6, 2, 3, '2025-02-01', NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(12, 11, 1, 1, '2026-09-27', NULL, 1, '2026-09-27 21:47:37', '2026-09-27 21:47:37'),
	(13, 11, 2, 1, '2026-09-27', NULL, 1, '2026-09-27 21:47:37', '2026-09-27 21:47:37');

-- appapartman.kvkk_metin: ~0 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `kvkk_metin` (`metin_no`, `baslik`, `icerik`, `versiyon`, `yayin_tarihi`, `aktif_mi`) VALUES
	(1, 'KVKK Aydinlatma Metni', 'Bu metin KVKK kapsaminda kisisel verilerin islenmesine iliskin aydinlatma metnidir...', '1.0', '2026-09-27 16:08:57', 1);

-- appapartman.kvkk_onay: ~14 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `kvkk_onay` (`onay_no`, `kullanici_no`, `metin_no`, `onay_tipi`, `onaylandi_mi`, `onay_tarihi`, `ip_adresi`) VALUES
	(1, 1, 1, 'AYDINLATMA', 1, '2026-09-27 16:08:57', NULL),
	(2, 2, 1, 'AYDINLATMA', 1, '2026-09-27 16:08:57', NULL),
	(3, 4, 1, 'AYDINLATMA', 1, '2026-09-27 16:08:57', NULL),
	(4, 5, 1, 'AYDINLATMA', 1, '2026-09-27 16:08:57', NULL),
	(5, 6, 1, 'AYDINLATMA', 1, '2026-09-27 16:08:57', NULL),
	(6, 7, 1, 'AYDINLATMA', 1, '2026-09-27 15:23:37', _binary 0x7f000001),
	(7, 8, 1, 'AYDINLATMA', 1, '2026-09-27 15:42:17', _binary 0x7f000001),
	(8, 9, 1, 'AYDINLATMA', 1, '2026-09-27 15:47:20', _binary 0x7f000001),
	(9, 10, 1, 'AYDINLATMA', 1, '2026-09-27 15:47:49', _binary 0x7f000001),
	(10, 11, 1, 'AYDINLATMA', 1, '2026-09-27 15:49:30', _binary 0x7f000001),
	(11, 12, 1, 'AYDINLATMA', 1, '2026-09-27 16:52:13', _binary 0x7f000001),
	(12, 13, 1, 'AYDINLATMA', 1, '2026-09-27 16:56:24', _binary 0x7f000001),
	(13, 14, 1, 'AYDINLATMA', 1, '2026-09-27 17:29:09', _binary 0x7f000001),
	(14, 15, 1, 'AYDINLATMA', 1, '2026-09-27 17:46:12', _binary 0x7f000001);

-- appapartman.login_denemesi: ~43 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `login_denemesi` (`deneme_no`, `e_posta`, `kullanici_no`, `ip_adresi`, `user_agent`, `basarili_mi`, `hata_mesaji`, `deneme_tarihi`) VALUES
	(1, 'test.user@example.com', 7, _binary 0x7f000001, NULL, 1, 'KAYIT', '2026-09-27 15:23:37'),
	(2, 'test.user@example.com', 7, _binary 0x7f000001, NULL, 1, NULL, '2026-09-27 15:23:38'),
	(3, 'ahmet.test@example.com', 8, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36', 1, 'KAYIT', '2026-09-27 15:42:17'),
	(4, 'ahmet.test@example.com', 8, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36', 1, NULL, '2026-09-27 15:43:14'),
	(5, 'ahmet.test@example.com', 8, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36', 1, NULL, '2026-09-27 15:46:28'),
	(6, 'test2@example.com', 9, _binary 0x7f000001, 'curl/8.21.0', 1, 'KAYIT', '2026-09-27 15:47:20'),
	(7, 'yeni.kullanici@example.com', 10, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36', 1, 'KAYIT', '2026-09-27 15:47:49'),
	(8, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, 'KAYIT', '2026-09-27 15:49:30'),
	(9, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 15:50:14'),
	(10, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 15:50:53'),
	(11, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 0, 'PAROLA_YANLIS', '2026-09-27 15:50:55'),
	(12, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 0, 'PAROLA_YANLIS', '2026-09-27 15:51:45'),
	(13, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 15:52:25'),
	(14, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 0, 'PAROLA_YANLIS', '2026-09-27 15:52:28'),
	(15, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 15:52:45'),
	(16, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 0, 'PAROLA_YANLIS', '2026-09-27 15:52:46'),
	(17, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 16:12:37'),
	(18, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 16:12:51'),
	(19, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 0, 'PAROLA_YANLIS', '2026-09-27 16:30:38'),
	(20, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 0, 'PAROLA_YANLIS', '2026-09-27 16:30:39'),
	(21, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 0, 'PAROLA_YANLIS', '2026-09-27 16:30:39'),
	(22, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 0, 'PAROLA_YANLIS', '2026-09-27 16:30:41'),
	(23, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 0, 'KILITLENDI', '2026-09-27 16:30:41'),
	(24, 'audit.test2@example.com', 12, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, 'KAYIT', '2026-09-27 16:52:13'),
	(25, 'test.audit.final@example.com', 13, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, 'KAYIT', '2026-09-27 16:56:24'),
	(26, 'yeni.audit@example.com', 14, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, 'KAYIT', '2026-09-27 17:29:09'),
	(27, 'final.audit2@example.com', 15, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, 'KAYIT', '2026-09-27 17:46:12'),
	(38, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 18:49:52'),
	(39, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 18:51:48'),
	(40, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 18:52:32'),
	(41, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 18:56:38'),
	(42, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 18:56:52'),
	(43, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 19:40:33'),
	(44, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 20:22:07'),
	(45, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 20:23:50'),
	(46, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 20:27:48'),
	(47, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 20:30:31'),
	(48, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 20:34:08'),
	(49, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 20:58:08'),
	(50, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 20:59:17'),
	(51, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 21:02:03'),
	(52, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 21:03:28'),
	(53, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 21:03:57'),
	(54, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 21:06:15'),
	(55, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 21:06:29'),
	(56, 'test.kullanici@example.com', 11, _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', 1, NULL, '2026-09-27 21:14:22');

-- appapartman.mesaj: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `mesaj` (`mesaj_no`, `gonderen_no`, `alici_no`, `site_no`, `parent_mesaj_no`, `konu`, `icerik`, `gonderim_tarihi`, `okundu_mu`, `okunma_tarihi`) VALUES
	(1, 4, 1, 1, NULL, 'Aidat Dekontu', 'Eylul aidat odeme dekontumu iletiyorum.', '2026-09-27 16:08:57', 1, NULL),
	(2, 1, 4, 1, NULL, 'Re: Aidat Dekontu', 'Odemeniz onaylanmistir, tesekkurler.', '2026-09-27 16:08:57', 1, NULL),
	(3, 6, 1, 2, NULL, 'Otopark Talebi', 'Arac kaydi icin plaka bilgilerimi iletiyorum.', '2026-09-27 16:08:57', 0, NULL);

-- appapartman.odeme: ~5 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `odeme` (`odeme_no`, `site_no`, `odeme_tarihi`, `toplam_tutar`, `odeme_kanali_no`, `dekont_no`, `referans_no`, `onay_durum_no`, `onaylayan_no`, `onay_tarihi`, `aciklama`, `olusturan_no`, `olusturma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 1, '2026-09-05 10:30:00', 1500.00, 5, NULL, 'POS-778899', 1, 2, NULL, NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(2, 1, '2026-09-08 09:15:00', 1500.00, 6, NULL, 'OTM-445566', 1, 2, NULL, NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(3, 1, '2026-08-25 14:00:00', 1500.00, 1, NULL, NULL, 1, 2, NULL, NULL, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(4, 1, '2026-09-27 20:23:53', 1800.00, 1, 'HB-TEST-001', NULL, 3, 11, '2026-09-27 20:23:53', 'Test tahsilat - aidat 2 | IPTAL: Yanlis girilen tutar', 11, '2026-09-27 23:23:52', '2026-09-27 23:24:25'),
	(5, 1, '2026-09-27 20:34:09', 1800.00, 1, 'HB-FIX-001', NULL, 3, 11, '2026-09-27 20:34:09', ' | IPTAL: Test iptal', 11, '2026-09-27 23:34:08', '2026-09-27 23:34:09');

-- appapartman.odeme_detay: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `odeme_detay` (`detay_no`, `odeme_no`, `aidat_no`, `gider_no`, `tutar`, `aciklama`) VALUES
	(1, 1, 1, NULL, 1500.00, NULL),
	(2, 2, 3, NULL, 1500.00, NULL),
	(3, 3, 7, NULL, 1500.00, NULL),
	(4, 5, 2, NULL, 1800.00, NULL);

-- appapartman.odeme_kanali: ~6 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `odeme_kanali` (`kanal_no`, `ad`) VALUES
	(2, 'EFT'),
	(1, 'HAVALE'),
	(4, 'KREDI_KARTI'),
	(3, 'NAKIT'),
	(6, 'OTOMATIK_TALEP'),
	(5, 'SANAL_POS');

-- appapartman.onay_durum: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `onay_durum` (`durum_no`, `ad`) VALUES
	(2, 'BEKLIYOR'),
	(1, 'ONAYLANDI'),
	(3, 'REDDEDILDI');

-- appapartman.otopark_yeri: ~6 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `otopark_yeri` (`yer_no`, `site_no`, `yer_kodu`, `tip`) VALUES
	(1, 1, 'A-01', 'KAPALI'),
	(2, 1, 'A-02', 'KAPALI'),
	(3, 1, 'M-01', 'MISAFIR'),
	(4, 1, 'E-01', 'ENGELLI'),
	(5, 2, 'P-01', 'ACIK'),
	(6, 2, 'P-02', 'ACIK');

-- appapartman.oturum: ~17 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `oturum` (`oturum_no`, `kullanici_no`, `refresh_token_hash`, `ip_adresi`, `user_agent`, `olusturma_tarihi`, `son_kullanma_tarihi`, `iptal_mi`, `iptal_tarihi`) VALUES
	(29, 11, '39918dfecd23a20f6b4e01cc55c518b33df9afd272738d6a21aa4a1474d77452', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:49:52', '2026-10-04 18:49:52', 0, NULL),
	(30, 11, 'efce7c7d5ac03adc8e3ce1b10d96c60272292e104ae25551e0deba77a7ce1301', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:51:48', '2026-10-04 18:51:48', 0, NULL),
	(31, 11, '0d505432b0d57089a38461d7aa91f408b7a9bdfb53fb7082aae32d0d27c979d5', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:52:32', '2026-10-04 18:52:32', 0, NULL),
	(32, 11, '2a0287f32c161a6bf47c83e8fe856f4e0250969ab3cb227c6d70b0db32ee3eb7', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:56:38', '2026-10-04 18:56:38', 0, NULL),
	(33, 11, '918d0916cc1f3eaa73975d33f7e3ab6b90c9d855777a5449793df802aee00b86', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 18:56:52', '2026-10-04 18:56:52', 0, NULL),
	(34, 11, 'f88db82fa60fbea51636af20b5a9c4cd83f760e83439596616af231877e067d1', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 19:40:34', '2026-10-04 19:40:34', 0, NULL),
	(35, 11, 'b6a398a54299326d6777fbce70adac61e3dd4055fbb2bdad8ec7dc4b8bb559a1', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:22:08', '2026-10-04 20:22:08', 0, NULL),
	(36, 11, '7a7642e6eb8f69b7851175e017fef0dce49f2e5b07bfe5a69acf4d65bce6151d', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:23:50', '2026-10-04 20:23:50', 0, NULL),
	(37, 11, '12bc6368f0f5926be86b135503a16bef519c5e825eebcf632c30521b629b843b', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:27:48', '2026-10-04 20:27:48', 0, NULL),
	(38, 11, '77515e933097abb0805150fba155f1bec2081e51d6c282965781676a8823ffd3', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:30:31', '2026-10-04 20:30:31', 0, NULL),
	(39, 11, '57c10deab4ae286959611e70a879e2c4266ac3e94d685190167ef0547963a113', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:34:08', '2026-10-04 20:34:08', 0, NULL),
	(40, 11, '57b76ab61f4bb9b421b2bc65f827200b9aee46ada6de93d95c1f96087469998c', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:58:08', '2026-10-04 20:58:08', 0, NULL),
	(41, 11, 'b2eb0d971d7d4d1f4817cd5f780afe2b93d5a3e61a9dad67c6958564832f433e', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 20:59:17', '2026-10-04 20:59:17', 0, NULL),
	(42, 11, 'b2a380c900b4a45b2d49c66c985969189bccfbb58138efa60208add2b6b6677a', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:02:03', '2026-10-04 21:02:03', 0, NULL),
	(43, 11, 'e2657fc935a4efb9921c5830d7d6cf1ec3b6d5648f0a5245faf7e77f687f0120', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:03:28', '2026-10-04 21:03:28', 0, NULL),
	(44, 11, '245db6f7c25eeb7829212423f0f59393d336e88f40c187ed4ef813192782668d', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:03:57', '2026-10-04 21:03:57', 0, NULL),
	(45, 11, 'faf25109878d53d56769f4b2e32ff2c46a136f9440d2bcbae0553eaeadad7ba2', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:06:15', '2026-10-04 21:06:15', 0, NULL),
	(46, 11, '218aa6459ea5dd593403a39dec5f5b67d9ee0a018460eb22f6a448920d9716d1', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:06:29', '2026-10-04 21:06:29', 0, NULL),
	(47, 11, 'e43af276219742ce48b6417b06ed45a1a21da65f23dfaaa057049c0999083c43', _binary 0x7f000001, 'Mozilla/5.0 (Windows NT; Windows NT 10.0; tr-TR) WindowsPowerShell/5.1.26100.9444', '2026-09-27 21:14:22', '2026-10-04 21:14:22', 0, NULL);

-- appapartman.parola_sifirlama_token: ~0 rows (yaklaşık) tablosu için veriler indiriliyor

-- appapartman.personel: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `personel` (`personel_no`, `firma_no`, `kullanici_no`, `ad`, `soyad`, `gorevi`, `telefon`, `e_posta`, `tc_kimlik_sifreli`, `ise_baslama_tarihi`, `isten_cikis_tarihi`, `aktif_mi`) VALUES
	(1, 1, 3, 'Mehmet', 'Demir', 'TEKNIK PERSONEL', '05011110003', NULL, NULL, '2025-01-01', NULL, 1),
	(2, 1, NULL, 'Emine', 'Temiz', 'TEMIZLIK PERSONELI', '05011110007', NULL, NULL, '2025-03-01', NULL, 1);

-- appapartman.personel_izin: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `personel_izin` (`izin_no`, `personel_no`, `izin_tipi`, `baslangic_tarihi`, `bitis_tarihi`, `gun_sayisi`, `aciklama`, `onaylayan_no`, `onay_durum_no`, `olusturma_tarihi`) VALUES
	(1, 1, 'YILLIK', '2026-08-01', '2026-08-05', 5, 'Yaz izni', 1, 1, '2026-09-27 16:08:57'),
	(2, 2, 'RAPOR', '2026-09-10', '2026-09-12', 3, 'Grip raporu', 1, 1, '2026-09-27 16:08:57');

-- appapartman.personel_maas_odeme: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `personel_maas_odeme` (`maas_odeme_no`, `personel_no`, `donem_yil`, `donem_ay`, `brut_maas`, `kesintiler`, `odeme_tarihi`) VALUES
	(1, 1, 2026, 8, 30000.00, 4500.00, '2026-08-31'),
	(2, 2, 2026, 8, 24000.00, 3600.00, '2026-08-31');

-- appapartman.personel_puantaj: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `personel_puantaj` (`puantaj_no`, `personel_no`, `tarih`, `giris_saati`, `cikis_saati`, `toplam_saat`, `devamsiz_mi`, `aciklama`) VALUES
	(1, 1, '2026-09-01', '08:00:00', '17:00:00', 9.00, 0, NULL),
	(2, 1, '2026-09-02', '08:15:00', '17:00:00', 8.75, 0, NULL),
	(3, 2, '2026-09-01', '09:00:00', '16:00:00', 7.00, 0, NULL);

-- appapartman.personel_site: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `personel_site` (`kayit_no`, `personel_no`, `site_no`, `baslangic_tarihi`, `bitis_tarihi`) VALUES
	(1, 1, 1, '2025-01-01', NULL),
	(2, 1, 2, '2025-06-01', NULL),
	(3, 2, 1, '2025-03-01', NULL);

-- appapartman.rol: ~5 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `rol` (`rol_no`, `ad`, `aciklama`, `sistem_rolu`) VALUES
	(1, 'YONETICI', 'Site yoneticisi - tam yetki', 1),
	(2, 'MUHASEBECI', 'Muhasebe islemleri', 1),
	(3, 'SAKIN', 'Daire sakini', 1),
	(4, 'PERSONEL', 'Site personeli', 1),
	(5, 'DENETCI', 'Salt okunur denetci', 1);

-- appapartman.rol_yetki: ~17 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `rol_yetki` (`rol_no`, `yetki_no`) VALUES
	(1, 1),
	(2, 1),
	(3, 1),
	(4, 1),
	(5, 1),
	(1, 2),
	(1, 3),
	(1, 4),
	(2, 4),
	(5, 4),
	(1, 5),
	(2, 5),
	(1, 6),
	(1, 7),
	(1, 8),
	(2, 8),
	(5, 8);

-- appapartman.sayac_birim: ~4 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `sayac_birim` (`birim_no`, `ad`) VALUES
	(2, 'kWh'),
	(3, 'lt'),
	(1, 'm3'),
	(4, 'ton');

-- appapartman.sayac_faturasi: ~0 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `sayac_faturasi` (`fatura_no`, `site_no`, `sayac_turu_no`, `donem_yil`, `donem_ay`, `toplam_tutar`, `ortak_alan_tutar`, `dagitim_sekli`, `olusturma_tarihi`) VALUES
	(1, 1, 1, 2026, 8, 2500.00, 300.00, 'TUKETIME_GORE', '2026-09-27 16:08:57');

-- appapartman.sayac_fatura_payi: ~4 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `sayac_fatura_payi` (`pay_no`, `fatura_no`, `daire_no`, `tuketim`, `daire_tutari`, `aidat_no`) VALUES
	(1, 1, 1, 25.50, 260.25, NULL),
	(2, 1, 2, 34.00, 346.99, NULL),
	(3, 1, 3, 22.25, 227.11, NULL),
	(4, 1, 4, 21.00, 214.35, NULL);

-- appapartman.sayac_okuma: ~5 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `sayac_okuma` (`okuma_no`, `daire_sayac_no`, `okuma_tarihi`, `guncel_deger`, `tuketim`, `okuyan_no`, `olusturma_tarihi`) VALUES
	(1, 1, '2026-08-31', 145.50, 145.50, 3, '2026-09-27 16:08:57'),
	(2, 2, '2026-08-31', 234.00, 234.00, 3, '2026-09-27 16:08:57'),
	(3, 3, '2026-08-31', 112.25, 112.25, 3, '2026-09-27 16:08:57'),
	(4, 4, '2026-08-31', 171.00, 171.00, 3, '2026-09-27 16:08:57'),
	(5, 5, '2026-08-31', 348.75, 348.75, 3, '2026-09-27 16:08:57');

-- appapartman.sayac_turu: ~4 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `sayac_turu` (`sayac_turu_no`, `adi`, `birim_no`) VALUES
	(1, 'Soguk Su', 1),
	(2, 'Sicak Su', 1),
	(3, 'Dogalgaz', 1),
	(4, 'Elektrik', 2);

-- appapartman.sigorta_policesi: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `sigorta_policesi` (`police_no`, `site_no`, `demirbas_no`, `sigorta_sirketi`, `police_tipi`, `police_numarasi`, `baslangic_tarihi`, `bitis_tarihi`, `prim_tutar`, `teminat_tutar`, `belge_no`, `aktif_mi`) VALUES
	(1, 1, 1, 'Allianz', 'SORUMLULUK', 'POL-2026-001', '2026-01-01', '2026-12-31', 12000.00, 1000000.00, NULL, 1),
	(2, 2, 2, 'Anadolu Sigorta', 'YANGIN', 'POL-2026-002', '2026-03-01', '2027-02-28', 8000.00, 500000.00, NULL, 1);

-- appapartman.site: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `site` (`site_no`, `firma_no`, `site_adi`, `site_tipi_no`, `adres`, `il`, `ilce`, `daire_sayisi`, `aylik_aidat`, `aidat_gunu`, `otomatik_borclandir`, `aktif_mi`, `olusturma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 1, 'Gul Sitesi', 2, 'Cumhuriyet Mah. Gul Sok. No:1', 'Istanbul', 'Kadikoy', 24, 1500.00, 5, 1, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57'),
	(2, 1, 'Yildiz Apartmani', 1, 'Baris Mah. Yildiz Cad. No:12', 'Ankara', 'Cankaya', 12, 2000.00, 10, 1, 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57');

-- appapartman.site_aidat_ayari: ~3 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `site_aidat_ayari` (`ayar_no`, `site_no`, `aidat_tipi_no`, `tutar`, `aktif_mi`, `baslangic_tarihi`, `bitis_tarihi`) VALUES
	(1, 1, 1, 1500.00, 1, '2025-01-01', NULL),
	(2, 1, 6, 300.00, 1, '2025-01-01', NULL),
	(3, 2, 1, 2000.00, 1, '2025-01-01', NULL);

-- appapartman.site_tipi: ~4 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `site_tipi` (`tip_no`, `ad`) VALUES
	(1, 'APARTMAN'),
	(4, 'PLAZA'),
	(3, 'REZIDANS'),
	(2, 'SITE');

-- appapartman.talep: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `talep` (`talep_no`, `site_no`, `acan_no`, `daire_no`, `kategori_no`, `konu`, `aciklama`, `oncelik_no`, `durum_no`, `acilis_tarihi`, `cozum_tarihi`, `cozen_no`, `cozum_notu`) VALUES
	(1, 1, 4, 1, 1, 'Merdiven Aydinlatmasi', '2. kat merdiven lambasi yanmiyor.', 3, 1, '2026-09-27 16:08:57', NULL, NULL, NULL),
	(2, 2, 6, 6, 2, 'Ortak Alan Temizligi', 'Giris holu zemini kirli.', 4, 2, '2026-09-27 16:08:57', NULL, NULL, NULL);

-- appapartman.talep_durum: ~5 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `talep_durum` (`durum_no`, `ad`, `kapanis_mi`) VALUES
	(1, 'ACIK', 0),
	(2, 'INCELENIYOR', 0),
	(3, 'COZULDU', 1),
	(4, 'REDDEDILDI', 1),
	(5, 'KAPANDI', 1);

-- appapartman.talep_kategori: ~5 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `talep_kategori` (`kategori_no`, `ad`) VALUES
	(1, 'ARIZA'),
	(5, 'DIGER'),
	(4, 'IZIN'),
	(3, 'ONERI'),
	(2, 'SIKAYET');

-- appapartman.toplanti: ~0 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `toplanti` (`toplanti_no`, `site_no`, `baslik`, `aciklama`, `toplanti_tarihi`, `yer`, `olusturan_no`, `durum`) VALUES
	(1, 1, 'Eylul Yonetim Toplantisi', 'Aylik gider degerlendirmesi.', '2026-09-15 19:00:00', 'Site Toplanti Salonu', 1, 'PLANLANDI');

-- appapartman.toplanti_karar: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `toplanti_karar` (`karar_no`, `toplanti_no`, `karar_metni`, `karar_tarihi`) VALUES
	(1, 1, 'Ekim ayindan itibaren asansor bakim sozlesmesi 2 yil uzatilacaktir.', '2026-09-27 16:08:57'),
	(2, 1, 'Ortak alan elektrik faturalarinin takibi icin otomatik odeme talimati verilecektir.', '2026-09-27 16:08:57');

-- appapartman.toplanti_katilimci: ~4 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `toplanti_katilimci` (`katilim_no`, `toplanti_no`, `kullanici_no`, `katildi_mi`, `vekalet_kullanici_no`) VALUES
	(1, 1, 1, 1, NULL),
	(2, 1, 2, 1, NULL),
	(3, 1, 4, 1, NULL),
	(4, 1, 5, 0, NULL);

-- appapartman.yetki: ~8 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `yetki` (`yetki_no`, `kod`, `ad`, `modul`) VALUES
	(1, 'aidat.goruntule', 'Aidat Goruntule', 'aidat'),
	(2, 'aidat.olustur', 'Aidat Olustur', 'aidat'),
	(3, 'aidat.sil', 'Aidat Sil', 'aidat'),
	(4, 'gider.goruntule', 'Gider Goruntule', 'gider'),
	(5, 'gider.olustur', 'Gider Olustur', 'gider'),
	(6, 'kullanici.yonet', 'Kullanici Yonet', 'kullanici'),
	(7, 'site.yonet', 'Site Yonet', 'site'),
	(8, 'rapor.goruntule', 'Rapor Goruntule', 'rapor');

-- appapartman.yonetim_firmasi: ~0 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `yonetim_firmasi` (`firma_no`, `firma_adi`, `vergi_no`, `adres`, `telefon`, `e_posta`, `yetkili_kisi`, `aktif_mi`, `olusturma_tarihi`, `guncellenme_tarihi`) VALUES
	(1, 'Ornek Yonetim Ltd. Sti.', '1234567890', 'Ataturk Cad. No:45 Kadikoy/Istanbul', '02161234567', 'info@ornekyonetim.com', 'Ahmet Yilmaz', 1, '2026-09-27 16:08:57', '2026-09-27 16:08:57');

-- appapartman.ziyaretci_kaydi: ~2 rows (yaklaşık) tablosu için veriler indiriliyor
INSERT INTO `ziyaretci_kaydi` (`ziyaret_no`, `site_no`, `daire_no`, `ad_soyad`, `telefon`, `ziyaret_sebebi`, `arac_plaka`, `giris_tarihi`, `cikis_tarihi`, `onaylayan_kullanici_no`) VALUES
	(1, 1, 1, 'Ali Veli', '05551112233', 'Misafir', NULL, '2026-09-27 16:08:57', NULL, 4),
	(2, 2, 5, 'Hasan Kaya', '05554445566', 'Kargo teslimi', NULL, '2026-09-27 16:08:57', NULL, 6);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
