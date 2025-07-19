#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
面试总结评分模块
使用星火大模型对面试各板块进行评分分析，生成综合评价报告
"""

import json
import os
import re
import asyncio
import concurrent.futures
import time
from datetime import datetime
from openai import OpenAI

class InterviewSummary:
    def __init__(self):
        """初始化面试总结功能"""
        # 初始化星火大模型客户端
        self.client = OpenAI(
            api_key='QcGCOyVichfHetzkUDeM:AUoiqAJtarlstnrJMcTI',
            base_url='https://spark-api-open.xf-yun.com/v1/'
        )
        
        # 创建线程池执行器
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)
        
        # 板块权重配置
        self.section_weights = {
            "自我介绍": 0.10,      # 10%
            "简历深挖": 0.20,      # 20%
            "能力评估": 0.15,      # 15%
            "岗位匹配度": 0.10,    # 10%
            "专业能力测试": 0.20,  # 20%
            "反问环节": 0.05       # 5%
        }
        
        # 板块映射（QA.md中的标记到标准板块名称）
        self.section_mapping = {
            "自我介绍": "自我介绍",
            "简历深挖": "简历深挖",
            "能力评估": "能力评估", 
            "岗位匹配度": "岗位匹配度",
            "专业能力测试": "专业能力测试",
            "反问环节": "反问环节"
        }
    
    def parse_qa_md(self, qa_file="QA.md"):
        """解析QA.md文件，提取各板块内容"""
        if not os.path.exists(qa_file):
            print(f"❌ QA文件 {qa_file} 不存在")
            return {}
        
        try:
            with open(qa_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sections = {}
            
            # 解析自我介绍
            self_intro_pattern = r'<!-- START: 自我介绍 -->(.*?)<!-- END: 自我介绍 -->'
            self_intro_match = re.search(self_intro_pattern, content, re.DOTALL)
            if self_intro_match:
                sections["自我介绍"] = self_intro_match.group(1).strip()
            
            # 解析简历深挖（多题模式）
            resume_sections = []
            resume_pattern = r'<!-- START: 简历深挖-第\d+题 -->(.*?)<!-- END: 简历深挖-第\d+题 -->'
            resume_matches = re.findall(resume_pattern, content, re.DOTALL)
            if resume_matches:
                sections["简历深挖"] = '\n\n'.join([match.strip() for match in resume_matches])
            
            # 解析能力评估（多题模式）
            ability_sections = []
            ability_pattern = r'<!-- START: 能力评估-第\d+题 -->(.*?)<!-- END: 能力评估-第\d+题 -->'
            ability_matches = re.findall(ability_pattern, content, re.DOTALL)
            if ability_matches:
                sections["能力评估"] = '\n\n'.join([match.strip() for match in ability_matches])
            
            # 解析岗位匹配度（多题模式）
            position_sections = []
            position_pattern = r'<!-- START: 岗位匹配度-第\d+题 -->(.*?)<!-- END: 岗位匹配度-第\d+题 -->'
            position_matches = re.findall(position_pattern, content, re.DOTALL)
            if position_matches:
                sections["岗位匹配度"] = '\n\n'.join([match.strip() for match in position_matches])
            
            # 解析专业能力测试（多题模式）
            professional_sections = []
            professional_pattern = r'<!-- START: 专业能力测试-第\d+题 -->(.*?)<!-- END: 专业能力测试-第\d+题 -->'
            professional_matches = re.findall(professional_pattern, content, re.DOTALL)
            if professional_matches:
                sections["专业能力测试"] = '\n\n'.join([match.strip() for match in professional_matches])
            
            # 解析反问环节
            reverse_pattern = r'<!-- START: 反问环节 -->(.*?)<!-- END: 反问环节 -->'
            reverse_match = re.search(reverse_pattern, content, re.DOTALL)
            if reverse_match:
                sections["反问环节"] = reverse_match.group(1).strip()
            
            print(f"✅ 解析QA.md成功，找到 {len(sections)} 个板块:")
            for section in sections.keys():
                print(f"  📋 {section}")
            
            return sections
            
        except Exception as e:
            print(f"❌ 解析QA.md失败: {e}")
            return {}
    
    def get_section_prompt(self, section_name, content):
        """根据板块名称生成专门的评分提示词"""
        
        base_instruction = """
        请仔细分析以下面试内容，给出客观公正的评分和建议。
        注意，文字中有些许错误，无需在意，是实时转录产生的问题。

        评分标准：
        - 90-100分：表现优秀，充分展示了相关能力
        - 80-89分：表现良好，基本符合要求
        - 70-79分：表现一般，有改进空间
        - 60-69分：表现较差，需要重点提升
        - 60分以下：表现不合格

        请返回JSON格式，包含：
        1. "score": 数字评分(0-100)
        2. "evaluation": 详细评价(200字以内)
        3. "suggestions": 具体改进建议(150字以内)
        """
        
        section_prompts = {
            "自我介绍": f"""
            {base_instruction}
            
            【自我介绍评分要点】：
            - 逻辑清晰度：介绍是否条理清晰、结构合理
            - 内容相关性：是否突出与岗位相关的经验和技能
            - 表达能力：语言表达是否流畅、自信
            - 时间控制：内容是否简洁有效，避免冗长
            - 个人特色：是否展现出独特优势和个人亮点
            
            面试内容：
            {content}
            """,
            
            "简历深挖": f"""
            {base_instruction}
            
            【简历深挖评分要点】：
            - 回答真实性：对自身经历的描述是否真实可信
            - 细节丰富度：能否提供具体的工作细节和案例
            - 经验总结：是否能从经历中总结出有价值的经验教训
            - 问题应对：面对深入追问时的应答能力
            - 职业连续性：工作经历的逻辑性和发展轨迹
            
            面试内容：
            {content}
            """,
            
            "能力评估": f"""
            {base_instruction}
            
            【能力评估评分要点】：
            - 自我认知：对自身能力的准确认知和客观评价
            - 学习能力：展现的学习意愿和学习方法
            - 解决问题：分析和解决问题的思路和能力
            - 抗压能力：面对挑战和压力时的应对方式
            - 团队协作：在团队中的角色和贡献能力
            
            面试内容：
            {content}
            """,
            
            "岗位匹配度": f"""
            {base_instruction}
            
            【岗位匹配度评分要点】：
            - 岗位理解：对目标岗位职责和要求的理解程度
            - 技能匹配：个人技能与岗位需求的匹配度
            - 职业规划：个人发展方向与岗位发展的一致性
            - 动机真实：求职动机的真实性和合理性
            - 适应能力：适应新岗位和新环境的能力
            
            面试内容：
            {content}
            """,
            
            "专业能力测试": f"""
            {base_instruction}
            
            【专业能力测试评分要点】：
            - 专业知识：核心专业知识的掌握程度
            - 技术深度：对技术细节的理解和应用能力
            - 实践经验：理论结合实践的能力
            - 技术视野：对行业技术趋势的了解
            - 问题解决：运用专业知识解决实际问题的能力
            
            面试内容：
            {content}
            """,
            
            "反问环节": f"""
            {base_instruction}
            
            【反问环节评分要点】：
            - 问题质量：提问是否有针对性和价值
            - 职业关注：是否关注职业发展相关问题
            - 沟通技巧：提问的方式和沟通技巧
            - 思维深度：问题是否体现了深度思考
            - 主动性：展现的主动了解和参与意愿
            
            面试内容：
            {content}
            """
        }
        
        return section_prompts.get(section_name, f"{base_instruction}\n\n面试内容：\n{content}")
    
    def _sync_evaluate_section(self, section_name, content):
        """同步评估单个板块"""
        task_start_time = time.time()
        task_id = f"{section_name}_{int(task_start_time * 1000) % 10000}"
        print(f"🔄 [{task_id}] 开始评估 {section_name}... (时间: {time.strftime('%H:%M:%S')})")
        
        try:
            prompt = self.get_section_prompt(section_name, content)
            
            response = self.client.chat.completions.create(
                model='generalv3.5',
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                temperature=0.3,  # 降低温度以获得更稳定的评分
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content
            
            # 清理markdown代码块标记
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # 解析JSON
            try:
                evaluation = json.loads(result_text)
                
                # 验证必要字段
                if not all(key in evaluation for key in ['score', 'evaluation', 'suggestions']):
                    raise ValueError("缺少必要字段")
                
                # 确保分数在合理范围内
                score = float(evaluation['score'])
                if not 0 <= score <= 100:
                    score = max(0, min(100, score))
                    evaluation['score'] = score
                
                task_end_time = time.time()
                task_time = task_end_time - task_start_time
                
                print(f"📊 [{task_id}] {section_name} 评估统计:")
                print(f"   - 评分: {score}分")
                print(f"   - 耗时: {task_time:.2f} 秒")
                print(f"   - 响应长度: {len(result_text)} 字符")
                
                evaluation['task_time'] = task_time
                evaluation['section'] = section_name
                return evaluation
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ [{task_id}] JSON解析失败，使用备用解析: {e}")
                
                # 备用解析：从文本中提取关键信息
                score_match = re.search(r'(\d+(?:\.\d+)?)', result_text)
                score = float(score_match.group(1)) if score_match else 70
                score = max(0, min(100, score))
                
                task_end_time = time.time()
                task_time = task_end_time - task_start_time
                
                evaluation = {
                    'score': score,
                    'evaluation': f"AI回答格式异常，但估计得分约{score}分。请人工review原始回答: {result_text[:100]}...",
                    'suggestions': "建议重新进行该板块评估以获得更准确的反馈。",
                    'task_time': task_time,
                    'section': section_name
                }
                
                print(f"📊 [{task_id}] {section_name} 备用评估:")
                print(f"   - 估计评分: {score}分")
                print(f"   - 耗时: {task_time:.2f} 秒")
                
                return evaluation
                
        except Exception as e:
            task_end_time = time.time()
            task_time = task_end_time - task_start_time
            print(f"❌ [{task_id}] {section_name} 评估失败: {e}")
            
            # 返回默认评估
            return {
                'score': 60,
                'evaluation': f"评估过程出现技术错误，无法给出准确评分。错误信息: {str(e)[:100]}",
                'suggestions': "建议重新进行面试评估，确保网络连接正常。",
                'task_time': task_time,
                'section': section_name
            }
    
    async def _async_evaluate_section(self, section_name, content):
        """异步评估单个板块"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, self._sync_evaluate_section, section_name, content)
        return result
    
    async def evaluate_all_sections(self, sections_content):
        """并行评估所有板块"""
        start_time = time.time()
        print(f"\n=== 开始并行评估面试表现 ===")
        print(f"开始时间: {time.strftime('%H:%M:%S')}")
        print(f"待评估板块: {list(sections_content.keys())}")
        print(f"使用线程池执行器，最大工作线程数: 6")
        
        # 创建评估任务
        tasks = []
        for section_name, content in sections_content.items():
            if content.strip():  # 只评估有内容的板块
                task = asyncio.create_task(
                    self._async_evaluate_section(section_name, content),
                    name=f"evaluate_{section_name}"
                )
                tasks.append(task)
        
        if not tasks:
            print("❌ 没有可评估的板块内容")
            return {}
        
        print(f"🚀 并行启动 {len(tasks)} 个评估任务...")
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        evaluations = {}
        success_count = 0
        task_times = []
        
        for i, result in enumerate(results):
            if isinstance(result, dict) and 'section' in result:
                section_name = result['section']
                task_time = result.pop('task_time', 0)
                task_times.append(task_time)
                
                evaluations[section_name] = result
                success_count += 1
                print(f"✅ {section_name} 评估完成 (得分: {result['score']}, 耗时: {task_time:.2f}秒)")
            elif isinstance(result, Exception):
                print(f"❌ 评估任务执行出错: {result}")
            else:
                print(f"⚠️ 收到意外的结果类型: {type(result)}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== 并行评估完成 ===")
        print(f"完成时间: {time.strftime('%H:%M:%S')}")
        print(f"总耗时: {total_time:.2f} 秒")
        print(f"成功评估: {success_count}/{len(tasks)} 个板块")
        
        # 性能分析
        if len(task_times) > 1:
            max_time = max(task_times)
            min_time = min(task_times)
            avg_time = sum(task_times) / len(task_times)
            
            print(f"\n📊 性能分析:")
            print(f"   - 最长评估耗时: {max_time:.2f} 秒")
            print(f"   - 最短评估耗时: {min_time:.2f} 秒")
            print(f"   - 平均评估耗时: {avg_time:.2f} 秒")
            print(f"   - 并行效率: {(max_time/total_time)*100:.1f}%")
        
        return evaluations
    
    def calculate_final_score(self, evaluations):
        """计算加权最终得分"""
        if not evaluations:
            return 0, 0
        
        total_weighted_score = 0
        total_used_weight = 0
        
        print(f"\n📊 得分计算详情:")
        print(f"{'板块名称':<12} {'得分':<8} {'权重':<8} {'加权得分':<10}")
        print("-" * 50)
        
        for section_name, evaluation in evaluations.items():
            score = evaluation['score']
            weight = self.section_weights.get(section_name, 0)
            weighted_score = score * weight
            
            total_weighted_score += weighted_score
            total_used_weight += weight
            
            print(f"{section_name:<12} {score:<8.1f} {weight*100:<7.1f}% {weighted_score:<10.2f}")
        
        # 计算最终得分
        if total_used_weight > 0:
            final_score = total_weighted_score / total_used_weight
        else:
            final_score = 0
        
        print("-" * 50)
        print(f"{'总计':<12} {'':<8} {total_used_weight*100:<7.1f}% {total_weighted_score:<10.2f}")
        print(f"\n🎯 最终得分: {final_score:.2f} / 100")
        
        return final_score, total_used_weight
    
    def generate_summary_report(self, evaluations, final_score, total_weight):
        """生成面试总结报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 等级评定
        if final_score >= 90:
            grade = "优秀"
            recommendation = "强烈推荐录用"
        elif final_score >= 80:
            grade = "良好"
            recommendation = "推荐录用"
        elif final_score >= 70:
            grade = "一般"
            recommendation = "考虑录用，需要进一步培训"
        elif final_score >= 60:
            grade = "较差"
            recommendation = "不推荐录用，建议提升后再次面试"
        else:
            grade = "不合格"
            recommendation = "不推荐录用"
        
        # 构建报告
        report = f"""# 面试总结报告

