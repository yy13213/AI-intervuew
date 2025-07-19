# coding: utf-8
import _thread as thread
import threading
import queue
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket
import os
import time
import pygame
import io
import tempfile
from openai import OpenAI

# 初始化pygame音频
pygame.mixer.init()

class AudioQueue:
    """音频播放队列管理器"""
    def __init__(self):
        self.audio_queue = queue.PriorityQueue()  # 使用优先级队列
        self.is_playing = False
        self.play_thread = None
        self.stop_playback = False
        self.sequence_counter = 0  # 序号计数器
        
    def add_audio(self, audio_file_path, sequence_number):
        """添加音频文件到播放队列，带序号保证顺序"""
        self.audio_queue.put((sequence_number, audio_file_path))
        if not self.is_playing:
            self.start_playback()
    
    def start_playback(self):
        """开始播放队列中的音频"""
        if self.play_thread is None or not self.play_thread.is_alive():
            self.play_thread = threading.Thread(target=self._playback_worker)
            self.play_thread.daemon = True
            self.play_thread.start()
    
    def _playback_worker(self):
        """播放工作线程"""
        self.is_playing = True
        while not self.stop_playback:
            try:
                # 从队列中获取音频文件，超时1秒
                sequence_number, audio_file = self.audio_queue.get(timeout=1)
                if audio_file and os.path.exists(audio_file):
                    print(f"[播放第{sequence_number}段音频]")
                    self._play_single_audio(audio_file)
                    # 播放完成后删除临时文件
                    try:
                        os.unlink(audio_file)
                    except:
                        pass
                self.audio_queue.task_done()
            except queue.Empty:
                # 队列为空，停止播放
                break
        self.is_playing = False
    
    def _play_single_audio(self, audio_file):
        """播放单个音频文件"""
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"播放音频时出错: {e}")
    
    def stop(self):
        """停止播放"""
        self.stop_playback = True
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=2)
    
    def get_next_sequence(self):
        """获取下一个序号"""
        self.sequence_counter += 1
        return self.sequence_counter

class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, gpt_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(gpt_url).netloc
        self.path = urlparse(gpt_url).path
        self.gpt_url = gpt_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.gpt_url + '?' + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)
    print(f"错误类型: {type(error)}")
    print(f"错误详情: {str(error)}")


# 收到websocket关闭的处理
def on_close(ws, ws1, ws2):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    print("### 连接建立成功 ###")
    thread.start_new_thread(run, (ws,))


# 收到websocket消息的处理
def on_message(ws, message):
    try:
        print(f"收到消息: {message[:200]}...")  # 只打印前200个字符
        message = json.loads(message)
        code = message['header']['code']
        if code != 0:
            print("### 请求出错： ", message)
            print(f"错误代码: {code}")
            print(f"错误信息: {message['header'].get('message', '未知错误')}")
        else:
            payload = message.get("payload")
            status = message['header']['status']
            print(f"状态: {status}")
            if status == 2:
                print("### 合成完毕")
                ws.close()
            if payload and payload != "null":
                audio = payload.get("audio")
                if audio:
                    audio_data = audio["audio"]
                    print(f"音频数据长度: {len(audio_data)}")
                    try:
                        with open(ws.save_file_name, 'ab') as f:
                            f.write(base64.b64decode(audio_data))
                        print(f"音频数据已写入文件: {ws.save_file_name}")
                    except Exception as e:
                        print(f"写入文件时出错: {e}")
                        print(f"当前工作目录: {os.getcwd()}")
                        print(f"文件路径: {ws.save_file_name}")
                        print(f"文件是否存在: {os.path.exists(ws.save_file_name)}")
                else:
                    print("未找到音频数据")
            else:
                print("payload为空或为null")
                print(f"完整payload内容: {payload}")
    except Exception as e:
        print(f"处理消息时出错: {e}")
        import traceback
        traceback.print_exc()


