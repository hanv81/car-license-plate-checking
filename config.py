import schedule, requests, traceback
from jproperties import Properties
from dataclasses import dataclass
from ultralytics import YOLO

@dataclass
class Config:
    model = None
    model_path = None
    backend_url = None
    video_src = None
    roi = None

    def __init__(self):
        self.read_config()
        schedule.every(1).minutes.do(self.read_config)

    def get_config_from_backend(self):
        response = requests.get(self.backend_url + '/get_config')
        config = response.json()
        self.roi = list(map(int, config['roi'].split()))
        self.obj_size = int(config['obj_size'])
        self.video_src = config['file']

    def read_config(self):
        prop = Properties()
        with open('config.properties', 'rb') as f:
            prop.load(f)

        self.backend_url = prop.get('backend_url').data
        self.video_src = prop.get('video_src').data
        self.roi = list(map(int, prop.get('roi').data.split()))
        self.obj_size = int(prop.get('obj_size').data)
        
        if self.model_path != prop.get('model_path').data:
            self.model_path = prop.get('model_path').data
            self.model = YOLO(self.model_path, task='detect')

        try:
            self.get_config_from_backend()
        except:
            traceback.print_exc()

    def run_schedule(self):
        schedule.run_pending()

    def stop_schedule(self):
        schedule.clear()