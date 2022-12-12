import serial    # pip install serial pyserial
import os, sys
import getopt
import time
import yaml

# My laptop: com5
# NUC      : com4 for RVP
# NUC      : com3 for DUMMY
comports = {'DUMMY': {'name': 'DUMMY', 'port': 'com3', 'fd': None, 'zeroed': None, 'pos': None},
            'RVP':   {'name': 'RVP',   'port': 'com4', 'fd': None, 'zeroed': None, 'pos': None}} 


def open_all_ports():

    global comports

    for curr in (comports['DUMMY'], comports['RVP']):
        try:
            curr['fd'] = serial.Serial(curr['port'], 115200, timeout=1)
            print('open_all_ports: openning port', curr['port'])
            set_and_wait_for_ok(curr, 'CT();')
            print('   CT Init(0)')
            set_and_wait_for_ok(curr, 'CT+HEARTBEAT(0);')
            print('   HeartBeat(0)')
            set_and_wait_for_ok(curr, 'CT+SETPAUSETIME(0);')
            print('   SetPauseTime(0)')
            set_and_wait_for_ok(curr, 'CT+SETZERO();', True)
            print('   SetZero() and done with initalization')
        except: #  FileNotFoundError 
            print('Error in open serial port!', curr)
    return 


def close_all_ports():
    for curr in (comports['DUMMY'], comports['RVP']):
        try:
            print('close_all_ports: closing port', curr['port'], 'and wait for completion...')
            zero_and_wait_for_completion(curr)
            curr['fd'].close()
            curr['zeroed'] = None
            curr['pos'] = None
            print('   port close complete')
        except:
            pass

    return


def set_and_wait_for_ok(current, command, zeroed=False):

    fd = current['fd']
    fd.write(command.encode())

    # Simple set commands only return CR+OK;
    while True:
        buffer = fd.readline()
        if 'CR+OK;' in buffer.decode('utf-8'):
            break
    current['zeroed'] = zeroed
    return 



def zero_and_wait_for_completion(curr):

    fd = curr['fd']
    fd.write('CT+TOZERO();'.encode())

    # In zero position, we'll only get a CR+OK
    # In non-zero position, we'll get a CR+OK, then CR+EVENT=TB_END once completed
    if curr['zeroed']:
        while True:
            buffer = fd.readline()
            if 'CR+OK;' in buffer.decode('utf-8'):
                break
    else:
        while True:
            buffer = fd.readline()
            if 'CR+EVENT=TB_END;' in buffer.decode('utf-8'):
               break

    # Now we're zeroed
    curr['zeroed'] = True

    return True



def turn_and_wait_for_completion(curr, command):

    fd = curr['fd']
    fd.write(command.encode())

    while True:
        buffer = fd.readline()
        if 'CR+EVENT=TB_END;' in buffer.decode('utf-8'):
            break

    # Now we're non-zeroed
    curr['zeroed'] = False
    return


def menu(curr):

    if curr is None:
        print('Command Examples:')
        print('    go dummy   - Switch to dummy control')
        print('    go rvp     - Switch to rvp control')
        print('    dump       - Show all com ports status')
        print('    q|quit     - Quit & Exit')
        data = input("[MAIN] ").split(' ')
    elif curr['name'] == 'DUMMY' and curr['fd'] != None:
        print('Comand Examples')
        print('    r n|45     - Turn right n or 45 degree')
        print('    l n|30     - Turn left n or 30')
        print('    0          - Turn back to 0')
        print('    set        - Reset current position as zero')
        print('    dump       - Dumy current port status')
        print('    main       - Go back to previous top menu')
        print('    q|quit     - Quit & exit')
        data = input("[DUMMY] ").split(' ')
    elif curr['name'] == 'RVP' and curr['fd'] != None:
        print('Command Examples:')
        print('    r n|45     - Turn right n or 45 degree')
        print('    l n|30     - Turn left n or 30')
        print('    0          - Turn back to 0')
        print('    set        - Reset current position as zero')
        print('    2d         - Set RVP to 2D (zero degree)')
        print('    3d         - Set RVP to 3D (90 right degree)')
        print('    dump       - Dumy current port status')
        print('    q|quit     - Quit & exit')
        data = input("[RVP] ").split(' ')

    return data


def main():

    open_all_ports()

    curr = None
    while True:
        # [[-37, +37]] Present 
        # [[-52,-90],[52,90]]  Disengaged
        # [[90,180],[-90,-180] Absence
        
        # Usage
        data = menu(curr)

        if len(data[0]) == 0:
            continue  

        # Quit
        if data[0] == 'q' or data[0] == 'quit':
            break;

        # Show current
        if data[0] == 'dump':
            print('DUMP... comports\n', comports)
            print('DUMP... current\n', curr)

        # open
        if data[0] == 'go' or data[0] == 'open' and len(data) > 1:
            try:
                curr = comports[data[1].upper()] 
                # Make sure the current fd is opened okay
                if curr['fd'] == None:
                    curr = None
            except:
                print('Cannot go switch to', data[1])

        
        if data[0] == 'main':
            curr = None

        if curr is None:
            continue
     
        # Current is either dummy or rvp port
        # Common command
        if data[0] == 'set':  # Set & Initialize
            set_and_wait_for_ok(curr, 'CT+SETZERO();', True)

        elif data[0] == '0':  # Zero
            zero_and_wait_for_completion(curr)

        elif data[0] == 'r' and len(data) > 1: # 1: right (counter clockwise)
            cmd = 'CT+TRUNSINGLE({},{});'.format(1, float(data[1]))
            turn_and_wait_for_completion(curr, cmd)

        elif data[0] == 'l' and len(data) > 1: # 0: left (clockwise)
            cmd = 'CT+TRUNSINGLE({},{});'.format(0, float(data[1]))
            turn_and_wait_for_completion(curr, cmd)
        else:
            pass

        # RVP only
        if curr['name'] == 'RVP':      
            if data[0] == '2d':
                if curr['pos'] != '2d':
                    zero_and_wait_for_completion(curr)
                    curr['pos'] = '2d'
            elif data[0] == '3d':
                if curr['pos'] != '3d':
                    zero_and_wait_for_completion(curr)
                    turn_and_wait_for_completion(curr, 'CT+TRUNSINGLE(1, 90.0);')   # 1: right 
                    curr['pos'] = '3d'

        # Dummy only
        elif curr['name'] == 'DUMMY':
            if data[0] == 'presence':    # Presence
                zero_and_wait_for_completion(curr)
                turn_and_wait_for_completion(curr, 'CT+TRUNSINGLE(0,30);')

            elif data[0] == 'disengage':  # Disangagei 60
                zero_and_wait_for_completion(curr)
                turn_and_wait_for_completion(curr, 'CT+TRUNSINGLE(0,60);')

            elif data[0] == 'walk-away':  # Walk away 180
                zero_and_wait_for_completion(curr)
                turn_and_wait_for_completion(curr, 'CT+TRUNSINGLE(0,180);')
    
        continue  # end of while





    close_all_ports()
    return


if __name__ == "__main__":
    main()



