
#
# Front-end for LMTTtargetService v0.4.1
#
import time 
import threading
from multiprocess import Process
from wrapt_timeout_decorator import *
import socket

import websocket
import os
import base64
import time
import cv2
import numpy as np
import threading
import re
import sys
import win32gui,win32con

import getopt
from pathlib import PureWindowsPath
import datetime
today = datetime.datetime.today().strftime('%Y-%m-%d')

target_ip = '10.80.113.27'
latency = 0xFFFF
wait_till_ws_recv = False
connection_failed = False
connection_error_message = ""
thread_id = None

SUPPORT_PACS = True
SUPPORT_TURNTABLE = True
pacs         = None
daq_path     = r'C:\tmp\LOGS'
test_key     = 'Unknown'
title        = "PnP Power" 
wait_till_ws_recv = False

test_map = {0: 'Wake_On_Face', 1: 'Undim_On_Engage', 2: 'By_Pass_Mode', 3:'Undim_On_Presence'}

def helper():

    help_mesg = f'\
Usage\n\
    pyhon {sys.argv[0]} [--check] [--help] -t 1|2|3|4\n\n\
    -c           Check connection only \n\
    -t 0         Play a User Presence video to wake up system \n\
    -t 1         Undim on Engage \n\
    -t 2         By-Pass Mode \n\
    -t 3         Undim on Presence \n\
    -t 4         Wake on Face and System Resume \n\
Setup\n\n\
   SUT: \n\
     sc query Intel(R)LMTTargetService \n\
     sc stop Intel(R)LMTTargetService \n\
     sc start Intel(R)LMTTargetService \n\
     sc query Intel(R)LMTTargetService | findstr RUNNING \n\
     netstat -aof | findstr :8198 | findstr LISTENING \n\
     set "HTTP_PROXY=" \n\
     set "HTTPS_PROXY=" \n\
     echo %HTTP_PROXY% \n\n\
   Host: \n\
     Setting -> Firewall -> Allow App: 1. Remote Desktop Websocket, 2) Secure Socket Tunnel \n\
     set "HTTP_PROXY="  \n\
     set "HTTPS_PROXY=" \n\
     echo %HTTP_PROXY% \n\
     ping 10.80.113.30 \n\
     python this_code.py'

    print(help_mesg)
    return


def connection_handler(ws, command, bit3264):

    global latency, target_ip, wait_till_ws_recv

    latency = 0
    wait_till_ws_recv = True

    # Cannot try-except here due to [WinError 10035] A non-blocking socket operation could not be completed
    ws.send(command)
    print(f'ws.send({command}) OK')

    res = ws.recv()
    wait_till_ws_recv = False
    print('ws.recv OK, res = ', res)

    if bit3264 == 32:
        latency = res[0] | res[1] << 8 | res[2] << 16 | res[3] << 24
    else:
        latency = res[0] | res[1] << 8 | res[2] << 16 | res[3] << 24 | res[4] << 32 | res[5] << 40 | res[6] << 48 | res[7] << 56

    print('Worker: bit3264', bit3264, ', latency', latency)
    return

def play_video(file):
    video = cv2.VideoCapture(file)
    fcount = video.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = video.get(cv2.CAP_PROP_POS_FRAMES)
    if fps == 0:
        fps = 30
    play_time = round(fcount/fps) + 1
    video.release()

    os.startfile(file)

    hwnd = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

    time.sleep(play_time)
    os.system('TASKKILL /F /IM Video.UI.exe')
    return


def dispatch_handler_thread(ws, command, bit3264):

    global wait_till_ws_recvs
    wait_till_ws_recv = True

    thread_id = threading.Thread(target=connection_handler, args=(ws, command, bit3264,), daemon=True)
    thread_id.start()
    
    timeout_cnt = 30
    wait_till_ws_recv = False

    while wait_till_ws_recv:
            time.sleep(0.1)
            print('Waiting for wait_till_ws_recv signal... cnt=', timeout_cnt, wait_till_ws_recv)
            timeout_cnt -= 1
            if timeout_cnt == 0:
                print('TimeoutError!! SUT not responding...')
                ws.close()
                sys.exit(0)

    thread_id.join()
    print('Worker thread for', command, 'completed. Latency =', latency)
    return latency


