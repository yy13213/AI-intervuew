#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反问环节功能模块
使用QA-API录音收集用户问题，调用星火大模型判断意图并回答
"""

import json
import os
import sys
import random
from datetime import datetime
from openai import OpenAI

# 导入QA-API模块
sys.path.append('.')
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("QA_API", "QA-API.py")
    qa_api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qa_api_module)
    InterviewQA = qa_api_module.InterviewQA
except ImportError as e:
    print(f"❌ 导入QA_API失败: {e}")
    print("请确保QA-API.py文件存在")
    sys.exit(1)

class ReverseQuestion:
    def __init__(self):
        """初始化反问环节功能"""
        # 初始化星火大模型客户端
        self.client = OpenAI(
            api_key='QcGCOyVichfHetzkUDeM:AUoiqAJtarlstnrJMcTI',
            base_url='https://spark-api-open.xf-yun.com/v1/'
        )
        
        # 反问历史记录
        self.qa_history = []
        self.round_count = 0
        
        # 面试配置信息
        self.interview_config = {}
        self.load_interview_config()
        
        # 反问提示语列表
        self.question_prompts = [
            "接下来是反问环节，你有什么想问的吗？",
            "还有其他问题吗？",
            "您还有什么想了解的吗？",
            "有什么问题想要咨询的吗？",
            "还有什么疑问需要解答吗？",
            "您还想了解哪些方面的情况？",
            "有什么其他想知道的吗？",
            "还需要了解什么信息吗？"
        ]
    
    def load_interview_config(self, config_file="test_result_config.json"):
        """加载面试配置信息"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.interview_config = config_data.get('interview_config', {})
                print(f"✅ 加载面试配置成功")
            else:
                print(f"⚠️ 配置文件 {config_file} 不存在，使用默认配置")
                self.interview_config = {}
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
            self.interview_config = {}
    
    def create_qa_api(self):
        """创建新的QA-API实例"""
        return InterviewQA()
    
    def analyze_user_question(self, user_question):
        """使用星火大模型分析用户问题和意图"""
        # 获取配置信息
        target_company = self.interview_config.get('target_company', '某公司')
        position = self.interview_config.get('position', '某岗位')
        tech_domain = self.interview_config.get('tech_domain', '相关技术领域')
        candidate_name = self.interview_config.get('candidate_name', '面试者')
        
        prompt = f"""
        这是一个面试反问环节，面试者向面试官提问。请分析用户的问题并回答。

        【面试背景信息】：
        - 目标公司：{target_company}
        - 面试岗位：{position}
        - 技术领域：{tech_domain}
        - 面试者：{candidate_name}

        用户问题："{user_question}"

        请返回JSON格式的响应，包含以下字段：
        1. "want_to_stop": boolean - 判断用户是否想要结束反问环节（如"没有了"、"结束"、"停止"等）
        2. "answer": string - 对用户问题的专业回答
        3. "question_type": string - 问题类型（如"薪资福利"、"工作内容"、"公司文化"、"发展前景"等）

        注意：
        - 如果用户有不想继续问答的意愿时，将want_to_stop设为true，以停止问答。
        - 回答要专业、详细，符合面试官的身份，但要尽量简洁，不要啰嗦。
        - 回答时要结合{target_company}的背景和{position}岗位的特点
        - 如果问题不清楚，可以要求用户澄清

        返回格式：
        {{
            "want_to_stop": false,
            "answer": "具体的回答内容",
            "question_type": "问题类型"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model='generalv3.5',
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content
            
            # 清理markdown代码块标记
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]  # 去除 ```json
            if result_text.startswith('```'):
                result_text = result_text[3:]   # 去除 ```
            if result_text.endswith('```'):
                result_text = result_text[:-3]  # 去除结尾的 ```
            result_text = result_text.strip()
            
            # 尝试解析JSON
            try:
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                # 如果不是有效JSON，创建默认响应
                return {
                    "want_to_stop": False,
                    "answer": result_text,
                    "question_type": "其他"
                }
                
        except Exception as e:
            print(f"❌ 星火大模型调用失败: {e}")
            return {
                "want_to_stop": False,
                "answer": "抱歉，我暂时无法理解您的问题，请您再详细说明一下。",
                "question_type": "未识别"
            }
    
    def save_qa_history(self, question, answer, question_type, round_num):
        """保存反问历史到QA.md"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 读取现有内容
        existing_content = ""
        if os.path.exists("QA.md"):
            with open("QA.md", 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # 查找反问环节板块
        start_marker = "<!-- START: 反问环节 -->"
        end_marker = "<!-- END: 反问环节 -->"
        
        # 构建新的反问内容
        if start_marker in existing_content and end_marker in existing_content:
            # 获取现有反问内容
            start_pos = existing_content.find(start_marker)
            end_pos = existing_content.find(end_marker)
            current_content = existing_content[start_pos:end_pos + len(end_marker)]
            
            # 在现有内容中添加新的问答
            new_qa = f"""

### 第{round_num}轮反问 - {timestamp}
**问题类型**: {question_type}
**面试者问题**: {question}
**面试官回答**: {answer}
"""
            
            # 插入新问答到结束标记前
            insert_pos = current_content.rfind("<!-- END: 反问环节 -->")
            updated_section = current_content[:insert_pos] + new_qa + "\n" + current_content[insert_pos:]
            
            # 替换整个文档中的反问环节
            updated_content = existing_content[:start_pos] + updated_section + existing_content[end_pos + len(end_marker):]
        else:
            # 创建新的反问环节板块
            new_section = f"""<!-- START: 反问环节 -->
## 反问环节 - {timestamp}

### 第{round_num}轮反问 - {timestamp}
**问题类型**: {question_type}
**面试者问题**: {question}
**面试官回答**: {answer}

<!-- END: 反问环节 -->"""
            
            updated_content = existing_content + "\n\n" + new_section
        
        # 保存到文件
        with open("QA.md", 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ 反问记录已保存到 QA.md")
    
    def conduct_reverse_qa_session(self):
        """进行反问环节"""
        print("=== 反问环节开始 ===")
        print("👤 现在轮到您向我提问了")
        
        while True:
            self.round_count += 1
            print(f"\n🔄 第 {self.round_count} 轮反问")
            
            # 1. 使用QA-API录音收集用户问题
            qa_api = self.create_qa_api()
            
            # 随机选择提示语
            if self.round_count == 1:
                question_prompt = self.question_prompts[0]  # 第一轮固定使用第一个
            else:
                question_prompt = random.choice(self.question_prompts[1:])  # 后续轮次随机选择
            
            section_name = f"反问环节-第{self.round_count}轮-录音"
            
            print(f"\n📝 准备录音收集您的问题...")
            try:
                success = qa_api.ask_question(question_prompt, section_name)
                if not success:
                    print("❌ 录音失败，反问环节结束")
                    break
                
                # 获取用户问题
                if hasattr(qa_api, 'all_sentences') and qa_api.all_sentences:
                    user_question = ' '.join([s for s in qa_api.all_sentences if s.strip()])
                elif qa_api.transcription_parts:
                    user_question = qa_api.transcription_parts[-1] if qa_api.transcription_parts else ""
                else:
                    print("⚠️ 未检测到有效问题")
                    continue
                
                print(f"📋 您的问题: {user_question}")
                
            except KeyboardInterrupt:
                print("\n👋 用户中断，反问环节结束")
                break
            except Exception as e:
                print(f"❌ 录音过程出错: {e}")
                continue
            
            # 2. 使用星火大模型分析问题和生成回答
            print(f"🤖 正在分析您的问题...")
            analysis_result = self.analyze_user_question(user_question)
            
            # 3. 判断用户是否想要停止
            if analysis_result.get("want_to_stop", False):
                print("\n🎯 检测到您想要结束反问环节")
                print("📝 感谢您的提问，反问环节结束")
                break
            
            # 4. 获取AI回答
            ai_answer = analysis_result.get("answer", "抱歉，我无法回答这个问题。")
            question_type = analysis_result.get("question_type", "其他")
            
            print(f"\n🎯 问题类型: {question_type}")
            print(f"💬 面试官回答: {ai_answer}")
            
            # 5. 使用TTS播放回答（只播放answer字段内容）
            print(f"\n🎤 播放语音回答...")
            try:
                qa_api_for_answer = self.create_qa_api()
                qa_api_for_answer.play_question(ai_answer)
            except Exception as e:
                print(f"⚠️ 语音播放失败: {e}")
            
            # 6. 保存问答历史
            self.save_qa_history(user_question, ai_answer, question_type, self.round_count)
            self.qa_history.append({
                "round": self.round_count,
                "question": user_question,
                "answer": ai_answer,
                "type": question_type,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            print(f"✅ 第 {self.round_count} 轮反问完成")
            
            # 防止无限循环，最多10轮
            if self.round_count >= 10:
                print(f"\n⏰ 已达到最大反问轮数限制(10轮)，反问环节结束")
                break
        
        # 反问环节总结
        print(f"\n" + "="*60)
        print(f"📊 反问环节总结")
        print(f"✅ 总共进行了 {self.round_count} 轮反问")
        print(f"📝 所有问答已保存到 QA.md")
        print(f"🕒 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        return self.qa_history

def main():
    """主函数"""
    reverse_qa = ReverseQuestion()
    
    print("=== 反问环节功能 ===")
    
    # 开始反问环节
    qa_history = reverse_qa.conduct_reverse_qa_session()
    
    # 显示历史记录
    if qa_history:
        print(f"\n📋 反问历史记录:")
        for record in qa_history:
            print(f"第{record['round']}轮 [{record['type']}]: {record['question']}")

if __name__ == "__main__":
    main() 