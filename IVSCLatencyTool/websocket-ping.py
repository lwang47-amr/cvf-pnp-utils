import websocket
ws = websocket.WebSocket()
print('Connecting 10.80.113.33:8189....')
ws.connect('ws://10.80.113.33:8198/echo')   
print('Connected')
ws.close()
print('Done')

