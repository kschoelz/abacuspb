import unittest, abacuspb, json
from test import test_data
from datetime import datetime

db = abacuspb.db

class AccountsAPI_TestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = abacuspb.app.test_client()
        db.accounts.drop()
        
    def tearDown(self):
        db.accounts.drop()
    
    # AccountListAPI Tests
    def test_AccountListAPI_Get_Empty(self):
        rv = self.app.get('/api/accounts')
        self.assertEqual(rv.status_code, 404)
        
    def test_AccountListAPI_Get_Entry(self):
        db.accounts.insert(test_data.db_account)
        rv = self.app.get('/api/accounts')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(obj['accounts']), 1)
        self.assertEqual(obj['accounts'][0]['uri'], '/api/accounts/acct_testaccountname')
        
    def test_AccountListAPI_Post_Empty(self):
        rv = self.app.post('/api/accounts',
                           data=json.dumps(test_data.account),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertEqual(obj['account']['uri'], '/api/accounts/acct_testaccountname')
        self.assertIsNotNone(db.accounts.find_one())
        
    def test_AccountListAPI_Post_EntryExists(self):
        db.accounts.insert(test_data.db_account)
        rv = self.app.post('/api/accounts',
                           data=json.dumps(test_data.account),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(obj['message'], 'Account already exists')
    
    # AccountAPI Tests
    def test_AccountAPI_Get_Empty(self):
        rv = self.app.get('/api/accounts/test_account')
        self.assertEqual(rv.status_code, 404)
    
    def test_AccountAPI_Get_Entry(self):
        db.accounts.insert(test_data.db_account)
        rv = self.app.get('/api/accounts/acct_testaccountname')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['account']['uri'], '/api/accounts/acct_testaccountname')
        
    def test_AccountAPI_Put_Empty(self):
        rv = self.app.put('/api/accounts/acct_testaccountname',
                          data=json.dumps(test_data.account_put),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 404)
        
    def test_AccountAPI_Put_Entry(self):
        db.accounts.insert(test_data.db_account)
        rv = self.app.put('/api/accounts/acct_testaccountname',
                          data=json.dumps(test_data.account_put),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['account']['name'], 'Savings Account')
        self.assertEqual(obj['account']['type'], 'Savings')
    
    def test_AccountAPI_Delete_Empty(self):
        rv = self.app.delete('/api/accounts/acct_testaccountname')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 404)
    
    def test_AccountAPI_Delete_Entry(self):
        db.accounts.insert(test_data.db_account)
        rv = self.app.delete('/api/accounts/acct_testaccountname')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(obj['result'])
        self.assertIsNone(db.accounts.find_one())
