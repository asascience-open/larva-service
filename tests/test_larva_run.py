from tests.flask_mongo import FlaskMongoTestCase
import json
import pytz
from datetime import datetime

class LarvaRunTestCase(FlaskMongoTestCase):
    
    def test_upload_run_parameters(self):

        timestamp = 1344460387672

        config = {
            'particles' : 10,
            'duration'  : 30,
            'start'     : timestamp,
            'geometry'  : "POLYGON ((153.2746875000000273 25.7885529585785953, -67.8581249999999727 27.9832813434000016, -67.8581249999999727 53.5328232787000005, -117.4284374999999727 67.0625260424999965, 138.5090625000000273 51.8279954420795335, 153.2746875000000273 25.7885529585785953))",
            'hydro_path': "http://thredds.axiomalaska.com/thredds/dodsC/PWS_L2_FCST.nc",
            'email'     : 'user@example.com',
            'behavior'  : 'https://larvamap.s3.amazonaws.com/resources/501c40e740a83e0006000000.json'
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


