from flask import abort
from flask.ext.restful import Resource, reqparse, fields, marshal
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
from abacuspb import db
import pymongo

transaction_fields = { # Request validator
    'date': fields.String,
    'type': fields.String, # check num, EFT, etc.
    'payee': fields.String,
    # TODO: need split -> consider fields.Nested
    'reconciled': fields.String, # ' ' | 'C' | 'R'
    'amount': fields.Float, # +/- dollar value
    'memo': fields.String,
    #'uri': fields.Url('transaction') # TODO: need to fix this? LOW PRIORITY (workaround in place)
    'cat_or_acct_id': fields.String,
    'uri': fields.String
}

class TransactionListAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        # Query parameters
        self.reqparse.add_argument('fromDate', type=str, location='args')
        self.reqparse.add_argument('toDate', type=str, location='args')
        # JSON parameters
        self.reqparse.add_argument('date', type=str, location='json')
        self.reqparse.add_argument('type', type=str, location='json')
        self.reqparse.add_argument('payee', type=str, location='json')
        self.reqparse.add_argument('reconciled', type=str, location='json')
        self.reqparse.add_argument('amount', type=float, location='json')
        self.reqparse.add_argument('memo', type=str, location='json')
        self.reqparse.add_argument('cat_or_acct_id', type=str, default='', location='json')
        super(TransactionListAPI, self).__init__()
    
    def get(self, account_id):
        """
        Returns last 60 transactions for the account.
        
        Optional query paramters:
            1) 'fromDate' & 'toDate' in YYYY-MM-DD format: returns transactions within the date range
            2) 'fromDate' in YYYY-MM-DD format: returns all transactions since fromDate  
        """
        args = self.reqparse.parse_args()
        if args['fromDate'] != None and args['toDate'] != None:
            fdate = datetime.strptime(args['fromDate'], '%Y-%m-%d')
            tdate = datetime.strptime(args['toDate'], '%Y-%m-%d')
            trans = db[account_id].find({'date': {'$gte': fdate, '$lte': tdate}}, sort=[('date', pymongo.DESCENDING)])
        elif args['fromDate'] != None:
            fdate = datetime.strptime(args['fromDate'], '%Y-%m-%d')
            trans = db[account_id].find({'date': {'$gte': fdate}}, sort=[('date', pymongo.DESCENDING)])
        else: # Default to get last 60 transactions
            trans = db[account_id].find(sort=[('date', pymongo.DESCENDING)], limit=60)
        
        if trans.count() == 0:
            abort(404)
        transactions = []
        for tran in trans:
            tran['date'] = tran['date'].strftime('%Y-%m-%d')
            tran['uri'] = '/api/transactions/' + account_id + '/' + tran['id']
            transactions.append(tran)
        return { 'transactions': map(lambda t: marshal(t, transaction_fields), transactions)}
    
    def post(self, account_id):
        """
        Create a new transaction
        """
        # Check if originating account exists
        account = db.accounts.find_one({'id': account_id})
        if not account:
            return { 'message': 'Account does not exist', 'status': 400 }, 400
        args = self.reqparse.parse_args()
        transaction = {
            'id': str(ObjectId()),
            'date': datetime.strptime(args['date'],'%Y-%m-%d'),
            'type': args['type'],
            'payee': args['payee'],
            # TODO: need split
            'reconciled': args['reconciled'],
            'amount': args['amount'],
            'memo': args['memo'],
            'cat_or_acct_id': args['cat_or_acct_id']
        }
        return_accts = []
        
        # Originating account: 1) insert transaction, 2) calculate new balances
        db[account_id].insert(transaction)
        updated_originating_acct = update_account_balances('CREATE_TRANS', account, transaction)
        return_accts.append(updated_originating_acct)
        
        # Transfer account: 1) Check if transfer trans, 2) insert trans, 3) calculate new balances
        if transaction['cat_or_acct_id'][0:5] == 'acct_':
            # Check if transfer account exists
            transfer_account = db.accounts.find_one({'id': transaction['cat_or_acct_id']})
            if not transfer_account:
                return { 'message': 'Transfer account does not exist', 'status': 400 }, 400
            transfer_transaction = transaction.copy() # Transaction ID stays same
            transfer_transaction['reconciled'] = '' # Don't assume we know this type
            transfer_transaction['amount'] = - transaction['amount']
            transfer_transaction['cat_or_acct_id'] = account_id # Set to originating account
            db[transaction['cat_or_acct_id']].insert(transfer_transaction)
            updated_transfer_acct = update_account_balances('CREATE_TRANS', transfer_account, transfer_transaction)
            return_accts.append(updated_transfer_acct)
         
        transaction['date'] = args['date']
        transaction['uri'] = '/api/transactions/' + account_id + '/' + transaction['id']
        
        return { 'transaction': marshal(transaction, transaction_fields),
                 'accounts': return_accts }, 201
    
