import unittest, abacuspb, json
from test import test_data
from datetime import datetime

db = abacuspb.db

class PayeesAPI_TestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = abacuspb.app.test_client()
        db.payees.drop()
    
    def tearDown(self):
        db.payees.drop()
    
    # PayeeListAPI Tests
    def test_PayeeListAPI_Get_Empty(self):
        rv = self.app.get('/api/payees')
        self.assertEqual(rv.status_code, 404)
        
    def test_PayeeListAPI_Get_Payees_SortedByName(self):
        db.payees.insert(test_data.db_payees)
        rv = self.app.get('/api/payees')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(obj['payees']), 5)
        self.assertEqual(obj['payees'][0]['uri'], '/api/payees/53f69e77137a001e344259f2')
        self.assertEqual(obj['payees'][4]['uri'], '/api/payees/53f69e77137a001e344259f3')

    def test_PayeeListAPI_Post_Empty(self):
        rv = self.app.post('/api/payees',
                           data=json.dumps(test_data.payee),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertEqual(obj['payee']['name'], 'Costco')
        self.assertIsNotNone(obj['payee']['uri'])
        self.assertIsNotNone(db.payees.find_one())

    def test_PayeeListAPI_Post_EntryExists(self):
        db.payees.insert(test_data.db_payees)
        rv = self.app.post('/api/payees',
                           data=json.dumps(test_data.payee),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(obj['message'], 'Payee already exists')
    
    # PayeeAPI Tests
    def test_PayeeAPI_Get_Empty(self):
        rv = self.app.get('/api/payees/123')
        self.assertEqual(rv.status_code, 404)
    
    def test_PayeeAPI_Get_Payee(self):
        db.payees.insert(test_data.db_payees)
        rv = self.app.get('/api/payees/53f69e77137a001e344259f2')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['payee']['name'], 'Amazon.com')
        self.assertEqual(obj['payee']['uri'], '/api/payees/53f69e77137a001e344259f2')
        
    def test_PayeeAPI_Put_Empty(self):
        rv = self.app.put('/api/payees/53f69e77137a001e344259f2',
                          data=json.dumps(test_data.payee_put),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 404)
    
    def test_PayeeAPI_Put_Entry(self):
        db.payees.insert(test_data.db_payees)
        rv = self.app.put('/api/payees/53f69e77137a001e344259f2',
                          data=json.dumps(test_data.payee_put),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['payee']['name'], 'Newegg.com')
        self.assertEqual(obj['payee']['uri'], '/api/payees/53f69e77137a001e344259f2')
    
    def test_PayeeAPI_Delete_Empty(self):
        rv = self.app.delete('/api/payees/53f69e77137a001e344259f2')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 404)
    
    def test_PayeeAPI_Delete_Entry(self):
        db.payees.insert(test_data.db_payees)
        rv = self.app.delete('/api/payees/53f69e77137a001e344259f2')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(obj['result'])
        self.assertIsNone(db.payees.find_one({'id': '53f69e77137a001e344259f2'}))
