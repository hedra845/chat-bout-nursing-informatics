import unittest
import json
from app import app
from database import init_db

class TestResearcherCognitiveMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    def test_researcher_dialogue_and_idea_logging(self):
        # 1. Researcher poses a hypothesis
        researcher_hypothesis = "أفترض أن تطبيق نظم دعم القرار CDSS في أقسام الطوارئ يقلل إجهاد التنبيهات إذا تم ربطه بنظام الفرز الذكي."
        payload = {
            "message": researcher_hypothesis,
            "session_id": "session_researcher_01",
            "mode": "local",
            "lang": "ar"
        }
        res = self.client.post('/api/chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        
        # Check that response acknowledges researcher's line of thought logically
        self.assertIn("مناقشة منطقية مع الباحث السريري", data['response'])
        self.assertIn("التحليل المنطقي لطرحك العلمي", data['response'])
        print("✓ Logical academic response generated.")

        # 2. Check profile updated
        self.assertIn("researcher_profile", data)
        self.assertEqual(data['researcher_profile']['style'], "تأملي استنتاجي (Hypothesis-Driven & Reflective)")
        print("✓ Tone & style detected:", data['researcher_profile']['style'])

        # 3. Check that idea was recorded in database
        ideas_res = self.client.get('/api/researcher/ideas?session_id=session_researcher_01')
        ideas_data = json.loads(ideas_res.data)
        self.assertTrue(ideas_data['success'])
        self.assertGreaterEqual(len(ideas_data['ideas']), 1)
        self.assertEqual(ideas_data['ideas'][0]['type'], "فرضية بحثية")
        print("✓ Hypothesis recorded in memory:", ideas_data['ideas'][0]['statement'])

    def test_second_turn_contextual_continuity(self):
        # Follow-up question continuing the logical dialogue
        follow_up = "بناءً على ذلك، ما هي المعايير القياسية مثل ICNP و NANDA التي تدعم هذا التوجه؟"
        payload = {
            "message": follow_up,
            "session_id": "session_researcher_01",
            "mode": "local",
            "lang": "ar"
        }
        res = self.client.post('/api/chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        # Confirms reference to past ideas in the logical synthesis
        self.assertIn("ربطاً بأفكارك وملاحظاتك السابقة", data['response'])
        print("✓ Continuity verified: AI referenced past thoughts in synthesis.")

if __name__ == '__main__':
    unittest.main()