#     def update_balances_on_post(self, account_id, amount, reconciled):
#         account = db.accounts.find_one({'id': account_id})
#         # update bal_uncleared (every transaction mods this)
#         bal_unclr = round(account['bal_uncleared'] + amount, 2)
#         db.accounts.update({'id': account_id}, {'$set': {'bal_uncleared': bal_unclr}})
#         bal_clr = account['bal_cleared']
#         bal_rec = account['bal_reconciled']
#         if reconciled in ['C', 'R']:
#             # update bal_cleared (only cleared and reconciled transactions mod this)
#             bal_clr = round(account['bal_cleared'] + amount, 2)
#             db.accounts.update({'id': account_id}, {'$set': {'bal_cleared': bal_clr}})
#         if reconciled == 'R':
#             # update bal_reconciled (only reconciled transactions mod this)
#             bal_rec = round(account['bal_reconciled'] + amount, 2)
#             db.accounts.update({'id': account_id}, {'$set': {'bal_reconciled': bal_rec}})
#             
#         return { 'uri': '/api/accounts/' + account_id, 'bal_uncleared': bal_unclr,
#                  'bal_cleared': bal_clr, 'bal_reconciled': bal_rec }

class TransactionAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('date', type=str, location='json')
        self.reqparse.add_argument('type', type=str, location='json')
        self.reqparse.add_argument('payee', type=str, location='json')
        # need: category/account split
        self.reqparse.add_argument('reconciled', type=str, location='json')
        self.reqparse.add_argument('amount', type=float, location='json')
        self.reqparse.add_argument('memo', type=str, location='json')
        self.reqparse.add_argument('cat_or_acct_id', type=str, location='json')
        super(TransactionAPI, self).__init__()
    
    def get(self, account_id, trans_id):
        """
        Return a single transaction
        """
        transaction = db[account_id].find({'id':trans_id})
        if transaction.count() == 0:
            abort(404)
        trans = transaction[0]
        trans['date'] = str(trans['date'])
        trans['uri'] = '/api/transactions/' + account_id + '/' + trans_id
        return { 'transaction': marshal(trans, transaction_fields) }
    
    def put(self, account_id, trans_id):
        """
        Update a single transaction
        """
        old_transaction = db[account_id].find_one({'id':trans_id})
        if old_transaction == None:
            abort(404)
        new_transaction = old_transaction.copy()
        
        args = self.reqparse.parse_args()
        for k, v in args.iteritems():
            if v != None:
                if k == 'date': new_transaction[k] = datetime.strptime(v,'%Y-%m-%d')
                else:
                    new_transaction[k] = v
                    # Check if transfer transaction for 'payee' and 'memo' only
                    if old_transaction['cat_or_acct_id'][0:5] == 'acct_' and (k == 'payee' or k == 'memo'):
                        db[old_transaction['cat_or_acct_id']].update({'id':trans_id}, {'$set': {k:v}})
        db[account_id].update({'id':trans_id}, new_transaction)
        new_transaction['date'] = new_transaction['date'].strftime('%Y-%m-%d')
        new_transaction['uri'] = '/api/transactions/' + account_id + '/' + trans_id
        
        return_accts = []
        
        # Originating account
        if (old_transaction['amount'] != new_transaction['amount']) or (old_transaction['reconciled'] != new_transaction['reconciled']):
            account = db.accounts.find_one({'id': account_id})
            update_account_balances('DELETE_TRANS', account, old_transaction)
            account = db.accounts.find_one({'id': account_id})
            updated_originating_acct = update_account_balances('CREATE_TRANS', account, new_transaction)
            return_accts.append(updated_originating_acct)

        # Transfer account
        if old_transaction['cat_or_acct_id'][0:5] == 'acct_':
            if new_transaction['cat_or_acct_id'][0:5] != 'acct_':
                print 'Account -> Category'
                # Account -> Category
                transfer_trans = db[old_transaction['cat_or_acct_id']].find_one({'id': trans_id})
                # Delete transfer transaction
                if not db[old_transaction['cat_or_acct_id']].remove({'id': trans_id})['n']:
                    abort(404)
                # Update transfer account balances only
                transfer_account = db.accounts.find_one({'id': old_transaction['cat_or_acct_id']})
                updated_transfer_acct = update_account_balances('DELETE_TRANS', transfer_account, transfer_trans)
                return_accts.append(updated_transfer_acct)
                
            elif old_transaction['cat_or_acct_id'] != new_transaction['cat_or_acct_id']:
                print 'Account -> Account'
                # Account -> Account
                transfer_trans = db[old_transaction['cat_or_acct_id']].find_one({'id': trans_id})
                # Delete original transfer transaction
                if not db[old_transaction['cat_or_acct_id']].remove({'id': trans_id})['n']:
                    abort(404)
                # Update original transfer account balances
                old_transfer_account = db.accounts.find_one({'id': old_transaction['cat_or_acct_id']})
                updated_old_transfer_acct = update_account_balances('DELETE_TRANS', old_transfer_account, transfer_trans)
                return_accts.append(updated_old_transfer_acct)
                
                # Check if new transfer account exists
                new_transfer_account = db.accounts.find_one({'id': new_transaction['cat_or_acct_id']})
                if not new_transfer_account:
                    return { 'message': 'Transfer account does not exist', 'status': 400 }, 400
                # Create new transfer transaction
                transfer_transaction = new_transaction.copy() # Transaction ID stays same
                transfer_transaction['reconciled'] = '' # Don't assume we know this type
                transfer_transaction['amount'] = - new_transaction['amount']
                transfer_transaction['cat_or_acct_id'] = account_id # Set to originating account
                db[new_transaction['cat_or_acct_id']].insert(transfer_transaction)
                # Update new transfer account balances
                updated_new_transfer_acct = update_account_balances('CREATE_TRANS', new_transfer_account, transfer_transaction)
                return_accts.append(updated_new_transfer_acct)
            
            elif old_transaction['amount'] != new_transaction['amount']:
                print 'Account stays same, amount changes'
                # Account stays the same, amount changes
                # Update transfer transaction's amount (opposite of originating transaction amount)
                db[new_transaction['cat_or_acct_id']].update({'id': trans_id}, {'$set': {'amount': -new_transaction['amount']}})
                # Update transfer account balances
                transfer_account = db.accounts.find_one({'id': new_transaction['cat_or_acct_id']})
                update_account_balances('DELETE_TRANS', transfer_account, old_transaction)
                transfer_account = db.accounts.find_one({'id': new_transaction['cat_or_acct_id']})
                updated_transfer_acct = update_account_balances('CREATE_TRANS', transfer_account, new_transaction)
                return_accts.append(updated_transfer_acct)
            
            else:
                pass
                
        elif new_transaction['cat_or_acct_id'][0:5] == 'acct_':
            print 'Category -> Account'
            # Category -> Account
            # Check if transfer account exists
            transfer_account = db.accounts.find_one({'id': new_transaction['cat_or_acct_id']})
            if not transfer_account:
                return { 'message': 'Transfer account does not exist', 'status': 400 }, 400
            # Create new transfer transaction
            transfer_transaction = new_transaction.copy() # Transaction ID stays same
            transfer_transaction['reconciled'] = '' # Don't assume we know this type
            transfer_transaction['amount'] = - new_transaction['amount']
            transfer_transaction['cat_or_acct_id'] = account_id # Set to originating account
            db[new_transaction['cat_or_acct_id']].insert(transfer_transaction)
            # Update new transfer account balances
            updated_transfer_acct = update_account_balances('CREATE_TRANS', transfer_account, transfer_transaction)
            return_accts.append(updated_transfer_acct)
        
        return { 'transaction': marshal(new_transaction, transaction_fields),
                 'accounts': return_accts }    
    
    def delete(self, account_id, trans_id):
        """
        Delete a single transaction
        """
        return_accts = []
        
        # Originating transaction
        account = db.accounts.find_one({'id': account_id})
        transaction = db[account_id].find_one({'id':trans_id})
        if not db[account_id].remove({'id':trans_id})['n']:
            abort(404)
        updated_originating_acct = update_account_balances('DELETE_TRANS', account, transaction)
        return_accts.append(updated_originating_acct)
        
        # Transfer transaction
        if transaction['cat_or_acct_id'][0:5] == 'acct_':
            transfer_account = db.accounts.find_one({'id': transaction['cat_or_acct_id']})
            transfer_transaction = db[transaction['cat_or_acct_id']].find_one({'id': trans_id})
            if not db[transaction['cat_or_acct_id']].remove({'id':trans_id})['n']:
                abort(404)
            updated_transfer_acct = update_account_balances('DELETE_TRANS', transfer_account, transfer_transaction)
            return_accts.append(updated_transfer_acct)
        
        return { 'accounts': return_accts }

