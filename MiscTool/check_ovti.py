import os

#DIR=['./ovti02c1','./ovti02c1']

DIR=[]
DEBUG=False    # True False

def main():  

    if len(DIR) == 0:
        for root,dir,files in os.walk('./'):
            if root.startswith('./ovti'):
                DIR.append(root)


    for dir in DIR:
        for root,dir,files in os.walk(dir):
            print('-'*30, '  ', root, '  ', '-'*30)
            for file in files:
                fname = os.path.join(root, file)
                size = os.path.getsize(fname)

                with open(fname, 'rb') as f:
                    buf =  f.read(128)
                    if fname.endswith('bin'):
                       if size > 1024:
                          print('%50s (%6d) - File greater than 1KB' % (fname, size))
                        # Only pick bin file
                       elif "_1_" in fname:
                            # File shall be non ASCII
                            if 'place-holder' in str(buf) or 'IVSC' in str(buf):
                                print('%50s (%6d) - File *_1_* HEX  : FAILED' % (fname, size))
                                print(buf[1:64])
                            else:
                                print('%50s (%6d) - File *_1_* HEX  : Passed' % (fname, size))
                            if DEBUG is True:
                               print(buf[1:64])
                       elif "_2_" in fname:
                            # File shall be ASCII
                            if 'place-holder' in str(buf) or 'IVSC' in str(buf):
                                print('%50s (%6d) - File *_2_* ASCII: Passed' % (fname, size))
                            else:
                                print('%50s (%6d) - File *_2_* ASCII: FAILED' % (fname, size))
                                print(buf[1:64])
                            if DEBUG is True:
                                print(buf[1:64])
                       else:
                            print('%50s (%6d) - File less than 1KB, neither _1_, nor _2_: FAILED' % (fname, size))
            print('\n')


    return

if __name__ == "__main__":
    main()
