
import getopt
import os, sys
import pandas as pd
import matplotlib.pyplot as plt

title = None
file = None


def do_plot():

    if file is None:
        print('No file assigned!')
        sys.exit(0)

    data = pd.read_csv(file)
    fig, ax = plt.subplots(figsize=(10,5))

    n = len(data['P_CVF'])
    CVF = data['P_CVF'] * 1000
    CAM = data['P_CAM'] * 1000
    print('*' * 40)
    print(f'   {title} - {n} samples')
    print()
    print('CVF Mean (in mW):', CVF.mean())
    print('CVF Std dev     : %5.2f' %(CVF.std()))
    print()
    print('Camera Mean (in mW):',  CAM.mean())
    print('Camera Std dev     : %5.2f ' % (CAM.std()))
    print('*' * 40)
    ax.scatter([i for i in range(0,n)], CVF, label='cvf', marker='o', s=1)
    ax.scatter([i for i in range(0,n)], CAM, label='cam', marker='o', s=1)
    plt.title(title, fontsize=12)
    plt.xlabel('ticks')
    plt.ylabel('mWatt')
    t0='CVF    (Avg %5.2f mw)' % (CVF.mean())
    t1='Camera (Avg %5.2f mW)' % (CAM.mean())
    plt.legend([t0, t1], fontsize=10, scatterpoints=1,loc='upper right')
    plt.ylim([0,300])
    plt.show()
    return


def get_option():

    global title, file
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h01234",['help', 'zero', 'one', 'two', 'three', 'four', 'five'])
        for name, val in opts:
            if name in ('-h', '-?', '--help'):
                print('Usage: {} [-1] [-2] [-3|-4|-5]')
                print('Where:')
                print('     -0  Mixed (experiment)')
                print('     -1  Pass Thru')
                print('     -2  No Lock On Presence')
                print('     -3  Wake on Face (LP5 R1)')
                print('     -4  Dim on Disengage (LP5 R1)')
                print('     -5  Lid Close CS\n\n')
                sys.exit(0)
            if name in ('-0'):
                title = 'Mixed Scenario'
                file  = r'Z:\PnP\mixed\mixed_math-traces.csv'

            if name in ('-1'):
                title = 'Pass Thru'
                file  = r'Z:\PnP\pass_thru\pass_thru_math-traces.csv'
            if name in ('-2'):
                title = 'No Lock On Presence'
                file = r'Z:\PnP\no_lock_on_presence\no_lock_on_presence_math-traces.csv'
                #file = r'Z:\PnP\xx90\xx90_math-traces.csv'
            if name in ('-3'):
                title = 'Wake on Face'
                file = r'Z:\PnP\wake_on_face\wake_on_face_math-traces.csv'
            if name in ('-4'):
                title = 'Dim on Disengage'
                file = r'Z:\PnP\dim_on_disengage\dim_on_disengage57_math-traces.csv'
            if name in ('-5'):
                print('-5: Not Implemented')
    except getopt.GetoptError as e:
        print("Option unknown or unsupported! Use -h for usage")
        sys.exit()
    
    return


def main():

    get_option()
    do_plot()
    sys.exit(0)
 

if __name__ == '__main__':
    main()