def update_account_balances(action, account, transaction, old_transaction = None):
    bal_unclr = account['bal_uncleared']
    bal_clr = account['bal_cleared']
    bal_rec = account['bal_reconciled']
    
    if action == 'CREATE_TRANS':
        bal_unclr = round(bal_unclr + transaction['amount'], 2)
        if transaction['reconciled'] in ['C', 'R']:
            bal_clr = round(bal_clr + transaction['amount'], 2)
        if transaction['reconciled'] == 'R':
            bal_rec = round(bal_rec + transaction['amount'], 2)    
    
    elif action == 'DELETE_TRANS':
        if transaction['reconciled'] == '':
            bal_unclr = round( account['bal_uncleared'] - transaction['amount'], 2)
        elif transaction['reconciled'] == 'C':
            bal_unclr = round( account['bal_uncleared'] - transaction['amount'], 2)
            bal_clr = round( account['bal_cleared'] - transaction['amount'], 2)
        elif transaction['reconciled'] == 'R':
            bal_unclr = round( account['bal_uncleared'] - transaction['amount'], 2)
            bal_clr = round( account['bal_cleared'] - transaction['amount'], 2)
            bal_rec = round( account['bal_reconciled'] - transaction['amount'], 2)
        
    else:
        return None
    
    db.accounts.update({'id': account['id']},
                       {'$set': {'bal_uncleared': bal_unclr,
                                 'bal_cleared': bal_clr,
                                 'bal_reconciled': bal_rec}})

    return { 'uri': '/api/accounts/' + account['id'],
             'bal_uncleared': bal_unclr,
             'bal_cleared': bal_clr,
             'bal_reconciled': bal_rec }
