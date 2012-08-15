import unittest
import larva_service
from larva_service import app
from mongokit import Connection

class FlaskMongoTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.raw_app = app
        self.app = app.test_client()
        self.db = Connection(app.config['MONGODB_HOST'], app.config['MONGODB_PORT'])[app.config['MONGODB_DATABASE']]

    def tearDown(self):
        self.db.drop_collection("tasks")
        self.db.drop_collection("runs")