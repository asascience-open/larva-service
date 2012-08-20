from tests.flask_mongo import FlaskMongoTestCase
import json
import pytz
from datetime import datetime

class LarvaRunTestCase(FlaskMongoTestCase):
    
    def setUp(self):
        super(LarvaRunTestCase,self).setUp()
        self.timestamp = 1345161600000

        self.config = {
            'particles'         : 10,
            'duration'          : 2,
            'start'             : self.timestamp,
            'timestep'          : 3600,
            'release_depth'     : 10.5,
            'vert_dispersion'   : 0.005,
            'horiz_dispersion'  : 0.005,
            'geometry'          : "POINT (-147 60.75)",
            'hydro_path'        : "http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc",
            'email'             : 'user@example.com',
            'behavior'          : 'https://larvamap.s3.amazonaws.com/resources/501c40e740a83e0006000000.json'
        }
        jd = json.dumps(self.config)

        assert len(list(self.db['runs'].find())) == 0
        rv = self.app.post('/run', data=dict(config=jd), follow_redirects=True)
        assert len(list(self.db['runs'].find())) == 1

        self.run = list(self.db['runs'].find())[0]
        
    def test_uploaded_run_parameters(self):
        assert self.run['particles'] == self.config['particles']
        assert self.run['duration'] == self.config['duration']
        assert self.run['start'].replace(tzinfo=pytz.utc) == datetime.fromtimestamp(self.timestamp / 1000, pytz.utc)
        assert self.run['geometry'] == self.config['geometry']
        assert self.run['hydro_path'] ==self.config['hydro_path']
        assert self.run['email'] == self.config['email']
        assert self.run['behavior'] == self.config['behavior']
        assert self.run['cached_behavior'] is not None
        assert self.run['horiz_dispersion'] == 0.005
        assert self.run['vert_dispersion'] == 0.005
        assert self.run['timestep'] == 3600
        assert self.run['release_depth'] == 10.5
        # Defaults
        assert self.run['time_chunk'] == 2
        assert self.run['horiz_chunk'] == 2
        
    def test_json_status(self):
        rv = self.app.get('/runs/%s/status.json' % self.run['_id'], follow_redirects=True)
        assert json.loads(rv.data)['status'] == "PENDING"

    def test_json_run_description(self):
        rv = self.app.get('/runs/%s.json' % self.run['_id'], follow_redirects=True)
        result_json = json.loads(rv.data)

        assert result_json['_id'] == str(self.run['_id'])
        assert result_json['particles'] == self.run['particles']
        assert result_json['duration'] == self.run['duration']
        assert result_json['start'] == self.timestamp
        assert result_json['geometry'] == self.run['geometry']
        assert result_json['hydro_path'] ==self.run['hydro_path']
        assert result_json['email'] == self.run['email']
        assert result_json['behavior'] == self.run['behavior']
        assert result_json['cached_behavior'] is not None
        assert result_json['horiz_dispersion'] == 0.005
        assert result_json['vert_dispersion'] == 0.005
        assert result_json['timestep'] == 3600
        assert result_json['release_depth'] == 10.5
        # Defaults
        assert result_json['time_chunk'] == 2
        assert result_json['horiz_chunk'] == 2