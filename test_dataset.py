import unittest
import json
from app import app
from database import init_db

class TestReferenceDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = app.test_client()

    def test_dataset_retrieval(self):
        res = self.client.get('/api/dataset')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(data['count'], 10)
        print("✓ Dataset Retrieval Passed. Total entries:", data['count'])

    def test_dataset_search_filter(self):
        res = self.client.get('/api/dataset?domain=Clinical+Decision+Support')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['dataset']), 1)
        self.assertEqual(data['dataset'][0]['domain'], 'Clinical Decision Support')
        print("✓ Dataset Domain Filtering Passed.")

    def test_chat_retrieves_from_reference_dataset(self):
        # Querying concept specifically in dataset
        payload = {
            "message": "ما هو مفهوم HL7 و FHIR؟",
            "mode": "local",
            "lang": "ar"
        }
        res = self.client.post('/api/chat', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        # Confirms reference dataset citation
        sources = [s['page_number'] for s in data['sources']]
        has_dataset_source = any('Dataset' in str(src) for src in sources)
        self.assertTrue(has_dataset_source)
        print("✓ RAG engine seamlessly used Reference Dataset as authoritative evidence source.")

if __name__ == '__main__':
    unittest.main()
