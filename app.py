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
left, top, right, bottom = 400, 400, 700, 665   # ROI

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
    cap = cv2.VideoCapture('video.avi')
    q=queue.Queue()
    stop = False
    def capture():
        while not stop:
            ret, frame = cap.read()
            if ret:q.put(frame)
            else:break

    thread = threading.Thread(target=capture)
    thread.start()
    time.sleep(5)

    tracking_info = None
    while not q.empty():
        # t = time.time()
        frame = q.get()
        key = cv2.waitKey(1)
        if key == ord("q"):
            stop = True
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
                    x1, y1, x2, y2 = int(d.rect.x), int(d.rect.y), int(d.rect.max_x), int(d.rect.max_y)
                    cv2.rectangle(roi, (x1, y1), (x2, y2), (255, 0, 0), 3)
                    cv2.putText(roi, f'{d.tracker_id}', org=(x1+2, y1+15), fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=.5, color=(0, 255, 0), thickness=2)
                    if tracking_info is None or tracking_info['id'] != d.tracker_id:
                        tracking_info = {'id':d.tracker_id, 'waiting':False, 'calls':MAX_CALL}
                    print(tracking_info)
                    if not tracking_info['waiting'] and tracking_info['calls'] > 0:
                        tracking_info['waiting'] = True
                        tracking_info['calls'] -= 1
                        response = call_plate_recognizer_api(roi)
                        print(response.json())

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow('frame', frame)

    cap.release()
    cv2.destroyAllWindows()

main()