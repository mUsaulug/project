# Evidence Klasörü

Bu klasör, demo ve staj görüşmesi için kanıt dosyalarını içerir.

## Klasör Yapısı

```
evidence/
├── README.md           ← Bu dosya
├── test_java.txt       ← Java test çıktısı (mvn test)
├── test_python.txt     ← Python test çıktısı (pytest)
├── eval_results.json   ← Eval script çıktısı
└── screenshots/        ← Postman response ekran görüntüleri
```

## Dosyaları Oluşturma Talimatları

### 1. Java Test Çıktısı

```powershell
cd backend-java
mvn test > ../docs/evidence/test_java.txt 2>&1
```

### 2. Python Test Çıktısı

```powershell
cd backend-python
pytest test_kvkk_compliance.py -v > ../docs/evidence/test_python.txt 2>&1
```

### 3. Eval Sonuçları

```powershell
cd backend-python
python scripts/run_eval.py --output ../docs/evidence/eval_results.json
```

### 4. Screenshots

Postman'da şu istekleri çalıştırın ve response'ları screenshot olarak kaydedin:

1. `fraud_with_pii.png` → Dolandırıcılık + PII örneği
2. `transfer_delay.png` → Transfer gecikmesi örneği
3. `masking_failed.png` → Python kapalıyken fail-closed
4. `eval_summary.png` → Eval script çıktısı terminal

---

## Demo Akışı için Hızlı Komutlar

**1. Servisleri Başlat:**
```powershell
# Terminal 1 - Python
cd backend-python
uvicorn main:app --reload --port 8000

# Terminal 2 - Java
cd backend-java
mvn spring-boot:run
```

**2. Demo Script Çalıştır:**
```powershell
cd scripts
.\demo.ps1
```

---

*Bu README, evidence klasörünün kullanım kılavuzudur.*
