import io, cv2, time, requests, threading, traceback
import numpy as np
import screeninfo
from PIL import Image
from helper import DamageHelper
from tracker import track,Detection
from jproperties import Properties

MAX_CALL = 3

def call_backend_api(url, frame, bbox):
    byte_io = io.BytesIO()
    Image.fromarray(frame).save(byte_io, format='PNG')
    response = requests.post(url=url + '/verify', files=dict(file=byte_io.getvalue()), params={'bbox':bbox})
    byte_io.close()
    return response

def check_detection(url:str, frame:np.ndarray, d:Detection, tracking:dict):
    bbox = str(int(d.rect.x)), str(int(d.rect.y)), str(int(d.rect.max_x)), str(int(d.rect.max_y))
    response = call_backend_api(url, frame, ' '.join(bbox))
    tracking['waiting'] = False
    print('server response', response.json(), d.tracker_id)
    tracking['info'] = response.json().get('msg')
    if response.json().get('identified'):
        tracking['done'] = True

def get_config_from_backend(url : str):
    response = requests.get(url + '/get_config')
    configs = response.json()
    roi = list(map(int, configs['roi'].split()))
    obj_size = int(configs['obj_size'])
    file = configs['file']
    return roi, obj_size, file

def read_config():
    configs = Properties()
    with open('config.properties', 'rb') as prop:
        configs.load(prop)

    model_path = configs.get('model_path').data
    backend_url = configs.get('backend_url').data
    try:
        roi, obj_size, video_src = get_config_from_backend(backend_url)
    except:
        traceback.print_exc()
        roi = list(map(int, configs.get('roi').data.split()))
        video_src = configs.get('video_src').data
        obj_size = int(configs.get('obj_size').data)

    return roi, obj_size, model_path, backend_url, video_src

def main():
    roi, obj_size, model_path, backend_url, video_src = read_config()
    left, top, right, bottom = roi
    model = DamageHelper(model_path)

    tracking_info = {}
    show_fps = True

    # cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    screen = screeninfo.get_monitors()[0]
    cap = cv2.VideoCapture('video/' + video_src)
    while cap.isOpened():
        t = time.time()
        ret, frame = cap.read()
        key = cv2.waitKey(1)
        if key == ord("q") or not ret:
            break
        elif key == ord('f'):
            show_fps = not show_fps
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        roi = frame[top:bottom, left:right]
        results = model.process(roi, 416) # detect in ROI only
        if results is not None:
            results = [p for p in results if p[-1] == 2] # car
        if results:
            # results = np.array(results, dtype=float)
            detections = track(roi, np.array(results, dtype=float))
            for d in detections:
                if d.tracker_id is not None and d.rect.width * d.rect.height >= obj_size:
                    tracking = tracking_info.get(d.tracker_id)
                    if tracking is None:
                        tracking = {'waiting':False, 'done':False, 'calls':MAX_CALL, 'info':''}
                        tracking_info[d.tracker_id] = tracking

                    if not tracking['done'] and not tracking['waiting'] and tracking['calls'] > 0:
                        tracking['waiting'] = True
                        tracking['calls'] -= 1
                        threading.Thread(target=check_detection, args=(backend_url, roi, d, tracking)).start()
                        # time.sleep(.5)

                    info = tracking['info']
                    x1, y1, x2, y2 = int(d.rect.x), int(d.rect.y), int(d.rect.max_x), int(d.rect.max_y)
                    cv2.rectangle(roi, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(roi, f'{d.tracker_id} {info}', org=(x1+2, y1+17), 
                                fontFace = cv2.FONT_HERSHEY_SIMPLEX, 
                                fontScale=.8, color=(0, 255, 0), thickness=2)

        cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
        t = time.time() - t
        if show_fps and t != 0:
            # print('FPS:', int(1/t))
            cv2.putText(frame, f'FPS: {int(1/t)}', org=(0, 15), fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=.5, color=(0, 0, 255), thickness=2)

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, dsize=(screen.width*9//10, screen.height*9//10))
        cv2.imshow('frame', frame)

    cap.release()
    cv2.destroyAllWindows()

main()