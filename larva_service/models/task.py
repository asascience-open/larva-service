from flask.ext.mongokit import Document
from larva_service import db

class Task(Document):
    __collection__= 'tasks'
    use_schemaless = True

db.register([Task])