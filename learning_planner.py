import json
from openai import OpenAI

class LearningPlanner:
    def __init__(self):
        self.client = OpenAI(
            api_key='QcGCOyVichfHetzkUDeM:AUoiqAJtarlstnrJMcTI',
            base_url='https://spark-api-open.xf-yun.com/v1/'
        )
        
    def generate_learning_plan(self, position, study_content, study_goal, time_commitment):
        """生成个性化学习计划"""
        prompt = f"""
        请根据以下信息为用户制定详细的学习计划：

        【目标岗位】: {position}
        【学习内容】: {study_content}
        【学习目标】: {study_goal}
        【时间投入】: {time_commitment}

        要求：
        1. 制定分阶段的学习路线图
        2. 推荐具体的学习资源和方法
        3. 提供时间管理建议
        4. 给出学习效果评估方法
        5. 包含可能的挑战及应对策略

        请用清晰的结构化格式输出，适当使用emoji和标题分级。
        """
        
        try:
            response = self.client.chat.completions.create(
                model='generalv3.5',
                messages=[{"role": "user", "content": prompt}],
                stream=True  # 启用流式输出
            )
            return self._parse_streaming_response(response)
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")
    
    def _parse_streaming_response(self, response):
        """解析流式响应"""
        full_response = ""
        try:
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
        except Exception as e:
            raise Exception(f"流式响应解析失败: {str(e)}")
        return full_response
    
    def chat_with_ai(self, messages, new_message):
        """与AI进行对话"""
        try:
            response = self.client.chat.completions.create(
                model='generalv3.5',
                messages=messages + [{"role": "user", "content": new_message}]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")
    
    def get_learning_suggestions(self, learning_type):
        """获取学习建议"""
        suggestions = {
            "技术学习": [
                "制定每日编程练习计划",
                "参与开源项目贡献",
                "观看技术分享视频",
                "阅读官方文档和最佳实践",
                "建立个人技术博客"
            ],
            "管理技能": [
                "学习项目管理方法论（如敏捷、瀑布）",
                "培养团队沟通与协调能力",
                "掌握数据分析和决策工具",
                "参加领导力培训课程",
                "实践员工激励和绩效管理"
            ],
            "语言学习": [
                "制定每日单词学习目标",
                "参与语言交换活动",
                "观看外语影视作品",
                "使用语言学习应用",
                "参加线上/线下语言课程"
            ]
        }
        return suggestions.get(learning_type, []) 