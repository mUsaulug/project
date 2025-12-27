# ComplaintOps Copilot — MVP İnceleme Raporu v2

**Hazırlayan:** AI Ürün Yöneticisi Perspektifi  
**Tarih:** 27 Aralık 2024  
**Versiyon:** 2.0 (Güncellenmiş)

---

## 1. Executive Summary (12 Madde)

| # | Başlık | Durum | Kanıt |
|---|--------|-------|-------|
| 1 | **Fail-Closed PII Koruması** | ✅ Tamamlandı | Maskeleme hatası → pipeline durur, raw text korunur |
| 2 | **No-Raw-Text-in-DB** | ✅ Tamamlandı | `Complaint.java` → `originalText` alanı yok |
| 3 | **Türkçe API Kontratı** | ✅ Tamamlandı | `/api/sikayet` → TR response schema |
| 4 | **RAG Kaynak Döndürme** | ✅ Tamamlandı | Response'ta `kaynaklar` array mevcut |
| 5 | **Request ID Propagation** | ✅ Tamamlandı | Java→Python X-Request-ID header |
| 6 | **Architecture Dokumentasyonu** | ✅ Tamamlandı | `docs/architecture.md` (Mermaid) |
| 7 | **README + Quickstart** | ✅ Tamamlandı | Repo kökünde kapsamlı README |
| 8 | **Postman Demo Collection** | ✅ Tamamlandı | `docs/postman_collection.json` |
| 9 | **Golden Set (20 Örnek)** | ✅ Tamamlandı | Human-written eval örnekleri |
| 10 | **Eval Script + Metrikler** | ✅ Tamamlandı | Accuracy, PII leak, latency ölçümü |
| 11 | **Human-in-the-Loop** | ✅ Backend'de Var | `needs_human_review` Python'da mevcut |
| 12 | **Graceful Degradation** | ✅ Tamamlandı | RAG/LLM hatalarında fallback + sistem_durumu |

---

## 2. Ürün Problemi ve Seçilen Yaklaşım

### 2.1 Problem Tanımı

Bankacılık sektöründe günde binlerce müşteri şikayeti geliyor. Bu şikayetlerin:
- **Doğru kategoriye yönlendirilmesi** kritik (fraud vs bilgi talebi)
- **Kişisel verilerin korunması** yasal zorunluluk (KVKK)
- **Hızlı ilk yanıt** müşteri memnuniyeti için önemli
- **Prosedür uyumu** tutarlılık gerektiriyor

### 2.2 Neden Bu Yaklaşım?

| Karar | Neden | Trade-off |
|-------|-------|-----------|
| Java + Python ayrımı | Kurumsal entegrasyon + ML ekosistemi | 2 servis yönetimi |
| Presidio PII | Türkçe TCKN/IBAN regex desteği | spaCy model boyutu |
| ChromaDB RAG | Embedded deployment, SQLite benzeri | Production'da ölçek? |
| OpenAI API | Hızlı prototipleme | Vendor lock-in |
| Fail-closed tasarım | Güvenlik > kullanılabilirlik | Maskeleme down = sistem down |

### 2.3 Demo MVP İçin Bilinçli Sınırlamalar

Bu proje "Production-ready" değil, **demo amaçlı MVP**:
- Kubernetes/Docker Compose yok → basit local çalıştırma
- JWT/OAuth yok → CORS açık
- Multi-tenant yok → tek banka senaryosu
- Real-time streaming yok → sync HTTP

---

## 3. Yapılan İyileştirmeler ve Çözdükleri Sorular

| İyileştirme | Hangi Soruyu Çözüyor? | Kanıt Dosya |
|-------------|----------------------|-------------|
| **Sources DB** | "AI bu cevabı nereden buldu?" | `Complaint.sources` field |
| **Request ID** | "Bu istek hangi servisten geçti?" | `X-Request-ID` header |
| **Kaynaklar Response** | "Müşteri temsilcisi kaynağı görebilir mi?" | `SikayetResponse.kaynaklar` |
| **Golden Set** | "Sistem gerçekten doğru çalışıyor mu?" | 20 human-written örnek |
| **Eval Script** | "Metriklerle nasıl ölçeriz?" | accuracy, pii leak, latency |
| **Postman Collection** | "Demo'da nasıl gösteririz?" | 10 endpoint örneği |
| **Architecture Doc** | "Sistem nasıl çalışıyor?" | Mermaid diagramlar |

