import tensorflow as tf
import requests
from jproperties import Properties
from dataclasses import dataclass

@dataclass
class Config:
    backend_url = None
    video_src = None
    roi = None

    def __init__(self):
        self.read_config()
        self.load_model()

    def load_model(self):
        self.interpreter = tf.lite.Interpreter(model_path="model/model.tflite")
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]

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

        # try:
        #     self.get_config_from_backend()
        # except:
        #     traceback.print_exc()