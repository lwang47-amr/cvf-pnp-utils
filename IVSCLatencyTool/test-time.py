import websocket
import time

# Get Target system time in sec
ws = websocket.WebSocket()
ws.connect('ws://10.80.113.33:8198/echo', timeout = 3)
ws.settimeout(10)

ws.send('TargetTime')
res = ws.recv()
targ_time = res[0] | res[1] << 8 | res[2] << 16 | res[3] << 24 | res[4] << 32 | res[5] << 40 | res[6] << 48 | res[7] << 56
print('TargetTime = ', targ_time) 
ws.close()

# Get Localhost system time rounded to sec
sys_time = int(time.time())
print('SystemTime = ', sys_time)

# Difference....
print('Diff = ', sys_time - targ_time)

print('Done')
