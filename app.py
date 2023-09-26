import io
import sys
import cv2
import time
import json
import requests
import numpy as np
from PIL import Image
from helper import DamageHelper

MAX_CALL = 3
API_URL = 'https://api.platerecognizer.com/v1/plate-reader/'
HEADER={'Authorization': 'Token 45f3172a25b6ea562e6174ac2475b7ca26b8e2fc'}

def call_plate_recognizer_api(frame):
    byte_io = io.BytesIO()
    Image.fromarray(frame).save(byte_io, format='PNG')
    # t = time.time()
    response = requests.post(url=API_URL, headers=HEADER, files=dict(upload=byte_io.getvalue()))
    # print(time.time() - t)
    byte_io.close()
    return response

def read_file():
    roi = [400, 400, 700, 665]
    left, top, right, bottom = roi
    cap = cv2.VideoCapture('video.avi')
    calls = MAX_CALL
    model = DamageHelper('yolov5s_openvino_model/yolov5s.xml')
    last_call = 0
    while cap.isOpened():
        ret, frame = cap.read()
        # t = time.time()
        key = cv2.waitKey(1)
        if key == ord("q") or not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # results = model.process(frame, 416) # detect all frame
        results = model.process(frame[top:bottom, left:right], 416) # detect in ROI only
        if results is not None:
            results = [p for p in results if p[-1] == 2] # car
            for l,t,r,b,_,_ in results:
                if (r-l)*(b-t) >= 30000:
                    cv2.rectangle(frame[top:bottom, left:right], (l,t), (r,b), (0,0,255), 3)
                    cur_time = time.time()
                    if cur_time - last_call > 5:
                        print('reset calls')
                        calls = MAX_CALL
                    if calls > 0 and cur_time - last_call > 2:
                        last_call = time.time()
                        calls -= 1
                        response = call_plate_recognizer_api(frame[top:bottom, left:right])
                        if response.json()['results']:
                            plate = response.json()['results'][0]['plate']
                            print(plate)

        cv2.rectangle(frame, (roi[0], roi[1]), (roi[2], roi[3]), (0,255,0), 3)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow('frame', frame)

    cap.release()
    cv2.destroyAllWindows()

read_file()