import pytest
from app.services.masking_service import masker

class TestPersonMasking:
    """PERSON entity detection"""
    
    @pytest.mark.parametrize("text,should_mask", [
        ("Sayın Ahmet Yılmaz", True),
        ("Müşteri Fatma Öztürk ile görüşüldü", True),
        ("Bay Mehmet bey aradı", True),
        ("Bu bir test metnidir", False),  # No name
    ])
    def test_person_detection(self, text, should_mask):
        result = masker.mask(text)
        has_person = "PERSON" in result["masked_entities"]
        assert has_person == should_mask

class TestCCVMasking:
    """CCV detection with context requirement"""
    
    def test_ccv_with_context(self):
        result = masker.mask("CVV kodunuz 123")
        assert "CCV" in result["masked_entities"]
        assert "123" not in result["masked_text"]
    
    def test_ccv_without_context_no_mask(self):
        result = masker.mask("123 adet sipariş verdim")
        assert "CCV" not in result["masked_entities"]
        assert "123" in result["masked_text"]

class TestPasswordMasking:
    """PASSWORD/PIN detection"""
    
    @pytest.mark.parametrize("text", [
        ("Şifrem: abc123xyz", True),
        ("PIN kodunu unuttum: 1234", True),
        ("Internet şifresi: MyP@ss2024!", True),
        ("Bu normal bir metindir", False),
    ])
    def test_password_masked(self, text, should_mask):
        result = masker.mask(text)
        has_password = "PASSWORD" in result["masked_entities"]
        assert has_password == should_mask

class TestDateOfBirthMasking:
    """DOB detection with context"""
    
    def test_dob_with_context(self):
        result = masker.mask("Doğum tarihi: 15/03/1990")
        assert "DATE_OF_BIRTH" in result["masked_entities"]
    
    def test_transaction_date_not_masked(self):
        result = masker.mask("İşlem tarihi: 15/03/2024")
        assert "DATE_OF_BIRTH" not in result["masked_entities"]

class TestMaidenNameMasking:
    """MAIDEN_NAME detection"""

    def test_maiden_name_detection(self):
        result = masker.mask("Annenin kızlık soyadı: Yıldırım")
        assert "MAIDEN_NAME" in result["masked_entities"]

class TestAccountNumberMasking:
    """ACCOUNT_NUMBER detection"""

    def test_account_number_with_context(self):
        result = masker.mask("Hesap no: 1234567890123456")
        assert "ACCOUNT_NUMBER" in result["masked_entities"]
        assert "1234567890123456" not in result["masked_text"]

class TestFalsePositivePrevention:
    """Ensure common text doesn't trigger false positives"""
    
    @pytest.mark.parametrize("text", [
        "Toplam 500 TL ödeme yaptım",
        "2024 yılında başvurdum",
        "3 gün içinde çözüldü",
    ])
    def test_common_text_not_masked(self, text):
        result = masker.mask(text)
        # Should have minimal or no masking
        assert len(result["masked_entities"]) == 0
