import io, cv2, time, requests, threading
import numpy as np
from PIL import Image
from helper import DamageHelper
from tracker import track
from jproperties import Properties

MAX_CALL = 3

def call_plate_recognizer_api(frame, url):
    byte_io = io.BytesIO()
    Image.fromarray(frame).save(byte_io, format='PNG')
    response = requests.post(url=url, files=dict(file=byte_io.getvalue()))
    byte_io.close()
    return response

def read_config():
    configs = Properties()
    with open('config.properties', 'rb') as prop:
        configs.load(prop)
    
    roi = list(map(int, configs.get('roi').data.split()))
    model_path = configs.get('model_path').data
    backend_url = configs.get('backend_url').data
    video_src = configs.get('video_src').data
    calibration_path = configs.get('calibration').data
    return roi, model_path, backend_url, video_src, calibration_path

def main():
    roi, model_path, backend_url, _, _ = read_config()
    left, top, right, bottom = roi
    model = DamageHelper(model_path)

    tracking_info = None

    def capture(frame):
        response = call_plate_recognizer_api(frame, backend_url)
        tracking_info['waiting'] = False
        print('server response', response.json())
        msg = response.json().get('msg')
        if msg != 'Fail':
            tracking_info['done'] = msg

    show_fps = True

    # cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    cap = cv2.VideoCapture('video.mp4')
    while cap.isOpened():
        t = time.time()
        ret, frame = cap.read()
        key = cv2.waitKey(1)
        if key == ord("q") or not ret:
            break
        elif key == ord('f'):
            show_fps = not show_fps
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
                        # time.sleep(.5)

                    info = '' if not tracking_info['done'] else tracking_info['done']
                    x1, y1, x2, y2 = int(d.rect.x), int(d.rect.y), int(d.rect.max_x), int(d.rect.max_y)
                    cv2.rectangle(roi, (x1, y1), (x2, y2), (255, 0, 0), 3)
                    cv2.putText(roi, f'{d.tracker_id} {info}', org=(x1+2, y1+17), fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=.8, color=(0, 255, 0), thickness=2)

        t = time.time() - t
        if show_fps and t != 0:
            # print('FPS:', int(1/t))
            cv2.putText(frame, f'FPS: {int(1/t)}', org=(0, 15), fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=.5, color=(0, 0, 255), thickness=2)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow('frame', frame)

    cap.release()
    cv2.destroyAllWindows()

main()