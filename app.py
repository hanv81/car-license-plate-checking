import io, cv2, time, requests, threading
import numpy as np
from config import Config
import screeninfo
from PIL import Image
from model import CustomModel
from boxmot import BYTETracker

MAX_CALL = 3

def call_backend_api(url, frame, bbox):
    byte_io = io.BytesIO()
    Image.fromarray(frame).save(byte_io, format='PNG')
    response = requests.post(url=url + '/verify', files=dict(file=byte_io.getvalue()), params={'bbox':bbox})
    byte_io.close()
    return response

def check_detection(url:str, frame:np.ndarray, bbox, id, tracking:dict):
    response = call_backend_api(url, frame, ' '.join(bbox))
    tracking['waiting'] = False
    print('server response', response.json(), id)
    tracking['info'] = response.json().get('msg')
    if response.json().get('identified'):
        tracking['done'] = True

def main():
    tracker = BYTETracker(track_thresh = 0.25)
    model = CustomModel()
    cf = Config()
    left, top, right, bottom = cf.roi

    tracking_info = {}
    show_fps = True
    draw_bbox = True
    resize = True
    frame_size = None
    screen = screeninfo.get_monitors()[0]
    
    winname = 'Frame'
    cv2.namedWindow(winname)
    def mouse_callback(event, x, y, flags, param):
        left, top, right, bottom = cf.roi
        if event == cv2.EVENT_LBUTTONUP:
            d1 = np.linalg.norm([[x-left, y-top]])
            d2 = np.linalg.norm([[x-right, y-bottom]])
            cf.roi = [x , y, right, bottom] if d1 < d2 else [left, top, x, y]
    cv2.setMouseCallback(winname, mouse_callback)

    cap = cv2.VideoCapture('video/' + cf.video_src)
    while cap.isOpened():
        left, top, right, bottom = cf.roi
        cf.run_schedule()
        t = time.time()
        ret, frame = cap.read()
        key = cv2.waitKey(1)
        if key == ord("q") or not ret:
            cf.stop_schedule()
            break
        elif key == ord('f'):
            show_fps = not show_fps
        elif key == ord('b'):
            draw_bbox = not draw_bbox
        elif key == ord('r'):
            resize = not resize
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        track_roi(frame[top:bottom, left:right], model, tracker, cf, tracking_info, draw_bbox)
        if draw_bbox:
            cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)

        if key == ord("-") or key == ord('+'):
            resize = False
            if frame_size is None:
                h,w,_ = frame.shape
                frame_size = w,h
            w,h = frame_size
            frame_size = (int(w*.9), int(h*.9)) if key == ord('-') else (int(w*1.1), int(h*1.1))

        if resize:
            frame = cv2.resize(frame, dsize=(screen.width*9//10, screen.height*9//10))
            frame_size = None
        elif frame_size:
            frame = cv2.resize(frame, dsize=frame_size)

        t = time.time() - t
        if show_fps and t != 0:
            # print('FPS:', int(1/t))
            cv2.putText(frame, f'FPS: {int(1/t)}', org=(0, 15), fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=.5, color=(0, 255, 255), thickness=2)

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow(winname, frame)

    cap.release()
    cv2.destroyAllWindows()

def track_roi(roi:np.ndarray, model: CustomModel, tracker:BYTETracker, config:Config, tracking_info:dict, draw_bbox:bool):
    preds = model(roi, classes=[2])
    if len(preds) == 0:
        return
    
    roi_api = roi.copy()
    tracks = tracker.update(np.array(preds), roi)
    for t in tracks:
        x1, y1, x2, y2, id = list(map(int, t[:5]))
        if (x2-x1) * (y2-y1) < config.obj_size:
            continue

        tracking = tracking_info.get(id)
        if tracking is None:
            tracking = {'waiting':False, 'done':False, 'calls':MAX_CALL, 'info':''}
            tracking_info[id] = tracking

        if not tracking['done'] and not tracking['waiting'] and tracking['calls'] > 0:
            tracking['waiting'] = True
            tracking['calls'] -= 1
            threading.Thread(target=check_detection, 
                             args=(config.backend_url, roi_api, map(str, (x1,y1,x2,y2)), id, tracking)
                            ).start()

        if draw_bbox:
            info = tracking['info']
            cv2.rectangle(roi, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(roi, f'{id} {info}', org=(x1+2, y1+17), 
                        fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=.8, color=(0, 255, 0), thickness=2)

main()