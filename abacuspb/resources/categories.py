from flask import abort
from flask.ext.restful import Resource, reqparse, fields, marshal
from bson.objectid import ObjectId
from abacuspb import db
import pymongo

category_fields = { # Request validator
    'name': fields.String,
    'parent_id': fields.String,
    'uri': fields.Url('category')
}

class CategoryListAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, required=True, location='json')
        self.reqparse.add_argument('parent_id', type=str, location='json')
        super(CategoryListAPI, self).__init__()
    
    def get(self):
        """
        Get all categories
        """
        categories = []
        cats = db.categories.find(sort=[('name', pymongo.ASCENDING)])
        if cats.count() == 0:
            abort(404)
        for cat in cats:
            categories.append(cat)
        return { 'categories': map(lambda t: marshal(t, category_fields), categories) }
    
    def post(self):
        """
        Create a new category/sub-category
        """
        args = self.reqparse.parse_args()
        # Check if category already exists
        if db.categories.find({'name': args['name']}).count() != 0:
            return { 'message': 'category already exists', 'status': 400 }, 400
        # If parent_id set, check if parent exists first
        if args['parent_id'] and (db.categories.find({'id': args['parent_id']}).count() == 0):
            return { 'message': 'parent category does not exist', 'status': 404}, 404
        # Save new category
        if not args.has_key('parent_id'): args['parent_id'] = None
        category = {
            'id': str(ObjectId()),
            'name': args['name'],
            'parent_id': args['parent_id'],
        }
        db.categories.insert(category)
        return { 'category': marshal(category, category_fields) }, 201


class CategoryAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, location='json')
        self.reqparse.add_argument('parent_id', type=str, location='json')
        super(CategoryAPI, self).__init__()
    
    def get(self, id):
        """
        Get single category by id
        """
        category = db.categories.find_one({'id':id})
        if category == None:
            abort(404)
        return { 'category': marshal(category, category_fields) }
    
    def put(self, id):
        """
        Update single category by id
        """
        category = db.categories.find_one({'id':id})
        if category == None:
            abort(404)
        args = self.reqparse.parse_args()
        for k, v in args.iteritems():
            if v != None:
                category[k] = v
        db.categories.update({'id':id}, category)
        return { 'category': marshal(category, category_fields) }
    
    def delete(self, id):
        """
        Delete single category by id
        """
        if not db.categories.remove({'id':id})['n']:
            abort(404)
        return { 'result': True }
