#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
面试问题API模块
基于Self_introduction.py的逻辑，构建面试问题API
输入题目文本和板块，合成语音播放，接着开启录音转写，保存在QA中指定板块
"""

import json
import time
import threading
import sys
import os
from datetime import datetime

# 添加TTS-API和ASR-API到路径
sys.path.append('TTS-API')
sys.path.append('ASR-API/python')

from TTS import AIVoiceChat
from realtime_rtasr import RealtimeRTASR

class InterviewQA:
    def __init__(self):
        """初始化面试问答功能"""
        # 初始化TTS
        self.tts_chat = AIVoiceChat()
        
        # 初始化ASR
        self.asr = RealtimeRTASR(
            app_id="daa9d5d9",
            api_key="57e1dcd91156c7b12c078b5ad372870b"
        )
        
        # 录音状态
        self.is_recording = False
        self.last_speech_time = 0
    
    def play_question(self, question_text):
        """播放面试问题"""
        print(f"\n🎤 播放面试问题: {question_text}")
        
        try:
            # 使用纯文本转语音模式
            success = self.tts_chat.text_to_speech(question_text)
            if success:
                print("✅ 问题播放完成")
                return True
            else:
                print("❌ 问题播放失败")
                return False
        except Exception as e:
            print(f"❌ 播放问题时出错: {e}")
            return False
    
    def start_recording_with_timeout(self):
        """开始录音，先等待10秒，然后5秒无新转写自动停止"""
        print(f"\n🎙️ 开始录音，请开始自我介绍...")
        print(f"⏰ 录音至少持续10秒，之后5秒无新转写自动停止")
        
        self.transcription_parts = []
        self.is_recording = True
        self.last_speech_time = time.time()
        self.all_sentences = []
        
        # 启动ASR转写
        self.asr.start_recording()
        print("⏳ 等待ASR服务启动...")
        time.sleep(2)
        print("✅ ASR服务已启动，开始录音")
        start_time = time.time()
        
        # 监控线程：先等8秒，再检测5秒无新转写自动停止
        def monitor():
            # 先等8秒
            while self.is_recording and (time.time() - start_time < 8):
                time.sleep(0.2)
            # 8秒后，开始检测3秒无新转写
            last_check_time = self.last_speech_time
            while self.is_recording:
                # 检查是否有新的转写更新
                if self.last_speech_time > last_check_time:
                    last_check_time = self.last_speech_time
                
                if time.time() - self.last_speech_time > 3.0:
                    print(f"\n🔇 3秒无新转写，自动停止录音")
                    self.stop_recording()
                    break
                time.sleep(0.2)
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 实时收集转写内容
        def collect_transcription():
            accumulated_text = ""
            all_transcriptions = []  # 存储所有转写结果
            final_sentences = []     # 存储最终的完整句子
            
            while self.is_recording and self.asr.ws and self.asr.ws.connected:
                try:
                    result = self.asr.ws.recv()
                    if result:
                        result_str = str(result)
                        result_dict = json.loads(result_str)
                        
                        if result_dict.get("action") == "result":
                            from rtasr_result_parser import format_result
                            formatted_result = format_result(result_str)
                            if formatted_result and "转写结果:" in formatted_result:
                                text = formatted_result.split("转写结果:")[-1].strip()
                                if text and text != accumulated_text:
                                    accumulated_text = text
                                    self.last_speech_time = time.time()  # ✅重置静音计时器
                                    
                                    # 存储所有转写结果用于后续分析
                                    all_transcriptions.append(text)
                                    print(f"📝 转写: {text}")
                                    
                                    # 更新转写部分供监控使用
                                    if self.transcription_parts:
                                        self.transcription_parts[-1] = text
                                    else:
                                        self.transcription_parts.append(text)
                        
                        elif result_dict.get("action") == "end":
                            print("📡 收到转写结束信号")
                            break
                            
                except Exception as e:
                    print(f"⚠️ 转写收集异常: {e}")
                    break
            
            # 录音结束后，按照用户逻辑进行句子提取
            print(f"🔍 分析 {len(all_transcriptions)} 个转写结果...")
            
            if all_transcriptions:
                # 显示所有转写结果用于调试
                #print("📝 所有转写结果:")
                #for i, trans in enumerate(all_transcriptions):
                #    print(f"  {i+1}: {trans}")
                
                # 按照用户逻辑进行句子分割
                final_sentences = []
                previous_text = ""
                
                for i, current_text in enumerate(all_transcriptions):
                    #print(f"🔄 处理第{i+1}个转写: '{current_text}' (长度: {len(current_text)})")
                    
                    if previous_text:
                        #print(f"   与上一个比较: '{previous_text}' (长度: {len(previous_text)})")
                        
                        # 如果当前转写比上一个短或长度相等但内容不同，说明进入下一句
                        if (len(current_text) < len(previous_text) or 
                            (len(current_text) == len(previous_text) and current_text != previous_text)):
                            # 保存上一个转写结果（完整的句子）
                            if previous_text.strip():
                                final_sentences.append(previous_text.strip())
                                #print(f"✅ 保存句子: '{previous_text.strip()}'")
                    
                    previous_text = current_text
                
                # 转写终止，保存最后一个转写结果
                if previous_text and previous_text.strip():
                    final_sentences.append(previous_text.strip())
                    #print(f"✅ 保存最后句子: '{previous_text.strip()}'")
                
                #print(f"📋 提取到的句子列表: {final_sentences}")
            
            # 保存最终结果到实例变量
            self.all_sentences = final_sentences if 'final_sentences' in locals() else []
            #print(f"🔍 最终句子结果: {self.all_sentences}")
        
        collect_thread = threading.Thread(target=collect_transcription)
        collect_thread.daemon = True
        collect_thread.start()
        
        # 等待录音结束
        while self.is_recording:
            time.sleep(0.1)
    
    def stop_recording(self):
        """停止录音"""
        if self.is_recording:
            self.is_recording = False
            self.asr.stop_recording()
            print("✅ 录音已停止")
            
            # 等待一下确保获取到最终转写结果
            print("⏳ 等待最终转写结果处理...")
            time.sleep(2)
    
    def save_qa_to_md(self, question, answer, section):
        """保存问答到QA.md文件的指定板块"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 清理转写结果，使用最完整的版本
        if isinstance(answer, list) and answer:
            # 拼接所有句子
            clean_answer = ' '.join([s for s in answer if s.strip()])
        else:
            clean_answer = answer
        
        # 简单的文本清理
        clean_answer = clean_answer.replace("  ", " ").strip()
        
        # 读取现有内容
        existing_content = ""
        if os.path.exists("QA.md"):
            with open("QA.md", 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # 查找指定板块
        start_marker = f"<!-- START: {section} -->"
        end_marker = f"<!-- END: {section} -->"
        
        # 构建新的问答内容
        new_qa = f"""<!-- START: {section} -->
## {section} - {timestamp}

**面试官问题：**
{question}

**面试者回答：**
{clean_answer}

<!-- END: {section} -->"""
        
        # 替换或添加指定板块
        if start_marker in existing_content and end_marker in existing_content:
            # 替换现有内容
            start_pos = existing_content.find(start_marker)
            end_pos = existing_content.find(end_marker) + len(end_marker)
            updated_content = existing_content[:start_pos] + new_qa + existing_content[end_pos:]
        else:
            # 添加新内容
            updated_content = existing_content + "\n\n" + new_qa
        
        # 保存到文件
        with open("QA.md", 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ 问答已保存到 QA.md 的 [{section}] 板块")
        print(f"📝 最终转写结果: {clean_answer}")
    
    def ask_question(self, question_text, section):
        """执行完整的面试问答流程"""
        print(f"=== 面试问答 - {section} ===")
        
        # 1. 播放问题
        if not self.play_question(question_text):
            return False
        
        # 2. 开始录音和转写
        try:
            self.start_recording_with_timeout()
            
            # 等待一下确保句子收集完成
            time.sleep(1)
            
            # 3. 保存问答结果
            if hasattr(self, 'all_sentences') and self.all_sentences:
                # 显示句子分割结果
                print(f"\n🔍 调试信息 - 句子分割结果:")
                for i, sentence in enumerate(self.all_sentences):
                    print(f"  句子{i+1}: {sentence}")
                
                # 使用所有收集到的句子
                self.save_qa_to_md(question_text, self.all_sentences, section)
                print(f"\n📋 问答完成，已保存到QA.md的[{section}]板块")
                final_answer = ' '.join([s for s in self.all_sentences if s.strip()])
                print(f"💬 面试者回答: {final_answer}")
                return True
            elif self.transcription_parts:
                # 显示所有收集到的转写部分
                print(f"\n🔍 调试信息 - 所有转写部分:")
                for i, part in enumerate(self.transcription_parts):
                    print(f"  部分{i+1}: {part}")
                
                # 如果没有句子分割，使用最完整的转写结果
                final_answer = self.transcription_parts[-1] if self.transcription_parts else ""
                self.save_qa_to_md(question_text, final_answer, section)
                print(f"\n📋 问答完成，已保存到QA.md的[{section}]板块")
                print(f"💬 面试者回答: {final_answer}")
                return True
            else:
                print(f"\n⚠️ 未检测到有效回答")
                return False
        except KeyboardInterrupt:
            print(f"\n👋 用户中断，停止录音")
            self.stop_recording()
            return False
        except Exception as e:
            print(f"❌ 录音过程中出错: {e}")
            self.stop_recording()
            return False

def main():
    """主函数 - 示例用法"""
    qa_api = InterviewQA()
    
    # 示例：技术面试问题
    question = "请介绍一下开发"
    section = "技术能力"
    
    # 执行问答
    qa_api.ask_question(question, section)

if __name__ == "__main__":
    main()
