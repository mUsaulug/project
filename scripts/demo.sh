#!/bin/bash
# ComplaintOps Copilot - Demo Script (Linux/Mac)
# Bu script, demo sırasında 3 senaryoyu otomatik olarak çalıştırır.
# Kullanım: ./demo.sh

JAVA_URL="${JAVA_URL:-http://localhost:8080}"
PYTHON_URL="${PYTHON_URL:-http://localhost:8000}"

echo ""
echo "=============================================="
echo "  ComplaintOps Copilot - Demo Script"
echo "=============================================="
echo ""

# Renk kodları
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

success() { echo -e "${GREEN}[✓] $1${NC}"; }
info() { echo -e "${CYAN}[i] $1${NC}"; }
warning() { echo -e "${YELLOW}[!] $1${NC}"; }
error() { echo -e "${RED}[✗] $1${NC}"; }

# Servis kontrolleri
info "Servis kontrolü yapılıyor..."

if curl -s "$PYTHON_URL/" > /dev/null 2>&1; then
    success "Python AI Service çalışıyor"
else
    error "Python servisi yanıt vermiyor: $PYTHON_URL"
    warning "Lütfen önce Python servisini başlatın:"
    echo "   cd backend-python && uvicorn main:app --port 8000"
    exit 1
fi

if curl -s "$JAVA_URL/api/complaints" > /dev/null 2>&1; then
    success "Java Backend çalışıyor"
else
    error "Java servisi yanıt vermiyor: $JAVA_URL"
    warning "Lütfen önce Java servisini başlatın:"
    echo "   cd backend-java && mvn spring-boot:run"
    exit 1
fi

echo ""
echo "=============================================="
echo "  SENARYO 1: Dolandırıcılık + PII"
echo "=============================================="
echo ""

info "İstek gönderiliyor..."

RESPONSE1=$(curl -s -X POST "$JAVA_URL/api/sikayet" \
    -H "Content-Type: application/json" \
    -d '{"metin": "Kartımdan bilgim dışında 5000 TL çekilmiş. TC: 12345678901, IBAN: TR330006100519786457841326"}')

echo "Response:"
echo "$RESPONSE1" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE1"
echo ""

if echo "$RESPONSE1" | grep -q "12345678901"; then
    warning "DİKKAT: Yanıtta PII görünüyor olabilir!"
else
    success "PII maskeleme başarılı"
fi

echo ""
echo "=============================================="
echo "  SENARYO 2: Transfer Gecikmesi"
echo "=============================================="
echo ""

RESPONSE2=$(curl -s -X POST "$JAVA_URL/api/sikayet" \
    -H "Content-Type: application/json" \
    -d '{"metin": "EFT yaptım 3 saattir ulaşmadı, acil para lazım"}')

echo "Response:"
echo "$RESPONSE2" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE2"

echo ""
echo "=============================================="
echo "  SENARYO 3: Fail-Closed Test"
echo "=============================================="
echo ""

warning "Bu senaryo için Python servisini DURDURUN!"
read -p "Devam etmek için ENTER'a basın..."

RESPONSE3=$(curl -s -X POST "$JAVA_URL/api/sikayet" \
    -H "Content-Type: application/json" \
    -d '{"metin": "Test şikayeti - fail-closed kontrolü"}' \
    --max-time 30)

echo "Response:"
echo "$RESPONSE3" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE3"

if echo "$RESPONSE3" | grep -q "MASKELEME_HATASI"; then
    success "Fail-closed çalışıyor!"
fi

echo ""
echo "=============================================="
echo "  EVAL SCRIPT"
echo "=============================================="
echo ""

warning "Python servisini YENİDEN BAŞLATIN!"
read -p "Devam etmek için ENTER'a basın..."

cd "$(dirname "$0")/../backend-python" || exit
python3 scripts/run_eval.py --output ../docs/evidence/eval_results.json

echo ""
success "Demo tamamlandı!"
echo ""
