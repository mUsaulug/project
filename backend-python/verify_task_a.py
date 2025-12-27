import sys
import os

# Set encoding to utf-8 for Windows console/redirection
sys.stdout.reconfigure(encoding='utf-8')

# Add current directory to path to allow imports
sys.path.append(os.getcwd())

from app.services.masking_service import masker

def test_person_masking():
    print("Testing PERSON masking...")
    cases = [
        ("Sayın Ahmet Yılmaz", True),
        ("Müşteri Fatma Öztürk ile görüşüldü", True),
        ("Bay Mehmet bey aradı", True),
        ("Bu bir test metnidir", False),
    ]
    failed = 0
    for text, should_mask in cases:
        result = masker.mask(text)
        has_person = "PERSON" in result["masked_entities"]
        if has_person != should_mask:
            print(f"FAIL: '{text}' -> Expected PERSON={should_mask}, got {has_person}")
            failed += 1
        else:
            print(f"PASS: '{text}'")
    return failed

def test_ccv_masking():
    print("\nTesting CCV masking...")
    # Context required
    text1 = "CVV kodunuz 123"
    res1 = masker.mask(text1)
    if "CCV" in res1["masked_entities"] and "123" not in res1["masked_text"]:
        print(f"PASS: '{text1}'")
    else:
        print(f"FAIL: '{text1}' -> Detected: {res1['masked_entities']}")
        return 1
        
    # No context
    text2 = "123 adet sipariş verdim"
    res2 = masker.mask(text2)
    if "CCV" not in res2["masked_entities"] and "123" in res2["masked_text"]:
        print(f"PASS: '{text2}'")
    else:
        print(f"FAIL: '{text2}' -> Detected: {res2['masked_entities']}")
        return 1
    return 0

def test_password_masking():
    print("\nTesting PASSWORD masking...")
    cases = [
        ("Şifrem: abc123xyz", True),
        ("PIN kodunu unuttum: 1234", True),
        ("Internet şifresi: MyP@ss2024!", True),
        ("Bu normal bir metindir", False),
    ]
    failed = 0
    for text, should_mask in cases:
        result = masker.mask(text)
        has_pass = "PASSWORD" in result["masked_entities"]
        if has_pass != should_mask:
            print(f"FAIL: '{text}' -> Expected PASSWORD={should_mask}, got {has_pass}")
            failed += 1
        else:
            print(f"PASS: '{text}'")
    return failed

def test_dob_masking():
    print("\nTesting DOB masking...")
    text1 = "Doğum tarihi: 15/03/1990"
    res1 = masker.mask(text1)
    if "DATE_OF_BIRTH" in res1["masked_entities"]:
        print(f"PASS: '{text1}'")
    else:
        print(f"FAIL: '{text1}'")
        return 1
        
    text2 = "İşlem tarihi: 15/03/2024"
    res2 = masker.mask(text2)
    if "DATE_OF_BIRTH" not in res2["masked_entities"]:
         print(f"PASS: '{text2}'")
    else:
         print(f"FAIL: '{text2}' -> False positive")
         return 1
    return 0

def main():
    failures = 0
    failures += test_person_masking()
    failures += test_ccv_masking()
    failures += test_password_masking()
    failures += test_dob_masking()
    
    print(f"\nTotal Failures: {failures}")
    if failures == 0:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
