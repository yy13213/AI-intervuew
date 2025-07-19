import json
import asyncio
import aiohttp
from typing import Dict, List, Optional
from openai import OpenAI
import os
import re
import time
import concurrent.futures
from urllib.parse import urlencode
from datetime import datetime
from wsgiref.handlers import format_date_time

class InterviewAgent:
    def __init__(self):
        """初始化面试智能体"""
        self.client = OpenAI(
            api_key='QcGCOyVichfHetzkUDeM:AUoiqAJtarlstnrJMcTI',
            base_url='https://spark-api-open.xf-yun.com/v1/'
        )
        
        # 面试配置
        self.interview_config = {}
        self.resume_content = ""
        
        # 创建线程池执行器
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
    def collect_user_input(self) -> Dict:
        """收集用户输入信息"""
        print("=== 模拟面试智能体初始化 ===")
        
        # 1. 面试者姓名
        candidate_name = input("请输入面试者姓名: ").strip()
        
        # 2. 面试岗位
        position = input("请输入面试岗位: ").strip()
        
        # 3. 目标公司
        target_company = input("请输入目标公司: ").strip()
        
        # 4. 技术领域
        tech_domain = input("请输入技术领域: ").strip()
        
        # 5. 有无简历
        has_resume = input("是否有简历？(y/n): ").strip().lower() == 'y'
        resume_path = ""
        if has_resume:
            resume_path = input("请输入简历文件路径 (默认: resume.txt): ").strip()
            if not resume_path:
                resume_path = "resume.txt"
            self.resume_content = self._load_resume(resume_path)
        
        # 6. 选择单人/多人面试
        interview_type = input("选择面试类型 (单人/多人): ").strip()
        
        # 7. 是否进行严格面试
        strict_mode = input("是否进行严格面试（抗压训练）？(y/n): ").strip().lower() == 'y'
        
        # 8. 六大板块选择
        print("\n请选择面试板块（输入数字，多个用逗号分隔）:")
        print("1. 自我介绍")
        print("2. 简历深挖" + (" (需要简历)" if has_resume else " (无简历，不可选)"))
        print("3. 能力评估")
        print("4. 岗位匹配度")
        print("5. 专业能力测试")
        print("6. 反问环节")
        
        available_sections = ["自我介绍", "简历深挖", "能力评估", "岗位匹配度", "专业能力测试", "反问环节"]
        if not has_resume:
            available_sections.remove("简历深挖")
        
        selected_sections_input = input("请选择板块 (如: 1,3,4,5): ").strip()
        selected_indices = [int(x.strip()) - 1 for x in selected_sections_input.split(',')]
        selected_sections = [available_sections[i] for i in selected_indices if 0 <= i < len(available_sections)]
        
        # 保存配置
        self.interview_config = {
            "candidate_name": candidate_name,
            "position": position,
            "target_company": target_company,
            "tech_domain": tech_domain,
            "has_resume": has_resume,
            "resume_path": resume_path,
            "interview_type": interview_type,
            "strict_mode": strict_mode,
            "selected_sections": selected_sections
        }
        
        return self.interview_config
    
    def _load_resume(self, resume_path: str) -> str:
        """加载简历内容"""
        try:
            with open(resume_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"警告: 简历文件 {resume_path} 未找到")
            return ""
        except Exception as e:
            print(f"读取简历文件时出错: {e}")
            return ""
    
    def _extract_json_from_response(self, response_text: str) -> Dict:
        """从AI响应中提取JSON内容"""
        try:
            # 尝试直接解析
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            try:
                # 查找JSON开始和结束的位置
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_content = response_text[json_start:json_end]
                    return json.loads(json_content)
                else:
                    print(f"无法在响应中找到JSON内容: {response_text[:200]}...")
                    return {}
            except Exception as e:
                print(f"提取JSON失败: {e}")
                print(f"原始响应: {response_text[:200]}...")
                return {}
    
    async def generate_interview_questions(self) -> Dict:
        """并行生成面试题目 - 使用线程池实现真正并行"""
        start_time = time.time()
        print(f"\n=== 开始并行生成面试题目 ===")
        print(f"开始时间: {time.strftime('%H:%M:%S')}")
        print(f"使用线程池执行器，最大工作线程数: 4")
        
        # 准备任务
        tasks = []
        task_info = []
        
        # 任务1: 生成技术题目
        if any(section in self.interview_config["selected_sections"] 
               for section in ["能力评估", "岗位匹配度", "专业能力测试"]):
            task_info.append({
                "name": "技术题目生成",
                "func": self._generate_technical_questions,
                "priority": 1
            })
            print("✓ 已准备技术题目生成任务")
        
        # 任务2: 生成简历深挖题目
        if "简历深挖" in self.interview_config["selected_sections"] and self.interview_config["has_resume"]:
            task_info.append({
                "name": "简历深挖题目生成", 
                "func": self._generate_resume_questions,
                "priority": 2
            })
            print("✓ 已准备简历深挖题目生成任务")
        
        if not task_info:
            print("⚠️ 没有需要生成的任务")
            return {}
        
        print(f"\n🚀 准备并行执行 {len(task_info)} 个任务...")
        print(f"任务列表: {', '.join([info['name'] for info in task_info])}")
        
        # 创建所有任务并立即启动
        print(f"⏰ 任务启动时间: {time.strftime('%H:%M:%S')}")
        for info in task_info:
            task = asyncio.create_task(info["func"]())
            tasks.append(task)
        
        print(f"✅ 所有任务已同时启动")
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        all_questions = {}
        success_count = 0
        task_times = []
        
        for i, result in enumerate(results):
            task_name = task_info[i]["name"]
            
            if isinstance(result, dict):
                # 移除task_time字段，避免污染结果
                task_time = result.pop('task_time', 0)
                task_times.append(task_time)
                
                all_questions.update(result)
                success_count += 1
                print(f"✅ {task_name} 完成 (耗时: {task_time:.2f}秒)")
            elif isinstance(result, Exception):
                print(f"❌ {task_name} 执行出错: {result}")
            else:
                print(f"⚠️ {task_name} 返回了意外的结果类型: {type(result)}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== 并行生成完成 ===")
        print(f"完成时间: {time.strftime('%H:%M:%S')}")
        print(f"总耗时: {total_time:.2f} 秒")
        print(f"成功任务: {success_count}/{len(tasks)}")
        print(f"生成板块数: {len(all_questions)}")
        
        # 性能分析
        if len(task_times) > 1:
            max_individual_time = max(task_times)
            min_individual_time = min(task_times)
            avg_individual_time = sum(task_times) / len(task_times)
            
            print(f"\n📊 性能分析:")
            print(f"   - 最长任务耗时: {max_individual_time:.2f} 秒")
            print(f"   - 最短任务耗时: {min_individual_time:.2f} 秒")
            print(f"   - 平均任务耗时: {avg_individual_time:.2f} 秒")
            print(f"   - 理论最优耗时: {max_individual_time:.2f} 秒")
            print(f"   - 实际总耗时: {total_time:.2f} 秒")
            print(f"   - 并行效率: {(max_individual_time/total_time)*100:.1f}%")
            
            if total_time > max_individual_time * 1.1:  # 允许10%的误差
                print(f"   - ⚠️ 并行效率较低，可能存在API排队或网络延迟")
            else:
                print(f"   - ✅ 并行执行效果良好")
        
        return all_questions
    
    def _sync_generate_technical_questions(self) -> Dict:
        """同步生成技术相关面试题目"""
        task_start_time = time.time()
        task_id = f"技术题目_{int(task_start_time * 1000) % 10000}"
        print(f"🔄 [{task_id}] 开始生成技术题目... (时间: {time.strftime('%H:%M:%S')})")
        
        prompt = f"""请根据以下信息生成面试题目，返回JSON格式：

面试岗位：{self.interview_config['position']}
目标公司：{self.interview_config['target_company']}
技术领域：{self.interview_config['tech_domain']}
严格模式：{'是' if self.interview_config['strict_mode'] else '否'}

请为以下板块生成题目：
1. 能力评估
2. 岗位匹配度  
3. 专业能力测试

要求：
1. 每个板块生成1-2道题目
2. 题目按重要性排序
3. 严格模式下题目难度大幅提高
4. 结合目标公司特点设计相关问题
5. 只返回JSON格式，不要其他内容

返回格式示例：
{{
    "能力评估": [
        {{"question": "请描述您解决过的最复杂的技术问题", "importance": 1, "difficulty": "medium"}},
        {{"question": "您如何评估自己的学习能力？", "importance": 2, "difficulty": "easy"}}
    ],
    "岗位匹配度": [
        {{"question": "您认为这个岗位最需要哪些技能？", "importance": 1, "difficulty": "medium"}},
        {{"question": "您为什么选择这个岗位？", "importance": 2, "difficulty": "easy"}}
    ],
    "专业能力测试": [
        {{"question": "请解释Python中的装饰器模式", "importance": 1, "difficulty": "hard"}},
        {{"question": "Django和Flask的区别是什么？", "importance": 2, "difficulty": "medium"}}
    ]
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model='generalv3.5',  # 技术题目使用generalv3.5模型
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                temperature=0.7,
                max_tokens=2000
            )
            result = response.choices[0].message.content
            
            task_end_time = time.time()
            task_time = task_end_time - task_start_time
            
            print(f"📊 [{task_id}] 技术题目生成统计:")
            print(f"   - 使用模型: generalv3.5")
            print(f"   - AI响应长度: {len(result)} 字符")
            print(f"   - 耗时: {task_time:.2f} 秒")
            print(f"   - 响应前100字符: {result[:100]}...")
            
            result_dict = self._extract_json_from_response(result)
            result_dict['task_time'] = task_time
            return result_dict
        except Exception as e:
            task_end_time = time.time()
            task_time = task_end_time - task_start_time
            print(f"❌ [{task_id}] 生成技术题目时出错: {e}")
            print(f"   - 耗时: {task_time:.2f} 秒")
            
            # 返回默认题目
            default_result = {
                "能力评估": [
                    {"question": "请描述您解决过的最复杂的技术问题", "importance": 1, "difficulty": "medium"},
                    {"question": "您如何评估自己的学习能力？", "importance": 2, "difficulty": "easy"}
                ],
                "岗位匹配度": [
                    {"question": "您认为这个岗位最需要哪些技能？", "importance": 1, "difficulty": "medium"},
                    {"question": "您为什么选择这个岗位？", "importance": 2, "difficulty": "easy"}
                ],
                "专业能力测试": [
                    {"question": "请解释Python中的装饰器模式", "importance": 1, "difficulty": "hard"},
                    {"question": "Django和Flask的区别是什么？", "importance": 2, "difficulty": "medium"}
                ]
            }
            default_result['task_time'] = task_time
            return default_result
    
    def _sync_generate_resume_questions(self) -> Dict:
        """同步生成简历深挖题目"""
        task_start_time = time.time()
        task_id = f"简历深挖_{int(task_start_time * 1000) % 10000}"
        print(f"🔄 [{task_id}] 开始生成简历深挖题目... (时间: {time.strftime('%H:%M:%S')})")
        
        # 获取面试者姓名，如果没有则设为空字符串
        candidate_name = self.interview_config.get('candidate_name', '')
        
        prompt = f"""请根据以下简历内容生成简历深挖面试题目，返回JSON格式：

