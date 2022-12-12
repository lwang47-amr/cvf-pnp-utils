
import getopt
import os, sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path, PureWindowsPath

log_files = ['./LOGS/pass_thru_math-traces.csv']

Latency = {'by-pass mode': 1039 }

COLOR0='violet'
COLOR1='skyblue'
COLOR2='darkolivegreen'
COLOR3='navy'

def plot_one(title, file, ofile):

    data = pd.read_csv(PureWindowsPath(file))
    fig, ax = plt.subplots(figsize=(8,4))
    ax.xaxis.grid(b=False, which='major', color='gray', linestyle='--')

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
    ax.scatter([i for i in range(0,n)], CVF, label='cvf', marker='o', s=1, color=COLOR0)
    ax.scatter([i for i in range(0,n)], CAM, label='cam', marker='o', s=1, color=COLOR1)
    ax.plot([0,n], [CVF.mean(), CVF.mean()], linewidth=1.5, color=COLOR2)
    ax.plot([0,n], [CAM.mean(), CAM.mean()], linewidth=1.5, color=COLOR3)
    plt.title(title, fontsize=12)
    plt.xlabel('ticks')
    plt.ylabel('mWatt')
    t0='CVF    (Avg %5.2f mw)' % (CVF.mean())
    t1='Camera (Avg %5.2f mW)' % (CAM.mean())
    plt.legend(['CvfAvg', 'CamAvg', t0, t1], fontsize=10, scatterpoints=1,loc='upper right')
    plt.ylim([0,300])
    plt.axis([0, n ,0, 300])   # [xmin, xmax, ymin, ymax]
    if ofile:
        plt.savefig(PureWindowsPath(ofile), dpi=80)
        print('saving file...', ofile)
    else:
        plt.show()
    return


def plot_latency():

    fig, ax = plt.subplots()

    ypos = np.arange(4) 
    width=0.2   # Bar width
    hbar1 = plt.barh(ypos, [100, 110, 90, 103], width, align='center')
    ax.invert_yaxis()
    plt.xlabel('ms', fontsize=10, style='italic')  # Only show x-label in fig-1 to save space
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.set_yticks(ypos+width-0.2)
    ax.set_yticklabels(('one', 'two', 'three', 'four'))
    plt.show()


def autolabel_stack(ax, rects, fontsize=10):
    """
    Attach a text label above each bar displaying its height
    """
    i=0
    for rect in rects:
        length = rect.get_width()
        ax.text(length/2,
                rect.get_y() + 0.08,
                '%d' % int(length),
                horizontalalignment ='center',
                verticalalignment ='top',
                fontsize=fontsize,
                rotation=0,
                color='lightyellow')
        i+=1
    return


def plot_all():

    global log_files
    subplot = [311, 323, 324, 325, 326]   # nRow, nCol, n-th
    
    all_buffer = []
    plt.figure(figsize=(18,10))
    for i in range(0,5):
        try:
            buf = pd.read_csv(log_files[i])
            all_buffer.append(buf)
        except:
            all_buffer[i].append(None)

    for i in range(0, 5):
        #fig, ax = plt.subplots(3,2)   # plt.subplot(subplot[i])
        ax = plt.subplot(subplot[i])
        if i > 0:

            data = all_buffer[i]
            n = len(data['P_CVF'])
            CVF = data['P_CVF'] * 1000
            CAM = data['P_CAM'] * 1000
            t0  = 'CVF    (Avg %5.2f mw)' % (CVF.mean())
            t1  = 'Camera (Avg %5.2f mW)' % (CAM.mean())
            ax.scatter([k for k in range(0,n)], CVF, label='cvf', marker='o', s=1, color=COLOR0)
            ax.scatter([k for k in range(0,n)], CAM, label='cam', marker='o', s=1, color=COLOR1)
            ax.plot([0,n], [CVF.mean(), CVF.mean()], color=COLOR2, linewidth=1.5)
            ax.plot([0,n], [CAM.mean(), CAM.mean()], color=COLOR3, linewidth=1.5)
            ax.set_title(log_files[i].split('/')[1] + ' power', fontweight='bold')
            #plt.xlabel('ms', fontsize=10, style='italic')  # Only show x-label in fig-1 to save space
            ax.set_ylabel('mWatt', fontsize=10)

            ax.legend(['CvfAvg', 'CamAvg', t0, t1], fontsize=8, scatterpoints=1, loc='upper right')
            #ax.ylim([0, 300])
            ax.axis([0, n ,0, 300])   # [xmin, xmax, ymin, ymax]
            if i > 3:
                ax.set_xlabel('samples', fontsize=10)
        else:
            ypos = np.arange(4)
            print('ypos = ', ypos)
            width=0.4   # Bar width
            hbar1 = plt.barh(ypos, [v for v in Latency.values()], width, align='center')
            ax.invert_yaxis()
            plt.xlabel('ms', fontsize=10, style='italic')  # Only show x-label in fig-1 to save space
            ax.xaxis.grid(b=False, which='major', color='gray', linestyle='--')
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.set_title('Latency',  fontweight='bold')
            ax.set_yticks(ypos+width - 0.4)   # Move up by offset 0.4
            ax.set_yticklabels(([k for k in Latency.keys()]))
            lefts_01 = [0]*len(ypos)
            autolabel_stack(ax=ax, rects = hbar1, fontsize=12)

    plt.show()
    return


def get_option():

    title = "PnP Power"
    file = None
    ofile = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:t:o:",['help', 'file', 'title', 'output'])
        for name, val in opts:
            if name in ('-h', '-?', '--help'):
                print('Usage: ')
                print('    python pnp_plot.py -t title -f file -o file.pnp')
                print('Example:')
                print(r'    python pnp_plot.py -t "ByPass Mode" -f "C:\tmp\LOGS\2022-7-28\ByPass-094342\ByPass-094342_summary.csv"')

            if name in ('-f', '--file'):
                file = r'{}'.format(val)
            if name in ('-t', '--title'):
                title += val + val
            if name in ('-o', '--out', '--output'):
                ofile = r'{}'.format(val)
    except getopt.GetoptError as e:
        print("Option unknown or unsupported! Use -h for usage")
        sys.exit()
    
    if file is None:
        print('No log file specified! Use "-h" for usage')
        sys.exit(0)

    return title, file, ofile


def main():

    title, file, ofile = get_option()

    file = 'haha_math-traces.csv'
    title = 'ByPass Mode PnP'
    plot_one(title, file, ofile)
    sys.exit(0)
 

if __name__ == '__main__':
    main()