**生成时间**: {timestamp}
**最终得分**: {final_score:.2f} / 100
**评级等级**: {grade}
**录用建议**: {recommendation}

## 📊 各板块详细评估

"""
        
        # 各板块详情
        for section_name, evaluation in evaluations.items():
            weight = self.section_weights.get(section_name, 0)
            report += f"""### {section_name} (权重: {weight*100:.0f}%)

**得分**: {evaluation['score']:.1f} / 100

**评价**: 
{evaluation['evaluation']}

**改进建议**: 
{evaluation['suggestions']}

---

"""
        
        # 总体建议
        report += f"""## 📋 综合建议

基于本次面试的整体表现，该候选人在{len(evaluations)}个评估维度中表现如下：

"""
        
        # 强项和弱项分析
        sorted_sections = sorted(evaluations.items(), key=lambda x: x[1]['score'], reverse=True)
        
        if sorted_sections:
            best_section = sorted_sections[0]
            worst_section = sorted_sections[-1]
            
            report += f"""**表现最佳板块**: {best_section[0]} ({best_section[1]['score']:.1f}分)
**需要改进板块**: {worst_section[0]} ({worst_section[1]['score']:.1f}分)

"""
        
        report += f"""**整体建议**: 
根据{final_score:.1f}分的综合得分，{recommendation}。

