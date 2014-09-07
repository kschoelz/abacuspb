from flask import abort
from flask.ext.restful import Resource, reqparse, fields, marshal
from bson.objectid import ObjectId
from abacuspb import db
import pymongo

payee_fields = { # Request validator
    'name': fields.String,
    'uri': fields.Url('payee')
}

class PayeeListAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, required=True, location='json')
        super(PayeeListAPI, self).__init__()
    
    def get(self):
        """
        Get all payees
        """
        payees = []
        pays = db.payees.find(sort=[('name', pymongo.ASCENDING)])
        if pays.count() == 0:
            abort(404)
        for pay in pays:
            payees.append(pay)
        return { 'payees': map(lambda t: marshal(t, payee_fields), payees) }
    
    def post(self):
        """
        Create a new payee
        """
        args = self.reqparse.parse_args()
        # Check if payee already exists
        if db.payees.find({'name': args['name']}).count() != 0:
            return { 'message': 'Payee already exists', 'status': 400 }, 400
        # Save new payee
        payee = {
            'id': str(ObjectId()),
            'name': args['name']
        }
        db.payees.insert(payee)
        return { 'payee': marshal(payee, payee_fields) }, 201


class PayeeAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, location='json')
        super(PayeeAPI, self).__init__()
    
    def get(self, id):
        """
        Get single payee by id
        """
        payee = db.payees.find_one({'id':id})
        if payee == None:
            abort(404)
        return { 'payee': marshal(payee, payee_fields) }
    
    def put(self, id):
        """
        Update single payee by id
        """
        payee = db.payees.find_one({'id':id})
        if payee == None:
            abort(404)
        args = self.reqparse.parse_args()
        for k, v in args.iteritems():
            if v != None:
                payee[k] = v
        db.payees.update({'id':id}, payee)
        return { 'payee': marshal(payee, payee_fields) }
    
    def delete(self, id):
        """
        Delete single payee by id
        """
        if not db.payees.remove({'id':id})['n']:
            abort(404)
        return { 'result': True }
