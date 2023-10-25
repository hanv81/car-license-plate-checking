import cv2, requests, datetime, os, traceback, schedule
import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
from http import HTTPStatus
import subprocess

API_URL = 'http://127.0.0.1:8000/'

def login():
    placeholder = st.empty()
    with placeholder.form("login"):
        username = st.text_input("Username", 'admin')
        password = st.text_input("Password", value='admin', type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if username != '' and password != '':
            response = requests.post(url = API_URL + 'login', 
                                     data = {'username': username, 'password': password})
            if response.status_code == HTTPStatus.OK:
                placeholder.empty()
                st.success("Login successful")
                st.session_state['access_token'] = response.json()['access_token']
                st.session_state['username'] = username
            else:
                st.error('Login fail: ' + response.json()['detail'])
    return username

def main():
    username = st.session_state.get('username')
    if username is None:
        username = login()

    access_token = st.session_state.get('access_token')
    if access_token:
        headers={'Authorization': f'Bearer {access_token}'}
        tab1, tab2, tab3, tab4 = st.tabs(['Plates', 'History', 'Config', 'Statistic'])
        with tab1:
            cols = st.columns(2)
            with cols[0]:
                response = requests.post(url = API_URL + 'get_plates', 
                                        headers = headers)
                plates = response.json()
                plate = st.selectbox('Plates', plates)
                if st.button('Delete'):
                    response = requests.post(url = API_URL + 'delete_plate', 
                                            headers = headers, params = {'plate': plate})
                    if response.status_code == HTTPStatus.OK:
                        st.success("Plate deleted")

            with cols[1]:
                plate = st.text_input('Register plate')
                if st.button('Register'):
                    response = requests.post(url = API_URL + 'register_plate',
                                             headers = headers, params = {'plate': plate})
                    if response.status_code == HTTPStatus.OK:
                        st.success("Plate registered")

        response = requests.post(url = API_URL + 'get_history', headers = headers)
        with tab2:
            if st.button('Refresh'):
                response = requests.post(url = API_URL + 'get_history', headers = headers)
            if response.status_code == HTTPStatus.OK:
                history = response.json()
                for h in history:
                    # st.write(h)
                    left, top, right, bottom = map(float, h[1].split())
                    tmp = h[2].split('/')
                    t_ns = int(tmp[2][len(username):tmp[2].find('.')])
                    t = t_ns * 1e-9
                    dt_object = datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
                    img = np.array(Image.open('backend/' + h[2]))
                    cv2.rectangle(img, (int(left), int(top)), (int(right), int(bottom)), (255, 0, 0), 2)
                    st.image(img, h[0] + ' - ' + str(dt_object))
            else:
                st.write(response.json())
        with tab3:
            response = requests.get(url = API_URL + 'get_config')
            configs = response.json()
            with st.expander('Config', True):
                roi = list(map(int, configs['roi'].split()))
                cols = st.columns(5)
                with cols[0]:
                    left = st.number_input('Left', value=roi[0])
                with cols[1]:
                    top = st.number_input('Top', value=roi[1])
                with cols[2]:
                    right = st.number_input('Right', value=roi[2])
                with cols[3]:
                    bottom = st.number_input('Bottom', value=roi[3])
                with cols[4]:
                    obj_size = st.number_input('Object size', value=int(configs['obj_size']))
                
                col1, col2 = st.columns(2)
                with col1:file = st.selectbox('File', os.listdir('video'))
                cap = cv2.VideoCapture('video/' + file)
                while cap.isOpened():
                    _, frame = cap.read()
                    if frame is not None:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        with col2:
                            st.text('Frame Size')
                            st.write(frame.shape[:2])
                        cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
                        img = Image.fromarray(frame)
                        st.image(img)
                        break
                cap.release()

                cols = st.columns(2)
                success = True
                update_code = None
                with cols[0]:
                    if st.button('Update', use_container_width=True):
                        response = requests.post(url = API_URL + 'update_config', headers = headers,
                                                 params = {'file': file,
                                                           'roi': f'{left} {top} {right} {bottom}',
                                                           'obj_size': f'{obj_size}'})
                        update_code = response.status_code
                if update_code is not None:
                    if update_code == HTTPStatus.OK:
                        st.success("Config updated") 
                    else:
                        st.error(response.json()['detail'])

                with cols[1]:
                    if st.button('Start', use_container_width=True):
                        success = start_app()
                if not success:
                    st.error('App started failed')

        with tab4:
            response = requests.post(API_URL+'statistic', headers=headers)
            if response.status_code != HTTPStatus.OK:
                st.error(response.json()['detail'])
            else:
                _, cars, statistic = response.json()
                with st.expander('Cars'):
                    cars = pd.DataFrame(cars, columns=['Plate', 'Username'])
                    st.table(cars)
                with st.expander('Statistic'):
                    statistic = pd.DataFrame(statistic, columns=['Type', 'Date', 'Count'])
                    st.table(statistic)
                with st.form('Create'):
                    col1, col2 = st.columns(2)
                    with col1:user = st.text_input('Username')
                    with col2:pw = st.text_input('Password', type='password')
                    if st.form_submit_button('Create', use_container_width=True):
                        create_user(user, pw, headers)

def create_user(username, password, headers):
    response = requests.post(API_URL + 'create_user', headers = headers,
                            params={'username': username, 'password':password})
    if response.status_code == HTTPStatus.OK:
        st.success('User created')
    else:
        st.error(response.json())

def start_app():
    try:
        result = subprocess.run(["python", "app.py"])
        return result.returncode == 0
    except:
        traceback.print_exc()
        return False

main()