from flask import abort
from flask.ext.restful import Resource, reqparse, fields, marshal
from abacuspb import db

account_fields = { # Request validator
    'name': fields.String,
    'type': fields.String,
    'bank_name': fields.String,
    'account_num': fields.String,
    'bal_uncleared': fields.Float,
    'bal_cleared': fields.Float,
    'bal_reconciled': fields.Float,
    #'last_stmt_date': fields.DateTime,
    #'credit_limit': fields.Float,
    #'purchase_price': fields.Float,
    #'interest_rate': fields.Float,
    #'securities': ???,
    'uri': fields.Url('account')
}

class AccountListAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, required=True, help='No account name provided', location='json')
        self.reqparse.add_argument('type', type=str, required=True, help='No account type provided', location='json')
        self.reqparse.add_argument('bank_name', type=str, default="", location='json')
        self.reqparse.add_argument('account_num', type=str, default="", location='json')
        self.reqparse.add_argument('bal_uncleared', type=float, location='json')
        self.reqparse.add_argument('bal_cleared', type=float, location='json')
        self.reqparse.add_argument('bal_reconciled', type=float, location='json')
        self.reqparse.add_argument('budget_monitored', type=bool, default=False, location='json')
        super(AccountListAPI, self).__init__()
    
    def get(self):
        """
        Get all accounts
        """
        accounts = []
        accts = db.accounts.find()
        if accts.count() == 0:
            abort(404)
        for account in accts:
            accounts.append(account)
        return { 'accounts': map(lambda t: marshal(t, account_fields), accounts) }
    
    def post(self):
        """
        Create a new account
        """
        args = self.reqparse.parse_args()
        # Check if account id already exists
        id = 'acct_' + args['name'].translate(None,"'!@#$%^&*()-_=+[{]}\|;:,<.>/?`~\"").lower().replace(" ","")
        if db.accounts.find({'id': id}).count() != 0:
            return { 'message': 'Account already exists', 'status': 400 }, 400
        # Save new account
        account = {
            'id': id,
            'name': args['name'],
            'type': args['type'],
            'bank_name': args['bank_name'],
            'account_num': args['account_num'],
            'bal_uncleared': 0.0,
            'bal_cleared': 0.0,
            'bal_reconciled': 0.0,
            'budget_monitored': args['budget_monitored']
        }
        db.accounts.insert(account)
        return { 'account': marshal(account, account_fields) }, 201


class AccountAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, location='json')
        self.reqparse.add_argument('type', type=str, location='json')
        self.reqparse.add_argument('bank_name', type=str, location='json')
        self.reqparse.add_argument('account_num', type=str, location='json')
        self.reqparse.add_argument('bal_uncleared', type=float, location='json')
        self.reqparse.add_argument('bal_cleared', type=float, location='json')
        self.reqparse.add_argument('bal_reconciled', type=float, location='json')
        self.reqparse.add_argument('budget_monitored', type=bool, location='json')
        super(AccountAPI, self).__init__()
    
    def get(self, id):
        """
        Get single account by id
        """
        account = db.accounts.find({'id':id})
        if account.count() == 0:
            abort(404)
        return { 'account': marshal(account[0], account_fields) }
    
    def put(self, id):
        """
        Update single account by id
        """
        account = db.accounts.find({'id':id})
        if account.count() == 0:
            abort(404)
        account = account[0]
        args = self.reqparse.parse_args()
        for k, v in args.iteritems():
            if v != None:
                account[k] = v
        db.accounts.update({'id':id}, account)
        return { 'account': marshal(account, account_fields) }
    
    def delete(self, id):
        """
        Delete single account by id
        """
        if not db.accounts.remove({'id':id})['n']:
            abort(404)
        # Remove associated transactions collection for account
        db[id].drop()
        return { 'result': True }
