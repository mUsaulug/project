# ComplaintOps Copilot - Demo Script (Windows PowerShell)
# Bu script, demo sirasinda 3 senaryoyu otomatik olarak calistirir.
# Kullanim: .\scripts\demo.ps1

param(
    [string]$JavaUrl = "http://localhost:8080",
    [string]$PythonUrl = "http://localhost:8000"
)

Write-Host ""
Write-Host "=============================================="
Write-Host "  ComplaintOps Copilot - Demo Script"
Write-Host "=============================================="
Write-Host ""

# Renk fonksiyonlari
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERR] $msg" -ForegroundColor Red }

# Servis kontrolleri
Write-Info "Servis kontrolu yapiliyor..."

try {
    $null = Invoke-RestMethod -Uri "$PythonUrl/" -Method Get -TimeoutSec 5
    Write-Success "Python AI Service calisiyor"
}
catch {
    Write-Error "Python servisi yanit vermiyor: $PythonUrl"
    Write-Warning "Lutfen once Python servisini baslatin:"
    Write-Host "   cd backend-python; uvicorn app.main:app --port 8000"
    exit 1
}

try {
    $null = Invoke-RestMethod -Uri "$JavaUrl/api/complaints" -Method Get -TimeoutSec 5
    Write-Success "Java Backend calisiyor"
}
catch {
    Write-Error "Java servisi yanit vermiyor: $JavaUrl"
    Write-Warning "Lutfen once Java servisini baslatin:"
    Write-Host "   cd backend-java; mvn spring-boot:run"
    exit 1
}

Write-Host ""
Write-Host "=============================================="
Write-Host "  SENARYO 1: Dolandiricilik + PII"
Write-Host "=============================================="
Write-Host ""

$scenario1 = @{
    metin = "Kartimdan bilgim disinda 5000 TL cekilmis. TC: 12345678901, IBAN: TR330006100519786457841326"
} | ConvertTo-Json -Compress

Write-Info "Istek gonderiliyor..."
Write-Host "Request: $scenario1"
Write-Host ""

try {
    $response1 = Invoke-RestMethod -Uri "$JavaUrl/api/sikayet" -Method Post -Body $scenario1 -ContentType "application/json"
    Write-Success "Yanit alindi!"
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Yellow
    $response1 | ConvertTo-Json -Depth 5
    Write-Host ""
    
    # PII kontrolu
    if ($response1.oneri -notmatch "12345678901" -and $response1.oneri -notmatch "TR330006") {
        Write-Success "PII maskeleme basarili - ham veri yanitta yok"
    }
    else {
        Write-Warning "DIKKAT: Yanitta PII gorunuyor olabilir!"
    }
    
    # Kaynaklar kontrolu
    if ($response1.kaynaklar.Count -gt 0) {
        Write-Success "RAG kaynaklari dondu: $($response1.kaynaklar.Count) kaynak"
    }
    else {
        Write-Info "Kaynak dondurulemedi (RAG bos veya mock mode)"
    }
}
catch {
    Write-Error "Istek basarisiz: $_"
}

Write-Host ""
Write-Host "=============================================="
Write-Host "  SENARYO 2: Transfer Gecikmesi"
Write-Host "=============================================="
Write-Host ""

$scenario2 = @{
    metin = "EFT yaptim 3 saattir ulasmadi, acil para lazim"
} | ConvertTo-Json -Compress

Write-Info "Istek gonderiliyor..."

try {
    $response2 = Invoke-RestMethod -Uri "$JavaUrl/api/sikayet" -Method Post -Body $scenario2 -ContentType "application/json"
    Write-Success "Yanit alindi!"
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Yellow
    $response2 | ConvertTo-Json -Depth 5
    
    if ($response2.kategori -eq "TRANSFER_GECIKMESI") {
        Write-Success "Kategori dogru tahmin edildi"
    }
    else {
        Write-Info "Kategori: $($response2.kategori)"
    }
}
catch {
    Write-Error "Istek basarisiz: $_"
}

Write-Host ""
Write-Host "=============================================="
Write-Host "  SENARYO 3: Fail-Closed Test (Python Kapali)"
Write-Host "=============================================="
Write-Host ""

Write-Warning "Bu senaryo icin Python servisini DURDURUN!"
Write-Host "Devam etmek icin ENTER'a basin (veya Ctrl+C ile cikin)..."
$null = Read-Host

$scenario3 = @{
    metin = "Test sikayeti - fail-closed kontrolu"
} | ConvertTo-Json -Compress

Write-Info "Istek gonderiliyor (Python kapali olmali)..."

try {
    $response3 = Invoke-RestMethod -Uri "$JavaUrl/api/sikayet" -Method Post -Body $scenario3 -ContentType "application/json" -TimeoutSec 30
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Yellow
    $response3 | ConvertTo-Json -Depth 5
    
    if ($response3.durum -eq "MASKELEME_HATASI") {
        Write-Success "Fail-closed calisiyor! durum: MASKELEME_HATASI"
    }
    else {
        Write-Info "durum: $($response3.durum)"
    }
}
catch {
    Write-Warning "Hata alindi (beklenen davranis olabilir): $_"
}

Write-Host ""
Write-Host "=============================================="
Write-Host "  EVAL SCRIPT CALISTIRMA"
Write-Host "=============================================="
Write-Host ""

Write-Warning "Python servisini YENIDEN BASLATIN!"
Write-Host "Devam etmek icin ENTER'a basin..."
$null = Read-Host

Write-Info "Eval script calistiriliyor..."

$evalPath = Join-Path $PSScriptRoot "..\backend-python"
Push-Location $evalPath

try {
    py scripts/run_eval.py --output ..\docs\evidence\eval_results.json
    Write-Success "Eval sonuclari kaydedildi: docs/evidence/eval_results.json"
}
catch {
    Write-Error "Eval script hatasi: $_"
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "=============================================="
Write-Host "  DEMO TAMAMLANDI"
Write-Host "=============================================="
Write-Host ""
Write-Info "Sonraki adimlar:"
Write-Host "  1. docs/evidence/ klasorundeki dosyalari kontrol edin"
Write-Host "  2. Postman'da collection'i acin ve screenshot alin"
Write-Host "  3. Sunuma hazirsiniz!"
Write-Host ""
