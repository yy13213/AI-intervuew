#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI面试系统主程序
集成所有面试模块，提供完整的面试流程
"""

import json
import os
import sys
import asyncio
import time
from datetime import datetime

# 导入所有面试模块
try:
    # 导入初始化模块
    from init import InterviewAgent
    
    # 导入各个面试功能模块
    from Self_introduction import SelfIntroduction
    from Resume_Digging import ResumeDigging
    from Ability_Assessment import AbilityAssessment  
    from Position_Matching import PositionMatching
    from Professional_Skills import ProfessionalSkills
    from Reverse_Question import ReverseQuestion
    
    # 导入面试总结模块
    from interview_summary import InterviewSummary
    
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保所有必要的模块文件都存在")
    sys.exit(1)

class InterviewSystem:
    def __init__(self):
        """初始化面试系统"""
        self.config_file = "test_result_config.json"
        self.questions_file = "test_result_questions.json"
        self.interview_config = {}
        self.selected_sections = []
        
        # 模块映射
        self.module_mapping = {
            "自我介绍": {
                "class": SelfIntroduction,
                "method": "run_self_introduction",
                "description": "自我介绍环节"
            },
            "简历深挖": {
                "class": ResumeDigging,
                "method": "conduct_resume_interview",
                "description": "简历深挖面试"
            },
            "能力评估": {
                "class": AbilityAssessment,
                "method": "conduct_ability_interview", 
                "description": "能力评估面试"
            },
            "岗位匹配度": {
                "class": PositionMatching,
                "method": "conduct_position_interview",
                "description": "岗位匹配度面试"
            },
            "专业能力测试": {
                "class": ProfessionalSkills,
                "method": "conduct_professional_interview",
                "description": "专业能力测试面试"
            },
            "反问环节": {
                "class": ReverseQuestion,
                "method": "conduct_reverse_qa_session",
                "description": "反问环节"
            }
        }
    
    async def initialize_system(self):
        """初始化系统，生成配置和题目文件"""
        print("="*80)
        print("🚀 AI面试系统初始化")
        print("="*80)
        
        # 检查是否已有配置文件
        if os.path.exists(self.config_file) and os.path.exists(self.questions_file):
            use_existing = input(f"检测到已存在配置文件，是否使用现有配置？(y/n): ").strip().lower()
            if use_existing == 'y':
                print("✅ 使用现有配置文件")
                return self.load_existing_config()
        
        print("\n📋 开始收集面试配置...")
        
        # 运行初始化流程
        try:
            agent = InterviewAgent()
            
            # 1. 收集用户输入
            config = agent.collect_user_input()
            print(f"\n✅ 配置收集完成")
            
            # 2. 并行生成面试题目  
            print(f"\n🎯 开始生成面试题目...")
            questions = await agent.generate_interview_questions()
            
            # 3. 保存配置和题目文件
            agent.save_interview_questions(
                questions, 
                config_filename=self.config_file,
                questions_filename=self.questions_file
            )
            
            print(f"\n✅ 系统初始化完成！")
            print(f"📁 配置文件: {self.config_file}")
            print(f"📁 题目文件: {self.questions_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 初始化过程出错: {e}")
            return False
    
    def load_existing_config(self):
        """加载现有配置"""
        try:
            # 加载配置文件
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.interview_config = config_data['interview_config']
            self.selected_sections = self.interview_config.get('selected_sections', [])
            
            # 检查题目文件
            if not os.path.exists(self.questions_file):
                print(f"❌ 题目文件 {self.questions_file} 不存在")
                return False
            
            print(f"✅ 配置加载成功")
            print(f"📋 面试者: {self.interview_config.get('candidate_name', '未提供')}")
            print(f"🎯 面试岗位: {self.interview_config.get('position', '未知')}")
            print(f"📝 选择板块: {', '.join(self.selected_sections)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return False
    
    def show_interview_plan(self):
        """显示面试计划"""
        print("\n" + "="*80)
        print("📋 面试计划")
        print("="*80)
        
        print(f"👤 面试者: {self.interview_config.get('candidate_name', '未提供')}")
        print(f"🎯 面试岗位: {self.interview_config.get('position', '未知')}")  
        print(f"🔧 技术领域: {self.interview_config.get('tech_domain', '未知')}")
        print(f"⚡ 严格模式: {'是' if self.interview_config.get('strict_mode') else '否'}")
        print(f"📝 面试类型: {self.interview_config.get('interview_type', '未知')}")
        
        print(f"\n🎯 面试流程 (共 {len(self.selected_sections)} 个环节):")
        for i, section in enumerate(self.selected_sections):
            description = self.module_mapping.get(section, {}).get('description', section)
            print(f"  {i+1}. {description}")
        
        print("="*80)
    
    def run_interview_module(self, section_name):
        """运行指定的面试模块"""
        if section_name not in self.module_mapping:
            print(f"❌ 未知的面试模块: {section_name}")
            return False
        
        module_info = self.module_mapping[section_name]
        module_class = module_info["class"]
        method_name = module_info["method"]
        description = module_info["description"]
        
        print(f"\n🚀 开始 {description}")
        print("="*60)
        
        try:
            # 创建模块实例
            module_instance = module_class()
            
            # 获取执行方法
            if hasattr(module_instance, method_name):
                method = getattr(module_instance, method_name)
                
                # 特殊处理不同模块的参数
                if section_name == "自我介绍":
                    success = method(self.config_file)
                elif section_name in ["简历深挖", "能力评估", "岗位匹配度", "专业能力测试"]:
                    # 这些模块需要先加载题目
                    if module_instance.load_questions(self.questions_file):
                        if section_name == "专业能力测试":
                            success = method(num_questions=3)  # 专业能力测试3题
                        else:
                            success = method(num_questions=2)  # 其他模块2题
                    else:
                        success = False
                elif section_name == "反问环节":
                    success = method()  # 反问环节不需要参数，返回历史记录
                    success = True  # 反问环节总是认为成功
                else:
                    success = method()
                
                if success:
                    print(f"✅ {description} 完成")
                    return True
                else:
                    print(f"❌ {description} 失败")
                    return False
            else:
                print(f"❌ 模块 {section_name} 没有方法 {method_name}")
                return False
                
        except Exception as e:
            print(f"❌ 执行 {description} 时出错: {e}")
            return False
    
    async def run_complete_interview(self):
        """运行完整的面试流程"""
        print("\n" + "="*80)
        print("🎬 开始AI面试")
        print("="*80)
        
        start_time = datetime.now()
        completed_sections = []
        failed_sections = []
        
        # 显示面试计划
        self.show_interview_plan()
        
        # 确认开始
        confirm = input(f"\n是否开始面试？(y/n): ").strip().lower()
        if confirm != 'y':
            print("👋 面试取消")
            return
        
        print(f"\n⏰ 面试开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 依次执行每个模块
        for i, section in enumerate(self.selected_sections):
            print(f"\n🔄 进度: {i+1}/{len(self.selected_sections)}")
            
            # 模块间间隔
            if i > 0:
                print(f"⏳ 准备下一个环节...")
                time.sleep(2)
            
            # 执行模块
            success = self.run_interview_module(section)
            
            if success:
                completed_sections.append(section)
            else:
                failed_sections.append(section)
                
                # 询问是否继续
                if i < len(self.selected_sections) - 1:
                    continue_interview = input(f"\n{section} 执行失败，是否继续下一个环节？(y/n): ").strip().lower()
                    if continue_interview != 'y':
                        print("👋 面试提前结束")
                        break
        
        # 面试总结
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n" + "="*80)
        print("📊 面试总结")
        print("="*80)
        print(f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ 总耗时: {duration}")
        print(f"✅ 成功完成: {len(completed_sections)}/{len(self.selected_sections)} 个环节")
        
        if completed_sections:
            print(f"📝 已完成环节:")
            for section in completed_sections:
                print(f"  ✅ {section}")
        
        if failed_sections:
            print(f"❌ 失败环节:")
            for section in failed_sections:
                print(f"  ❌ {section}")
        
        print(f"📁 面试记录已保存到 QA.md")
        print("="*80)
        
        # 询问是否生成面试总结报告
        if completed_sections:  # 只有成功完成的环节才提供总结
            print(f"\n🤔 是否生成AI面试总结报告？")
            generate_summary = input(f"包含评分、评价和改进建议 (y/n): ").strip().lower()
            
            if generate_summary == 'y':
                print(f"\n📊 开始生成面试总结报告...")
                try:
                    summary = InterviewSummary()
                    await summary.run_complete_summary()
                except Exception as e:
                    print(f"❌ 生成面试总结报告失败: {e}")
            else:
                print("👋 跳过面试总结报告生成")
        else:
            print("⚠️ 没有成功完成的面试环节，无法生成总结报告")

async def main():
    """主函数"""
    print("🎯 AI面试系统 v1.0")
    print("支持自我介绍、简历深挖、能力评估、岗位匹配、专业测试、反问环节")
    
    # 创建面试系统
    interview_system = InterviewSystem()
    
    try:
        # 1. 系统初始化
        if not await interview_system.initialize_system():
            print("❌ 系统初始化失败")
            return
        
        # 2. 加载配置
        if not interview_system.load_existing_config():
            print("❌ 配置加载失败")
            return
        
        # 3. 运行完整面试流程
        await interview_system.run_complete_interview()
        
    except KeyboardInterrupt:
        print(f"\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")

if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main()) 