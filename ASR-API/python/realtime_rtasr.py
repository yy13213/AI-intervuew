# -*- encoding:utf-8 -*-
import hashlib
import hmac
import base64
import json
import time
import threading
from websocket import create_connection
import websocket
from urllib.parse import quote
import logging
import pyaudio
import numpy as np
from rtasr_result_parser import format_result

class RealtimeRTASR:
    def __init__(self, app_id, api_key):
        self.app_id = app_id
        self.api_key = api_key
        self.ws = None
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        
        # 音频参数设置
        self.CHUNK = 1280  # 每次读取的字节数
        self.FORMAT = pyaudio.paInt16  # 16位深度
        self.CHANNELS = 1  # 单声道
        self.RATE = 16000  # 16kHz采样率
        
    def create_connection(self):
        """创建WebSocket连接"""
        base_url = "ws://rtasr.xfyun.cn/v1/ws"
        ts = str(int(time.time()))
        tt = (self.app_id + ts).encode('utf-8')
        md5 = hashlib.md5()
        md5.update(tt)
        baseString = md5.hexdigest()
        baseString = bytes(baseString, encoding='utf-8')

        apiKey = self.api_key.encode('utf-8')
        signa = hmac.new(apiKey, baseString, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')

        self.ws = create_connection(base_url + "?appid=" + self.app_id + "&ts=" + ts + "&signa=" + quote(signa))
        print("WebSocket连接已建立")
        
    def start_recording(self):
        """开始录音和转写"""
        if self.ws is None:
            self.create_connection()
            
        self.is_recording = True
        
        # 启动接收线程
        self.recv_thread = threading.Thread(target=self.recv_messages)
        self.recv_thread.daemon = True
        self.recv_thread.start()
        
        # 启动录音线程
        self.record_thread = threading.Thread(target=self.record_audio)
        self.record_thread.daemon = True
        self.record_thread.start()
        
        print("开始录音，请说话...")
        print("按 Ctrl+C 停止录音")
        
    def record_audio(self):
        """录音线程"""
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            while self.is_recording:
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    if self.ws and self.ws.connected:
                        self.ws.send(data)
                    time.sleep(0.04)  # 40ms间隔
                except Exception as e:
                    print(f"录音错误: {e}")
                    break
                    
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"启动录音失败: {e}")
            
    def recv_messages(self):
        """接收转写结果线程"""
        try:
            while self.is_recording and self.ws and self.ws.connected:
                try:
                    result = self.ws.recv()
                    if result:
                        result_str = str(result)
                        result_dict = json.loads(result_str)
                        
                        if result_dict.get("action") == "started":
                            print("转写服务已启动")
                            
                        elif result_dict.get("action") == "result":
                            formatted_result = format_result(result_str)
                            if formatted_result and "转写结果:" in formatted_result:
                                print(formatted_result)
                                
                        elif result_dict.get("action") == "error":
                            print(f"转写错误: {result_str}")
                            break
                            
                except websocket.WebSocketConnectionClosedException:
                    print("WebSocket连接已关闭")
                    break
                except Exception as e:
                    print(f"接收消息错误: {e}")
                    break
                    
        except Exception as e:
            print(f"接收线程错误: {e}")
            
    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        
        # 发送结束标记
        if self.ws and self.ws.connected:
            end_tag = "{\"end\": true}"
            try:
                self.ws.send(bytes(end_tag.encode('utf-8')))
                print("已发送结束标记")
            except:
                pass
                
        # 关闭连接
        if self.ws:
            self.ws.close()
            
        # 释放音频资源
        self.audio.terminate()
        print("录音已停止")

def main():
    # 配置参数
    app_id = "daa9d5d9"
    api_key = "57e1dcd91156c7b12c078b5ad372870b"
    
    print("=== 讯飞实时语音转写 - 麦克风模式 ===")
    print(f"APPID: {app_id}")
    print("准备启动实时转写...")
    
    rtasr = RealtimeRTASR(app_id, api_key)
    
    try:
        rtasr.start_recording()
        
        # 等待用户中断
        while rtasr.is_recording:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n用户中断，正在停止...")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        rtasr.stop_recording()
        print("程序结束")

if __name__ == "__main__":
    main() 