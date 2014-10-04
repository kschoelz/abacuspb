import unittest, abacuspb, json
from test import test_data
from datetime import datetime

db = abacuspb.db

class CategoriesAPI_TestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = abacuspb.app.test_client()
        db.categories.drop()
    
    def tearDown(self):
        db.categories.drop()
    
    # CategoryListAPI Tests
    def test_CategoryListAPI_GET_Empty(self):
        rv = self.app.get('/api/categories')
        self.assertEqual(rv.status_code, 404)
        
    def test_CategoryListAPI_GET_Categories_SortedByName(self):
        db.categories.insert(test_data.db_categories)
        rv = self.app.get('/api/categories')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(obj['categories']), 5)
        self.assertEqual(obj['categories'][0]['name'], 'Auto')
        self.assertEqual(obj['categories'][4]['name'], 'Tithe')
        self.assertEqual(obj['categories'][4]['parent_id'], None)    
    
    def test_CategoryListAPI_POST_EmptyDb(self):
        rv = self.app.post('/api/categories',
                           data=json.dumps(test_data.category_1),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 201)
        self.assertEqual(obj['category']['name'], 'Tithe')
        self.assertIsNotNone(obj['category']['uri'])
        self.assertIsNotNone(db.categories.find_one())
 
    def test_CategoryListAPI_POST_CatNameAlreadyExists(self):
        db.categories.insert(test_data.db_categories)
        rv = self.app.post('/api/categories',
                           data=json.dumps(test_data.category_1),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(obj['message'], 'category already exists')
        
    def test_CategoryListAPI_POST_ParentDoesNotExist(self):
        db.categories.insert(test_data.db_categories)
        rv = self.app.post('/api/categories',
                           data=json.dumps(test_data.category_2),
                           content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(obj['message'], 'parent category does not exist')
     
    # CategoryAPI Tests
    def test_CategoryAPI_GET_Empty(self):
        rv = self.app.get('/api/categories/123')
        self.assertEqual(rv.status_code, 404)
     
    def test_CategoryAPI_GET_Category(self):
        db.categories.insert(test_data.db_categories)
        rv = self.app.get('/api/categories/53f69e77137a001e344259f2')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['category']['name'], 'Dining & Entertainment')
        self.assertEqual(obj['category']['uri'], '/api/categories/53f69e77137a001e344259f2')
         
    def test_CategoryAPI_PUT_CatDoesNotExist(self):
        rv = self.app.put('/api/categories/53f69e77137a001e344259f2',
                          data=json.dumps(test_data.category_put),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 404)
     
    def test_CategoryAPI_PUT_ChangeParentId(self):
        db.categories.insert(test_data.db_categories)
        rv = self.app.put('/api/categories/53f69e77137a001e344259f2',
                          data=json.dumps(test_data.category_put),
                          content_type='application/json')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(obj['category']['name'], 'Dining & Entertainment')
        self.assertEqual(obj['category']['parent_id'], '1234567890')
        self.assertEqual(obj['category']['uri'], '/api/categories/53f69e77137a001e344259f2')
     
    def test_CategoryAPI_DELETE_EmptyDb(self):
        rv = self.app.delete('/api/categories/53f69e77137a001e344259f2')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 404)
     
    def test_CategoryAPI_DELETE_Entry(self):
        db.categories.insert(test_data.db_categories)
        rv = self.app.delete('/api/categories/53f69e77137a001e344259f2')
        obj = json.loads(rv.get_data())
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(obj['result'])
        self.assertIsNone(db.categories.find_one({'id': '53f69e77137a001e344259f2'}))

if __name__ == '__main__':
    unittest.main()
