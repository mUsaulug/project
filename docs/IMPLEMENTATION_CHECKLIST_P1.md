# Implementation Checklist - P1 İyileştirmeler

Bu checklist, Human-in-the-Loop görünürlüğü ve Graceful Degradation için yapılacak değişiklikleri listeler.

---

## A) Response'a Yeni Alanlar Ekleme

### A1. SikayetResponse Güncelleme

**Dosya:** `backend-java/src/main/java/com/complaintops/backend/ComplaintController.java`

**Değişiklik:** `SikayetResponse` class'ına yeni alanlar ekle

```java
// Mevcut alanların altına ekle:
@JsonProperty("insan_incelemesi_gerekli")
private Boolean insanIncelemesiGerekli;

@JsonProperty("review_id")
private String reviewId;

@JsonProperty("guven_skorlari")
private GuvenSkorlari guvenSkorlari;
```

**Kabul Kriteri:**
- [x] `insanIncelemesiGerekli` field eklendi
- [x] `reviewId` field eklendi
- [x] `guvenSkorlari` nested object eklendi
- [x] JSON serialize doğru çalışıyor

---

### A2. GuvenSkorlari Class Ekleme

**Dosya:** `backend-java/src/main/java/com/complaintops/backend/ComplaintController.java`

**Değişiklik:** Yeni nested class ekle

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public static class GuvenSkorlari {
    @JsonProperty("kategori")
    private Double kategori;
    
    @JsonProperty("oncelik")
    private Double oncelik;
}
```

**Kabul Kriteri:**
- [ ] Class eklendi
- [ ] Builder/AllArgsConstructor çalışıyor

---

### A3. Complaint Entity Güncelleme

**Dosya:** `backend-java/src/main/java/com/complaintops/backend/Complaint.java`

**Değişiklik:** Yeni DB alanları ekle

```java
private Boolean needsHumanReview;
private String reviewId;
private Double categoryConfidence;
private Double urgencyConfidence;
```

**Kabul Kriteri:**
- [ ] Alanlar eklendi
- [ ] Getter/Setter (@Data ile) çalışıyor

---

### A4. OrchestratorService Güncelleme

**Dosya:** `backend-java/src/main/java/com/complaintops/backend/OrchestratorService.java`

**Değişiklik:** Triage response'tan confidence değerlerini kaydet

```java
// L136-162 arasına ekle:
complaint.setNeedsHumanReview(triageResp.isNeedsHumanReview());
complaint.setReviewId(triageResp.getReviewId());
complaint.setCategoryConfidence(triageResp.getCategoryConfidence());
complaint.setUrgencyConfidence(triageResp.getUrgencyConfidence());
```

**Kabul Kriteri:**
- [ ] Confidence değerleri DB'ye kaydediliyor
- [ ] Review ID propagate ediliyor

---

### A5. Controller Response Mapping

**Dosya:** `backend-java/src/main/java/com/complaintops/backend/ComplaintController.java`

**Değişiklik:** `sikayetAnaliz` method'unda yeni alanları set et

```java
// L47-53 arasına ekle:
response.setInsanIncelemesiGerekli(complaint.getNeedsHumanReview());
response.setReviewId(complaint.getReviewId());
response.setGuvenSkorlari(new GuvenSkorlari(
    complaint.getCategoryConfidence(),
    complaint.getUrgencyConfidence()
));
```

**Kabul Kriteri:**
- [ ] Response'ta yeni alanlar görünüyor
- [ ] null değerler graceful handle ediliyor

---

## B) Graceful Degradation

### B1. RAG Hata Durumu

**Dosya:** `backend-java/src/main/java/com/complaintops/backend/OrchestratorService.java`

**Değişiklik:** RAG hatası için flag ekle

```java
// L108-112 catch bloğunda:
complaint.setRagStatus("UNAVAILABLE");
// veya risk_flags listesine ekle
```

**Kabul Kriteri:**
- [ ] RAG hatası loglanıyor
- [ ] Sistem fallback ile devam ediyor

---

### B2. LLM Hata Durumu

**Dosya:** `backend-java/src/main/java/com/complaintops/backend/OrchestratorService.java`

**Değişiklik:** LLM hatası için durum flag'i

```java
// L128-134 catch bloğunda:
complaint.setLlmStatus("TEMPLATE_FALLBACK");
```

**Kabul Kriteri:**
- [ ] LLM hatası loglanıyor
- [ ] Template yanıt kullanıcıya dönüyor

---

### B3. Genel Timeout Handling

**Dosya:** `backend-java/src/main/java/com/complaintops/backend/OrchestratorService.java`

**Değişiklik:** WebClient'a timeout ekle

```java
// WebClient oluşturma:
.timeout(Duration.ofSeconds(10))
```

**Kabul Kriteri:**
- [ ] Tüm WebClient çağrılarında timeout var
- [ ] Timeout → graceful fallback

---

## C) README Güncellemesi

**Dosya:** `README.md`

**Değişiklik:** Failure Modes bölümü ekle

**Kabul Kriteri:**
- [ ] 8-10 satırlık özet bölüm eklendi
- [ ] `docs/FAILURE_MODES.md` linki mevcut

---

## Öncelik Sırası

| # | Görev | Efor | Etki |
|---|-------|------|------|
| 1 | A1-A2: SikayetResponse alanları | S | Yüksek |
| 2 | A3: Complaint entity | S | Orta |
| 3 | A4-A5: Service + Controller | M | Yüksek |
| 4 | B1-B2: Graceful flags | S | Orta |
| 5 | B3: Timeout | S | Orta |
| 6 | C: README | S | Düşük |

**Toplam Tahmini Süre:** 2-3 saat

---

*Bu checklist v1.0 - 27 Aralık 2024*
