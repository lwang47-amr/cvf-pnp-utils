import PySimpleGUI as sg
import websocket
import os
import time
# import cv2
import threading
import re
import sys
import json
import ast
import ctypes

ws = websocket.WebSocket()
target_ip = None
stored_ip = None
latency = 0xFFFF
wait_till_ws_recv = False
connection_failed = False
connection_error_message = ""
thread_id = None
time_diff = 0
current_time = 0

regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"  #
# regular expression to validate IP Address
ENGAGE_EVENT = '2'
DISENGAGE_EVENT = '1'
NOT_PRESENT_EVENT = '0'
start_cmd = {"Version": "0.1", "Command": "StartEventWatcher", "NumberOfArguments": 2,
             "Arguments": ["UserPresenceEvents", "BrightnessEvents"]}
stop_cmd = {"Version": "0.1", "Command": "StopEventWatcher", "NumberOfArguments": 2,
            "Arguments": ["UserPresenceEvents", "BrightnessEvents"]}
get_events_data_cmd = {"Version": "0.1", "Command": "GetEventsData", "NumberOfArguments": 2,
                       "Arguments": ["UserPresenceEvents", "BrightnessEvents"]}
get_info_cmd = {"Version": "0.1", "Command": "GetInfo", "NumberOfArguments": 1, "Arguments": ["ByPassModeLatency"]}
set_info_cmd = {"Version": "0.1", "Command": "SetInfo", "NumberOfArguments": 1, "Arguments": {"SystemEvents": 0}}

sg.theme("LightBlue")

# Admin check
if ctypes.windll.shell32.IsUserAnAdmin() == 0:
    sg.Popup("Please run application with admin privileges", title="Privileges Error", icon="Intel.ico")
    sys.exit()

"""scenario_column_list = [[sg.Listbox(values=(
    "Undim on Engage", "By-Pass Mode", "Undim on Presence", "Wake On Face and System Resume",
    "Wake On Face and Windows Hello", "Lid Closed", "Wake On Face", "Walk Away Lock", "Undim On Engage(Functional)",
    "Dim On Disengage(Functional)"), enable_events=True, font='Calibri', size=(40, 20), key="-SCENARIO-")]]"""

scenario_column_list = [[sg.Listbox(values=(
    "Undim on Engage", "By-Pass Mode", "Undim on Presence", "Wake On Face and System Resume", "Lid Closed"),
    enable_events=True, font='Calibri', size=(40, 20), key="-SCENARIO-")]]
# [sg.Button("Run All", key="-RUNALL-")]]

description_column = [[sg.Text(key="-SCENARIOTITLE-", font='CalibriLight')],
                      [sg.Text(key="-SCENARIODSC-", font='Calibri')],
                      [sg.Image(key="-IMAGE-")],
                      [sg.Button("Run", key="-RUN-", border_width=5)],
                      [sg.Text(key="-OUTPUT-", font='Calibri', text_color="Blue")]]
# [sg.Multiline(key="-OUTPUT-",background_color="White",text_color="Blue",disabled="True")]]


# ------ Menu Definition ------ #
menu_def = [['&Help', '&About']]

# Define the window's contents
# layout = [ [sg.Button(button_text = 'Latency Report Generator', pad = (100,120), key="-Report Generator-")] ]

layout = [
    [
        sg.Menu(menu_def),
        sg.Column(scenario_column_list),
        sg.VSeparator(),
        sg.Column(description_column, size=(650, 450))
    ]
]


'''def play_video(video_file_name):
    # cv2.namedWindow("Video", cv2.WINDOW_FULLSCREEN)
    cap = cv2.VideoCapture(video_file_name)
    if not cap.isOpened():
        sg.Popup("Error opening video file")

    while cap.isOpened():
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret:
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
    return'''


