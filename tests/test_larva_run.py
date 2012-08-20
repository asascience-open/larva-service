from tests.flask_mongo import FlaskMongoTestCase
import json
import pytz
from datetime import datetime

class LarvaRunTestCase(FlaskMongoTestCase):
    
    def test_upload_run_parameters(self):

        timestamp = 1345161600000

        config = {
            'particles'         : 10,
            'duration'          : 2,
            'start'             : timestamp,
            'timestep'          : 3600,
            'release_depth'     : 10.5,
            'vert_dispersion'   : 0.005,
            'horiz_dispersion'  : 0.005,
            'geometry'          : "POINT (-147 60.75)",
            'hydro_path'        : "http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc",
            'email'             : 'user@example.com',
            'behavior'          : 'https://larvamap.s3.amazonaws.com/resources/501c40e740a83e0006000000.json'
        }
        jd = json.dumps(config)

        assert len(list(self.db['runs'].find())) == 0
        rv = self.app.post('/run', data=dict(config=jd), follow_redirects=True)

        runs = list(self.db['runs'].find())

        assert len(runs) == 1

        assert runs[0]['particles'] == config['particles']
        assert runs[0]['duration'] == config['duration']
        assert runs[0]['start'].replace(tzinfo=pytz.utc) == datetime.fromtimestamp(timestamp / 1000, pytz.utc)
        assert runs[0]['geometry'] == config['geometry']
        assert runs[0]['hydro_path'] == config['hydro_path']
        assert runs[0]['email'] == config['email']
        assert runs[0]['behavior'] == config['behavior']
        assert runs[0]['cached_behavior'] is not None
        assert runs[0]['horiz_dispersion'] == 0.005
        assert runs[0]['vert_dispersion'] == 0.005
        assert runs[0]['timestep'] == 3600
        assert runs[0]['release_depth'] == 10.5
        # Defaults
        assert runs[0]['time_chunk'] == 2
        assert runs[0]['horiz_chunk'] == 2
        