面试者姓名：{candidate_name if candidate_name else '未提供'}
简历内容：
{self.resume_content}

面试岗位：{self.interview_config['position']}
目标公司：{self.interview_config['target_company']}
技术领域：{self.interview_config['tech_domain']}
严格模式：{'是' if self.interview_config['strict_mode'] else '否'}

要求：
1. 生成2-3道简历深挖题目
2. 题目按重要性排序
3. 重点关注工作经验、技能匹配度、项目经历
4. 严格模式下增加挑战性问题
5. 结合目标公司背景设计相关问题
6. 只返回JSON格式，不要其他内容

返回格式示例：
{{
    "candidate_name": "{candidate_name if candidate_name else ''}",
    "简历深挖": [
        {{"question": "您在贵泽实业有限公司担任行政主管期间，最大的挑战是什么？", "importance": 1, "difficulty": "medium", "focus_area": "工作经验"}},
        {{"question": "您如何管理团队和协调各部门工作？", "importance": 2, "difficulty": "medium", "focus_area": "管理能力"}},
        {{"question": "您的英语六级证书对当前岗位有什么帮助？", "importance": 3, "difficulty": "easy", "focus_area": "技能匹配"}}
    ]
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model='generalv3.5',  # 简历深挖也使用generalv3.5模型（暂时）
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                temperature=0.7,
                max_tokens=2000
            )
            result = response.choices[0].message.content
            
            task_end_time = time.time()
            task_time = task_end_time - task_start_time
            
            print(f"📊 [{task_id}] 简历深挖题目生成统计:")
            print(f"   - 使用模型: generalv3.5")
            print(f"   - AI响应长度: {len(result)} 字符")
            print(f"   - 耗时: {task_time:.2f} 秒")
            print(f"   - 响应前100字符: {result[:100]}...")
            
            result_dict = self._extract_json_from_response(result)
            result_dict['task_time'] = task_time
            return result_dict
        except Exception as e:
            task_end_time = time.time()
            task_time = task_end_time - task_start_time
            print(f"❌ [{task_id}] 生成简历题目时出错: {e}")
            print(f"   - 耗时: {task_time:.2f} 秒")
            
            # 返回默认题目
            default_result = {
                "candidate_name": candidate_name if candidate_name else "",
                "简历深挖": [
                    {"question": "您在贵泽实业有限公司担任行政主管期间，最大的挑战是什么？", "importance": 1, "difficulty": "medium", "focus_area": "工作经验"},
                    {"question": "您如何管理团队和协调各部门工作？", "importance": 2, "difficulty": "medium", "focus_area": "管理能力"},
                    {"question": "您的英语六级证书对当前岗位有什么帮助？", "importance": 3, "difficulty": "easy", "focus_area": "技能匹配"}
                ]
            }
            default_result['task_time'] = task_time
            return default_result
    
    async def _generate_technical_questions(self) -> Dict:
        """异步生成技术相关面试题目 - 使用线程池"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, self._sync_generate_technical_questions)
        return result
    
    async def _generate_resume_questions(self) -> Dict:
        """异步生成简历深挖题目 - 使用线程池"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, self._sync_generate_resume_questions)
        return result
    
    def save_interview_config(self, filename: str = "interview_config.json"):
        """保存面试配置"""
        config_data = {
            "interview_config": self.interview_config,
            "resume_content": self.resume_content
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            print(f"面试配置已保存到 {filename}")
        except Exception as e:
            print(f"保存配置时出错: {e}")
    
    def load_interview_config(self, filename: str = "interview_config.json"):
        """加载面试配置"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self.interview_config = config_data["interview_config"]
                self.resume_content = config_data["resume_content"]
            print(f"面试配置已从 {filename} 加载")
        except FileNotFoundError:
            print(f"配置文件 {filename} 未找到")
        except Exception as e:
            print(f"加载配置时出错: {e}")
    
    def save_interview_questions(self, questions: Dict, config_filename: str = "interview_config.json", questions_filename: str = "interview_questions.json"):
        """分别保存面试配置和题目到不同的JSON文件"""
        try:
            # 保存面试配置
            config_data = {
                "generated_at": datetime.now().isoformat(),
                "interview_config": self.interview_config,
                "resume_content": self.resume_content
            }
            
            with open(config_filename, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 面试配置已保存到 {config_filename}")
            print(f"📊 配置信息包含: 面试者姓名、岗位、技术领域、面试类型、严格模式、选择板块等")
            
            # 保存面试题目
            questions_data = {
                "generated_at": datetime.now().isoformat(),
                "candidate_name": self.interview_config.get('candidate_name', ''),
                "interview_position": self.interview_config.get('position', ''),
                "tech_domain": self.interview_config.get('tech_domain', ''),
                "strict_mode": self.interview_config.get('strict_mode', False),
                "questions": questions
            }
            
            with open(questions_filename, 'w', encoding='utf-8') as f:
                json.dump(questions_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 面试题目已保存到 {questions_filename}")
            print(f"📊 保存的题目板块数: {len(questions)}")
            print(f"📝 题目文件大小: {os.path.getsize(questions_filename)} 字节")
            
            # 统计题目数量
            total_questions = 0
            for section, section_questions in questions.items():
                if isinstance(section_questions, list):
                    total_questions += len(section_questions)
            print(f"📋 总题目数量: {total_questions} 道")
            
        except Exception as e:
            print(f"❌ 保存面试题目时出错: {e}")

async def main():
    """主函数"""
    agent = InterviewAgent()
    
    # 1. 收集用户输入
    config = agent.collect_user_input()
    print("\n=== 收集到的配置信息 ===")
    print(json.dumps(config, ensure_ascii=False, indent=2))
    
    # 2. 并行生成面试题目
    questions = await agent.generate_interview_questions()
    
    # 3. 输出生成的题目
    print("\n=== 生成的面试题目 ===")
    print(json.dumps(questions, ensure_ascii=False, indent=2))
    
    # 4. 分别保存面试配置和题目到JSON文件
    agent.save_interview_questions(questions)
    
    return agent, questions

if __name__ == "__main__":
    # 运行主函数
    agent, questions = asyncio.run(main())