def connection_handler(commands, stop_delay, window, response):
    global ws
    global target_ip

    index = 0
    status = True
    try:
        ws.connect('ws://' + target_ip + ':8198/echo')
    except ConnectionRefusedError as er:
        window.write_event_value('-CONNECTION_ERROR-',
                                 "Failed to connect to DUT server, Please ensure that Intel(R)LMTTarget Service "
                                 "running on DUT")
        return
    for command in commands:
        print(command)
        if command['Command'].__contains__("StopEventWatcher"):
            time.sleep(stop_delay)
        try:
            ws.send(json.dumps(command))
        except:
            window.write_event_value('-CONNECTION_ERROR-', "Failed to Send request to DUT")
            status = False
            break

        try:
            response.append(json.loads(ws.recv()))
        except:
            window.write_event_value('-CONNECTION_ERROR-', "Failed to Receive response from DUT")
            status = False
            break

        if response[index]["Status"] != "Success":
            window.write_event_value('-CONNECTION_ERROR-', "{}".format(response[index]["Status"]))
            status = False
            break
        index = index + 1
    if status:
        window.write_event_value('-LATENCYOUTPUT-', "{}".format(response[-1]))
    ws.close()


def execute_cmd(command):
    global ws
    global target_ip

    response = {}
    status = True
    try:
        ws.connect('ws://' + target_ip + ':8198/echo')
    except ConnectionRefusedError as er:
        window.write_event_value('-CONNECTION_ERROR-',
                                 "Failed to connect to DUT server, Please ensure that Intel(R)LMTTarget Service "
                                 "running on DUT")
        return

    try:
        ws.send(json.dumps(command))
    except:
        window.write_event_value('-CONNECTION_ERROR-', "Failed to Send request to DUT")
        status = False

    try:
        response = json.loads(ws.recv())
    except:
        window.write_event_value('-CONNECTION_ERROR-', "Failed to Receive response from DUT")
        status = False

    if response["Status"] != "Success":
        window.write_event_value('-CONNECTION_ERROR-', "{}".format(response["Status"]))
        status = False
    ws.close()
    if status:
        return response

    return None


# Create the window
window = sg.Window('Intel® VSC Latency Measurement Tool', layout, icon="Intel.ico")  # Part 3 - Window Defintion

if os.path.exists("IP.txt"):
    fp = open("IP.txt", "r")
    stored_ip = fp.read()
    fp.close()

while target_ip is None:
    try:
        target_ip = sg.popup_get_text("Provide DUT IP", title="DUT IP", default_text=stored_ip, icon="Intel.ico")
        if not re.search(regex, target_ip):
            sg.Popup("Invalid IP Address provided, please verify and provide again", title="Invalid IP")
            target_ip = None
    except TypeError:
        sys.exit()

# Storing IP to local file
if target_ip is not None:
    fp = open("IP.txt", "w")
    fp.write(target_ip)
    fp.close()

