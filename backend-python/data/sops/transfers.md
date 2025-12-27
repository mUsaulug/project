# Para Transferleri Prosedürü (SOP-TR-002)

## 1. EFT ve Havale Ayrımı
- **Havale:** Banka içi transferdir. 7/24 anında gerçekleşir.
- **EFT:** Başka bankaya transferdir. Merkez Bankası saatlerine tabidir (09:00 - 17:00).
- **FAST:** 7/24 anlık transfer sistemidir. Limit şu an için 50.000 TL'dir.

## 2. Transfer Limitleri
| Kanal | Günlük Havale Limiti | Günlük EFT Limiti |
|-------|----------------------|-------------------|
| Mobil | 250.000 TL           | 250.000 TL        |
| Web   | 500.000 TL           | 500.000 TL        |
| Şube  | Limitsiz             | Limitsiz          |

*Limit artışı için şubeye ıslak imzalı talimat gereklidir.*

## 3. Transferin Hesaba Geçmemesi (Sorgulama)
Müşteri "para gitti ama karşıya ulaşmadı" derse:
1. **Sorgu No (Referans No):** Müşteriden dekont üzerindeki ref no istenir.
2. **Havuz Kontrolü:** Para bazen alıcı bankanın havuzunda "isim uyuşmazlığı" nedeniyle bekler.
3. **İade Süreci:** İsim/IBAN uyuşmazlığında para en geç **24 saat** içinde göndericiye iade olur.
   - *Müşteri Diliyle:* "Paranız havada kaybolmaz, ya karşıya geçer ya size döner."

## 4. Yanlış Hesaba Transfer (EFT İptali)
Transfer gerçekleştikten sonra (FAST veya gerçekleşmiş EFT) banka tarafından **tek taraflı iptal edilemez**.
- **Prosedür:** Bankamız, alıcı bankaya "İade Talebi" (MT199 mesajı) iletir.

## 5. Sıkça Sorulan Sorular (SSS)
**Soru:** EFT yaptım ama karşı hesaba geçmedi, neden?
**Cevap:** Alıcı isim/IBAN uyuşmazlığı olabilir veya işlem Merkez Bankası saatleri (09:00-17:00) dışındadır. FAST ile 7/24 gönderim deneyebilirsiniz.

**Soru:** Yanlış kişiye para gönderdim, geri alabilir miyim?
**Cevap:** Bankamız parayı hesabınızdan çıkardıysa tek taraflı iptal edemeyiz. Karşı bankaya iade talebi (MT199) iletilir, alıcı onaylarsa iade edilir.

**Soru:** Hafta sonu havale yapılır mı?
**Cevap:** Evet, banka içi havale işlemleri 7/24 anında gerçekleşir.
