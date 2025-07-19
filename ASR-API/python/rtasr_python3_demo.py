# -*- encoding:utf-8 -*-
import hashlib
import hmac
import base64
from socket import *
import json, time, threading
from websocket import create_connection
import websocket
from urllib.parse import quote
import logging
from rtasr_result_parser import format_result

# reload(sys)
# sys.setdefaultencoding("utf8")
class Client():
    def __init__(self):
        base_url = "ws://rtasr.xfyun.cn/v1/ws"
        ts = str(int(time.time()))
        tt = (app_id + ts).encode('utf-8')
        md5 = hashlib.md5()
        md5.update(tt)
        baseString = md5.hexdigest()
        baseString = bytes(baseString, encoding='utf-8')

        apiKey = api_key.encode('utf-8')
        signa = hmac.new(apiKey, baseString, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')
        self.end_tag = "{\"end\": true}"

        self.ws = create_connection(base_url + "?appid=" + app_id + "&ts=" + ts + "&signa=" + quote(signa))
        self.trecv = threading.Thread(target=self.recv)
        self.trecv.start()

    def send(self, file_path):
        print(f"开始发送音频文件: {file_path}")
        file_object = open(file_path, 'rb')
        try:
            index = 1
            while True:
                chunk = file_object.read(1280)
                if not chunk:
                    break
                self.ws.send(chunk)

                index += 1
                time.sleep(0.04)
        finally:
            file_object.close()

        self.ws.send(bytes(self.end_tag.encode('utf-8')))
        print("send end tag success")

    def recv(self):
        try:
            while self.ws.connected:
                result = str(self.ws.recv())
                if len(result) == 0:
                    print("receive result end")
                    break
                result_dict = json.loads(result)
                # 解析结果
                if result_dict["action"] == "started":
                    print("handshake success, result: " + result)

                if result_dict["action"] == "result":
                    # 使用解析器格式化显示结果
                    formatted_result = format_result(result)
                    if formatted_result and "转写结果:" in formatted_result:
                        print(formatted_result)

                if result_dict["action"] == "error":
                    print("rtasr error: " + result)
                    self.ws.close()
                    return
        except websocket.WebSocketConnectionClosedException:
            print("receive result end")

    def close(self):
        self.ws.close()
        print("connection closed")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # 配置您的APPID和APIKey
    app_id = "daa9d5d9"
    api_key = "57e1dcd91156c7b12c078b5ad372870b"
    file_path = r"./test_1.pcm"

    print("=== 讯飞实时语音转写API测试 ===")
    print(f"APPID: {app_id}")
    print(f"音频文件: {file_path}")
    print("开始连接...")

    try:
        client = Client()
        client.send(file_path)
        
        # 等待接收结果
        print("等待转写结果...")
        client.trecv.join(timeout=30)  # 等待最多30秒
        
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        if 'client' in locals():
            client.close()
        print("测试完成")
