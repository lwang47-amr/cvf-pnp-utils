#! python
import os, sys
import subprocess
import getopt
import winreg
sys.path.append(r'C:\Users\Local_Admin\test')
import devmgr

ro_optd = {'force': False, 'error': 3, 'install': True, 'uninstall': True, 'reboot': False}
COUNTER_FILE = r'C:\Users\{}\test\cnt.txt'.format(os.environ.get('USERNAME'))
STATUS_FILE  = r'C:\Users\{}\test\status.txt'.format(os.environ.get('USERNAME'))
DEVMGR       = r'C:\Users\Local_Admin\test\devmgr.py'


def run_cmd(cmd_list):

    ret = subprocess.run(cmd_list,
                    shell=True, stdout=subprocess.PIPE, universal_newlines=True)

    return ret.returncode, ret.stdout


def set_run_key(key, value):

    reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                        r'Software\Microsoft\Windows\CurrentVersion\RunOnce',
                        0, 
                        winreg.KEY_SET_VALUE)
    with reg_key:
        if value is None:
            try:
                winreg.DeleteValue(reg_key, key)
            except FileNotFoundError:
                print(r'No value to delete in Software\Microsoft\Windows\CurrentVersion\RunOnce')
                pass
        else:
            if '%' in value:
                var_type = winreg.REG_EXPAND_SZ
            else:
                var_type = winreg.REG_SZ
            winreg.SetValueEx(reg_key, key, 0, var_type, value)


def latest_status(status = None):

    if status is None:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                  return f.read()
    else:    
         with open(STATUS_FILE, 'w+') as f:
               f.write(status)

    return None


def add_counter():

    try:
       with open(COUNTER_FILE, 'r') as f:
            cnt = int(f.read())
    except FileNotFoundError:
       cnt = 0

    cnt += 1
    with open(COUNTER_FILE, 'w+') as f:
            f.write(str(cnt))
    return cnt


def get_options():

    global ro_optd
    try:
       opts, args = getopt.getopt(sys.argv[1:], "hiadfyiue:", 
               ["help", "init", "add", "del", "force", "yb", "install", "uninstall", "error"])
       for name, val in opts:
           if name in ('-h', '-?', '--help'):
               print('Usage: {} [-h] [-f|--force] [-y|--yb] [-e|--err n]'.format(sys.argv[0]))
               print('Where')
               print('       -i | --init       initialize counter and set status to installed')
               print('       -a | --add        add RunOnce registry entry')
               print('       -d | --del        delete RunOnce registry entry')
               print('       -f | --force      force reboot without user input')
               print('       -i | --install    install')
               print('       -u | --uninstall  uninstall')
               print('       -y | --yb         check YB devices')
               print('       -e | --error n    max number or yellow-bang devices accepted, or stop execution')
               print('\n\n')
               sys.exit(0)
           if name in ('-f', '--force'):
               ro_optd['force'] = True
           if name in ('-i', '--init'):
               try:
                  os.remove(COUNTER_FILE)
               except FileNotFoundError:
                  pass
               latest_status(status = 'installed')
               print('counter initailized and status set to INSTALLED')
               sys.exit(0)
           if name in ('-a', '--add'):
               cmd = r'%windir%\system32\cmd.exe /c "python {}"'.format(__file__)
               set_run_key('MyCvfCmd', cmd)
               print(r'RunOnce MyCvfCmd added in Software\Microsoft\Windows\CurrentVersion\RunOnce')
               sys.exit(0)
           if name in ('-d', '--del'):
               set_run_key('MyCvfCmd', None)
               print(r'RunOnce MyCvfCmd removed from Software\Microsoft\Windows\CurrentVersion\RunOnce')
               sys.exit(0)
           if name in ('-e', '--error'):
               ro_optd['error'] = int(val)
           if name in ('-y', '--yb'):
               devmgr.check_yellow_bang()
               sys.exit()
           if name in ('-i', '--install'):
               devmgr.do_install(devmgr.INSTALL_DIR)
               latest_status(status = 'installed')
               sys.exit()
           if name in ('-u', '--uninstall'):
               os.system('python devmgr.py --uninstall')
               latest_status(status = 'uninstalled')
               sys.exit()

    except getopt.GetoptError:
        print('Unknown option! Use -h for usage')
    return


def main():

    get_options()
    print('get_opt: ', ro_optd)

    while True:
       rc = add_counter()
       status = latest_status()
       x = input('\n[STATUS] Latest counter {} and status {}. Press any key to continue...'.format(rc, status))

       # Uninstall - TBD: should do from py, not shell
       if ro_optd['uninstall'] and status == 'installed':
           os.system('python {} --uninstall'.format(DEVMGR))
           latest_status(status = 'uninstalled')
           # Reboot
           ans = input('\n[UNINSTALLED] Enter any key to reboot & install, or "STOP" to stop RunOnce and exit...')
           if ans == 'STOP':
              set_run_key('MyCvfCmd', None)
              sys.exit()
           else:
              cmd = r'%windir%\system32\cmd.exe /c "python {}"'.format(__file__)
              set_run_key('MyCvfCmd', cmd)
              os.system('shutdown /r /t 0')

       # Install IVSC and D21 Drivers
       if ro_optd['install'] and status == 'uninstalled':
           devmgr.do_install(devmgr.INSTALL_DIR)
           latest_status(status = 'installed')

           # Check YB devices
           rc = devmgr.check_yellow_bang()
 
           x = input('\n[INSTALLED] YB check - found {}, max allowance {}. Press any key to continue...'.format(
               rc, ro_optd['error']))
           if rc >= ro_optd['error']:
               print('YB Checking ERROR!!!')
               sys.exit(rc)

    return

if __name__ == '__main__':

    main()

