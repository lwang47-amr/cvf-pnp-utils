import os
import sys
import re
import subprocess
import glob
import getopt
import getpass
import wmidevicemanager as wmi


#r'C:\Users\Local_Admin\Documents\IVSC-1.2.3.569-x64-Release',
#r'C:\Users\Local_Admin\Documents\D21USB-1.0.1.183'

INSTALL_DIR=[r'C:\Users\Local_Admin\Documents\IVSC-preprod-2004',
        r'C:\Users\Local_Admin\Documents\D21USB-preprod-3003']

ENUM_DEVICE = ['Instance ID', 'Device Description', 'Class Name', 'Class GUID', 
        'Manufacturer Name', 'Status', 'Driver Name']
D0_IID    = ENUM_DEVICE[0] 
D0_DESC   = ENUM_DEVICE[1]
D0_CNAME  = ENUM_DEVICE[2]
D0_CGUID  = ENUM_DEVICE[3]
D0_MANUNF = ENUM_DEVICE[4]
D0_STATUS = ENUM_DEVICE[5]
D0_DRIVER = ENUM_DEVICE[6]
enum_dev_dict = {D0_IID: [], D0_DESC:[], D0_CNAME: [], D0_CGUID: [], D0_MANUNF: [], 
        D0_STATUS: [], D0_DRIVER: [] } 

ENUM_DRIVER = ['Published Name', 'Original Name', 'Provider Name', 'Class Name',
        'Class GUID', 'Driver Version', 'Signer Name']
D1_PUBLISH  = ENUM_DRIVER[0] 
D1_OIRIGIN  = ENUM_DRIVER[1]
D1_PROVIDER = ENUM_DRIVER[2]
D1_CLASS    = ENUM_DRIVER[3]
D1_GUID     = ENUM_DRIVER[4]
D1_DRIVER   = ENUM_DRIVER[5]
D1_SIGNER   = ENUM_DRIVER[6]
enum_drv_dict = {D1_PUBLISH: [], D1_OIRIGIN:[], D1_PROVIDER: [], D1_CLASS: [], D1_GUID: [], 
        D1_DRIVER: [], D1_SIGNER: [] } 

HWID = ['INTC1059',    'INTC1058',    'INTC1074',    'INTC1075',    'INTC1091',
        'INTC1095',    'INTC1094',    'INTC1096',    'INTC1097',    'INTC1098',
        'INTC100A',    'INTC1009',    'INTC100B',    'INTC100C',    'INTC100D']

# https://support.microsoft.com/en-us/topic/error-codes-in-device-manager-in-windows-524e9e89-4dee-8883-0afa-6bca0456324e
dev_manager_error = {
        1  : "This device is not configured correctly. (Code 1)",
        3  : "The driver for this devicemight be corrupted…  (Code 3)",
        9  : "Windows cannot identify this hardware…  (Code 9)",
        10 : "This device cannot start. (Code 10)",
        12 : "This device cannot find enough free resources that it can use... (Code 12) ",
        14 : "This device cannotwork properly until you restart your computer. (Code 14)",
        16 : "Windows cannot identify all the resources this device uses. (Code 16)",
        18 : "Reinstall the drivers for this device. (Code 18)",
        19 : "Windows cannot start this hardware device…  (Code 19)",
        21 : "Windows is removing this device...(Code 21)",
        22 : "This device is disabled. (Code 22)" ,
        24 : "This device is notpresent, is not working properly…  (Code 24)",
        28 : "The drivers for this device are not installed. (Code 28)",
        29 : "This device is disabled...(Code 29)",
        31 : "This device is not working properly...(Code 31)",
        32 : "A driver (service) for this device has been disabled. (Code 32)",
        33 : "Windows cannot determinewhich resources are required for this device. (Code 33)",
        34 : "Windows cannot determine the settings for this device... (Code 34)",
        35 : "Your computer's system firmware does not…  (Code 35)",
        36 :  "This device is requesting a PCI interrupt…  (Code 36)",
        37 : "Windows cannot initialize the device driver for this hardware. (Code 37)",
        38 : "Windows cannot load the device driver…  (Code 38)",
        39 : "Windows cannot load the device driver for this hardware... (Code 39).",
        40 : "Windows cannot access this hardware…  (Code 40)",
        41 : "Windows successfully loaded the device driver…  (Code 41)",
        42 : "Windows cannot load the device driver…   (Code 42)",
        43 : "Windows has stopped this device because it has reported problems. (Code 43)",
        44 : "An application or service has shut down this hardware device. (Code 44)",
        45 : "Currently, this hardware device is not connected to the computer... (Code 45)",
        46 : "Windows cannot gain accessto this hardware device…  (Code 46)",
        47 : "Windows cannot use this hardware device…  (Code 47)",
        48 : "The software for this device has been blocked…  (Code 48).",
        49 : "Windows cannot start new hardware devices…  (Code 49).",
        50 : "Windows cannot apply all of the properties for this device... (Code 50)",
        51 : "This device is currently waiting on another device…  (Code 51).",
        52 : "Windows cannot verify the digital signature for the drivers required for this device. (Code 52)",
        53 : "This device has been reserved for use by the Windows kernel debugger... (Code 53)",
        54 : "This device has failed and is undergoing a reset. (Code 54)",
        }




