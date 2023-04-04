import base64
import hashlib
import random
import socket
import json
from pymongo import MongoClient

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8080))
server_socket.listen(5)

# client = MongoClient('mongodb://root:password@mongodb')  # submission
client = MongoClient('mongodb://root:password@localhost:27017/admin?authSource=admin&authMechanism=SCRAM-SHA-1')  # testing
db = client["myDB"]
coll1 = db.get_collection("coll1")  # hw1
coll2 = db.get_collection("coll2")  # hw2
img_coll2 = db.get_collection("img_coll2")  # hw2
token_coll2 = db.get_collection("token_coll2")  # hw2

while True:
    # print("text: " + str(coll2.count_documents({})))
    # print("image: " + str(img_coll2.count_documents({})))
    # print("token: " + str(token_coll2.count_documents({})))
    client_connection, client_address = server_socket.accept()
    raw_request = client_connection.recv(1048576)
    request = raw_request.decode('utf-8', 'ignore')
    headers = request.split('\n')
    filename = '/'
    if len(headers) != 0:
        if 'GET' in headers[0] or 'POST' in headers[0] or 'PUT' in headers[0] or 'DELETE' in headers[0]:
            filename = headers[0].split()[1]

    print(headers)

    if filename == '/':
        tkn = ""
        for i in range(20):
            tkn += str(chr(random.randint(65, 122)))
        token_coll2.insert_one({'token': tkn})
        f = open('index.html', 'rb')
        temp = 0
        for line in f:
            temp += len(line)
        temp += 35  # <div class="outer-container"></div>
        for i in list(coll2.find({})):
            count1 = str(i['message']).count("&")
            count2 = str(i['message']).count("<")
            count3 = str(i['message']).count(">")
            count4 = str(i['message']).count('"')
            count5 = str(i['message']).count("'")
            temp += len(i['message']) + 35 + 3*count1 + 2*count2 + 2*count3 + 4*count4 + 3*count5  # <div class="inner-container"></div> + replaces
        # response = f'HTTP/1.1 200 OK\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\Content-Length: {temp}\r\n\r\n'  # hw1
        response = f'HTTP/1.1 200 OK\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/html; charset=utf-8\r\n\r\n'  # hw2, might use later
        tkn_html = f'<input type="hidden" value="{tkn}" name="xsrf_token"/>'
        response += tkn_html
        f2 = open('index.html', 'r', encoding='utf-8')
        for line in f2:
            if 'name="xsrf_token"' in line:
                response += tkn_html
            else:
                response += line
        response += '<div class="outer-container">'
        for i in list(coll2.find({})):
            msg = str(i['message'])
            msg = msg.replace("&", "&amp")
            msg = msg.replace("<", "&lt")
            msg = msg.replace(">", "&gt")
            msg = msg.replace('"', "&quot")
            msg = msg.replace("'", "&#39")
            boundaryID = i['boundaryID']
            imgfound = len(list(img_coll2.find({'boundaryID': boundaryID})))
            if imgfound == 0:
                response += '<div class="inner-container">' + msg + "</div>"
            else:
                img = list(img_coll2.find({'boundaryID': boundaryID}))[0]['imgName']
                response += '<div class="inner-container">' + msg + f'<img src="image/{img}"></div>'
        response += '</div>'
        client_connection.send(response.encode())
    elif filename == '/functions.js':
        f = open('functions.js', 'rb')
        temp = 0
        for line in f:
            temp += len(line)
        response = f'HTTP/1.1 200 OK\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/javascript; charset=utf-8\r\nContent-Length: {temp}\r\n\r\n'
        f2 = open('functions.js', 'r', encoding='utf-8')
        for line in f2:
            response += line
        # print('functions.js: ' + response)
        client_connection.send(response.encode())
    elif filename == '/style.css':
        f = open('style.css', 'rb')
        temp = 0
        for line in f:
            temp += len(line)
        response = f'HTTP/1.1 200 OK\r\nX-Content-Type-Options: nosniff\r\nContent-Type: text/css; charset=utf-8\r\nContent-Length: {temp}\r\n\r\n'
        f2 = open('style.css', 'r', encoding='utf-8')
        for line in f2:
            response += line
        # print('style.css: ' + response)
        client_connection.send(response.encode())
    elif filename == '/hello':
        client_connection.send('HTTP/1.1 200 OK\n\nHello World!\n\n'.encode())
    elif filename == '/hi':
        client_connection.send('HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation: /hello\n\n'.encode())
    elif len(filename) >= 6 and filename[0:6] == '/users':
        if filename == '/users':
            if headers[0][0] == 'POST':
                o = {}
                for i in headers:
                    try:
                        json.loads(i)
                    except ValueError as e:
                        continue
                    o = json.loads(i)
                    break
                o['id'] = len(list(coll1.find({}))) + 1
                coll1.insert_one(o)
                temp = json.dumps(o)
                client_connection.send(f'HTTP/1.1 201 Created\r\n\r\n{temp}\r\n\r\n'.encode())
            elif headers[0][0] == 'GET':
                lst = []
                for i in list(coll1.find({})):
                    lst += i
                temp = json.dumps(lst)
                client_connection.send(f'HTTP/1.1 200 OK\r\n\r\n{temp}\r\n\r\n'.encode())
        else:
            id_no = filename.replace('/users/', '')
            if headers[0][0] == 'GET':
                temp = list(coll1.find({'id': id_no}))
                if len(temp) == 0:
                    client_connection.send('HTTP/1.1 404 Not Found\n\n'.encode())
                else:
                    temp2 = json.dumps(temp[0])
                    client_connection.send(f'HTTP/1.1 200 OK\r\n\r\n{temp2}\r\n\r\n'.encode())
            elif headers[0][0] == 'PUT':
                o = {}
                for i in headers:
                    try:
                        json.loads(i)
                    except ValueError as e:
                        continue
                    o = json.loads(i)
                    break
                if len(list(coll1.find({'id': id_no}))) == 0:
                    client_connection.send('HTTP/1.1 404 Not Found\n\n'.encode())
                else:
                    coll1.update_one({'id': id_no}, {'$set': {'email': o['email'], 'username': o['username']}})
                    temp = list(coll1.find({'id': id_no}))[0]
                    client_connection.send(f'HTTP/1.1 200 OK\r\n\r\n{temp}\r\n\r\n'.encode())
            elif headers[0][0] == 'DELETE':
                if len(list(coll1.find({'id': id_no}))) == 0:
                    client_connection.send('HTTP/1.1 404 Not Found\n\n'.encode())
                else:
                    coll1.delete_one({'id': id_no})
                    client_connection.send('HTTP/1.1 204 No Content\n\n'.encode())
    elif filename == '/image-upload':
        found = True
        if headers[-7][0:6] == '------':
            idx = headers.index('Content-Disposition: form-data; name="xsrf_token"\r') + 2
            xsrf = headers[idx].replace('\r', '')
            if len(list(token_coll2.find({"token": xsrf}))) != 0:
                boundaryID = headers[-7].replace("------WebKitFormBoundary", "")
                temp = {"boundaryID": boundaryID, "message": headers[-8]}
                res = list(coll2.find({"boundaryID": boundaryID}))
                if len(res) == 0:
                    coll2.insert_one(temp)
            else:
                found = False
        else:
            boundary = b'--' + raw_request.split(b'\r\n')[10].split(b';')[1].split(b'=')[1] + b'--'
            while raw_request.split(b'\r\n')[-2] != boundary:
                raw_request += client_connection.recv(1048576)
            if b'Content-Type: image/jpeg' in raw_request:
                boundaryID = boundary.decode().replace("------WebKitFormBoundary", "").replace("--", "")
                headers2 = raw_request.split(b"image/jpeg\r\n\r\n")[0].decode().split(f"------WebKitFormBoundary{boundaryID}")
                xsrf = headers2[-3].split('\r\n')[-2]
                if len(list(token_coll2.find({"token": xsrf}))) != 0:
                    msg = headers2[-2].split('name="comment"')[1].replace("\r\n", "")
                    temp = {"boundaryID": boundaryID, "message": msg}
                    res = list(coll2.find({"boundaryID": boundaryID}))
                    if len(res) == 0:
                        coll2.insert_one(temp)
                    raw_image = raw_request.split(b'image/jpeg\r\n\r\n')[1].split(boundary)[0][:-2]
                    cnt = len(list(img_coll2.find({})))
                    img = {"boundaryID": boundaryID, "imgName": "image" + str(cnt + 1) + ".jpg", "data": raw_image}
                    res2 = list(img_coll2.find({"boundaryID": boundaryID}))
                    if len(res2) == 0:
                        img_coll2.insert_one(img)
                else:
                    found = False
        if found is True:
            client_connection.send('HTTP/1.1 303 Redirect to home\r\nContent-Length: 0\r\nLocation: /\n\n'.encode())
        else:
            client_connection.send('HTTP/1.1 403 Forbidden\n\nRequest was rejected\n\n'.encode())
    elif filename[0:6] == '/image' and filename[-4:] == '.jpg':
        temp = filename.split("/")[2]
        found = list(img_coll2.find({"imgName": f'{temp}'}))
        if len(found) == 0:
            f = open(f'image{filename[6:]}', 'rb')
            r = f.read()
            temp = len(r)
            response = f'HTTP/1.1 200 OK \r\nX-Content-Type-Options: nosniff\r\nContent-Type: image/jpeg\r\nContent-Length: {temp}\r\n\r\n'
            response = response.encode() + r
            client_connection.send(response)
        else:
            temp = found[0]['data']
            response = f'HTTP/1.1 200 OK \r\nX-Content-Type-Options: nosniff\r\nContent-Type: image/jpeg\r\n\r\n'
            response = response.encode() + temp
            client_connection.send(response)
    elif filename == '/websocket':
        temp = headers[-4].split(' ')[1] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        temp = hashlib.sha1(temp.encode()).digest()
        temp = base64.b64encode(temp)
        response = f'HTTP/1.1 101 Switching Protocols\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Accept: {temp}\r\n\r\n'
        client_connection.send(response.encode())
    elif filename == '/chat-history':
        response = f'HTTP/1.1 200 OK \r\n'
        client_connection.send(response.encode())
    elif filename == '/clear-database':
        coll1.delete_many({})
        coll2.delete_many({})
        img_coll2.delete_many({})
        token_coll2.delete_many({})
        client_connection.send('HTTP/1.1 303 Redirect to home\r\nContent-Length: 0\r\nLocation: /\n\n'.encode())
    else:
        client_connection.send(
            'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 36\n\nThe requested content does not exist\n\n'.encode())
    client_connection.close()

# server_socket.close()