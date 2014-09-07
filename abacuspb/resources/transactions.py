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
    # need: category/account, split -> consider fields.Nested
    'reconciled': fields.String, # ' ' | 'C' | 'R'
    'amount': fields.Float, # +/- dollar value
    'memo': fields.String,
    #'uri': fields.Url('transaction') # TODO: need to fix this? LOW PRIORITY (workaround in place)
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
        # Check if account exists
        account = db.accounts.find_one({'id': account_id}) 
        if account == None:
            return { 'message': 'Account does not exist', 'status': 400 }, 400
        args = self.reqparse.parse_args()
        transaction = {
            'id': str(ObjectId()),
            'date': datetime.strptime(args['date'],'%Y-%m-%d'),
            'type': args['type'],
            'payee': args['payee'],
            # TODO: need category/account split
            'reconciled': args['reconciled'],
            'amount': args['amount'],
            'memo': args['memo'],
        }
        db[account_id].insert(transaction)
        transaction['date'] = args['date']
        transaction['uri'] = '/api/transactions/' + account_id + '/' + transaction['id']
        
        # Calculate new balances
        # update bal_uncleared (every transaction mods this)
        bal_unclr = round(account['bal_uncleared'] + args['amount'], 2)
        db.accounts.update({'id': account_id}, {'$set': {'bal_uncleared': bal_unclr}})
        bal_clr = account['bal_cleared']
        bal_rec = account['bal_reconciled']
        if args['reconciled'] in ['C', 'R']:
            # update bal_cleared (only cleared and reconciled transactions mod this)
            bal_clr = round(account['bal_cleared'] + args['amount'], 2)
            db.accounts.update({'id': account_id}, {'$set': {'bal_cleared': bal_clr}})
        if args['reconciled'] == 'R':
            # update bal_reconciled (only reconciled transactions mod this)
            bal_rec = round(account['bal_reconciled'] + args['amount'], 2)
            db.accounts.update({'id': account_id}, {'$set': {'bal_reconciled': bal_rec}})
        
        return { 'transaction': marshal(transaction, transaction_fields),
                 'account': {'uri': '/api/accounts/' + account_id, 'bal_uncleared': bal_unclr,
                             'bal_cleared': bal_clr, 'bal_reconciled': bal_rec} }, 201

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
        # TODO: if linked to another account, will need to update that entry
        transaction = db[account_id].find_one({'id':trans_id})
        if transaction == None:
            abort(404)
        old_reconciled = transaction['reconciled']
        old_amount = transaction['amount']
        
        args = self.reqparse.parse_args()
        for k, v in args.iteritems():
            if v != None:
                if k == 'date':
                    transaction[k] = datetime.strptime(v,'%Y-%m-%d')
                else:
                    transaction[k] = v
        db[account_id].update({'id':trans_id}, transaction)
        transaction['date'] = transaction['date'].strftime('%Y-%m-%d')
        transaction['uri'] = '/api/transactions/' + account_id + '/' + trans_id
        
        # Calculate new balances
        account = db.accounts.find_one({'id': account_id})
        bal_unclr = account['bal_uncleared']
        bal_clr = account['bal_cleared']
        bal_rec = account['bal_reconciled']
        
        # Update amount first
        if args['amount'] != None:
            diff = round(old_amount - args['amount'], 2)
            old_amount = args['amount']
            if old_reconciled == '':
                bal_unclr = round( account['bal_uncleared'] - diff, 2)
            elif old_reconciled == 'C':
                bal_unclr = round( account['bal_uncleared'] - diff, 2)
                bal_clr = round( account['bal_cleared'] - diff, 2)
            elif old_reconciled == 'R':
                bal_unclr = round( account['bal_uncleared'] - diff, 2)
                bal_clr = round( account['bal_cleared'] - diff, 2)
                bal_rec = round( account['bal_reconciled'] - diff, 2)
            
        # Update reconciled transition
        if args['reconciled'] != None:
            # Transition UP
            if old_reconciled == '' and args['reconciled'] == 'C':
                # bal_unclr = NO CHANGE
                bal_clr = round( account['bal_cleared'] + old_amount, 2)
                # bal_rec = NO CHANGE
            elif old_reconciled == '' and args['reconciled'] == 'R':
                # bal_unclr = NO CHANGE
                bal_clr = round( account['bal_cleared'] + old_amount, 2)
                bal_rec = round( account['bal_reconciled'] + old_amount, 2)
            elif old_reconciled == 'C' and args['reconciled'] == 'R':
                # bal_unclr = NO CHANGE
                # bal_clr = NO CHANGE 
                bal_rec = round( account['bal_reconciled'] + old_amount, 2)
            
            # Transition DOWN
            elif old_reconciled == 'C' and args['reconciled'] == '':
                # bal_unclr = NO CHANGE
                bal_clr = round( account['bal_cleared'] - old_amount, 2)
                # bal_rec = NO CHANGE
            elif old_reconciled == 'R' and args['reconciled'] == 'C':
                # bal_unclr = NO CHANGE
                # bal_clr = NO CHANGE
                bal_rec = round( account['bal_reconciled'] - old_amount, 2)
            elif old_reconciled == 'R' and args['reconciled'] == '':
                # bal_unclr = NO CHANGE
                bal_clr = round( account['bal_cleared'] - old_amount, 2)
                bal_rec = round( account['bal_reconciled'] - old_amount, 2)
        
        # Perform single db update
        db.accounts.update({'id': account_id}, {'$set': {'bal_uncleared': bal_unclr},
                                                '$set': {'bal_cleared': bal_clr},
                                                '$set': {'bal_reconciled': bal_rec}})
        return { 'transaction': marshal(transaction, transaction_fields),
                 'account': {'uri': '/api/accounts/' + account_id, 'bal_uncleared': bal_unclr,
                             'bal_cleared': bal_clr, 'bal_reconciled': bal_rec} }
        
    def delete(self, account_id, trans_id):
        """
        Delete a single transaction
        """
        account = db.accounts.find_one({'id': account_id})
        transaction = db[account_id].find_one({'id':trans_id})
        if not db[account_id].remove({'id':trans_id})['n']:
            abort(404)
        
        bal_unclr = account['bal_uncleared']
        bal_clr = account['bal_cleared']
        bal_rec = account['bal_reconciled']
        
        if transaction['reconciled'] == '':
            bal_unclr = round( account['bal_uncleared'] - transaction['amount'], 2)
        elif transaction['reconciled'] == 'C':
            bal_unclr = round( account['bal_uncleared'] - transaction['amount'], 2)
            bal_clr = round( account['bal_cleared'] - transaction['amount'], 2)
        elif transaction['reconciled'] == 'R':
            bal_unclr = round( account['bal_uncleared'] - transaction['amount'], 2)
            bal_clr = round( account['bal_cleared'] - transaction['amount'], 2)
            bal_rec = round( account['bal_reconciled'] - transaction['amount'], 2)
        
        db.accounts.update({'id': account_id}, {'$set': {'bal_uncleared': bal_unclr},
                                                '$set': {'bal_cleared': bal_clr},
                                                '$set': {'bal_reconciled': bal_rec}})
        return { 'account': {'uri': '/api/accounts/' + account_id, 'bal_uncleared': bal_unclr,
                             'bal_cleared': bal_clr, 'bal_reconciled': bal_rec} }
