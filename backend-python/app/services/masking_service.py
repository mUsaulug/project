from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import List, Dict, Tuple
import re
import logging

class PIIMasker:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.pdf_analyzer = None # Placeholder for PDF analysis if needed
        self.logger = logging.getLogger("complaintops.pii_masker")
        
        # Add Custom Recognizer for Turkish TCKN (Identity Number)
        # TCKN is 11 digits, valid algorithm check is complex but for regex we can use \d{11}
        # and maybe context words like "TC", "TCKN", "Kimlik"
        tckn_pattern = Pattern(name="tckn_pattern", regex=r"\b[1-9][0-9]{10}\b", score=0.5)
        tckn_recognizer = PatternRecognizer(
            supported_entity="TCKN",
            patterns=[tckn_pattern],
            context=["tc", "tckn", "kimlik", "no", "numarası"]
        )
        self.analyzer.registry.add_recognizer(tckn_recognizer)

        # IBAN is usually supported, but we can verify or add specific TR IBAN regex
        # TR IBAN: TR + 24 digits
        tr_iban_pattern = Pattern(name="tr_iban_pattern", regex=r"TR\d{2}\s?(\d{4}\s?){6}", score=0.8)
        tr_iban_recognizer = PatternRecognizer(
            supported_entity="TR_IBAN",
            patterns=[tr_iban_pattern],
            context=["iban", "hesap"]
        )
        self.analyzer.registry.add_recognizer(tr_iban_recognizer)

        # 1. PERSON Entity (Presidio built-in + Turkish context)
        # Note: We add a broad pattern for names (capitalized words) with low score
        # to allow context ("Sayın", "Bay" etc.) to boost confidence.
        person_pattern = Pattern(
            name="person_caps", 
            regex=r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)*\b", 
            score=0.2
        )
        person_recognizer = PatternRecognizer(
            supported_entity="PERSON",
            patterns=[person_pattern],
            context=["sayın", "bay", "bayan", "adı", "soyadı", "müşteri", "kişi"],
            deny_list=["Bu", "Şu", "O", "Ben", "Sen", "Biz", "Siz", "Onlar", "Evet", "Hayır", "Yok", "Var", "Merhabalar", "Merhaba", "Selam"]
        )
        self.analyzer.registry.add_recognizer(person_recognizer)

        # 2. CCV/CVV Recognition (Context-Required)
        ccv_pattern = Pattern(
            name="ccv_pattern",
            regex=r"\b\d{3,4}\b",
            score=0.3  # Low base score, context will boost
        )
        ccv_recognizer = PatternRecognizer(
            supported_entity="CCV",
            patterns=[ccv_pattern],
            context=["cvv", "ccv", "güvenlik kodu", "güvenlik numarası", 
                     "arkasındaki", "kartın arkası", "3 haneli", "4 haneli"]
        )
        self.analyzer.registry.add_recognizer(ccv_recognizer)

        # 3. PASSWORD/PIN Recognition
        password_pattern = Pattern(
            name="password_pattern",
            regex=r"\b[\w@#$%^&*]{4,20}\b",  # 4-20 chars, alphanumeric + special
            score=0.2  # Very low base, MUST have context
        )
        password_recognizer = PatternRecognizer(
            supported_entity="PASSWORD",
            patterns=[password_pattern],
            context=["şifre", "parola", "pin", "gizli kod", "internet şifresi",
                     "mobil şifre", "şifrem", "parolam", "password", "pin kodu"]
        )
        self.analyzer.registry.add_recognizer(password_recognizer)

        # 4. DATE_OF_BIRTH Recognition (Turkish formats)
        dob_patterns = [
            Pattern(name="dob_slash", regex=r"\b\d{2}/\d{2}/\d{4}\b", score=0.4),
            Pattern(name="dob_dot", regex=r"\b\d{2}\.\d{2}\.\d{4}\b", score=0.4),
            Pattern(name="dob_dash", regex=r"\b\d{4}-\d{2}-\d{2}\b", score=0.4),
        ]
        dob_recognizer = PatternRecognizer(
            supported_entity="DATE_OF_BIRTH",
            patterns=dob_patterns,
            context=["doğum", "doğum tarihi", "d.tarihi", "yaş", "doğumlu"]
        )
        self.analyzer.registry.add_recognizer(dob_recognizer)

        # 5. MAIDEN_NAME Recognition (Context-only)
        maiden_pattern = Pattern(
            name="maiden_name_word",
            regex=r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\b", # Single capitalized word
            score=0.2
        )
        maiden_recognizer = PatternRecognizer(
            supported_entity="MAIDEN_NAME",
            patterns=[maiden_pattern],
            context=["kızlık soyadı", "anne kızlık", "annenin kızlık", 
                     "kızlık soyadınız", "güvenlik sorusu"]
        )
        self.analyzer.registry.add_recognizer(maiden_recognizer)

        # 6. ACCOUNT_NUMBER Recognition
        account_pattern = Pattern(
            name="account_pattern",
            regex=r"\b\d{10,16}\b",
            score=0.4
        )
        account_recognizer = PatternRecognizer(
            supported_entity="ACCOUNT_NUMBER",
            patterns=[account_pattern],
            context=["hesap no", "hesap numarası", "hesabım", "hesap", 
                     "müşteri no", "müşteri numarası"]
        )
        self.analyzer.registry.add_recognizer(account_recognizer)

    def mask(self, text: str) -> Dict:
        # Analyze
        results = self.analyzer.analyze(
            text=text, 
            entities=[
                "TCKN", "TR_IBAN", "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD",
                "PERSON", "CCV", "PASSWORD", "DATE_OF_BIRTH", "MAIDEN_NAME", "ACCOUNT_NUMBER"
            ], 
            language='en',
            score_threshold=0.45  # Filter out low confidence (no-context) matches
        )
        
        # Anonymize
        operators = {
            "TCKN": OperatorConfig("replace", {"new_value": "[MASKED_TCKN]"}),
            "TR_IBAN": OperatorConfig("replace", {"new_value": "[MASKED_IBAN]"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[MASKED_PHONE]"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[MASKED_EMAIL]"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[MASKED_CC]"}),
            # New PII Types
            "PERSON": OperatorConfig("replace", {"new_value": "[MASKED_NAME]"}),
            "CCV": OperatorConfig("replace", {"new_value": "[MASKED_CCV]"}),
            "PASSWORD": OperatorConfig("replace", {"new_value": "[MASKED_PASSWORD]"}),
            "DATE_OF_BIRTH": OperatorConfig("replace", {"new_value": "[MASKED_DOB]"}),
            "MAIDEN_NAME": OperatorConfig("replace", {"new_value": "[MASKED_MAIDEN_NAME]"}),
            "ACCOUNT_NUMBER": OperatorConfig("replace", {"new_value": "[MASKED_ACCOUNT]"}),
        }
        
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        
        return {
            "original_text": text,
            "masked_text": anonymized_result.text,
            "masked_entities": [res.entity_type for res in results]
        }

    def mask_with_double_pass(self, text: str) -> Tuple[str, List[Dict], List[Dict]]:
        """
        Two-stage PII masking to achieve 0% leak rate.
        
        Stage 1: Presidio NLP-based detection
        Stage 2: Deterministic regex failsafe for Turkish patterns
        
        Returns:
            (masked_text, presidio_entities, regex_entities)
        """
        # Stage 1: Presidio
        result = self.mask(text)
        masked_text = result["masked_text"]
        presidio_entities = [{"type": ent, "source": "presidio"} for ent in result["masked_entities"]]
        
        # Stage 2: Deterministic regex patterns (Turkish banking specific)
        regex_patterns = {
            "IBAN": r"TR\s?[0-9]{2}\s?[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\s?[0-9]{2}",
            "TCKN": r"\b[1-9][0-9]{10}\b",
            "PHONE": r"(?:\+90|0)?\s?[5][0-9]{2}\s?[0-9]{3}\s?[0-9]{2}\s?[0-9]{2}",
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "CREDIT_CARD": r"\b[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}\b",
            # New failsafe patterns
            "ACCOUNT": r"(?:hesap\s*(?:no|numarası)?[:\s]*)\d{10,16}",
        }
        
        regex_entities = []
        for entity_type, pattern in regex_patterns.items():
            for match in re.finditer(pattern, masked_text, re.IGNORECASE):
                masked_text = masked_text.replace(match.group(0), f"[MASKED_{entity_type}]")
                regex_entities.append({
                    "type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "text": "[REDACTED]",  # Don't log actual PII
                    "source": "regex_failsafe"
                })
        
        # Log audit trail
        self.logger.info(
            "pii_masking_complete presidio_count=%d regex_count=%d",
            len(presidio_entities),
            len(regex_entities)
        )
        
        return masked_text, presidio_entities, regex_entities


# Global instance
masker = PIIMasker()