# Display and interact with the Window
while True:
    event, values = window.read()  # Part 4 - Event loop or Window.read call
    print(event, values)
    if event == sg.WIN_CLOSED:
        print("Closed")
        break
    elif event == "About":
        sg.popup('Intel® VSC Latency Measurement Tool',
                 'Version 0.5.0', title="About")
    elif event == "-CONNECTION_ERROR-":
        window.Enable()
        window["-OUTPUT-"].update(values[event])
    elif event == "-LATENCYOUTPUT-":
        window.Enable()
        print("LATENCYOUTPUT : {}".format(values))
        # window["-OUTPUT-"].update(values[event])
        response = ast.literal_eval(values[event])

        if values["-SCENARIO-"][0] == "Undim on Engage":
            user_engage_time = bt_event_time = 0
            for index in range(len(response["Data"]["UserPresenceEvents"])):
                if user_engage_time != 0 and bt_event_time != 0:
                    break
                for key in response["Data"]["UserPresenceEvents"][index]:
                    if key == ENGAGE_EVENT:
                        user_engage_time = response["Data"]["UserPresenceEvents"][index][key]
                        for bt_index in range(len(response["Data"]["BrightnessEvents"])):
                            for bt_key in response["Data"]["BrightnessEvents"][bt_index]:
                                if bt_key == '100' and response["Data"]["BrightnessEvents"][bt_index][bt_key] > user_engage_time:
                                    bt_event_time = response["Data"]["BrightnessEvents"][bt_index][bt_key]
                                    break
                    if user_engage_time != 0 and bt_event_time != 0:
                        break
            latency = bt_event_time - user_engage_time
            if latency >= 0:
                window["-OUTPUT-"].update("Latency for Undim on Engage : %d ms" % latency)
            else:
                window["-OUTPUT-"].update("DUT is not responding to Request")
        elif values["-SCENARIO-"][0] == "By-Pass Mode":
            latency = response["Data"]["ByPassModeLatency"]
            if latency >= 0:
                window["-OUTPUT-"].update("Latency for By-Pass Mode : %d ms" % latency)
            else:
                window["-OUTPUT-"].update("DUT is not responding to Request")
        elif values["-SCENARIO-"][0] == "Undim on Presence":
            user_engage_time = bt_event_time = 0
            for index in range(len(response["Data"]["UserPresenceEvents"])):
                if user_engage_time != 0 and bt_event_time != 0:
                    break
                for key in response["Data"]["UserPresenceEvents"][index]:
                    if key == ENGAGE_EVENT:
                        user_engage_time = response["Data"]["UserPresenceEvents"][index][key]
                        for bt_index in range(len(response["Data"]["BrightnessEvents"])):
                            for bt_key in response["Data"]["BrightnessEvents"][bt_index]:
                                if bt_key == '100' and response["Data"]["BrightnessEvents"][bt_index][bt_key] > user_engage_time:
                                    bt_event_time = response["Data"]["BrightnessEvents"][bt_index][bt_key]
                                    break
                    if user_engage_time != 0 and bt_event_time != 0:
                        break
            latency = bt_event_time - user_engage_time
            if latency >= 0:
                window["-OUTPUT-"].update("Latency for Undim on Presence : %d ms" % latency)
            else:
                window["-OUTPUT-"].update("DUT is not responding to Request")
        elif values["-SCENARIO-"][0] == "Wake On Face and System Resume":
            stand_by_exit_time = response["Data"]["StandByExitEvents"][0]['507']
            latency = (stand_by_exit_time + time_diff) - current_time
            if latency >= 0:
                window["-OUTPUT-"].update("Latency for Wake On Face : %d ms" % latency)
            else:
                window["-OUTPUT-"].update("DUT is not responding to Request")
        elif values["-SCENARIO-"][0] == "Wake On Face and Windows Hello":
            user_logon_time = user_engage_time = 0
            for index in range(len(response["Data"]["UserPresenceEvents"])):
                if user_engage_time != 0 and user_logon_time != 0:
                    break
                for key in response["Data"]["UserPresenceEvents"][index]:
                    if key == ENGAGE_EVENT:
                        user_engage_time = response["Data"]["UserPresenceEvents"][index][key]
                        for user_logon_index in range(len(response["Data"]["UserLogonEvents"])):
                            for user_logon_key in response["Data"]["UserLogonEvents"][user_logon_index]:
                                if user_logon_key == '100' and response["Data"]["UserLogonEvents"][user_logon_index][user_logon_key] > user_engage_time:
                                    bt_event_time = response["Data"]["UserLogonEvents"][user_logon_index][
                                        user_logon_key]
                                    break
                    if user_engage_time != 0 and user_logon_time != 0:
                        break
            latency = user_logon_time - user_engage_time
            if latency >= 0:
                window["-OUTPUT-"].update("Latency for System Resume : %d ms" % latency)
            else:
                window["-OUTPUT-"].update("Failed to get the User Logon event from DUT")
        elif values["-SCENARIO-"][0] == "Lid Closed":
            cvf_disable_time = lid_close_time = 0
            for lid_close_event in response["Data"]["LidClosedEvents"]:
                lid_close_time = lid_close_event['1']
                break
            for cvf_disable_event in response["Data"]["CVFDisabledEvents"]:
                cvf_disable_time = cvf_disable_event['1']
                break

            latency = cvf_disable_time - lid_close_time
            if latency >= 0:
                window["-OUTPUT-"].update("Latency for Lid Closed : %d ms" % latency)
            else:
                window["-OUTPUT-"].update("Failed to get the CVF D3 event from DUT")
        elif values["-SCENARIO-"][0] == "Wake On Face":
            test_status = False
            for index in range(len(response["Data"]["UserPresenceEvents"])):
                for key in response["Data"]["UserPresenceEvents"][index]:
                    if key == ENGAGE_EVENT:
                        for index1 in range(len(response["Data"]["StandByExitEvents"])):
                            for key in response["Data"]["StandByExitEvents"][index1]:
                                if key == '507':
                                    test_status = True
                                    break
                        break
            if test_status:
                window["-OUTPUT-"].update("Wake on Face Test is passed")
            else:
                window["-OUTPUT-"].update("Wake on Face Test is failed")
        elif values["-SCENARIO-"][0] == "Walk Away Lock":
            test_status = False
            for index in range(len(response["Data"]["UserPresenceEvents"])):
                for key in response["Data"]["UserPresenceEvents"][index]:
                    if key == NOT_PRESENT_EVENT:
                        for index1 in range(len(response["Data"]["StandByEntryEvents"])):
                            for key in response["Data"]["StandByEntryEvents"][index1]:
                                if key == '506':
                                    test_status = True
                                    break
                        break
            if test_status:
                window["-OUTPUT-"].update("Walk Away Lock Test is passed")
            else:
                window["-OUTPUT-"].update("Walk Away Lock Test is failed")
        elif values["-SCENARIO-"][0] == "Undim On Engage(Functional)":
            test_status = False
            for index in range(len(response["Data"]["UserPresenceEvents"])):
                for key in response["Data"]["UserPresenceEvents"][index]:
                    if key == ENGAGE_EVENT:
                        for index1 in range(len(response["Data"]["BrightnessEvents"])):
                            for key in response["Data"]["BrightnessEvents"][index1]:
                                if key == '100':
                                    test_status = True
                                    break
                        break
            if test_status:
                window["-OUTPUT-"].update("Undim On Engage Test is passed")
            else:
                window["-OUTPUT-"].update("Undim On Engage Test is failed")
        elif values["-SCENARIO-"][0] == "Dim On Disengage(Functional)":
            test_status = False
            for index in range(len(response["Data"]["UserPresenceEvents"])):
                for key in response["Data"]["UserPresenceEvents"][index]:
                    if key == DISENGAGE_EVENT:
                        for index1 in range(len(response["Data"]["BrightnessEvents"])):
                            for key in response["Data"]["BrightnessEvents"][index1]:
                                if key == '0':
                                    test_status = True
                                    break
                        break
            if test_status:
                window["-OUTPUT-"].update("Dim On Disengage Test is passed")
            else:
                window["-OUTPUT-"].update("Dim On Disengage Test is failed")

    elif event == "-SCENARIO-":
        if values["-SCENARIO-"][0] == "Undim on Engage":
            filename = os.path.join(os.getcwd(), "Dependencies\\Undim on Engage Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update(
                "Latency from User Engaged to Display default brightness reached\nPreconditions:-\n‣ Lid open, "
                "display on, backlight dimmed to 0%, system in idle S0(unlocked)")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "By-Pass Mode":
            filename = os.path.join(os.getcwd(), "Dependencies\\By-pass Mode Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update(
                "Latency from Start at click on Camera app to Video stream appears\nPreconditions:-\n‣ Lid open, "
                "display on, system in S0(unlocked)")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "Undim on Presence":
            filename = os.path.join(os.getcwd(), "Dependencies\\Undim on Presence Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update(
                "Latency from User Face Engaged to Display default brightness reached\nPreconditions:-\n‣ Lid open, "
                "display on and backlight dimming, system in idle S0(unlocked)")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "Wake On Face and System Resume":
            filename = os.path.join(os.getcwd(), "Dependencies\\Wake On Face and System Resume Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update(
                "Latency from User In front of Camera to System Resume\nPreconditions:-\n‣ Lid open, display off, "
                "system in S0ix and locked\n‣ User outside camera field-of-view")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "Wake On Face and Windows Hello":
            filename = os.path.join(os.getcwd(), "Dependencies\\Wake On Face and Windows Hello Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0] + " (Live User)")
            window["-SCENARIODSC-"].update(
                "Latency from Motion trigger to User Login\nPreconditions:-\n‣ Lid open, display off, system in S0ix "
                "and locked\n‣ User outside camera field-of-view")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
        elif values["-SCENARIO-"][0] == "Lid Closed":
            filename = os.path.join(os.getcwd(), "Dependencies\\Lid Closed Info.png")
            window["-SCENARIOTITLE-"].update(values["-SCENARIO-"][0])
            window["-SCENARIODSC-"].update(
                "Latency from Lid close to CVF enters D3-hot state\nPreconditions:-\n‣ Lid open, system in S0")
            window["-IMAGE-"].update(filename=filename)
            window["-OUTPUT-"].update("")
    elif event == "-RUN-" and len(values["-SCENARIO-"]) != 0:
        response = []
        if values["-SCENARIO-"][0] == "Undim on Engage":
            start_cmd["NumberOfArguments"] = stop_cmd["NumberOfArguments"] = get_events_data_cmd[
                "NumberOfArguments"] = 2
            start_cmd["Arguments"] = stop_cmd["Arguments"] = get_events_data_cmd["Arguments"] = ["UserPresenceEvents",
                                                                                                 "BrightnessEvents"]
            commands = [start_cmd, stop_cmd, get_events_data_cmd]
            os.startfile("Dependencies\\Undim_On_Engage_Trim.mp4")
            thread_id = threading.Thread(target=connection_handler, args=(commands, 18, window, response,), daemon=True)
            thread_id.start()
            window.Disable()
        elif values["-SCENARIO-"][0] == "By-Pass Mode":
            get_info_cmd["NumberOfArguments"] = 1
            get_info_cmd["Arguments"] = ["ByPassModeLatency"]
            commands = [get_info_cmd]
            thread_id = threading.Thread(target=connection_handler, args=(commands, 0, window, response,), daemon=True)
            thread_id.start()
            window.Disable()
        elif values["-SCENARIO-"][0] == "Undim on Presence":
            start_cmd["NumberOfArguments"] = stop_cmd["NumberOfArguments"] = get_events_data_cmd[
                "NumberOfArguments"] = 2
            start_cmd["Arguments"] = stop_cmd["Arguments"] = get_events_data_cmd["Arguments"] = ["UserPresenceEvents",
                                                                                                 "BrightnessEvents"]
            commands = [start_cmd, stop_cmd, get_events_data_cmd]
            os.startfile("Dependencies\\Undim_On_Presence_Trim.mp4")
            thread_id = threading.Thread(target=connection_handler, args=(commands, 12, window, response,), daemon=True)
            thread_id.start()
            window.Disable()
        elif values["-SCENARIO-"][0] == "Wake On Face and System Resume":
            start_cmd["NumberOfArguments"] = stop_cmd["NumberOfArguments"] = get_events_data_cmd[
                "NumberOfArguments"] = 1
            start_cmd["Arguments"] = stop_cmd["Arguments"] = get_events_data_cmd["Arguments"] = ["StandByExitEvents"]
            commands = [start_cmd, stop_cmd, get_events_data_cmd]
            get_info_cmd["NumberOfArguments"] = 1
            get_info_cmd["Arguments"] = ["SystemTime"]
            set_info_cmd["NumberOfArguments"] = 1
            set_info_cmd["Arguments"] = {"SystemEvents": 0}
            res = execute_cmd(set_info_cmd)
            system_time = round(time.time() * 1000)
            res = execute_cmd(get_info_cmd)
            target_time = res["Data"]["SystemTime"]
            time_diff = system_time - target_time

            thread_id = threading.Thread(target=connection_handler, args=(commands, 3, window, response,), daemon=True)
            thread_id.start()
            window.Disable()
            os.startfile("Dependencies\\User_Presense.jpg")
            current_time = round(time.time() * 1000)
        elif values["-SCENARIO-"][0] == "Wake On Face and Windows Hello":
            start_cmd["NumberOfArguments"] = stop_cmd["NumberOfArguments"] = get_events_data_cmd[
                "NumberOfArguments"] = 2
            start_cmd["Arguments"] = stop_cmd["Arguments"] = get_events_data_cmd["Arguments"] = ["UserPresenceEvents",
                                                                                                 "UserLogonEvents"]
            commands = [start_cmd, stop_cmd, get_events_data_cmd]
            set_info_cmd["NumberOfArguments"] = 1
            set_info_cmd["Arguments"] = {"SecurityEvents": 0}
            res = execute_cmd(set_info_cmd)
            thread_id = threading.Thread(target=connection_handler, args=(commands, 20, window, response,), daemon=True)
            thread_id.start()
            window.Disable()
        elif values["-SCENARIO-"][0] == "Lid Closed":
            start_cmd["NumberOfArguments"] = stop_cmd["NumberOfArguments"] = get_events_data_cmd[
                "NumberOfArguments"] = 2
            start_cmd["Arguments"] = stop_cmd["Arguments"] = get_events_data_cmd["Arguments"] = ["LidClosedEvents",
                                                                                                 "CVFDisabledEvents"]
            commands = [start_cmd, stop_cmd, get_events_data_cmd]
            thread_id = threading.Thread(target=connection_handler, args=(commands, 30, window, response,), daemon=True)
            thread_id.start()
            for index in range(320):
                sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=100,
                                 grab_anywhere=False)
                time.sleep(0.1)
                continue
            sg.PopupAnimated(None)
            # window.Disable()
        elif values["-SCENARIO-"][0] == "Wake On Face":
            start_cmd["NumberOfArguments"] = stop_cmd["NumberOfArguments"] = get_events_data_cmd[
                "NumberOfArguments"] = 2
            start_cmd["Arguments"] = stop_cmd["Arguments"] = get_events_data_cmd["Arguments"] = ["UserPresenceEvents",
                                                                                                 "StandByExitEvents"]
            commands = [start_cmd, stop_cmd, get_events_data_cmd]
            set_info_cmd["NumberOfArguments"] = 1
            set_info_cmd["Arguments"] = {"SystemEvents": 0}
            res = execute_cmd(set_info_cmd)
            thread_id = threading.Thread(target=connection_handler, args=(commands, 20, window, response,), daemon=True)
            thread_id.start()
            window.Disable()
            os.startfile("Dependencies\\Undim_On_Presence_Trim.mp4")
        elif values["-SCENARIO-"][0] == "Walk Away Lock":
            start_cmd["NumberOfArguments"] = stop_cmd["NumberOfArguments"] = get_events_data_cmd[
                "NumberOfArguments"] = 2
            start_cmd["Arguments"] = stop_cmd["Arguments"] = get_events_data_cmd["Arguments"] = ["UserPresenceEvents",
                                                                                                 "StandByEntryEvents"]
            commands = [start_cmd, stop_cmd, get_events_data_cmd]
            set_info_cmd["NumberOfArguments"] = 1
            set_info_cmd["Arguments"] = {"SystemEvents": 0}
            res = execute_cmd(set_info_cmd)
            thread_id = threading.Thread(target=connection_handler, args=(commands, 25, window, response,), daemon=True)
            thread_id.start()
            window.Disable()
            os.startfile("Dependencies\\Walk_Away_Lock_Trim.mp4")
        elif values["-SCENARIO-"][0] == "Undim On Engage(Functional)":
            start_cmd["NumberOfArguments"] = stop_cmd["NumberOfArguments"] = get_events_data_cmd[
                "NumberOfArguments"] = 2
            start_cmd["Arguments"] = stop_cmd["Arguments"] = get_events_data_cmd["Arguments"] = ["UserPresenceEvents",
                                                                                                 "BrightnessEvents"]
            commands = [start_cmd, stop_cmd, get_events_data_cmd]
            os.startfile("Dependencies\\Undim_On_Engage_Trim.mp4")
            thread_id = threading.Thread(target=connection_handler, args=(commands, 25, window, response,), daemon=True)
            thread_id.start()
            window.Disable()
        elif values["-SCENARIO-"][0] == "Dim On Disengage(Functional)":
            start_cmd["NumberOfArguments"] = stop_cmd["NumberOfArguments"] = get_events_data_cmd[
                "NumberOfArguments"] = 2
            start_cmd["Arguments"] = stop_cmd["Arguments"] = get_events_data_cmd["Arguments"] = ["UserPresenceEvents",
                                                                                                 "BrightnessEvents"]
            commands = [start_cmd, stop_cmd, get_events_data_cmd]
            os.startfile("Dependencies\\Dim_On_Disengage_Trim.mp4")
            thread_id = threading.Thread(target=connection_handler, args=(commands, 25, window, response,), daemon=True)
            thread_id.start()
            window.Disable()

    event = None
    values = None

if ws.connected:
    ws.close()
# Finish up by removing from the screen
window.close()
