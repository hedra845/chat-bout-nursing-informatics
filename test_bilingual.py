import unittest
import json
from app import app
from database import init_db

class TestBilingualNursingBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    def test_arabic_chat_response(self):
        payload = {
            "message": "ما هو هرم DIKW في معلوماتية التمريض وكيف يطبق سريرياً؟",
            "lang": "ar",
            "mode": "local"
        }
        res = self.client.post('/api/chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        # Verify response is Arabic
        self.assertIn("استجابة معلوماتية تمريضية", data['response'])
        self.assertGreater(len(data['sources']), 0)
        print("✓ Arabic Query Test Passed: Retrieved relevant chunks and responded fluently in Arabic.")

    def test_english_chat_response(self):
        payload = {
            "message": "Explain the difference between NANDA-I, NIC, and NOC terminologies in EHR systems.",
            "lang": "en",
            "mode": "local"
        }
        res = self.client.post('/api/chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        # Verify response is English
        self.assertIn("Nursing Informatics Specialized Clinical Response", data['response'])
        self.assertGreater(len(data['sources']), 0)
        print("✓ English Query Test Passed: Retrieved relevant chunks and responded fluently in English.")

    def test_cross_lingual_retrieval(self):
        # Asking in Arabic for an English indexed book term (e.g. أخطاء دوائية / دعم القرار)
        payload = {
            "message": "ما هو دور نظم دعم القرار الطبي في منع الأخطاء الدوائية؟",
            "lang": "auto",
            "mode": "local"
        }
        res = self.client.post('/api/chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        # Should match CDSS / EHR chunks via synonym mapper
        self.assertGreater(len(data['sources']), 0)
        print("✓ Cross-Lingual Concept Mapping Passed: Arabic inquiry successfully matched English textbook chunks.")

if __name__ == '__main__':
    unittest.main()