---

## 4. Kanıt İndeksi (Evidence Index)

### 4.1 Java Backend

| Dosya | Satır | Kanıt |
|-------|-------|-------|
| [Complaint.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/Complaint.java) | L19-20 | `originalText` kaldırıldı yorumu |
| [Complaint.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/Complaint.java) | L34-35 | `sources` field eklendi |
| [OrchestratorService.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/OrchestratorService.java) | L35 | Request ID generation |
| [OrchestratorService.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/OrchestratorService.java) | L44, L85, L103, L119 | X-Request-ID header |
| [OrchestratorService.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/OrchestratorService.java) | L49-61 | Fail-closed masking exception |
| [OrchestratorService.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/OrchestratorService.java) | L150-155 | Sources kaydetme |
| [ComplaintController.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/ComplaintController.java) | L53 | `kaynaklar` response'a eklendi |
| [ComplaintController.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/ComplaintController.java) | L105-124 | `parseKaynaklar()` method |
| [DTOs.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/DTOs.java) | L85-98 | `SourceItem` class |
| [DTOs.java](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-java/src/main/java/com/complaintops/backend/DTOs.java) | L100-120 | `TriageResponseFull` class |

### 4.2 Python AI Service

| Dosya | Satır | Kanıt |
|-------|-------|-------|
| [main.py](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-python/main.py) | L106-113 | Request ID middleware |
| [main.py](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-python/main.py) | L148-164 | Human review trigger (confidence < 0.60) |
| [pii_masker.py](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-python/pii_masker.py) | L15-31 | TCKN + IBAN regex |
| [llm_client.py](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-python/llm_client.py) | L99-104 | Prompt injection sanitization |
| [llm_client.py](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-python/llm_client.py) | L114-117 | PII leak detection |
| [review_store.py](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-python/review_store.py) | L36-62 | Review audit tables |

### 4.3 Dokümantasyon