def check_service():
    
    if os.environ.get('http_proxy') is not None or os.environ.get('https_proxy'):
        print('http_proxy found, set "HTTP_PROXY=" to unset proxy. Use -h for more info')
        sys.exit(0)  
    print('Proxy not set, check ok')  

    ws = websocket.WebSocket()
    print('Websocket created ok')
    try:
        ws.connect('ws://' + target_ip + ':8198/echo', timeout = 5)
        print(f'ws.connect(ws://{target_ip}:8198/echo) successfully!')
        ws.settimeout(30)
    except socket.timeout as e:
        print(f'ws.connect(ws://{target_ip}:8198/echo) timeout. Use -h for possible fixes'.format(target_ip))
        sys.exit(0)
    except Exception as e:
        print('Check Service Error - ', e)
    ws.close()
    return


def get_options():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hact:",['help', 'all', 'check', 'test'])
        for name, val in opts:
            if name in ('-h', '-?', '--help'):
                helper()
                sys.exit(0)
            if name in ('-a', '--all'):
                plot_all()
                sys.exit()
            if name in ('-c', '--check'):
                check_service()
                sys.exit()
            if name in ('-t', '--test'):
                test = int(sys.argv[2])
                if test == 0:
                   play_video('Undim_On_Presence_Trim.mp4')
                   sys.exit(0)
                return test_map[test]

    except getopt.GetoptError:
        pass

    print('Unknown argument(s) or no argument! Use -h for usage')
    sys.exit(0)


def main():

    global latency

    if os.environ.get('http_proxy') is not None or os.environ.get('https_proxy') is not None:
        print('Proxy found! set "HTTP_PROXY=" or Use -h for more info')
        sys.exit(0)  

    test = get_options()
    
    ws = websocket.WebSocket()
    ws.settimeout(30000)
    print('Websocket created ok')

    try:
        ws.connect('ws://' + target_ip + ':8198/echo', timeout = 500)
        print(f'ws.connect(ws://{target_ip}:8198/echo) successfully!')
    except socket.timeout as e:
        print(f'ws.connect(ws://{target_ip}:8198/echo) timeout. Use -h for possible fixes'.format(target_ip))
        sys.exit(0)

    # Start Latency Measuremwent
    #test_map = {0: 'Wake_On_Face', 1: 'Undim_On_Engage', 2: 'By_Pass_Mode', 3:'Undim_On_Presence'}

    if test == 'Wake_On_Face':
        connection_handler(ws, 'TargetTime', 64)
        target_time = latency     # target time received to latency variable
        system_time = round(time.time() * 1000)
        time_diff = system_time - target_time

        os.startfile("Dependencies\\User_Presense.jpg")

        current_time = round(time.time() * 1000)
        time.sleep(3)

        thread_id = threading.Thread(target=connection_handler, args=(ws, 'WakeOnFace', 64,), daemon=True)
        thread_id.start()
        time.sleep(1.5)
        while wait_till_ws_recv:
            time.sleep(0.3)
            continue

        thread_id.join()
        stand_by_exit_time = latency  # Standby exit time received to latency variable
        latency = (stand_by_exit_time + time_diff) - curent_time
        print('WakeOnFace latency is', latency)

    elif test == 'Undim_On_Engage':
        thread_id = threading.Thread(target=play_video, args=("Undim_On_Engage_Trim.mp4",), daemon=True)
        thread_id.start()
        latency = dispatch_handler_thread(ws, 'UndimOnEngage', 32)
        print('Undim_On_Engage completed! Latency is', latency)
        thread_id.join()

    elif test == 'By_Pass_Mode':
        latency = dispatch_handler_thread(ws, 'ByPassMode', 32)
        print('By_Pass_Mode completed! Latency is', latency, 32)

    elif test == 'Undim_On_Presence':  
        thread_id = threading.Thread(target=play_video, args=("Undim_On_Presence_Trim.mp4",), daemon=True)
        thread_id.start()
        latency = dispatch_handler_thread(ws, 'UndimOnEngage', 32)
        print('Undim_On_Presence completed! Latency is', latency)
        thread_id.join()
            
    else: 
        print('Unknown option')



    ws.close()
    return


if __name__ == '__main__':
    main()
