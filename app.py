import io
import cv2
import time
import json
import requests
import queue
import threading
import numpy as np
from PIL import Image
from helper import DamageHelper
from tracker import track

MAX_CALL = 3
API_URL = 'https://api.platerecognizer.com/v1/plate-reader/'
HEADER={'Authorization': 'Token 45f3172a25b6ea562e6174ac2475b7ca26b8e2fc'}
left, top, right, bottom = 400, 400, 900, 665   # ROI

def call_plate_recognizer_api(frame):
    byte_io = io.BytesIO()
    Image.fromarray(frame).save(byte_io, format='PNG')
    # t = time.time()
    response = requests.post(url=API_URL, headers=HEADER, files=dict(upload=byte_io.getvalue()))
    # print(time.time() - t)
    byte_io.close()
    return response

def main():
    model = DamageHelper('yolov5s_openvino_model/yolov5s.xml')
    cap = cv2.VideoCapture('video.mp4')
    tracking_info = None

    def capture(frame):
        response = call_plate_recognizer_api(frame)
        results = response.json().get('results')
        tracking_info['waiting'] = False
        if results is not None and len(results) > 0:
            plate = results[0]['plate']
            print(plate)
            if plate in ('ar606l', 'a3k961', 'cav2889'):
                tracking_info['done'] = plate

    while cap.isOpened():
        # t = time.time()
        ret, frame = cap.read()
        key = cv2.waitKey(1)
        if key == ord("q") or not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 3)
        roi = frame[top:bottom, left:right]
        results = model.process(roi, 416) # detect in ROI only
        if results is not None:
            results = [p for p in results if p[-1] == 2] # car
        if results:
            # results = np.array(results, dtype=float)
            detections = track(roi, np.array(results, dtype=float))
            for d in detections:
                if d.rect.width * d.rect.height >= 30000:
                    if tracking_info is None or tracking_info['id'] != d.tracker_id:
                        tracking_info = {'id':d.tracker_id, 'waiting':False, 'done':False, 'calls':MAX_CALL}

                    if not tracking_info['done'] and not tracking_info['waiting'] and tracking_info['calls'] > 0:
                        tracking_info['waiting'] = True
                        tracking_info['calls'] -= 1
                        threading.Thread(target=capture, args=(roi,)).start()

                    info = '' if not tracking_info['done'] else tracking_info['done']
                    x1, y1, x2, y2 = int(d.rect.x), int(d.rect.y), int(d.rect.max_x), int(d.rect.max_y)
                    cv2.rectangle(roi, (x1, y1), (x2, y2), (255, 0, 0), 3)
                    cv2.putText(roi, f'{d.tracker_id} {info}', org=(x1+2, y1+15), fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=.5, color=(0, 255, 0), thickness=2)

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow('frame', frame)

    cap.release()
    cv2.destroyAllWindows()

main()