from flask import Flask, make_response, jsonify
from flask.ext.restful import Api
from pymongo import MongoClient

app = Flask(__name__)
app.config.from_object('abacuspb.settings')
db = MongoClient()[app.config['MONGO_DBNAME']]

from abacuspb.resources.accounts import AccountListAPI, AccountAPI
from abacuspb.resources.transactions import TransactionListAPI, TransactionAPI
from abacuspb.resources.payees import PayeeListAPI, PayeeAPI
from abacuspb.resources.categories import CategoryListAPI, CategoryAPI

api = Api(app)
api.add_resource(AccountListAPI, '/api/accounts', endpoint = 'accounts')
api.add_resource(AccountAPI, '/api/accounts/<id>', endpoint = 'account')
api.add_resource(TransactionListAPI, '/api/transactions/<account_id>', endpoint = 'transactions')
api.add_resource(TransactionAPI, '/api/transactions/<account_id>/<trans_id>', endpoint = 'transaction')
api.add_resource(PayeeListAPI, '/api/payees', endpoint = 'payees')
api.add_resource(PayeeAPI, '/api/payees/<id>', endpoint = 'payee')
api.add_resource(CategoryListAPI, '/api/categories', endpoint = 'categories')
api.add_resource(CategoryAPI, '/api/categories/<id>', endpoint = 'category')

@app.route('/')
def index():
    return make_response(open('abacuspb/templates/abacuspb.html').read())
