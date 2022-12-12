from logging import error
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import TIMEOUT_KEY, Menu                        # Part 1 - The import
import websocket
import os
import base64
import time
import cv2
import numpy as np
import threading
import re
import sys

ws = websocket.WebSocket()
target_ip = None
latency = 0xFFFF
wait_till_ws_recv = False
connection_failed = False
connection_error_message = ""
thread_id = None

regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$" # regular expression to validate IP Address

sg.theme("LightBlue")

scenario_column_list = [[sg.Listbox(values=("Undim on Engage", "By-Pass Mode", "Undim on Presence", "Wake On Face and System Resume", "Wake On Face and Windows Hello", "Lid Closed"), enable_events=True, font='Calibri', size=(40,20), key="-SCENARIO-")]]
                        #[sg.Button("Run All", key="-RUNALL-")]]

description_column = [[sg.Text(key="-SCENARIOTITLE-", font='CalibriLight')],
                      [sg.Text(key="-SCENARIODSC-", font='Calibri')],
                      [sg.Image(key="-IMAGE-")],
                      [sg.Button("Run", key="-RUN-", border_width=5)],
                      [sg.Text(key="-OUTPUT-", font='Calibri',text_color="Blue")]]
                      # [sg.Multiline(key="-OUTPUT-",background_color="White",text_color="Blue",disabled="True")]]


# ------ Menu Definition ------ #
menu_def = [['&Help', '&About']]

# Define the window's contents
#layout = [ [sg.Button(button_text = 'Latency Report Generator', pad = (100,120), key="-Report Generator-")] ]

layout = [
    [
        sg.Menu(menu_def),
        sg.Column(scenario_column_list),
        sg.VSeparator(),
        sg.Column(description_column, size=(650, 450))
    ]
]


def play_video(video_file_name):
     # cv2.namedWindow("Video", cv2.WINDOW_FULLSCREEN)
     cap = cv2.VideoCapture(video_file_name)
     if (cap.isOpened()== False):
         sg.Popup("Error opening video file")

     while(cap.isOpened()):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == True:
            # Display the resulting frame
            cv2.imshow('Video', frame)

            if cv2.waitKey(19):
                pass
        else:
            break
     # When everything done, release
     # the video capture object
     cap.release()

     # Closes all the frames
     cv2.destroyAllWindows()
     return


def connection_handler(message):
    global latency
    global ws
    global target_ip
    global wait_till_ws_recv
    global connection_failed
    global connection_error_message

    connection_failed = True
    try:
        ws.connect('ws://' + target_ip + ':8198/echo')
    except ConnectionRefusedError as er:
        # sg.Popup("Failed to connect to WebSocket server, Please ensure that Intel(R)LMTTarget Service running on DUT", title="Connection Error", icon="Intel.ico")
        connection_error_message = "Failed to connect to DUT server, Please ensure that Intel(R)LMTTarget Service running on DUT"
        #window.write_event_value('-CONNECTION_ERROR-', "Failed to connect to WebSocket server, Please ensure that Intel(R)LMTTarget Service running on DUT")
        return
    try:
        ws.send(message)
    except:
        # sg.Popup("Failed to Send request to DUT", title="Request Error", icon="Intel.ico")
        connection_error_message = "Failed to Send request to DUT"
        #window.write_event_value('-CONNECTION_ERROR-', "Failed to Send request to DUT")
        return
    
    try:
        wait_till_ws_recv = True
        res = ws.recv()
    except:
        # sg.Popup("Failed to Receive response from DUT", title="Response Error", icon="Intel.ico")
        connection_error_message = "Failed to Receive response from DUT"
        #window.write_event_value('-CONNECTION_ERROR-', "Failed to Receive response from DUT")
        wait_till_ws_recv = False
        return
    wait_till_ws_recv = False
    connection_failed = False
    latency = res[0] | res[1] << 8 | res[2] << 16 | res[3] << 24
    ws.close()


def connection_handler_64bit(message):
    global latency
    global ws
    global target_ip
    global wait_till_ws_recv
    global connection_failed
    global connection_error_message

    connection_failed = True
    try:
        ws.connect('ws://' + target_ip + ':8198/echo')
    except ConnectionRefusedError as er:
        # sg.Popup("Failed to connect to WebSocket server, Please ensure that Intel(R)LMTTarget Service running on DUT", title="Connection Error", icon="Intel.ico")
        connection_error_message = "Failed to connect to DUT server, Please ensure that Intel(R)LMTTarget Service running on DUT"
        #window.write_event_value('-CONNECTION_ERROR-', "Failed to connect to WebSocket server, Please ensure that Intel(R)LMTTarget Service running on DUT")
        return
    try:
        ws.send(message)
    except:
        # sg.Popup("Failed to Send request to DUT", title="Request Error", icon="Intel.ico")
        connection_error_message = "Failed to Send request to DUT"
        #window.write_event_value('-CONNECTION_ERROR-', "Failed to Send request to DUT")
        return
    
    try:
        wait_till_ws_recv = True
        res = ws.recv()
    except:
        # sg.Popup("Failed to Receive response from DUT", title="Response Error", icon="Intel.ico")
        connection_error_message = "Failed to Receive response from DUT"
        #window.write_event_value('-CONNECTION_ERROR-', "Failed to Receive response from DUT")
        wait_till_ws_recv = False
        return
    wait_till_ws_recv = False
    connection_failed = False
    latency = res[0] | res[1] << 8 | res[2] << 16 | res[3] << 24 | res[4] << 32 | res[5] << 40 | res[6] << 48 | res[7] << 56
    ws.close()


