#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
能力评估功能模块
从test_result_questions.json读取能力评估题目，使用QA-API进行面试问答
"""

import json
import os
import sys
from datetime import datetime

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

class AbilityAssessment:
    def __init__(self):
        """初始化能力评估功能"""
        self.questions_data = None
        self.candidate_name = ""
    
    def create_qa_api(self):
        """创建新的QA-API实例"""
        return InterviewQA()
    
    def load_questions(self, questions_file="test_result_questions.json"):
        """从JSON文件加载面试题目"""
        try:
            if not os.path.exists(questions_file):
                print(f"❌ 题目文件 {questions_file} 未找到")
                return False
            
            with open(questions_file, 'r', encoding='utf-8') as f:
                self.questions_data = json.load(f)
            
            # 提取候选人姓名
            self.candidate_name = self.questions_data.get('candidate_name', '面试者')
            
            print(f"✅ 面试题目加载成功")
            print(f"📋 面试者: {self.candidate_name}")
            print(f"🎯 面试岗位: {self.questions_data.get('interview_position', '未知')}")
            print(f"⚡ 严格模式: {self.questions_data.get('strict_mode', False)}")
            
            return True
            
        except FileNotFoundError:
            print(f"❌ 题目文件 {questions_file} 未找到")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ JSON文件解析错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 加载题目文件时出错: {e}")
            return False
    
    def get_ability_questions(self):
        """获取能力评估题目"""
        if not self.questions_data:
            print("❌ 请先加载题目文件")
            return []
        
        ability_questions = self.questions_data.get('questions', {}).get('能力评估', [])
        
        if not ability_questions:
            print("❌ 未找到能力评估题目")
            return []
        
        print(f"📝 找到 {len(ability_questions)} 个能力评估题目:")
        for i, q in enumerate(ability_questions):
            print(f"  {i+1}. {q.get('question', '')} (重要度: {q.get('importance', 'N/A')}, 难度: {q.get('difficulty', 'N/A')})")
        
        return ability_questions
    
    def conduct_ability_interview(self, num_questions=2):
        """进行能力评估面试"""
        print(f"\n=== 能力评估面试开始 ===")
        print(f"👤 面试者: {self.candidate_name}")
        
        # 获取能力评估题目
        ability_questions = self.get_ability_questions()
        
        if not ability_questions:
            print("❌ 没有可用的能力评估题目")
            return False
        
        # 限制题目数量
        questions_to_ask = ability_questions[:num_questions]
        print(f"\n🎯 将进行 {len(questions_to_ask)} 个能力评估问题的面试")
        
        success_count = 0
        
        for i, question_data in enumerate(questions_to_ask):
            question_text = question_data.get('question', '')
            importance = question_data.get('importance', 'N/A')
            difficulty = question_data.get('difficulty', 'N/A')
            
            print(f"\n" + "="*60)
            print(f"📋 第 {i+1} 题 / 共 {len(questions_to_ask)} 题")
            print(f"🎯 重要度: {importance} | 难度: {difficulty}")
            print(f"❓ 问题: {question_text}")
            print("="*60)
            
            # 使用QA-API进行提问
            section_name = f"能力评估-第{i+1}题"
            
            try:
                # 为每个问题创建新的QA-API实例，避免ASR资源重用问题
                qa_api = self.create_qa_api()
                success = qa_api.ask_question(question_text, section_name)
                if success:
                    success_count += 1
                    print(f"✅ 第 {i+1} 题完成")
                else:
                    print(f"❌ 第 {i+1} 题失败")
                
                # 题目间间隔
                if i < len(questions_to_ask) - 1:
                    print(f"\n⏳ 准备下一题...")
                    import time
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                print(f"\n👋 用户中断面试")
                break
            except Exception as e:
                print(f"❌ 第 {i+1} 题出现错误: {e}")
                continue
        
        # 面试总结
        print(f"\n" + "="*60)
        print(f"📊 能力评估面试总结")
        print(f"✅ 成功完成: {success_count}/{len(questions_to_ask)} 题")
        print(f"📝 结果已保存到 QA.md")
        print(f"🕒 面试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        return success_count > 0
    
    def show_all_questions(self):
        """显示所有能力评估题目"""
        ability_questions = self.get_ability_questions()
        
        if not ability_questions:
            return
        
        print(f"\n📋 所有能力评估题目:")
        for i, q in enumerate(ability_questions):
            print(f"\n--- 第 {i+1} 题 ---")
            print(f"问题: {q.get('question', '')}")
            print(f"重要度: {q.get('importance', 'N/A')}")
            print(f"难度: {q.get('difficulty', 'N/A')}")

def main():
    """主函数"""
    ability_assessment = AbilityAssessment()
    
    print("=== 能力评估功能 ===")
    
    # 1. 加载题目
    if not ability_assessment.load_questions():
        return
    
    # 2. 显示题目概览
    ability_assessment.show_all_questions()
    
    # 3. 进行面试（前两题）
    print(f"\n🚀 开始能力评估面试...")
    ability_assessment.conduct_ability_interview(num_questions=2)

if __name__ == "__main__":
    main() 