def run(ws, *args):
    print("开始发送TTS请求...")
    body = {
        "header": {
            "app_id": ws.appid,
            "status": 2,
        },
        "parameter": {
            "oral": {
                "oral_level": "mid"
            },
            "tts": {
                "vcn": ws.vcn,
                "speed": 50,
                "volume": 50,
                "pitch": 50,
                "bgs": 0,
                "reg": 0,
                "rdn": 0,
                "rhy": 0,
                "audio": {
                    "encoding": "lame",
                    "sample_rate": 24000,
                    "channels": 1,
                    "bit_depth": 16,
                    "frame_size": 0
                }
            }
        },
        "payload": {
            "text": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain",
                "status": 2,
                "seq": 0,
                "text": str(base64.b64encode(ws.text.encode('utf-8')), 'utf8')
            }
        }
    }

    print(f"发送文本: {ws.text}")
    print(f"请求体: {json.dumps(body, indent=2, ensure_ascii=False)}")
    ws.send(json.dumps(body))


def main(appid, api_secret, api_key, url, text, vcn, save_file_name):
    print(f"开始TTS转换...")
    print(f"文本: {text}")
    print(f"保存文件: {save_file_name}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"APPID: {appid}")
    print(f"API Key: {api_key[:10]}...")
    print(f"发音人: {vcn}")
    
    wsParam = Ws_Param(appid, api_key, api_secret, url)
    wsUrl = wsParam.create_url()
    print(f"WebSocket URL: {wsUrl}")
    
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    websocket.enableTrace(False)
    ws.appid = appid
    ws.text = text
    ws.vcn = vcn
    ws.save_file_name = save_file_name
    
    # 检查并删除已存在的文件
    if os.path.exists(ws.save_file_name):
        try:
            os.remove(ws.save_file_name)
            print(f"已删除旧文件: {ws.save_file_name}")
        except Exception as e:
            print(f"删除文件时出错: {e}")
    
    print("开始运行WebSocket连接...")
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


class RealtimeAITTS:
    def __init__(self):
        self.client = OpenAI(
            api_key='QcGCOyVichfHetzkUDeM:AUoiqAJtarlstnrJMcTI',
            base_url='https://spark-api-open.xf-yun.com/v1/'
        )
        # TTS配置
        self.appid = "daa9d5d9"
        self.api_secret = "YTBkNzA5MGVlNzYzNDVkMDk2MzcwOTIy"
        self.api_key = "c52e142d8749090d0caa6c0fab03d2d1"
        self.url = "wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6"
        self.vcn = "x5_lingfeiyi_flow"
        
        # 音频队列管理器
        self.audio_queue = AudioQueue()
        
        # 合成线程池
        self.synthesis_threads = []
        self.max_synthesis_threads = 3
        
    def stream_ai_and_parallel_tts(self, prompt):
        """AI流式输出并并行TTS合成播放"""
        print(f"AI正在思考并回答: {prompt}")
        print("=" * 50)
        
        try:
            response = self.client.chat.completions.create(
                model='generalv3.5',
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            full_response = ""
            current_sentence = ""
            sentence_buffer = []
            first_sentence_synthesized = False
            sentence_sequence = 0  # 句子序号
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    current_sentence += content
                    
                    # 实时显示AI输出
                    print(content, end='', flush=True)
                    
                    # 检测句子结束（句号、问号、感叹号）
                    if any(punct in content for punct in ['。', '！', '？', '.', '!', '?']):
                        if current_sentence.strip():
                            sentence_buffer.append(current_sentence.strip())
                            current_sentence = ""
                            
                            # 当缓冲区有足够内容时，进行并行TTS合成
                            if len(sentence_buffer) >= 1:
                                sentence_to_tts = " ".join(sentence_buffer)
                                sentence_sequence += 1  # 增加序号
                                self._parallel_synthesize_and_queue(sentence_to_tts, sentence_sequence)
                                
                                # 第一段语音合成后立即开始播放
                                if not first_sentence_synthesized:
                                    first_sentence_synthesized = True
                                    print("\n[开始播放语音队列...]")
                                
                                sentence_buffer = []
            
            # 处理最后可能未完成的句子
            if current_sentence.strip():
                sentence_buffer.append(current_sentence.strip())
            
            if sentence_buffer:
                sentence_to_tts = " ".join(sentence_buffer)
                sentence_sequence += 1  # 增加序号
                self._parallel_synthesize_and_queue(sentence_to_tts, sentence_sequence)
                
                # 如果还没有开始播放，现在开始
                if not first_sentence_synthesized:
                    first_sentence_synthesized = True
                    print("\n[开始播放语音队列...]")
            
            # 等待所有合成完成和播放完成
            self._wait_for_completion()
            
            print("\n" + "=" * 50)
            print("AI回答完成！")
            return full_response
            
        except Exception as e:
            print(f"AI流式输出失败: {str(e)}")
            return None
    
    def stream_ai_and_complete_tts(self, prompt):
        """AI流式输出，完成后一次性合成音频播放"""
        print(f"AI正在思考并回答: {prompt}")
        print("=" * 50)
        
        try:
            response = self.client.chat.completions.create(
                model='generalv3.5',
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            full_response = ""
            
            # 收集完整的AI回复
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    # 实时显示AI输出
                    print(content, end='', flush=True)
            
            print("\n" + "=" * 50)
            print("AI回答完成，开始合成音频...")
            
            # 一次性合成完整音频
            if full_response.strip():
                self._synthesize_complete_audio(full_response)
            
            print("音频播放完成！")
            return full_response
            
        except Exception as e:
            print(f"AI流式输出失败: {str(e)}")
            return None
    
    def _parallel_synthesize_and_queue(self, text, sequence_number):
        """并行合成音频并加入播放队列，带序号"""
        if not text.strip():
            return
            
        print(f"\n[正在并行合成第{sequence_number}段音频]: {text}")
        
        # 创建合成线程
        synthesis_thread = threading.Thread(
            target=self._synthesize_and_queue_worker,
            args=(text, sequence_number)
        )
        synthesis_thread.daemon = True
        synthesis_thread.start()
        
        # 添加到线程池
        self.synthesis_threads.append(synthesis_thread)
        
        # 清理已完成的线程
        self._cleanup_finished_threads()
    
    def _synthesize_and_queue_worker(self, text, sequence_number):
        """合成工作线程，带序号"""
        # 创建临时文件用于音频数据
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # 调用TTS合成到临时文件
            self._synthesize_to_file(text, temp_file_path)
            
            # 检查文件是否生成成功
            if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 1000:
                # 添加到播放队列，使用序号保证顺序
                self.audio_queue.add_audio(temp_file_path, sequence_number)
                print(f"[第{sequence_number}段音频已加入播放队列]: {text}")
            else:
                print(f"第{sequence_number}段音频文件生成失败或不完整，无法播放。")
                # 删除失败的文件
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"合成第{sequence_number}段音频时出错: {e}")
            # 清理临时文件
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except:
                pass
    
    def _synthesize_complete_audio(self, text):
        """一次性合成完整音频"""
        if not text.strip():
            return
            
        print(f"\n[正在合成完整音频]: {text[:50]}...")
        
        # 创建临时文件用于音频数据
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # 调用TTS合成到临时文件
            self._synthesize_to_file(text, temp_file_path)
            
            # 检查文件是否生成成功
            if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 1000:
                print(f"[开始播放完整音频]")
                # 直接播放完整音频
                if self._play_complete_audio(temp_file_path):
                    print(f"[完整音频播放完成]")
                else:
                    print(f"[完整音频播放失败]")
            else:
                print("完整音频文件生成失败或不完整，无法播放。")
                
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except:
                pass
    
    def _play_complete_audio(self, audio_file):
        """播放完整音频文件"""
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            pygame.mixer.music.unload()
            return True
        except Exception as e:
            print(f"播放完整音频时出错: {e}")
            return False
    
    def _wait_for_completion(self):
        """等待所有合成完成和播放完成"""
        print("\n[等待所有音频合成完成...]")
        for thread in self.synthesis_threads:
            if thread.is_alive():
                thread.join(timeout=10)
        self.synthesis_threads.clear()
        
        # 等待播放队列播放完成
        if self.audio_queue.is_playing:
            print("[等待播放队列完成...]")
            self.audio_queue.audio_queue.join()
    
    def _cleanup_finished_threads(self):
        """清理已完成的合成线程"""
        self.synthesis_threads = [t for t in self.synthesis_threads if t.is_alive()]
    
    def _synthesize_to_file(self, text, file_path):
        """合成音频到指定文件"""
        wsParam = Ws_Param(self.appid, self.api_key, self.api_secret, self.url)
        wsUrl = wsParam.create_url()
        
        # 创建WebSocket连接
        ws = websocket.WebSocketApp(
            wsUrl, 
            on_message=self._on_message, 
            on_error=self._on_error, 
            on_close=self._on_close, 
            on_open=self._on_open
        )
        
        ws.appid = self.appid
        ws.text = text
        ws.vcn = self.vcn
        ws.save_file_name = file_path
        
        # 删除已存在的文件
        if os.path.exists(ws.save_file_name):
            os.remove(ws.save_file_name)
        
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    
    def _on_message(self, ws, message):
        """处理WebSocket消息"""
        try:
            message = json.loads(message)
            code = message['header']['code']
            if code != 0:
                print("### 请求出错： ", message)
            else:
                payload = message.get("payload")
                status = message['header']['status']
                if status == 2:
                    print("### 合成完毕")
                    ws.close()
                if payload and payload != "null":
                    audio = payload.get("audio")
                    if audio:
                        audio_data = audio["audio"]
                        with open(ws.save_file_name, 'ab') as f:
                            f.write(base64.b64decode(audio_data))
        except Exception as e:
            print(f"处理消息时出错: {e}")
    
    def _on_error(self, ws, error):
        print("### error:", error)
    
    def _on_close(self, ws, ws1, ws2):
        print("### closed ###")
    
    def _on_open(self, ws):
        thread.start_new_thread(self._run_tts_request, (ws,))
    
    def _run_tts_request(self, ws):
        """发送TTS请求"""
        body = {
            "header": {
                "app_id": ws.appid,
                "status": 2,
            },
            "parameter": {
                "oral": {
                    "oral_level": "mid"
                },
                "tts": {
                    "vcn": ws.vcn,
                    "speed": 50,
                    "volume": 50,
                    "pitch": 50,
                    "bgs": 0,
                    "reg": 0,
                    "rdn": 0,
                    "rhy": 0,
                    "audio": {
                        "encoding": "lame",
                        "sample_rate": 24000,
                        "channels": 1,
                        "bit_depth": 16,
                        "frame_size": 0
                    }
                }
            },
            "payload": {
                "text": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain",
                    "status": 2,
                    "seq": 0,
                    "text": str(base64.b64encode(ws.text.encode('utf-8')), 'utf8')
                }
            }
        }
        ws.send(json.dumps(body))
    
    def interactive_ai_chat(self):
        """交互式AI聊天，并行TTS"""
        print("进入AI实时对话模式，输入exit退出。")
        print("AI会实时回答并播放语音（并行合成）。")
        
        try:
            while True:
                user_input = input("\n请输入您的问题（exit退出）：")
                if user_input.strip().lower() == "exit":
                    print("退出AI对话模式。")
                    break
                if not user_input.strip():
                    continue
                    
                self.stream_ai_and_parallel_tts(user_input)
        finally:
            # 清理资源
            self.audio_queue.stop()

    def interactive_ai_chat_complete(self, prompt):
        """交互式AI聊天，一次性合成音频"""
        print(f"AI正在思考并回答: {prompt}")
        print("=" * 50)
        
        try:
            response = self.client.chat.completions.create(
                model='generalv3.5',
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            full_response = ""
            
            # 收集完整的AI回复
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    # 实时显示AI输出
                    print(content, end='', flush=True)
            
            print("\n" + "=" * 50)
            print("AI回答完成，开始合成音频...")
            
            # 一次性合成完整音频
            if full_response.strip():
                self._synthesize_complete_audio(full_response)
            
            print("音频播放完成！")
            return full_response
            
        except Exception as e:
            print(f"AI流式输出失败: {str(e)}")
            return None
    
    def _synthesize_complete_audio(self, text):
        """一次性合成完整音频"""
        if not text.strip():
            return
            
        print(f"\n[正在合成完整音频]: {text[:50]}...")
        
        # 创建临时文件用于音频数据
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # 调用TTS合成到临时文件
            self._synthesize_to_file(text, temp_file_path)
            
            # 检查文件是否生成成功
            if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 1000:
                print(f"[开始播放完整音频]")
                # 直接播放完整音频
                if self._play_complete_audio(temp_file_path):
                    print(f"[完整音频播放完成]")
                else:
                    print(f"[完整音频播放失败]")
            else:
                print("完整音频文件生成失败或不完整，无法播放。")
                
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except:
                pass
    
    def _play_complete_audio(self, audio_file):
        """播放完整音频文件"""
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            pygame.mixer.music.unload()
            return True
        except Exception as e:
            print(f"播放完整音频时出错: {e}")
            return False
    
    def _wait_for_completion(self):
        """等待所有合成完成和播放完成"""
        print("\n[等待所有音频合成完成...]")
        for thread in self.synthesis_threads:
            if thread.is_alive():
                thread.join(timeout=10)
        self.synthesis_threads.clear()
        
        # 等待播放队列播放完成
        if self.audio_queue.is_playing:
            print("[等待播放队列完成...]")
            self.audio_queue.audio_queue.join()
    
    def _cleanup_finished_threads(self):
        """清理已完成的合成线程"""
        self.synthesis_threads = [t for t in self.synthesis_threads if t.is_alive()]
    
    def _synthesize_to_file(self, text, file_path):
        """合成音频到指定文件"""
        wsParam = Ws_Param(self.appid, self.api_key, self.api_secret, self.url)
        wsUrl = wsParam.create_url()
        
        # 创建WebSocket连接
        ws = websocket.WebSocketApp(
            wsUrl, 
            on_message=self._on_message, 
            on_error=self._on_error, 
            on_close=self._on_close, 
            on_open=self._on_open
        )
        
        ws.appid = self.appid
        ws.text = text
        ws.vcn = self.vcn
        ws.save_file_name = file_path
        
        # 删除已存在的文件
        if os.path.exists(ws.save_file_name):
            os.remove(ws.save_file_name)
        
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    
    def _on_message(self, ws, message):
        """处理WebSocket消息"""
        try:
            message = json.loads(message)
            code = message['header']['code']
            if code != 0:
                print("### 请求出错： ", message)
            else:
                payload = message.get("payload")
                status = message['header']['status']
                if status == 2:
                    print("### 合成完毕")
                    ws.close()
                if payload and payload != "null":
                    audio = payload.get("audio")
                    if audio:
                        audio_data = audio["audio"]
                        with open(ws.save_file_name, 'ab') as f:
                            f.write(base64.b64decode(audio_data))
        except Exception as e:
            print(f"处理消息时出错: {e}")
    
    def _on_error(self, ws, error):
        print("### error:", error)
    
    def _on_close(self, ws, ws1, ws2):
        print("### closed ###")
    
    def _on_open(self, ws):
        thread.start_new_thread(self._run_tts_request, (ws,))
    
    def _run_tts_request(self, ws):
        """发送TTS请求"""
        body = {
            "header": {
                "app_id": ws.appid,
                "status": 2,
            },
            "parameter": {
                "oral": {
                    "oral_level": "mid"
                },
                "tts": {
                    "vcn": ws.vcn,
                    "speed": 50,
                    "volume": 50,
                    "pitch": 50,
                    "bgs": 0,
                    "reg": 0,
                    "rdn": 0,
                    "rhy": 0,
                    "audio": {
                        "encoding": "lame",
                        "sample_rate": 24000,
                        "channels": 1,
                        "bit_depth": 16,
                        "frame_size": 0
                    }
                }
            },
            "payload": {
                "text": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain",
                    "status": 2,
                    "seq": 0,
                    "text": str(base64.b64encode(ws.text.encode('utf-8')), 'utf8')
                }
            }
        }
        ws.send(json.dumps(body))
    
    def interactive_ai_chat(self):
        """交互式AI聊天，并行TTS"""
        print("进入AI实时对话模式，输入exit退出。")
        print("AI会实时回答并播放语音（并行合成）。")
        
        try:
            while True:
                user_input = input("\n请输入您的问题（exit退出）：")
                if user_input.strip().lower() == "exit":
                    print("退出AI对话模式。")
                    break
                if not user_input.strip():
                    continue
                    
                self.stream_ai_and_parallel_tts(user_input)
        finally:
            # 清理资源
            self.audio_queue.stop()

    def interactive_ai_chat_complete(self):
        """交互式AI聊天，一次性合成音频"""
        print("进入AI一次性合成对话模式，输入exit退出。")
        print("AI会完整回答后一次性合成并播放语音。")
        
        try:
            while True:
                user_input = input("\n请输入您的问题（exit退出）：")
                if user_input.strip().lower() == "exit":
                    print("退出AI对话模式。")
                    break
                if not user_input.strip():
                    continue
                    
                self.stream_ai_and_complete_tts(user_input)
                
        except KeyboardInterrupt:
            print("\n👋 对话已中断")
        finally:
            # 清理资源
            self.audio_queue.stop()

def play_audio_file(file_path):
    """使用pygame播放音频文件"""
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        # 等待播放完成
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        pygame.mixer.music.unload()
        return True
    except Exception as e:
        print(f"播放音频时出错: {e}")
        return False

def realtime_tts():
    print("进入实时TTS模式，输入exit退出。")
    appid = "daa9d5d9"
    api_secret = "YTBkNzA5MGVlNzYzNDVkMDk2MzcwOTIy"
    api_key = "c52e142d8749090d0caa6c0fab03d2d1"
    url = "wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6"
    vcn = "x5_lingfeiyi_flow"
    while True:
        text = input("请输入要合成的文字（exit退出）：")
        if text.strip().lower() == "exit":
            print("退出实时TTS模式。")
            break
        if not text.strip():
            continue
        save_file_name = "./realtime_tts.mp3"
        main(appid, api_secret, api_key, url, text, vcn, save_file_name)
        # 等待文件写入完成
        for _ in range(10):
            if os.path.exists(save_file_name) and os.path.getsize(save_file_name) > 1000:
                break
            time.sleep(0.2)
        if os.path.exists(save_file_name) and os.path.getsize(save_file_name) > 1000:
            try:
                play_audio_file(save_file_name)
            except Exception as e:
                print(f"播放音频时出错: {e}")
        else:
            print("音频文件生成失败或不完整，无法播放。")

class AIVoiceChat:
    """AI语音对话接口类"""
    
    def __init__(self, api_key=None, base_url=None, tts_config=None):
        """
        初始化AI语音对话接口
        
        Args:
            api_key: OpenAI API密钥，默认使用内置密钥
            base_url: API基础URL，默认使用讯飞星火API
            tts_config: TTS配置字典，包含appid, api_secret, api_key, url, vcn等
        """
        # AI配置
        self.ai_client = OpenAI(
            api_key=api_key or 'QcGCOyVichfHetzkUDeM:AUoiqAJtarlstnrJMcTI',
            base_url=base_url or 'https://spark-api-open.xf-yun.com/v1/'
        )
        
        # TTS配置
        default_tts_config = {
            "appid": "daa9d5d9",
            "api_secret": "YTBkNzA5MGVlNzYzNDVkMDk2MzcwOTIy",
            "api_key": "c52e142d8749090d0caa6c0fab03d2d1",
            "url": "wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6",
            "vcn": "x5_lingfeiyi_flow"
        }
        self.tts_config = tts_config or default_tts_config
        
        # 创建RealtimeAITTS实例
        self.ai_tts = RealtimeAITTS()
        # 更新TTS配置
        self.ai_tts.appid = self.tts_config["appid"]
        self.ai_tts.api_secret = self.tts_config["api_secret"]
        self.ai_tts.api_key = self.tts_config["api_key"]
        self.ai_tts.url = self.tts_config["url"]
        self.ai_tts.vcn = self.tts_config["vcn"]
    
    def chat_with_voice_stream(self, message, system_prompt=None):
        """
        与AI进行流式语音对话（并行合成）
        
        Args:
            message: 用户输入的消息
            system_prompt: 系统提示词，用于设定AI角色和行为
        
        Returns:
            str: AI的文本回复
        """
        try:
            # 构建消息列表
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            # 更新AI客户端的消息
            self.ai_tts.client = OpenAI(
                api_key=self.ai_tts.client.api_key,
                base_url=self.ai_tts.client.base_url
            )
            
            # 执行流式语音对话
            return self.ai_tts.stream_ai_and_parallel_tts(message)
            
        except Exception as e:
            print(f"流式语音对话失败: {str(e)}")
            return None
    
    def chat_with_voice_complete(self, message, system_prompt=None):
        """
        与AI进行一次性语音对话（完整合成）
        
        Args:
            message: 用户输入的消息
            system_prompt: 系统提示词，用于设定AI角色和行为
        
        Returns:
            str: AI的文本回复
        """
        try:
            # 构建消息列表
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            # 更新AI客户端的消息
            self.ai_tts.client = OpenAI(
                api_key=self.ai_tts.client.api_key,
                base_url=self.ai_tts.client.base_url
            )
            
            # 执行一次性语音对话
            return self.ai_tts.stream_ai_and_complete_tts(message)
            
        except Exception as e:
            print(f"一次性语音对话失败: {str(e)}")
            return None
    
    def chat_with_voice(self, message, system_prompt=None):
        """
        与AI进行语音对话（默认使用流式）
        
        Args:
            message: 用户输入的消息
            system_prompt: 系统提示词，用于设定AI角色和行为
        
        Returns:
            str: AI的文本回复
        """
        return self.chat_with_voice_stream(message, system_prompt)
    
    def interactive_chat_stream(self, system_prompt=None):
        """
        启动流式交互式语音对话
        
        Args:
            system_prompt: 系统提示词，用于设定AI角色和行为
        """
        print("=" * 60)
        print("🤖 AI流式语音对话系统")
        print("=" * 60)
        if system_prompt:
            print(f"系统角色: {system_prompt}")
            print("-" * 60)
        print("输入 'exit' 退出对话")
        print("=" * 60)
        
        try:
            while True:
                user_input = input("\n💬 请输入您的问题: ")
                if user_input.strip().lower() == "exit":
                    print("👋 再见！")
                    break
                if not user_input.strip():
                    continue
                
                # 执行流式语音对话
                self.chat_with_voice_stream(user_input, system_prompt)
                
        except KeyboardInterrupt:
            print("\n👋 对话已中断")
        finally:
            # 清理资源
            self.ai_tts.audio_queue.stop()
    
    def interactive_chat_complete(self, system_prompt=None):
        """
        启动一次性交互式语音对话
        
        Args:
            system_prompt: 系统提示词，用于设定AI角色和行为
        """
        print("=" * 60)
        print("🤖 AI一次性语音对话系统")
        print("=" * 60)
        if system_prompt:
            print(f"系统角色: {system_prompt}")
            print("-" * 60)
        print("输入 'exit' 退出对话")
        print("=" * 60)
        
        try:
            while True:
                user_input = input("\n💬 请输入您的问题: ")
                if user_input.strip().lower() == "exit":
                    print("👋 再见！")
                    break
                if not user_input.strip():
                    continue
                
                # 执行一次性语音对话
                self.chat_with_voice_complete(user_input, system_prompt)
                
        except KeyboardInterrupt:
            print("\n👋 对话已中断")
        finally:
            # 清理资源
            self.ai_tts.audio_queue.stop()
    
    def interactive_chat(self, system_prompt=None):
        """
        启动交互式语音对话（默认使用流式）
        
        Args:
            system_prompt: 系统提示词，用于设定AI角色和行为
        """
        self.interactive_chat_stream(system_prompt)
    
    def set_tts_voice(self, vcn):
        """
        设置TTS发音人
        
        Args:
            vcn: 发音人ID，如 'x5_lingfeiyi_flow'
        """
        self.ai_tts.vcn = vcn
        print(f"TTS发音人已设置为: {vcn}")
    
    def set_ai_model(self, model):
        """
        设置AI模型
        
        Args:
            model: 模型名称，如 'generalv3.5'
        """
        # 这里可以扩展支持不同模型
        print(f"AI模型已设置为: {model}")
    
    def text_to_speech(self, text):
        """
        将文本转换为语音并播放
        
        Args:
            text: 要转换的文本
        
        Returns:
            bool: 转换是否成功
        """
        if not text.strip():
            print("文本为空，无法转换")
            return False
            
        print(f"正在将文本转换为语音: {text}")
        
        # 创建临时文件用于音频数据
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # 调用TTS合成到临时文件
            self.ai_tts._synthesize_to_file(text, temp_file_path)
            
            # 检查文件是否生成成功
            if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 1000:
                print(f"[开始播放音频]")
                # 直接播放音频
                if self.ai_tts._play_complete_audio(temp_file_path):
                    print(f"[音频播放完成]")
                    return True
                else:
                    print(f"[音频播放失败]")
                    return False
            else:
                print("音频文件生成失败或不完整，无法播放。")
                return False
                
        except Exception as e:
            print(f"文本转语音失败: {e}")
            return False
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except:
                pass
    
    def interactive_text_to_speech(self):
        """
        启动交互式文本转语音模式
        """
        print("=" * 60)
        print("🔊 纯文本转语音系统")
        print("=" * 60)
        print("输入文本将直接转换为语音并播放")
        print("输入 'exit' 退出")
        print("=" * 60)
        
        try:
            while True:
                user_input = input("\n📝 请输入要转换的文本: ")
                if user_input.strip().lower() == "exit":
                    print("👋 再见！")
                    break
                if not user_input.strip():
                    print("请输入有效的文本")
                    continue
                
                # 执行文本转语音
                self.text_to_speech(user_input)
                
        except KeyboardInterrupt:
            print("\n👋 程序已中断")
        finally:
            # 清理资源
            self.ai_tts.audio_queue.stop()

# 便捷函数
def create_ai_voice_chat(api_key=None, system_prompt=None, tts_config=None):
    """
    创建AI语音对话实例
    
    Args:
        api_key: OpenAI API密钥
        system_prompt: 系统提示词
        tts_config: TTS配置
    
    Returns:
        AIVoiceChat: AI语音对话实例
    """
    return AIVoiceChat(api_key=api_key, tts_config=tts_config)

def quick_chat_stream(message, system_prompt=None):
    """
    快速流式语音对话
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词
    
    Returns:
        str: AI回复
    """
    chat = AIVoiceChat()
    return chat.chat_with_voice_stream(message, system_prompt)

def quick_chat_complete(message, system_prompt=None):
    """
    快速一次性语音对话
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词
    
    Returns:
        str: AI回复
    """
    chat = AIVoiceChat()
    return chat.chat_with_voice_complete(message, system_prompt)

def quick_chat(message, system_prompt=None):
    """
    快速语音对话（默认使用流式）
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词
    
    Returns:
        str: AI回复
    """
    return quick_chat_stream(message, system_prompt)

def quick_text_to_speech(text):
    """
    快速文本转语音
    
    Args:
        text: 要转换的文本
    
    Returns:
        bool: 转换是否成功
    """
    chat = AIVoiceChat()
    return chat.text_to_speech(text)

# 使用示例
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "realtime":
            realtime_tts()
        elif sys.argv[1] == "ai_chat":
            ai_tts = RealtimeAITTS()
            ai_tts.interactive_ai_chat()
        elif sys.argv[1] == "ai_chat_complete":
            ai_tts = RealtimeAITTS()
            ai_tts.interactive_ai_chat_complete()
        elif sys.argv[1] == "voice_chat":
            # 新的语音对话接口（流式）
            chat = AIVoiceChat()
            system_prompt = "你是一个友好的AI助手，请用简洁明了的语言回答问题。"
            chat.interactive_chat_stream(system_prompt)
        elif sys.argv[1] == "voice_chat_complete":
            # 新的语音对话接口（一次性）
            chat = AIVoiceChat()
            system_prompt = "你是一个友好的AI助手，请用简洁明了的语言回答问题。"
            chat.interactive_chat_complete(system_prompt)
        elif sys.argv[1] == "text_to_speech":
            # 新的纯文本转语音接口
            chat = AIVoiceChat()
            chat.interactive_text_to_speech()
        else:
            print("使用方法:")
            print("  python TTS.py                    # 基础TTS测试")
            print("  python TTS.py realtime           # 实时TTS模式")
            print("  python TTS.py ai_chat            # AI流式对话模式")
            print("  python TTS.py ai_chat_complete   # AI一次性对话模式")
            print("  python TTS.py voice_chat         # 新接口流式对话")
            print("  python TTS.py voice_chat_complete # 新接口一次性对话")
            print("  python TTS.py text_to_speech     # 纯文本转语音模式")
    else:
        main(
            appid="daa9d5d9",
            api_secret="YTBkNzA5MGVlNzYzNDVkMDk2MzcwOTIy",
            api_key="c52e142d8749090d0caa6c0fab03d2d1",
            url="wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6",
            # 待合成文本
            text="你好",
            # 发音人参数 - 使用支持的发音人
            vcn="x5_lingfeiyi_flow",
            save_file_name="./test.mp3"
        )
