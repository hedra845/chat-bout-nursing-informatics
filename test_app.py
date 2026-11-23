import unittest
import json
import os
from app import app
from database import init_db, get_db_connection

class TestNursingInformaticsApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    def test_stats_endpoint(self):
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('books', data['stats'])
        self.assertGreaterEqual(data['stats']['books'], 1)
        print("✓ Stats Endpoint Passed:", data['stats'])

    def test_books_endpoint(self):
        response = self.client.get('/api/books')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['books']), 1)
        print("✓ Books list retrieved successfully. Found:", len(data['books']), "books")

    def test_chat_and_repetition(self):
        # Ask question
        payload = {
            "message": "What is the DIKW hierarchy in nursing?",
            "mode": "local"
        }
        res = self.client.post('/api/chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn("response", data)
        self.assertGreater(len(data['sources']), 0)
        print("✓ Chat AI response generated successfully with citations.")

        # Test repeated questions recording
        res_rep = self.client.get('/api/analytics/repeated-questions')
        rep_data = json.loads(res_rep.data)
        self.assertTrue(rep_data['success'])
        self.assertGreaterEqual(len(rep_data['questions']), 1)
        print("✓ Question repetition logged and analytics updated.")

    def test_notes_endpoint(self):
        # Create a new note
        new_note = {
            "title": "Interoperability in EHR",
            "content": "HL7 and FHIR are critical standards for nursing data exchange.",
            "category": "Terminology",
            "tags": ["FHIR", "HL7", "EHR"]
        }
        res = self.client.post('/api/notes', json=new_note)
        self.assertEqual(res.status_code, 200)
        
        # Fetch notes
        res_get = self.client.get('/api/notes')
        data = json.loads(res_get.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['notes']), 1)
        print("✓ Clinical & Study Notes created and retrieved.")

if __name__ == '__main__':
    unittest.main()