# Create the window
window = sg.Window('Intel® VSC Latency Measurement Tool', layout, icon="Intel.ico")      # Part 3 - Window Defintion

while(target_ip == None):
    try:
        target_ip = sg.popup_get_text("Provide DUT IP", title="DUT IP", icon="Intel.ico")
        if not re.search(regex,target_ip):
            sg.Popup("Invalid IP Address provided, please verify and provide again", title="Invalid IP")
            target_ip = None
    except TypeError:
        sys.exit()


# Display and interact with the Window
while(True):
    event, values = window.read()                   # Part 4 - Event loop or Window.read call
    if event == sg.WIN_CLOSED:
        print("Closed")
        break
    elif event == "About":
        sg.popup('Intel® VSC Latency Measurement Tool',
                 'Version 0.4', title="About")
    # elif event == "TargetTime":
    #     ws.send("TargetTime")
    #     t = ws.recv()
    #     ctime = t[0] | t[1] << 8 | t[2] << 16 | t[3] << 24
    #     print(ctime)
    #     sg.popup(time.ctime(ctime), title="Target Time")
    elif event == "-SCENARIO-":
        if values["-SCENARIO-"][0] == "Undim on Engage":
            filename = os.path.join(os.getcwd(),"Dependencies\\Undim on Engage Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update("Latency from User Engaged to Display default brightness reached\nPreconditions:-\n‣ Lid open, display on, backlight dimmed to 0%, system in idle S0(unlocked)")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "By-Pass Mode":
            filename = os.path.join(os.getcwd(),"Dependencies\\By-pass Mode Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update("Latency from Start at click on Camera app to Video stream appears\nPreconditions:-\n‣ Lid open, display on, system in S0(unlocked)")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "Undim on Presence":
            filename = os.path.join(os.getcwd(),"Dependencies\\Undim on Presence Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update("Latency from User Face Engaged to Display default brightness reached\nPreconditions:-\n‣ Lid open, display on and backlight dimming, system in idle S0(unlocked)")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "Wake On Face and System Resume":
            filename = os.path.join(os.getcwd(),"Dependencies\\Wake On Face and System Resume Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update("Latency from User In front of Camera to System Resume\nPreconditions:-\n‣ Lid open, display off, system in S0ix and locked\n‣ User outside camera field-of-view")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "Wake On Face and Windows Hello":
            filename = os.path.join(os.getcwd(),"Dependencies\\Wake On Face and Windows Hello Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0] + " (Live User)")
            window["-SCENARIODSC-"].update("Latency from Motion trigger to User Login\nPreconditions:-\n‣ Lid open, display off, system in S0ix and locked\n‣ User outside camera field-of-view")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "Lid Closed":
            filename = os.path.join(os.getcwd(),"Dependencies\\Lid Closed Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update("Latency from Lid close to CVF enters D3-hot state\nPreconditions:-\n‣ Lid open, system in S0")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
    elif event == "-RUN-" and len(values["-SCENARIO-"]) != 0:
        if values["-SCENARIO-"][0] == "Undim on Engage":
            os.startfile("Dependencies\\Undim_On_Engage_Trim.mp4")
            # connection_handler("UndimOnEngage")
            thread_id = threading.Thread(target=connection_handler, args=("UndimOnEngage",), daemon=True)
            thread_id.start()
            time.sleep(1.5)
            while wait_till_ws_recv:
                #window.Refresh()
                sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white',time_between_frames=100,grab_anywhere=False)
                time.sleep(0.1)
                continue
            sg.PopupAnimated(None)
            thread_id.join()
            if connection_failed:
                window["-OUTPUT-"].update(connection_error_message)
                continue

            if latency != 0 and latency != 0xFFFF:
                window["-OUTPUT-"].update("Latency for Undim on Engage : %d ms" % (latency))
            else:
                window["-OUTPUT-"].update("DUT is not responding to Request")
        elif values["-SCENARIO-"][0] == "By-Pass Mode":
            # connection_handler("ByPassMode")
            thread_id = threading.Thread(target=connection_handler, args=("ByPassMode",), daemon=True)
            thread_id.start()
            time.sleep(1.5)
            while wait_till_ws_recv:
                #window.Refresh()
                sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white',time_between_frames=100,grab_anywhere=False)
                time.sleep(0.1)
                continue
            sg.PopupAnimated(None)
            thread_id.join()
            if connection_failed:
                window["-OUTPUT-"].update(connection_error_message)
                continue
            if latency != 0 and latency != 0xFFFF:
                window["-OUTPUT-"].update("Latency for By-Pass Mode : %d ms" % (latency))
            else:
                window["-OUTPUT-"].update("DUT is not responding to Request")
        elif values["-SCENARIO-"][0] == "Undim on Presence":
            os.startfile("Dependencies\\Undim_On_Presence_Trim.mp4")
            # connection_handler("UndimOnEngage")
            thread_id = threading.Thread(target=connection_handler, args=("UndimOnEngage",), daemon=True)
            thread_id.start()
            time.sleep(1.5)
            while wait_till_ws_recv:
                #window.Refresh()
                sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white',time_between_frames=100,grab_anywhere=False)
                time.sleep(0.1)
                continue
            sg.PopupAnimated(None)
            thread_id.join()
            if connection_failed:
                window["-OUTPUT-"].update(connection_error_message)
                continue
            if latency != 0 and latency != 0xFFFF:
                window["-OUTPUT-"].update("Latency for Undim on Presence : %d ms" % (latency))
            else:
                window["-OUTPUT-"].update("DUT is not responding to Request")
        elif values["-SCENARIO-"][0] == "Wake On Face and System Resume":
            connection_handler_64bit("TargetTime")
            target_time = latency # target time received to latency variable
            system_time = round(time.time() * 1000)
            time_diff = system_time - target_time
            os.startfile("Dependencies\\User_Presense.jpg")
            curent_time = round(time.time() * 1000)
            time.sleep(3)
            # connection_handler("WakeOnFace")
            thread_id = threading.Thread(target=connection_handler_64bit, args=("WakeOnFace",), daemon=True)
            thread_id.start()
            time.sleep(1.5)
            while wait_till_ws_recv:
                #window.Refresh()
                sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white',time_between_frames=100,grab_anywhere=False,keep_on_top=False)
                time.sleep(0.1)
                continue
            sg.PopupAnimated(None)
            thread_id.join()
            if connection_failed:
                window["-OUTPUT-"].update(connection_error_message)
                continue
            stand_by_exit_time = latency # Standby exit time received to latency variable
            latency = (stand_by_exit_time + time_diff) - curent_time
            # sg.Popup("current time : %d, time diff : %d, exit time : %d" % (curent_time, time_diff, stand_by_exit_time))
            if stand_by_exit_time != int(0xFFFF) and (latency >= 0):
                if latency==0:
                    window["-OUTPUT-"].update("Latency for Wake On Face : <1 ms")
                else:
                    window["-OUTPUT-"].update("Latency for Wake On Face : %d ms" % (latency))
            else:
                window["-OUTPUT-"].update("Failed to get the Standby exit event from DUT")
            # thread_id.join()
        elif values["-SCENARIO-"][0] == "Wake On Face and Windows Hello":
            # os.startfile("Dependencies\\User_Presense.jpg")
            # connection_handler("SystemResume")
            thread_id = threading.Thread(target=connection_handler, args=("SystemResume",), daemon=True)
            thread_id.start()
            time.sleep(1.5)
            while wait_till_ws_recv:
                #window.Refresh()
                sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white',time_between_frames=100,grab_anywhere=False)
                time.sleep(0.1)
                continue
            sg.PopupAnimated(None)
            thread_id.join()
            if connection_failed:
                window["-OUTPUT-"].update(connection_error_message)
                continue
            if latency != int(0xFFFF) and (latency > 0):
                window["-OUTPUT-"].update("Latency for System Resume : %d s" % (latency))
            else:
                window["-OUTPUT-"].update("Failed to get the User Logon event from DUT")
        elif values["-SCENARIO-"][0] == "Lid Closed":
            # os.startfile("Dependencies\\User_Presense.jpg")
            # connection_handler("LidClosed")
            thread_id = threading.Thread(target=connection_handler, args=("LidClosed",), daemon=True)
            thread_id.start()
            time.sleep(1.5)
            while wait_till_ws_recv:
                #window.Refresh()
                ## window.Disable()
                sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white',time_between_frames=100,grab_anywhere=False)
                time.sleep(0.1)
                continue
            sg.PopupAnimated(None)
            # window.Enable()
            thread_id.join()
            if connection_failed:
                window["-OUTPUT-"].update(connection_error_message)
                continue
            if latency != int(0xFFFF) and (latency > 0):
                window["-OUTPUT-"].update("Latency for Lid Closed : %d ms" % (latency))
            else:
                window["-OUTPUT-"].update("Failed to get the CVF D3 event from DUT")
    
    event=None
    values=None

if ws.connected:
    ws.close()
# Finish up by removing from the screen
window.close()
