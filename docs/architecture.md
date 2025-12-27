# ComplaintOps Copilot - Mimari Dokümantasyonu

## Sistem Genel Görünümü

```mermaid
graph TB
    subgraph "Frontend"
        FE[React App]
    end
    
    subgraph "Java Orchestrator"
        API[REST API<br>/api/sikayet<br>/api/analyze]
        ORCH[OrchestratorService]
        REPO[ComplaintRepository]
    end
    
    subgraph "Python AI Service"
        MASK[PII Masker<br>Presidio]
        TRIAGE[Triage Model<br>scikit-learn]
        RAG[RAG Manager<br>ChromaDB]
        LLM[LLM Client<br>OpenAI]
        REVIEW[Review Store<br>SQLite]
    end
    
    subgraph "Data Stores"
        PG[(PostgreSQL<br>Complaints)]
        CHROMA[(ChromaDB<br>SOPs)]
    end
    
    FE -->|HTTP/JSON| API
    API --> ORCH
    ORCH -->|X-Request-ID| MASK
    ORCH -->|X-Request-ID| TRIAGE
    ORCH -->|X-Request-ID| RAG
    ORCH -->|X-Request-ID| LLM
    TRIAGE -.->|Low Confidence| REVIEW
    ORCH --> REPO
    REPO --> PG
    RAG --> CHROMA
```

---

## İstek Akışı (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant J as Java Orchestrator
    participant M as /mask
    participant T as /predict
    participant R as /retrieve
    participant G as /generate
    participant DB as PostgreSQL

    C->>J: POST /api/sikayet {metin}
    Note over J: Generate request_id (UUID)
    
    rect rgb(255, 240, 240)
        Note over J,M: FAIL-CLOSED Zone
        J->>M: POST /mask {text}<br>X-Request-ID: uuid
        alt Masking Success
            M-->>J: {masked_text, entities}
        else Masking Failure
            M--xJ: Error/Timeout
            J->>DB: INSERT MASKING_FAILED
            J-->>C: {durum: MASKELEME_HATASI}
        end
    end
    
    J->>T: POST /predict {masked_text}
    T-->>J: {category, urgency, confidence}
    Note over T: confidence < 0.60 → PENDING_REVIEW
    
    J->>R: POST /retrieve {masked_text, category}
    R-->>J: {relevant_sources[]}
    
    J->>G: POST /generate {text, category, sources}
    G-->>J: {action_plan, reply_draft, sources}
    
    J->>DB: INSERT complaint (no raw text)
    J-->>C: {kategori, oncelik, oneri, kaynaklar}
```

---

## Bileşen Detayları

### Java Orchestrator (Spring Boot)

| Dosya | Sorumluluk |
|-------|------------|
| `ComplaintController.java` | REST endpoints, Türkçe mapping |
| `OrchestratorService.java` | İş akışı, fail-closed logic, request ID |
| `Complaint.java` | JPA Entity (no originalText) |
| `DTOs.java` | API kontratları, SourceItem |

### Python AI Service (FastAPI)

| Dosya | Sorumluluk |
|-------|------------|
| `pii_masker.py` | TCKN, IBAN, Email, Telefon maskeleme |
| `triage_model.py` | Kategori + urgency prediction |
| `rag_manager.py` | ChromaDB embedding search |
| `llm_client.py` | OpenAI API, prompt injection guard |
| `review_store.py` | Human review audit trail |

---

## Veri Akışı

```mermaid
graph LR
    subgraph "Input"
        RAW[Raw Text<br>+ PII]
    end
    
    subgraph "Masking"
        SAFE[Masked Text<br>PII Removed]
    end
    
    subgraph "Analysis"
        CAT[Category]
        URG[Urgency]
        SRC[Sources]
    end
    
    subgraph "Output"
        RESP[Response<br>Draft]
    end
    
    subgraph "Storage"
        DB[(DB: Only<br>Masked Text)]
    end
    
    RAW -->|Presidio| SAFE
    SAFE --> CAT
    SAFE --> URG
    SAFE --> SRC
    CAT --> RESP
    URG --> RESP
    SRC --> RESP
    SAFE --> DB
    RESP --> DB
    
    style RAW fill:#ffcccc
    style SAFE fill:#ccffcc
    style DB fill:#ccffcc
```

---

## Güvenlik Katmanları

| Katman | Koruma | Dosya |
|--------|--------|-------|
| **L1: Input** | PII Maskeleme (Presidio) | `pii_masker.py` |
| **L2: Pipeline** | Fail-Closed (exception → stop) | `OrchestratorService.java` |
| **L3: LLM** | Prompt injection sanitization | `llm_client.py` |
| **L4: Output** | PII leak detection | `llm_client.py:_detect_pii` |
| **L5: Storage** | No raw text field | `Complaint.java` |
| **L6: Logs** | Only masked_text_length | `logging_config.py` |

---

## Konfigürasyon

### Java (application.properties)
```properties
ai-service.url=http://localhost:8000
spring.datasource.url=jdbc:postgresql://localhost:5432/complaintops
```

### Python (environment)
```bash
OPENAI_API_KEY=sk-...
LOG_LEVEL=INFO
RAG_TOP_K=4
ALLOW_RAW_PII_RESPONSE=false
```