**后续行动**: 
"""
        
        if final_score >= 80:
            report += "- 可以进入下一轮面试或直接录用\n- 关注候选人的薪资期望和入职时间\n"
        elif final_score >= 70:
            report += "- 需要针对弱项进行进一步确认\n- 考虑提供相关培训支持\n"
        else:
            report += "- 建议候选人提升相关技能后重新申请\n- 可提供具体的学习建议和资源\n"
        
        report += f"\n**评估完成时间**: {timestamp}\n**评估覆盖权重**: {total_weight*100:.1f}%\n"
        
        return report
    
    def save_summary_report(self, report, filename="interview_summary_report.md"):
        """保存总结报告到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 面试总结报告已保存到 {filename}")
            return True
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return False
    
    async def run_complete_summary(self, qa_file="QA.md"):
        """运行完整的面试总结流程"""
        print("="*80)
        print("📊 AI面试总结评估")
        print("="*80)
        
        # 1. 解析QA.md文件
        print("📋 步骤1: 解析面试记录文件...")
        sections_content = self.parse_qa_md(qa_file)
        
        if not sections_content:
            print("❌ 没有找到可评估的面试内容")
            return False
        
        # 2. 并行评估各板块
        print(f"\n🎯 步骤2: 并行评估 {len(sections_content)} 个面试板块...")
        evaluations = await self.evaluate_all_sections(sections_content)
        
        if not evaluations:
            print("❌ 没有成功评估的板块")
            return False
        
        # 3. 计算最终得分
        print(f"\n🧮 步骤3: 计算加权最终得分...")
        final_score, total_weight = self.calculate_final_score(evaluations)
        
        # 4. 生成总结报告
        print(f"\n📝 步骤4: 生成面试总结报告...")
        report = self.generate_summary_report(evaluations, final_score, total_weight)
        
        # 5. 保存报告
        success = self.save_summary_report(report)
        
        # 6. 显示简要总结
        print(f"\n" + "="*80)
        print("🎯 面试总结完成")
        print("="*80)
        print(f"📊 最终得分: {final_score:.2f} / 100")
        print(f"📋 评估板块: {len(evaluations)} 个")
        print(f"⚖️ 权重覆盖: {total_weight*100:.1f}%")
        print(f"📁 报告文件: interview_summary_report.md")
        print("="*80)
        
        return True

async def main():
    """主函数"""
    summary = InterviewSummary()
    
    # 检查QA.md文件
    if not os.path.exists("QA.md"):
        print("❌ QA.md文件不存在，请先完成面试")
        return
    
    # 运行完整评估
    await summary.run_complete_summary()

if __name__ == "__main__":
    asyncio.run(main()) 