| Dosya | İçerik |
|-------|--------|
| [README.md](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/README.md) | Proje açıklaması, kurulum, API docs |
| [docs/architecture.md](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/docs/architecture.md) | Component + sequence diagrams |
| [docs/postman_collection.json](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/docs/postman_collection.json) | 10 endpoint demo |
| [data/golden_set.json](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-python/data/golden_set.json) | 20 human-written örnek |
| [scripts/run_eval.py](file:///c:/Users/monster/Desktop/system-main/ComplaintOpsCopilot/backend-python/scripts/run_eval.py) | Metrik hesaplama scripti |

---

## 5. KPI ve Metrikler

### 5.1 Hedef Metrikler

| Metrik | Tanım | Hedef | Ölçüm |
|--------|-------|-------|-------|
| Schema Pass Rate | API response geçerli JSON + tüm alanlar | ≥99% | Test suite |
| PII Leak Rate | Raw PII DB/log/response'ta görünme | 0% | Eval script |
| Triage Accuracy | Kategori tahmini doğruluğu | ≥70% | Golden set |
| Urgency Accuracy | Aciliyet tahmini doğruluğu | ≥60% | Golden set |
| RAG Hit@4 | En az 1 ilgili kaynak bulma | ≥70% | Golden set |
| Latency p95 | End-to-end yanıt süresi | <5s | Eval script |
| Fail-Closed Rate | Masking hatası → doğru MASKING_FAILED | 100% | Unit test |

### 5.2 Eval Script Çıktısı

```bash
cd backend-python
python scripts/run_eval.py
```

Beklenen çıktı:
```
============================================================
EVALUATION SUMMARY
============================================================
Total Examples:       20
Successful:           X
Errors:               Y

Category Accuracy:    XX.XX%
Urgency Accuracy:     XX.XX%
PII Leak Rate:        0.00%

Latency (avg):        XXXms
Latency (p95):        XXXms
============================================================
```

---

## 6. Train Mixed, Eval Human-Written Yaklaşımı

### 6.1 Veri Stratejisi

| Veri Tipi | Kaynak | Kullanım | Dosya |
|-----------|--------|----------|-------|
| **Triage Train** | Sentetik + Augmented | ML model eğitimi | `data/triage_dataset.json` (35 örnek) |
| **SOP Train** | Sentetik | RAG knowledge base | `ingest_sops.py` (7 SOP) |
| **Golden Eval** | **Human-written** | Gerçek performans ölçümü | `data/golden_set.json` (20 örnek) |

### 6.2 Neden Bu Ayrım?

| Endişe | Çözüm |
|--------|-------|
| "Sentetik veri gerçeği yansıtmaz" | Eval **sadece** human-written veride |
| "20 örnek yeterli mi?" | Demo MVP için yeterli, production'da genişletilmeli |
| "Triage model overfitting?" | Train ≠ Eval veri seti, cross-validation gerekli (future) |

### 6.3 Önemli Not

> **DİKKAT:** `data/triage_dataset.json` eğitim amaçlı sentetik veridir.  
> Gerçek performans değerlendirmesi **sadece** `data/golden_set.json` üzerinde yapılmalıdır.

---

## 7. What We Did NOT Build (Anti-Overengineering)

| Yapmadık | Neden | Ne Zaman Gerekir? |
|----------|-------|-------------------|
| JWT/OAuth Authentication | Demo MVP, API key bile yok | Production |
| Kubernetes Deployment | Local demo yeterli | Ölçekleme gerektiğinde |
| Multi-LLM Routing | OpenAI-only demo için yeterli | Vendor diversification |
| Real-time Streaming | Sync HTTP demo için yeterli | UX iyileştirmesi |
| Kafka/RabbitMQ | 2 servis, HTTP yeterli | Event-driven architecture |
| Prometheus/Grafana | Console logging yeterli | Production observability |
| CI/CD Pipeline | Manual deployment | Team büyüdüğünde |
| Multi-tenant | Tek banka senaryosu | SaaS modeli |
| PDF/Image Processing | Metin şikayeti yeterli | Omni-channel |
| A/B Testing Framework | MVP'de tek model | Model karşılaştırması |

---

## 8. Güvenlik Katmanları (KVKK-Aware Design)

> **Not:** Bu proje "KVKK uyumludur" iddiası **yapmıyor**.  
> "KVKK-aware design" yaklaşımı benimsenmiştir.

| Katman | Koruma | Uygulama |
|--------|--------|----------|
| L1 | PII Maskeleme | Presidio + TR regex (TCKN, IBAN) |
| L2 | Fail-Closed | Exception → pipeline durur |
| L3 | No-Raw-in-DB | `originalText` alanı yok |
| L4 | Log Sanitization | Sadece `masked_text_length` |
| L5 | Prompt Injection | `<system>` tag temizleme |
| L6 | Output Validation | LLM çıktısında PII scan |
| L7 | Audit Trail | review_store audit tablosu |

---

## 9. Sonraki Adımlar (Roadmap)

### P0 (Demo İçin)
- [x] Tüm temel özellikler tamamlandı

### P1 (İyileştirme)
- [ ] `insan_incelemesi_gerekli` response'a ekle
- [ ] `guven_skorlari` response'a ekle
- [ ] Full graceful degradation
- [ ] Evidence klasörü doldur

### P2 (Future)
- [ ] Provider-agnostic LLM (Claude/Gemini)
- [ ] Docker Compose multi-service
- [ ] API key authentication
- [ ] Timeout/retry policies

---

## 10. Demo Konuşma Metni (Elevator Pitch)

> "ComplaintOps Copilot, bankacılık müşteri şikayetlerini analiz eden bir AI sistemidir.  
> Şikayet geldiğinde önce kişisel verileri maskeler—TCKN, IBAN, telefon otomatik temizlenir.  
> Eğer maskeleme servisi çökerse, **fail-closed** çalışır: pipeline durur, ham metin korunur.  
> Sonra ML ile kategori ve aciliyet tahmin eder; düşük güvende insan incelemesine yönlendirir.  
> RAG ile ilgili prosedürleri bulur, LLM ile profesyonel Türkçe yanıt taslağı üretir.  
> Tüm bunları yaparken veritabanına **asla ham metin kaydetmez**.  
> Bu bir demo MVP—production iddiası yok, ama 'ürün gibi düşünülmüş' bir sistem."

---

*Rapor Sonu - v2.0*
