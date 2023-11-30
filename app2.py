import io, cv2, time, requests, threading
import numpy as np
from config2 import Config
import screeninfo
from PIL import Image

MAX_CALL = 3

def call_backend_api(url, frame, bbox):
    byte_io = io.BytesIO()
    Image.fromarray(frame).save(byte_io, format='PNG')
    response = requests.post(url=url + '/verify', files=dict(file=byte_io.getvalue()), params={'bbox':bbox})
    byte_io.close()
    return response

def check_detection(url:str, frame:np.ndarray, tracking_info:dict):
    # bbox = str(int(d.rect.x)), str(int(d.rect.y)), str(int(d.rect.max_x)), str(int(d.rect.max_y))
    bbox = '0','0', str(frame.shape[1]), str(frame.shape[0])
    response = call_backend_api(url, frame, ' '.join(bbox))
    tracking_info['status'] = 'wait'
    print('server response', response.json())
    tracking_info['info'] = response.json().get('msg')
    if response.json().get('identified'):
        tracking_info['status'] = 'Done'

def main():
    cf = Config()
    left, top, right, bottom = cf.roi

    tracking = {'status':'wait', 'call':MAX_CALL, 'info':None}
    show_fps = True
    draw_bbox = True
    resize = False
    frame_size = None
    last_roi = None
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
        t = time.time()
        ret, frame = cap.read()
        key = cv2.waitKey(1)
        if key == ord("q") or not ret:
            break
        elif key == ord('f'):
            show_fps = not show_fps
        elif key == ord('b'):
            draw_bbox = not draw_bbox
        elif key == ord('r'):
            resize = not resize
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        process_roi(frame[top:bottom, left:right], last_roi, cf, tracking, draw_bbox)
        last_roi = frame[top:bottom, left:right]

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

THRESH = 25
ASSIGN_VALUE = 1
DIFF_THRESH = 5

def detect_motion(roi, last_roi):
    # roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    # last_roi = cv2.cvtColor(last_roi, cv2.COLOR_RGB2GRAY)
    diff = cv2.absdiff(roi, last_roi)
    # _, motion_mask = cv2.threshold(diff, THRESH, ASSIGN_VALUE, cv2.THRESH_BINARY)
    # cv2.imshow('Motion mask', motion_mask)
    if diff.mean() < DIFF_THRESH:
        return False
    return True

def detect_car(roi, cf:Config):
    roi = cv2.resize(roi, (224,224))
    # roi = roi[None, ...]
    # prediction = cf.model.predict(roi, verbose=0)[0]
    roi = roi[None, ...].astype("float32")
    cf.interpreter.set_tensor(cf.input_details["index"], roi)
    cf.interpreter.invoke()
    prediction = cf.interpreter.get_tensor(cf.output_details["index"])[0][0]
    return prediction < .5

def process_roi(roi, last_roi, cf:Config, tracking, draw_bbox):
    if last_roi is None:
        return

    if not detect_car(roi, cf):
        tracking['status'] = 'wait'
        tracking['call'] = MAX_CALL
        tracking['info'] = None
        cv2.putText(roi, 'NO CAR', org=(2, 20), fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=.8,
                    color=(255, 0, 0), thickness=2)
    else:
        if detect_motion(roi, last_roi):
            info = 'CAR MOVING'
        else:
            status = tracking['status']
            call = tracking['call']
            if status == 'wait' and call > 0:
                print(f'call {call}')
                threading.Thread(target=check_detection, args=(cf.backend_url, roi, tracking)).start()
                tracking['status'] = 'sent'
                tracking['call'] = call-1

            info = tracking['info']

        if info is None:
            info = tracking['status']
        
        cv2.putText(roi, f'{info}', org=(2, 20), fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=.8,
                    color=(0, 0, 255), thickness=2)

main()