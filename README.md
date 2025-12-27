# ComplaintOps Copilot - Bankacılık Şikayet Yönetim Sistemi

**AI-Destekli Müşteri Şikayeti Analiz ve Yanıt Sistemi**

## 🎯 Proje Özeti

ComplaintOps Copilot, bankacılık sektöründe müşteri şikayetlerini otomatik olarak analiz eden, kategorize eden ve çözüm önerileri üreten bir AI sistemidir.

### Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| **PII Maskeleme** | TCKN, IBAN, telefon, email otomatik maskelenir (KVKK uyumlu) |
| **Fail-Closed Güvenlik** | Maskeleme hatası → pipeline durur, raw text korunur |
| **AI Kategorizasyon** | ML model ile 7 kategori + aciliyet tahmini |
| **RAG Destekli Yanıt** | SOP dokümanlarından ilgili prosedürleri bulur |
| **LLM Yanıt Üretimi** | Müşteriye profesyonel Türkçe yanıt taslağı |
| **Human-in-the-Loop** | Düşük güvenli tahminler manuel incelemeye yönlendirilir |

---

## 🏗️ Mimari

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│  Java Backend   │────▶│  Python AI      │
│   (React)       │     │  (Orchestrator) │     │  (ML/LLM/RAG)   │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   PostgreSQL    │
                        │   (No Raw PII)  │
                        └─────────────────┘
```

**Java Orchestrator** → İş akışı, KVKK uyumu, DB yönetimi  
**Python AI Service** → PII maskeleme, ML triage, RAG, LLM

---

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Java 17+
- Python 3.10+
- PostgreSQL (veya H2 test için)

### 1. Python AI Service

```bash
cd backend-python
pip install -r requirements.txt

# ChromaDB için SOP'ları yükle
python ingest_sops.py

# Triage modelini eğit (opsiyonel, model repo'da mevcut)
python train_triage_model.py

# Servisi başlat
uvicorn main:app --reload --port 8000
```

### 2. Java Backend

```bash
cd backend-java

# application.properties'i düzenle (ai-service.url, db config)
mvn spring-boot:run
```

### 3. Test Et

```bash
# Türkçe API endpoint
curl -X POST http://localhost:8080/api/sikayet \
  -H "Content-Type: application/json" \
  -d '{"metin": "Kartımdan bilgim dışında 500 TL çekilmiş."}'
```

---

## 📡 API Referansı

### POST /api/sikayet (Türkçe)

**Request:**
```json
{
  "metin": "Kartımdan bilgim dışında 500 TL çekilmiş."
}
```

**Response:**
```json
{
  "id": 42,
  "kategori": "DOLANDIRICILIK_YETKISIZ_ISLEM",
  "oncelik": "YUKSEK",
  "oneri": "Sayın müşterimiz, kartınız güvenlik nedeniyle bloke edilmiştir...",
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

### POST /api/analyze (English)

Same functionality, returns raw English fields.

### GET /api/complaints

List all processed complaints.

### GET /api/complaints/{id}

Get complaint by ID.

---

## 🔐 Güvenlik & KVKK

| Özellik | Uygulama |
|---------|----------|
| **No Raw Text in DB** | `Complaint.originalText` alanı yok |
| **Fail-Closed PII** | Maskeleme hatası → `MASKING_FAILED` status |
| **Log Sanitization** | Sadece `masked_text_length` loglanır |
| **Prompt Injection Guard** | `<system>`, ` ``` ` tag'leri temizlenir |
| **PII Leak Detection** | LLM çıktısı tekrar PII taramasından geçer |

---

## 🧪 Testler

```bash
# Java testleri
cd backend-java
mvn test

# Python testleri
cd backend-python
pytest test_kvkk_compliance.py -v
```

### Test Coverage

- **KvkkComplianceTest.java** → Fail-closed, no-raw-text
- **SikayetSchemaTest.java** → Türkçe API kontratı
- **test_kvkk_compliance.py** → PII maskeleme, log sanitization

---

## 📁 Proje Yapısı

```
ComplaintOpsCopilot/
├── backend-java/
│   ├── src/main/java/com/complaintops/backend/
│   │   ├── ComplaintController.java   # REST API
│   │   ├── OrchestratorService.java   # İş akışı
│   │   ├── Complaint.java             # Entity (no raw text)
│   │   └── DTOs.java                  # API kontratları
│   └── src/test/java/                 # KVKK testleri
│
├── backend-python/
│   ├── main.py                        # FastAPI endpoints
│   ├── pii_masker.py                  # Presidio PII maskeleme
│   ├── triage_model.py                # ML kategorizasyon
│   ├── rag_manager.py                 # ChromaDB RAG
│   ├── llm_client.py                  # OpenAI entegrasyonu
│   └── review_store.py                # Human review audit
│
└── docs/
    ├── architecture.md                # Mimari detayları
    ├── postman_collection.json        # Demo collection
    ├── MVP_INCELEME_RAPORU_v2.md      # Ürün inceleme raporu
    ├── API_SCHEMA_TR_v2.md            # Türkçe API şeması
    ├── FAILURE_MODES.md               # Hata senaryoları
    └── evidence/                       # Test kanıtları
```

---

## ⚠️ Failure Modes (Hata Senaryoları)

| Senaryo | Sistem Davranışı |
|---------|------------------|
| **PII Maskeleme çöker** | Pipeline durur, raw text korunur, `MASKELEME_HATASI` döner |
| **RAG erişilemez** | Boş kaynak listesi, LLM devam eder |
| **LLM API çöker** | Template yanıt döner |
| **Triage hatası** | Varsayılan: `MANUEL_INCELEME`, `YUKSEK` öncelik |
| **Düşük güven skoru** | `insan_incelemesi_gerekli: true`, review kaydı oluşur |

> Detaylı bilgi için: [docs/FAILURE_MODES.md](docs/FAILURE_MODES.md)

---

## 🎯 Demo Senaryoları

### Senaryo 1: Dolandırıcılık Şikayeti
```json
{"metin": "Kartımdan bilgim dışında 5000 TL çekilmiş, TC: 12345678901"}
```
→ PII maskelenir → `FRAUD_UNAUTHORIZED_TX` → `YUKSEK` öncelik

### Senaryo 2: Transfer Gecikmesi
```json
{"metin": "EFT yaptım 3 saattir ulaşmadı"}
```
→ `TRANSFER_DELAY` → `ORTA` öncelik → FAST SOP önerisi

### Senaryo 3: Maskeleme Hatası (Fail-Closed)
Python servisi kapalıyken istek gönder → `MASKELEME_HATASI` status, raw text korunur

---

## 📜 Lisans

MIT License - Demo/MVP amaçlı
