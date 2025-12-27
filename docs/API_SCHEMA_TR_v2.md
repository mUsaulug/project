# ComplaintOps Copilot - API Şeması (Türkçe) v2

Bu doküman, `/api/sikayet` endpoint'inin güncel response şemasını ve örneklerini içerir.

---

## Endpoint: POST /api/sikayet

### Request

```json
{
  "metin": "Şikayet metni (string, zorunlu)"
}
```

### Response Schema

| Alan | Tip | Açıklama | Zorunlu |
|------|-----|----------|---------|
| `id` | Long | Veritabanı ID'si | ✅ |
| `kategori` | String | Türkçe kategori adı | ✅ |
| `oncelik` | String | `YUKSEK` / `ORTA` / `DUSUK` | ✅ |
| `oneri` | String | Müşteri yanıt taslağı | ✅ |
| `durum` | String | İşlem durumu (Türkçe) | ✅ |
| `kaynaklar` | Array | RAG kaynak listesi | ✅ (boş olabilir) |
| `insan_incelemesi_gerekli` | Boolean | Human review gerekli mi? | ✅ Eklendi |
| `review_id` | String/Null | İnceleme ID'si | ✅ Eklendi |
| `guven_skorlari` | Object | Confidence skorları | ✅ Eklendi |
| `sistem_durumu` | Object | RAG/LLM durum bilgisi | ✅ Eklendi |

> **Tüm alanlar uygulandı!** (27 Aralık 2024)

### Kategori Değerleri

| EN (Backend) | TR (Response) |
|--------------|---------------|
| `FRAUD_UNAUTHORIZED_TX` | `DOLANDIRICILIK_YETKISIZ_ISLEM` |
| `CHARGEBACK_DISPUTE` | `IADE_ITIRAZ` |
| `TRANSFER_DELAY` | `TRANSFER_GECIKMESI` |
| `ACCESS_LOGIN_MOBILE` | `ERISIM_GIRIS_MOBIL` |
| `CARD_LIMIT_CREDIT` | `KART_LIMIT_KREDI` |
| `INFORMATION_REQUEST` | `BILGI_TALEBI` |
| `CAMPAIGN_POINTS_REWARDS` | `KAMPANYA_PUAN_ODUL` |
| `MANUAL_REVIEW` | `MANUEL_INCELEME` |

### Durum Değerleri

| EN (Backend) | TR (Response) | Açıklama |
|--------------|---------------|----------|
| `NEW` | `YENI` | İlk durum |
| `MASKING_FAILED` | `MASKELEME_HATASI` | PII maskeleme başarısız |
| `ANALYZED` | `ANALIZ_EDILDI` | Başarılı analiz |
| `RESOLVED` | `COZUMLENDI` | Çözümlenmiş |

---

## Örnek Response'lar

### 1. Başarılı Analiz

```json
{
  "id": 42,
  "kategori": "DOLANDIRICILIK_YETKISIZ_ISLEM",
  "oncelik": "YUKSEK",
  "oneri": "Sayın müşterimiz, kartınız güvenlik nedeniyle bloke edilmiştir. En kısa sürede şube ile iletişime geçmenizi rica ederiz.",
  "durum": "ANALIZ_EDILDI",
  "kaynaklar": [
    {
      "dokuman_adi": "sop_3",
      "kaynak": "Bank_SOP_v1",
      "ozet": "Fraud Şüphesi: Karttan bilgisi dışında işlem yapıldığını..."
    }
  ]
}
```

### 2. Maskeleme Hatası (Fail-Closed)

```json
{
  "id": 43,
  "kategori": "MANUEL_INCELEME",
  "oncelik": "YUKSEK",
  "oneri": "Şikayetiniz alındı. Manuel inceleme için yönlendirildi.",
  "durum": "MASKELEME_HATASI",
  "kaynaklar": []
}
```

### 3. Hedef Response (P1 Sonrası)

```json
{
  "id": 44,
  "kategori": "TRANSFER_GECIKMESI",
  "oncelik": "ORTA",
  "oneri": "EFT işleminiz takip edilmektedir...",
  "durum": "ANALIZ_EDILDI",
  "kaynaklar": [
    {
      "dokuman_adi": "sop_0",
      "kaynak": "Bank_SOP_v1",
      "ozet": "FAST İşlemleri: FAST sistemi ile 7/24..."
    }
  ],
  "insan_incelemesi_gerekli": false,
  "review_id": null,
  "guven_skorlari": {
    "kategori": 0.87,
    "oncelik": 0.92
  }
}
```

### 4. Düşük Güven → İnsan İncelemesi

```json
{
  "id": 45,
  "kategori": "BILGI_TALEBI",
  "oncelik": "ORTA",
  "oneri": "Talebiniz kaydedilmiştir...",
  "durum": "ANALIZ_EDILDI",
  "kaynaklar": [],
  "insan_incelemesi_gerekli": true,
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "guven_skorlari": {
    "kategori": 0.45,
    "oncelik": 0.38
  }
}
```

---

## Kaynaklar (kaynaklar) Şeması

```json
{
  "dokuman_adi": "sop_X",        // SOP doküman adı
  "kaynak": "Bank_SOP_v1",       // Kaynak versiyonu
  "ozet": "İlk 100 karakter..."  // Snippet özeti
}
```

---

## Güven Skorları (guven_skorlari) Şeması (P1)

```json
{
  "kategori": 0.87,    // 0-1 arası kategori confidence
  "oncelik": 0.92      // 0-1 arası urgency confidence
}
```

**Kurallar:**
- `kategori < 0.60` veya `oncelik < 0.60` → `insan_incelemesi_gerekli: true`
- Her iki skor 0.60 üzeri → `insan_incelemesi_gerekli: false`

---

*Bu şema v2.0 - 27 Aralık 2024*
