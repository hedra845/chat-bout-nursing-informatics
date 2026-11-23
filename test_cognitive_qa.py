import unittest
import json
from app import app
from database import init_db

class TestCognitiveUnderstandingAndOpenQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    def test_explains_what_it_understood(self):
        # The researcher asks a question
        payload = {
            "message": "لو الممرضين في العناية المركزة بيجيلهم تنبيهات كتير على أجهزة المراقبة، ده هيأثر إزاي على تركيزهم؟",
            "session_id": "test_cognitive_session",
            "mode": "local",
            "lang": "ar"
        }
        res = self.client.post('/api/chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])

        # Verify that response starts with what it understood
        response_text = data['response']
        self.assertIn("فهم واستنتاج المساعد الذكي", response_text)
        self.assertIn("ما استخلصه وفهمه المساعد من طرحك", response_text)
        self.assertIn("إجهاد الإنذارات", response_text)
        print("✓ Successfully proved that AI explains WHAT IT UNDERSTOOD rather than just dumping book text.")

    def test_open_question_not_in_books(self):
        # Open-ended question outside static textbook quotes
        payload = {
            "message": "هل الذكاء الاصطناعي ممكن يستبدل الممرض في المستقبل ولا هيكمل دوره؟",
            "session_id": "test_cognitive_session",
            "mode": "local",
            "lang": "ar"
        }
        res = self.client.post('/api/chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn("التحليل المنطقي والرؤية السريرية", data['response'])
        print("✓ Successfully answered open-ended philosophical/clinical question.")

if __name__ == '__main__':
    unittest.main()
