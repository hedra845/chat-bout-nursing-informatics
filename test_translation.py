import unittest
import json
from app import app
from translator import translate_to_arabic, NURSING_INFORMATICS_GLOSSARY

class TestTranslationFeature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_offline_clinical_translation(self):
        sample_english = (
            "Nursing Informatics (NI) is the specialty that integrates nursing science "
            "with multiple information and analytical sciences to identify, define, manage, and communicate "
            "data, information, knowledge, and wisdom in nursing practice."
        )
        translated, provider = translate_to_arabic(sample_english)
        self.assertIn("معلوماتية التمريض", translated)
        self.assertIn("بيانات", translated)
        self.assertIn("معرفة", translated)
        self.assertIn("حكمة", translated)
        print("✓ Offline Clinical Translation Passed: Verified accurate translation with domain terms.")

    def test_translation_api_endpoint(self):
        payload = {
            "text": "Clinical Decision Support Systems (CDSS) reduce medication error and alert fatigue in EHR."
        }
        res = self.client.post('/api/translate', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn("translated_text", data)
        self.assertIn("دعم القرار السريري", data['translated_text'])
        print("✓ Translation API Endpoint Passed. Result:\n", data['translated_text'])

if __name__ == '__main__':
    unittest.main()
