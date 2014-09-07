import abacuspb
from test import test_data
import unittest
import json
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
        

class TransactionsAPI_TestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = abacuspb.app.test_client()
        db.accounts.drop()
        db['acct_testaccountname'].drop()
    
    def tearDown(self):
        db.accounts.drop()
        db['acct_testaccountname'].drop()
        test_data.db_transactions[4]['reconciled'] = '' # reset value
    
    # TransactionListAPI Tests
    def test_TransactionListAPI_Get_Empty(self):
        rv = self.app.get('/api/transactions/acct_testaccountname')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(obj['status'], 404)
    
    def test_TransactionListAPI_Get_Last60Transactions(self):
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.get('/api/transactions/acct_testaccountname')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertLessEqual(len(obj['transactions']), 60) # Check limit of 60
        # Check sort by date (descending)
        cnt = len(obj['transactions'])
        for it in range(cnt-1):
            first = datetime.strptime(obj['transactions'][it]['date'], '%Y-%m-%d')
            second = datetime.strptime(obj['transactions'][it+1]['date'], '%Y-%m-%d')
            self.assertGreaterEqual(first, second)
    
    def test_TransactionListAPI_Get_TransactionsSinceFromDate(self):
        db['acct_testaccountname'].insert(test_data.db_transactions)
        fromDate = '2014-08-07'
        fdate = datetime.strptime(fromDate, '%Y-%m-%d')
        rv = self.app.get('/api/transactions/acct_testaccountname?fromDate='+fromDate)
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        # Check sort by date (descending)
        cnt = len(obj['transactions'])
        for it in range(cnt-1):
            first = datetime.strptime(obj['transactions'][it]['date'], '%Y-%m-%d')
            second = datetime.strptime(obj['transactions'][it+1]['date'], '%Y-%m-%d')
            self.assertGreaterEqual(first, second) # check sort
            self.assertGreaterEqual(first, fdate) # check query
            self.assertGreaterEqual(second, fdate) # check query
    
    def test_TransactionListAPI_Get_TransactionsBetweenDates(self):
        db['acct_testaccountname'].insert(test_data.db_transactions)
        fromDate = '2014-08-06'
        fdate = datetime.strptime(fromDate, '%Y-%m-%d')
        toDate = '2014-08-12'
        tdate = datetime.strptime(toDate, '%Y-%m-%d')
        rv = self.app.get('/api/transactions/acct_testaccountname?fromDate='+fromDate+'&toDate='+toDate)
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        # Check sort by date (descending)
        cnt = len(obj['transactions'])
        for it in range(cnt-1):
            first = datetime.strptime(obj['transactions'][it]['date'], '%Y-%m-%d')
            second = datetime.strptime(obj['transactions'][it+1]['date'], '%Y-%m-%d')
            self.assertGreaterEqual(first, second) # check sort
            self.assertGreaterEqual(first, fdate) # check query >= fromDate
            self.assertLessEqual(first, tdate) # check query <= toDate
            self.assertGreaterEqual(second, fdate) # check query for last item
            self.assertLessEqual(second, tdate) # check query for last item
    
    def test_TransactionListAPI_Post_NoAccountExists(self):
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(obj['message'], 'Account does not exist')
        
    def test_TransactionListAPI_Post_AccountExists_UnclearedTrans(self):
        db.accounts.insert(test_data.db_account)
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertIsNotNone(obj['transaction']['uri'])
        self.assertEqual(obj['account']['uri'], '/api/accounts/acct_testaccountname')
        self.assertEqual(obj['account']['bal_uncleared'], 2583.55)
        self.assertEqual(obj['account']['bal_cleared'], -40.92)
        self.assertEqual(obj['account']['bal_reconciled'], 1021.61)
        self.assertEqual(db.accounts.find_one()['bal_uncleared'], 2583.55)
        self.assertEqual(db.accounts.find_one()['bal_cleared'], -40.92)
        self.assertEqual(db.accounts.find_one()['bal_reconciled'], 1021.61)
        
    def test_TransactionListAPI_Post_AccountExists_ClearedTrans(self):
        test_data.transaction['reconciled'] = 'C'
        db.accounts.insert(test_data.db_account)
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertIsNotNone(obj['transaction']['uri'])
        self.assertEqual(obj['account']['uri'], '/api/accounts/acct_testaccountname')
        self.assertEqual(obj['account']['bal_uncleared'], 2583.55)
        self.assertEqual(obj['account']['bal_cleared'], -93.00)
        self.assertEqual(obj['account']['bal_reconciled'], 1021.61)
        self.assertEqual(db.accounts.find_one()['bal_uncleared'], 2583.55)
        self.assertEqual(db.accounts.find_one()['bal_cleared'], -93.00)
        self.assertEqual(db.accounts.find_one()['bal_reconciled'], 1021.61)
        test_data.transaction['reconciled'] = '' # Rest test data
        
    def test_TransactionListAPI_Post_AccountExists_ReconciledTrans(self):
        test_data.transaction['reconciled'] = 'R'
        db.accounts.insert(test_data.db_account)
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertIsNotNone(obj['transaction']['uri'])
        self.assertEqual(obj['account']['uri'], '/api/accounts/acct_testaccountname')
        self.assertEqual(obj['account']['bal_uncleared'], 2583.55)
        self.assertEqual(obj['account']['bal_cleared'], -93.00)
        self.assertEqual(obj['account']['bal_reconciled'], 969.53)
        self.assertEqual(db.accounts.find_one()['bal_uncleared'], 2583.55)
        self.assertEqual(db.accounts.find_one()['bal_cleared'], -93.00)
        self.assertEqual(db.accounts.find_one()['bal_reconciled'], 969.53)
        test_data.transaction['reconciled'] = '' # Rest test data
        
    # TransactionAPI Tests
    def test_TransactionAPI_Get_TransactionDoesNotExist(self):
        rv = self.app.get('/api/transactions/acct_testaccountname/123')
        self.assertEqual(rv.status_code, 404)
        
    def test_TransactionAPI_Get_TransactionExists(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.get('/api/transactions/acct_testaccountname/53f69e77137a001e344259c8')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertIsNotNone(obj['transaction']['uri'])
    
    def test_TransactionAPI_Put_TransactionDoesNotExist(self):
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps(test_data.transaction_put_amount),
                          content_type='application/json')
        self.assertEqual(rv.status_code, 404)
    
    def test_TransactionAPI_Put_TransactionExists_ChangeAmount(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps(test_data.transaction_put_amount),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['amount'], -14.01)
        self.assertEqual(obj['transaction']['memo'], 'Birthday present')
        self.assertEqual(obj['account']['bal_uncleared'], 2635.51)
        
    def test_TransactionAPI_Put_TransationExists_ChangeRec_Unclr2Clr(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions) # trans is uncleared
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': 'C'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], 'C') # change from ''
        self.assertEqual(obj['account']['bal_uncleared'], 2635.63)
        self.assertEqual(obj['account']['bal_cleared'], -54.81)
        self.assertEqual(obj['account']['bal_reconciled'], 1021.61)
        
    def test_TransactionAPI_Put_TransationExists_ChangeRec_Unclr2Rec(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions) # trans is uncleared
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': 'R'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], 'R') # change from ''
        self.assertEqual(obj['account']['bal_uncleared'], 2635.63)
        self.assertEqual(obj['account']['bal_cleared'], -54.81)
        self.assertEqual(obj['account']['bal_reconciled'], 1007.72)
    
    def test_TransactionAPI_Put_TransationExists_ChangeRec_Clr2Unclr(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'C'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': ''}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], '')
        self.assertEqual(obj['account']['bal_uncleared'], 2635.63)
        self.assertEqual(obj['account']['bal_cleared'], -27.03)
        self.assertEqual(obj['account']['bal_reconciled'], 1021.61)
    
    def test_TransactionAPI_Put_TransationExists_ChangeRec_Clr2Rec(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'C'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': 'R'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], 'R')
        self.assertEqual(obj['account']['bal_uncleared'], 2635.63)
        self.assertEqual(obj['account']['bal_cleared'], -40.92)
        self.assertEqual(obj['account']['bal_reconciled'], 1007.72)
    
    def test_TransactionAPI_Put_TransationExists_ChangeRec_Rec2Unclr(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'R'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': ''}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], '')
        self.assertEqual(obj['account']['bal_uncleared'], 2635.63)
        self.assertEqual(obj['account']['bal_cleared'], -27.03)
        self.assertEqual(obj['account']['bal_reconciled'], 1035.50)
    
    def test_TransactionAPI_Put_TransationExists_ChangeRec_Rec2Clr(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'R'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': 'C'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], 'C')
        self.assertEqual(obj['account']['bal_uncleared'], 2635.63)
        self.assertEqual(obj['account']['bal_cleared'], -40.92)
        self.assertEqual(obj['account']['bal_reconciled'], 1035.50)
    
    def test_TransactionAPI_Put_TransationExists_ChangeAmountReconciled(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps(test_data.transaction_put_amountreconciled),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['amount'], -14.01)
        self.assertEqual(obj['transaction']['reconciled'], 'C') # change from ''
        self.assertEqual(obj['account']['bal_uncleared'], 2635.51)
        self.assertEqual(obj['account']['bal_cleared'], -54.93)
        self.assertEqual(obj['account']['bal_reconciled'], 1021.61)
    
    def test_TransactionAPI_Delete_TransactionDoesNotExist(self):
        rv = self.app.delete('/api/transactions/acct_testaccountname/123')
        self.assertEqual(rv.status_code, 404)
        
    def test_TransactionAPI_Delete_TransactionUnclr(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.delete('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['account']['bal_uncleared'], 2649.52)
        self.assertEqual(obj['account']['bal_cleared'], -40.92)
        self.assertEqual(obj['account']['bal_reconciled'], 1021.61)
        self.assertFalse(db['acct_testaccountname'].find({'id':'53f69e77137a001e344259cb'}).count())

    def test_TransactionAPI_Delete_TransactionClr(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'C'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.delete('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['account']['bal_uncleared'], 2649.52)
        self.assertEqual(obj['account']['bal_cleared'], -27.03)
        self.assertEqual(obj['account']['bal_reconciled'], 1021.61)
        self.assertFalse(db['acct_testaccountname'].find({'id':'53f69e77137a001e344259cb'}).count())
        
    def test_TransactionAPI_Delete_TransactionRec(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'R'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.delete('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['account']['bal_uncleared'], 2649.52)
        self.assertEqual(obj['account']['bal_cleared'], -27.03)
        self.assertEqual(obj['account']['bal_reconciled'], 1035.50)
        self.assertFalse(db['acct_testaccountname'].find({'id':'53f69e77137a001e344259cb'}).count())
        

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

if __name__ == '__main__':
    unittest.main()