def enum_from_file(fname):

    with open(fname, 'rb') as f:
        raw_data = f.read()

    #bytes_data = raw_data.decode('iso-8859-1')
    return 0, "".join(map(chr, raw_data))

def run_cmd(cmd_list):

    ret = subprocess.run(cmd_list, 
                  shell=True, stdout=subprocess.PIPE, universal_newlines=True)

    return ret.returncode, ret.stdout


def run_powershell(full_cmd):

    ret = subprocess.run(["C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", full_cmd],
                  shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    return ret.returncode, ret.stdout


def show_Win32_PnPEnty(dev):

    print('   CVF/MCF Yellow Band')
    print('   -------------------  ', '-'*40)
    print('      Name              ', dev.Name)
    print('      Manufacturer      ', dev.Manufacturer)
    print('      DeviceID          ', dev.DeviceID)
    try:
         print('      HWID              ', dev.DeviceID.split('\\')[1])
    except KeyError as e:
         print('      HWID                N/A')

    print('      Service           ', dev.Service)
    print('      Status            ', dev.Status)
    print('      ErrorCode         ', dev.ConfigManagerErrorCode)
    try:
        print('      Desc              ', dev_manager_error[dev.ConfigManagerErrorCode])
    except KeyError as e:
        print('      Desc              Error code {} not definied'.format(dev.ConfigManagerErrorCode))
    print()
    return



def check_yellow_bang():

    print('ERROR DEVICES')
    yb_list = wmi.yellow_bang_devices()
    if len(yb_list) == 0:
        print('Total of Yellow Bang Devices Detected: ', len(yb_list))
        return 0

    # Only look for devices we're interested
    others=[]
    for dev in yb_list:

        # dev.Name can be NoneType 
        if dev.Name and 'OV01A1S' in dev.Name:
            show_Win32_PnPEnty(dev)
        elif dev.Name and 'Camera Flash LED' in dev.Name:
            show_Win32_PnPEnty(dev)
        else:
            try:
               id = dev.DeviceID.split('\\')[1]
               if id in HWID:
                   show_Win32_PnPEnty(dev)
               else:
                   # Keep them for other uses...
                   others.append(f'{dev.Name} {id}')
            except:
                continue

    if len(others):
        print('   Non CVF/MCF YB')
        print('   -------------------  ')
        for line in others:
             print('   ', line)
    print('Total of Yellow Bang Devices Detected: ', len(yb_list))

    return len(yb_list)





def convert_enum_devices(lines):

    global enum_dev_dict
    lines = lines.replace('\r','').split('\n')

    for i in range(0, len(lines)):
        if lines[i].startswith(D0_IID) is True:
            inst = lines[i].split(':')[1].strip()
            enum_dev_dict[D0_IID].append(inst)

            # Make default N/A
            for key in (D0_DESC, D0_CNAME, D0_CGUID, D0_MANUNF, D0_STATUS, D0_DRIVER):
                enum_dev_dict[key].append('N/A')   

            # Find all data of this name
            pos = i+1
            while (pos < len(lines)) and not (D0_IID in lines[pos]):
                pos += 1

            # Fill all data items
            for j in range(i+1, pos):
                for key in (D0_DESC, D0_CNAME, D0_CGUID, D0_MANUNF, D0_STATUS, D0_DRIVER):
                    if key in lines[j]:
                        enum_dev_dict[key].pop()
                        contents = lines[j].split(':')[1].strip()
                        enum_dev_dict[key].append(contents)
    
    return enum_dev_dict


def convert_enum_drivers(lines):

    global enum_drv_dict
    lines = lines.replace('\r','').split('\n')

    for i in range(0, len(lines)):
        if lines[i].startswith(D1_PUBLISH) is True:
            publish = lines[i].split(':')[1].strip()
            enum_drv_dict[D1_PUBLISH].append(publish)

            # Make default N/A
            for key in (D1_OIRIGIN, D1_PROVIDER, D1_CLASS, D1_GUID, D1_DRIVER, D1_SIGNER):
                enum_drv_dict[key].append('N/A')

            # Find all data of this name
            pos = i+1
            while (pos < len(lines)) and not ("Published Name" in lines[pos]):
                pos += 1

            # Fill all data items
            for j in range(i+1, pos):
                for key in (D1_OIRIGIN, D1_PROVIDER, D1_CLASS, D1_GUID, D1_DRIVER, D1_SIGNER):
                   if key in lines[j]:
                       enum_drv_dict[key].pop()
                       contents = lines[j].split(':')[1].strip()
                       enum_drv_dict[key].append(contents)

    return enum_drv_dict



def dump_enum_dict(dictionary, flags=None):

    pkey = next(iter(dictionary))   # Get first key 
    print('Dump Dictionary')
    for i in range(0, len(dictionary[pkey])):
        for key in dictionary.keys():
            print('    %-20s : %s' % (key, dictionary[key][i]))
        print()

    for key in dictionary.keys():
        print('    # of %-20s %d' % (key, len(dictionary[key])))

    return



def search_dictionary(dictionary, key, name):

    try:
        pos = dictionary[key].index(name)
        #print(f'Search {key} for {name}')
        for key in dictionary.keys():
            print('      %-20s : %s' % (key, dictionary[key][pos]))
    except ValueError:
        print(f'{name} is NOT found in {key}!')
        return -1

    return pos

def do_install(dirs):

    print('Install drivers in ', dirs)
    for package in dirs:
        for root,dir,files in os.walk(package):
            for name in files:
                if name == 'ivsc.bat':
                    print('   ', os.path.join(root,'ivsc.bat'))
                    cwd = os.getcwd()
                    os.chdir(root)
                    ret, raw = run_cmd(['ivsc.bat'])
                    print('---> ', raw)
                    os.chdir(cwd)
                if name == 'd21usb.bat':
                    print('   ', os.path.join(root,'d21usb.bat'))
                    cwd = os.getcwd()
                    os.chdir(root)
                    ret, raw = run_cmd(['d21usb.bat'])
                    os.chdir(cwd)
                    print('===> ', raw)
                    
    return 0





def do_ivsctest(dirs=None):

    ivsvtest_dir = None
    #print('IVSCTest: dir is', dirs)

    for package in dirs:
        for root,dir,files in os.walk(package):
            #x = lambda files: [s for s in files if s == 'IVSCTest.exe'] 
            #app = x(files)
            #if len(app):
            #    print(app)

            for name in files:
                if name == 'IVSCTest.exe':
                   ivsctest_dir = root
                   break
        if ivsctest_dir:
            break
                    
    print('-' * 60)
    #print('FW: found ', ivsctest_dir)
    cwd = os.getcwd()
    os.chdir(ivsctest_dir)
    ret, raw = run_cmd(['IVSCTest.exe', '/debugAceGetFwVersion'])
    print(f'*** IVSCTest.exe /debugAceGetFwVersion ***\n\n{raw}')

    ret, raw = run_cmd(['IVSCTest.exe', '/debugPseGetFwVersion'])
    print(f'*** IVSCTest.exe /debugPseGetFwVersion ***\n\n{raw}')
    os.chdir(cwd)
    print()
    
    return




# INSTALL: SpiOed -> IshHeci -> IVSC -> UsbBridge -> UsbGpio -> UsbI2c -> UsbSpi

UNINSTALL_HWID = {
        'UsbSpi'   : 'INTC1098', 
        'UsbI2c'   : 'INTC1097',
        'UsbGpio'  : 'INTC1096',
        'UsbBridge': '0B63',  
        'IVSC'     : 'INTC1095', 
        'IshHeci'  : 'ISH_HECI', 
        'SpiOed'   : 'INTC1094'} 

optd = {'list': False, 'install': False, 'uninstall': False, 'dir':[], 'yb': False, 'firmware': False}

def get_options():

    global optd
    try:
        #opts, args = getopt.getopt(sys.argv[1:], "hluyi:", ["help", "list", "yb", "install", "uninstall"])
        opts, args = getopt.getopt(sys.argv[1:], "hluyif", ["help", "list", "yb", "install", "uninstall", "fw"])
        for name, val in opts:
            if name in ('-h', '-?', '--help'):
                print('Usage: {} [-h] [-l|--list] [-i|--install] [-u|--uninstall] [-y|--yb] [-f|--firmware]'.format(sys.argv[0]))
            if name in ('-l', '--list'):
                optd['list'] = True
            if name in ('-i', '--install'):
                optd['install'] = True
                #optd['dir'] = val.split(',')
                optd['dir'] = INSTALL_DIR
            if name in ('-u', '--uninstall'):
                optd['uninstall'] = True
            if name in ('-f', '--uninstall'):
                optd['dir'] = INSTALL_DIR
                optd['firmware'] = True
            if name in ('-y', '--yb', '--yellow-bang'):
                optd['yb'] = True
    except getopt.GetoptError:
        print('Unknown or unsupport options')
        sys.exit()
    return


def main():

    get_options()

    if optd['yb'] is True:
        rc = check_yellow_bang()
        sys.exit(rc)

    if optd['install'] is True:
        do_install(optd['dir'])

    if optd['firmware'] is True:
        # IVSCTest /debugAceGetFwVersion
        # IVSCTest /DebugPseGetFwVersion
        do_ivsctest(optd['dir'])

    if optd['list'] is True or optd['uninstall'] is True:
        uninstall = []
        _, raw = run_powershell(r'pnputil /enum-devices /connected')
        #_, raw = enum_from_file('x.1')    # //enum-devices
        assert len(raw) > 1 and isinstance(raw, str)

        enum_dev_dict = convert_enum_devices(raw)
        #dump_enum_dict(enum_dev_dict, False)

        _, raw = run_powershell(r'pnputil /enum-drivers')
        convert_enum_drivers(raw)
        #dump_enum_dict(enum_drv_dict, False)
        assert len(raw) > 1 and isinstance(raw, str)
               
        # Get full name from Uninstall HWID list
        for key, val in UNINSTALL_HWID.items():

            full_name = [s for s in enum_dev_dict[D0_IID] if val in s]
            for i in range(0, len(full_name)):
                print(f'   {val} ({key}) : {full_name}')
                print('   Device')
                pos = search_dictionary(enum_dev_dict, D0_IID, full_name[i])
                
                if pos >= 0:
                   #print(enum_dev_dict[D0_IID][pos], enum_dev_dict[D0_STATUS][pos], enum_dev_dict[D0_DRIVER][pos])
                   print('   Driver')
                   search_dictionary(enum_drv_dict, D1_PUBLISH, enum_dev_dict[D0_DRIVER][pos])

                   cmd = r'pnputil /delete-driver {} /uninstall /force'.format(enum_dev_dict[D0_DRIVER][pos]) 
                   #print('For %-10s(%-8s): %s' % (key, val, cmd))

                   uninstall.append(['For %-10s(%-8s):' % (key, val), cmd])
                print()


    if optd['uninstall'] is True:
        print('Uninstall')
        for c in uninstall:
            print('   ', c[0], c[1])
            run_powershell(c[1])

    return

if __name__ == '__main__':
    main()




