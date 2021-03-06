import unittest, abacuspb, json
from test import test_data
from datetime import datetime

db = abacuspb.db

class TransactionsAPI_TestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = abacuspb.app.test_client()
        db.accounts.drop()
        db['acct_testaccountname'].drop()
        db['acct_toaccountname'].drop()
    
    def tearDown(self):
        db.accounts.drop()
        db['acct_testaccountname'].drop()
        db['acct_toaccountname'].drop()
        test_data.db_transactions[4]['reconciled'] = '' # reset value
    
    # TransactionListAPI Tests
    def test_TransactionListAPI_GET_Empty(self):
        rv = self.app.get('/api/transactions/acct_testaccountname')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(obj['status'], 404)
    
    def test_TransactionListAPI_GET_Last60Transactions(self):
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
    
    def test_TransactionListAPI_GET_TransactionsSinceFromDate(self):
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
    
    def test_TransactionListAPI_GET_TransactionsBetweenDates(self):
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
    
    def test_TransactionListAPI_POST_NoAccountExists(self):
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(obj['message'], 'Account does not exist')
        
    def test_TransactionListAPI_POST_AccountExists_UnclearedTrans(self):
        test_data.transaction['reconciled'] = ''
        db.accounts.insert(test_data.db_account)
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertIsNotNone(obj['transaction']['uri'])
        self.assertEqual(obj['accounts'][0]['uri'], '/api/accounts/acct_testaccountname')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2583.55)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -40.92)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
        self.assertEqual(db.accounts.find_one()['bal_uncleared'], 2583.55)
        self.assertEqual(db.accounts.find_one()['bal_cleared'], -40.92)
        self.assertEqual(db.accounts.find_one()['bal_reconciled'], 1021.61)
        
    def test_TransactionListAPI_POST_AccountExists_ClearedTrans(self):
        test_data.transaction['reconciled'] = 'C'
        db.accounts.insert(test_data.db_account)
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertIsNotNone(obj['transaction']['uri'])
        self.assertEqual(obj['accounts'][0]['uri'], '/api/accounts/acct_testaccountname')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2583.55)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -93.00)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
        self.assertEqual(db.accounts.find_one()['bal_uncleared'], 2583.55)
        self.assertEqual(db.accounts.find_one()['bal_cleared'], -93.00)
        self.assertEqual(db.accounts.find_one()['bal_reconciled'], 1021.61)
        test_data.transaction['reconciled'] = '' # Rest test data
        
    def test_TransactionListAPI_POST_AccountExists_ReconciledTrans(self):
        test_data.transaction['reconciled'] = 'R'
        db.accounts.insert(test_data.db_account)
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertIsNotNone(obj['transaction']['uri'])
        self.assertEqual(obj['accounts'][0]['uri'], '/api/accounts/acct_testaccountname')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2583.55)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -93.00)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 969.53)
        self.assertEqual(db.accounts.find_one()['bal_uncleared'], 2583.55)
        self.assertEqual(db.accounts.find_one()['bal_cleared'], -93.00)
        self.assertEqual(db.accounts.find_one()['bal_reconciled'], 969.53)
        test_data.transaction['reconciled'] = '' # Rest test data
        
    # Transfer transaction POST tests    
    def test_TransactionListAPI_POST_TransferAcctDoesNotExist(self):
        db.accounts.insert(test_data.db_account)
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction_transfer),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(obj['message'], 'Transfer account does not exist')
      
    def test_TransactionListAPI_POST_TransferSuccess(self):
        db.accounts.insert([test_data.db_account, test_data.db_account_2])
        rv = self.app.post('/api/transactions/acct_testaccountname',
                           data=json.dumps(test_data.transaction_transfer),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertIsNotNone(obj['transaction']['uri'])
        self.assertEqual(obj['accounts'][0]['uri'], '/api/accounts/acct_testaccountname')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2535.63)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -40.92)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
        self.assertEqual(db.accounts.find_one({'id':'acct_testaccountname'})['bal_uncleared'], 2535.63)
        self.assertEqual(db.accounts.find_one({'id':'acct_testaccountname'})['bal_cleared'], -40.92)
        self.assertEqual(db.accounts.find_one({'id':'acct_testaccountname'})['bal_reconciled'], 1021.61)
        self.assertEqual(obj['accounts'][1]['bal_uncleared'], 200.00)
        self.assertEqual(obj['accounts'][1]['bal_cleared'], 100.00)
        self.assertEqual(obj['accounts'][1]['bal_reconciled'], 200.00)
        self.assertEqual(db.accounts.find_one({'id':'acct_toaccountname'})['bal_uncleared'], 200.00)
        self.assertEqual(db.accounts.find_one({'id':'acct_toaccountname'})['bal_cleared'], 100.00)
        self.assertEqual(db.accounts.find_one({'id':'acct_toaccountname'})['bal_reconciled'], 200.00)
        
    # TransactionAPI Tests
    def test_TransactionAPI_GET_TransactionDoesNotExist(self):
        rv = self.app.get('/api/transactions/acct_testaccountname/123')
        self.assertEqual(rv.status_code, 404)
        
    def test_TransactionAPI_GET_TransactionExists(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.get('/api/transactions/acct_testaccountname/53f69e77137a001e344259c8')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertIsNotNone(obj['transaction']['uri'])
    
    def test_TransactionAPI_PUT_TransactionDoesNotExist(self):
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps(test_data.transaction_put_amount),
                          content_type='application/json')
        self.assertEqual(rv.status_code, 404)
    
    def test_TransactionAPI_PUT_TransactionExists_ChangeAmount(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps(test_data.transaction_put_amount),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['amount'], -14.01)
        self.assertEqual(obj['transaction']['memo'], 'Birthday present')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2635.51)
        
    def test_TransactionAPI_PUT_TransationExists_ChangeRec_Unclr2Clr(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions) # trans is uncleared
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': 'C'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], 'C') # change from ''
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2635.63)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -54.81)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
        
    def test_TransactionAPI_PUT_TransationExists_ChangeRec_Unclr2Rec(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions) # trans is uncleared
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': 'R'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], 'R') # change from ''
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2635.63)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -54.81)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1007.72)
    
    def test_TransactionAPI_PUT_TransationExists_ChangeRec_Clr2Unclr(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'C'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': ''}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], '')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2635.63)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -27.03)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
    
    def test_TransactionAPI_PUT_TransationExists_ChangeRec_Clr2Rec(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'C'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': 'R'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], 'R')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2635.63)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -40.92)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1007.72)
    
    def test_TransactionAPI_PUT_TransationExists_ChangeRec_Rec2Unclr(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'R'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': ''}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], '')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2635.63)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -27.03)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1035.50)
    
    def test_TransactionAPI_PUT_TransationExists_ChangeRec_Rec2Clr(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'R'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps({'reconciled': 'C'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['reconciled'], 'C')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2635.63)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -40.92)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1035.50)
    
    def test_TransactionAPI_PUT_TransationExists_ChangeAmountReconciled(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb',
                          data=json.dumps(test_data.transaction_put_amountreconciled),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['amount'], -14.01)
        self.assertEqual(obj['transaction']['reconciled'], 'C') # change from ''
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2635.51)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -54.93)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
        
    # Transfer transaction tests for PUT
    def test_TransactionAPI_PUT_TransferUpdatePayee(self):
        db.accounts.insert([test_data.db_account, test_data.db_account_2])
        db['acct_testaccountname'].insert(test_data.db_transfer_transactions_fromAcct)
        db['acct_toaccountname'].insert(test_data.db_transfer_transactions_toAcct)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259c7',
                          data=json.dumps({'payee': 'To My Savings'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['payee'], 'To My Savings')
        self.assertEqual(db['acct_testaccountname'].find({'id':'53f69e77137a001e344259c7'})[0]['payee'], 'To My Savings')
        self.assertEqual(db['acct_toaccountname'].find({'id':'53f69e77137a001e344259c7'})[0]['payee'], 'To My Savings')
    
    def test_TransactionAPI_PUT_Transfer_UpdateMemo(self):
        db.accounts.insert([test_data.db_account, test_data.db_account_2])
        db['acct_testaccountname'].insert(test_data.db_transfer_transactions_fromAcct)
        db['acct_toaccountname'].insert(test_data.db_transfer_transactions_toAcct)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259c7',
                          data=json.dumps({'memo': 'Something Special!'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['memo'], 'Something Special!')
        self.assertEqual(db['acct_testaccountname'].find_one({'id':'53f69e77137a001e344259c7'})['memo'], 'Something Special!')
        self.assertEqual(db['acct_toaccountname'].find_one({'id':'53f69e77137a001e344259c7'})['memo'], 'Something Special!')
    
    def test_TransactionAPI_PUT_Transfer_UpdateAmountOnly(self):
        db.accounts.insert([test_data.db_account, test_data.db_account_2])
        db['acct_testaccountname'].insert(test_data.db_transfer_transactions_fromAcct)
        db['acct_toaccountname'].insert(test_data.db_transfer_transactions_toAcct)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259c7',
                          data=json.dumps({'amount': -50.00}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['amount'], -50.00)
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2685.63) # testaccountname
        self.assertEqual(obj['accounts'][0]['bal_cleared'], 9.08)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
        self.assertEqual(obj['accounts'][1]['bal_uncleared'], 150.00) # toaccountname
        self.assertEqual(obj['accounts'][1]['bal_cleared'], 150.00)
        self.assertEqual(obj['accounts'][1]['bal_reconciled'], 200.00)
        self.assertEqual(db['acct_testaccountname'].find_one({'id':'53f69e77137a001e344259c7'})['amount'], -50.00)
        self.assertEqual(db['acct_toaccountname'].find_one({'id':'53f69e77137a001e344259c7'})['amount'], 50.00)
    
    def test_TransactionAPI_PUT_Transfer_ChangeAccountToCategory(self):
        db.accounts.insert([test_data.db_account, test_data.db_account_2])
        db['acct_testaccountname'].insert(test_data.db_transfer_transactions_fromAcct)
        db['acct_toaccountname'].insert(test_data.db_transfer_transactions_toAcct)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259c7',
                          data=json.dumps({'cat_or_acct_id': 'somecategoryidstring'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['cat_or_acct_id'], 'somecategoryidstring')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 0.00) # toaccountname
        self.assertEqual(obj['accounts'][0]['bal_cleared'], 0.00)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 100.00)
        self.assertEqual(db['acct_testaccountname'].find_one({'id':'53f69e77137a001e344259c7'})['cat_or_acct_id'], 'somecategoryidstring')
        self.assertIsNone(db['acct_toaccountname'].find_one({'id':'53f69e77137a001e344259c7'})) # transaction removed
    
    def test_TransactionAPI_PUT_Transfer_ChangeAccountToDifferentAccount(self):
        db.accounts.insert([test_data.db_account, test_data.db_account_2, test_data.db_account_3])
        db['acct_testaccountname'].insert(test_data.db_transfer_transactions_fromAcct)
        db['acct_toaccountname'].insert(test_data.db_transfer_transactions_toAcct)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259c7',
                          data=json.dumps({'cat_or_acct_id': 'acct_to2accountname'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['cat_or_acct_id'], 'acct_to2accountname')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 0.00) # toaccountname
        self.assertEqual(obj['accounts'][0]['bal_cleared'], 0.00)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 100.00)
        self.assertEqual(obj['accounts'][1]['bal_uncleared'], 600.00) # to2accountname
        self.assertEqual(obj['accounts'][1]['bal_cleared'], 500.00)
        self.assertEqual(obj['accounts'][1]['bal_reconciled'], 600.00)
        self.assertIsNone(db['acct_toaccountname'].find_one({'id':'53f69e77137a001e344259c7'})) # transaction removed
        self.assertIsNotNone(db['acct_to2accountname'].find_one({'id':'53f69e77137a001e344259c7'})) # transaction added
    
    def test_TransactionAPI_PUT_Transfer_ChangeCategoryToAccount(self):
        db.accounts.insert([test_data.db_account, test_data.db_account_2])
        db['acct_testaccountname'].insert(test_data.db_transfer_transactions_fromAcct)
        db['acct_toaccountname'].insert(test_data.db_transfer_transactions_toAcct)
        rv = self.app.put('/api/transactions/acct_testaccountname/53f69e77137a001e344259c8',
                          data=json.dumps({'cat_or_acct_id': 'acct_toaccountname'}),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['transaction']['cat_or_acct_id'], 'acct_toaccountname')
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 200.00) # toaccountname
        self.assertEqual(obj['accounts'][0]['bal_cleared'], 100.00)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 200.00)
        self.assertEqual(db['acct_toaccountname'].find_one({'id':'53f69e77137a001e344259c8'})['cat_or_acct_id'], 'acct_testaccountname')
        self.assertEqual(db['acct_toaccountname'].find_one({'id':'53f69e77137a001e344259c8'})['reconciled'], '')
        
    # DELETE Tests
    def test_TransactionAPI_DELETE_TransactionDoesNotExist(self):
        rv = self.app.delete('/api/transactions/acct_testaccountname/123')
        self.assertEqual(rv.status_code, 404)
        
    def test_TransactionAPI_DELETE_TransactionUnclr(self):
        db.accounts.insert(test_data.db_account)
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.delete('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2649.52)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -40.92)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
        self.assertFalse(db['acct_testaccountname'].find({'id':'53f69e77137a001e344259cb'}).count())

    def test_TransactionAPI_DELETE_TransactionClr(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'C'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.delete('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2649.52)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -27.03)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
        self.assertFalse(db['acct_testaccountname'].find({'id':'53f69e77137a001e344259cb'}).count())
        
    def test_TransactionAPI_DELETE_TransactionRec(self):
        db.accounts.insert(test_data.db_account)
        test_data.db_transactions[4]['reconciled'] = 'R'
        db['acct_testaccountname'].insert(test_data.db_transactions)
        rv = self.app.delete('/api/transactions/acct_testaccountname/53f69e77137a001e344259cb')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2649.52)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], -27.03)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1035.50)
        self.assertFalse(db['acct_testaccountname'].find({'id':'53f69e77137a001e344259cb'}).count())
    
    # Transfer transaction tests for DELETE
    def test_TransactionAPI_DELETE_TransferDeleteSuccess(self):
        db.accounts.insert([test_data.db_account, test_data.db_account_2])
        db['acct_testaccountname'].insert(test_data.db_transfer_transactions_fromAcct)
        db['acct_toaccountname'].insert(test_data.db_transfer_transactions_toAcct)
        rv = self.app.delete('/api/transactions/acct_testaccountname/53f69e77137a001e344259c7')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['accounts'][0]['bal_uncleared'], 2735.63)
        self.assertEqual(obj['accounts'][0]['bal_cleared'], 59.08)
        self.assertEqual(obj['accounts'][0]['bal_reconciled'], 1021.61)
        self.assertEqual(obj['accounts'][1]['bal_uncleared'], 0.00)
        self.assertEqual(obj['accounts'][1]['bal_cleared'], 0.00)
        self.assertEqual(obj['accounts'][1]['bal_reconciled'], 100.00)
        
        