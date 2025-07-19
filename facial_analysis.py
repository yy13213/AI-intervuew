#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
面试表情肢体分析模块
定期拍摄照片并使用AI分析面试者的微表情和肢体动作
"""

import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
import cv2
import time
import os
from urllib.parse import urlparse, urlencode
import ssl
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
import websocket

# 星火图像理解API配置
appid = "daa9d5d9"
api_secret = "YTBkNzA5MGVlNzYzNDVkMDk2MzcwOTIy"
api_key = "c52e142d8749090d0caa6c0fab03d2d1"
imageunderstanding_url = "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image"

class FacialAnalysis:
    def __init__(self):
        """初始化面试表情肢体分析功能"""
        self.is_analyzing = False
        self.analysis_results = []
        self.photo_count = 0
        self.cap = None
        
    def initialize_camera(self):
        """初始化摄像头"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("❌ 无法打开摄像头")
                return False
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print("✅ 摄像头初始化成功")
            return True
        except Exception as e:
            print(f"❌ 摄像头初始化失败: {e}")
            return False
    
    def capture_photo(self):
        """拍摄照片"""
        if not self.cap or not self.cap.isOpened():
            print("❌ 摄像头未初始化")
            return None
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                print("❌ 拍照失败")
                return None
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interview_photo_{timestamp}_{self.photo_count}.jpg"
            
            # 保存照片
            cv2.imwrite(filename, frame)
            self.photo_count += 1
            
            print(f"📸 拍摄照片: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 拍照过程出错: {e}")
            return None
    
    def analyze_image(self, image_path):
        """分析图像中的微表情和肢体动作"""
        try:
            # 读取图像并转换为base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_base64 = str(base64.b64encode(image_data), 'utf-8')
            
            # 构建分析问题
            analysis_prompt = """
            请仔细分析这张面试照片中人物的微表情和肢体动作，并给出专业评估。

            分析要点：
            1. 微表情分析：眼神接触、面部表情、情绪状态、自信程度、
            是否出现紧张（如抿嘴、挑眉、频繁眨眼）、表情是否自然、有微笑
            2. 肢体动作分析：坐姿、手势、身体语言、专业形象、
            是否有眼神交流、是否坐姿自然、无小动作、手势是否得当

            评分标准（1-10分）：
            - 9-10分：表现优秀，非常专业自信
            - 7-8分：表现良好，基本符合要求  
            - 5-6分：表现一般，有改进空间
            - 3-4分：表现较差，需要重点改善
            - 1-2分：表现很差，严重影响面试效果

            请返回JSON格式，包含：
            1. "facial_score": 微表情评分(1-10)
            2. "body_score": 肢体动作评分(1-10)  
            3. "facial_suggestions": 微表情改进建议(简洁明确)
            4. "body_suggestions": 肢体动作改进建议(简洁明确)
            """
            
            # 构建消息
            question = [
                {"role": "user", "content": image_base64, "content_type": "image"},
                {"role": "user", "content": analysis_prompt}
            ]
            
            # 调用AI分析
            result = self.call_spark_api(question)
            return result
            
        except Exception as e:
            print(f"❌ 图像分析失败: {e}")
            return None
    
    def call_spark_api(self, question):
        """调用星火API进行图像分析"""
        self.api_result = ""
        self.api_finished = False
        
        try:
            wsParam = Ws_Param(appid, api_key, api_secret, imageunderstanding_url)
            websocket.enableTrace(False)
            wsUrl = wsParam.create_url()
            
            ws = websocket.WebSocketApp(
                wsUrl,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            ws.appid = appid
            ws.question = question
            ws.parent = self
            
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            
            # 等待API完成
            timeout = 30  # 30秒超时
            start_time = time.time()
            while not self.api_finished and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.api_finished:
                return self.parse_api_result(self.api_result)
            else:
                print("❌ API调用超时")
                return None
                
        except Exception as e:
            print(f"❌ API调用失败: {e}")
            return None
    
    def parse_api_result(self, result_text):
        """解析API返回结果"""
        try:
            # 清理markdown代码块标记
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # 尝试解析JSON
            try:
                analysis = json.loads(result_text)
                
                # 验证必要字段
                required_fields = ['facial_score', 'body_score', 'facial_suggestions', 'body_suggestions']
                if all(field in analysis for field in required_fields):
                    # 确保评分是数值类型
                    analysis['facial_score'] = float(analysis['facial_score'])
                    analysis['body_score'] = float(analysis['body_score'])
                    
                    # 限制评分范围在1-10之间
                    analysis['facial_score'] = max(1, min(10, analysis['facial_score']))
                    analysis['body_score'] = max(1, min(10, analysis['body_score']))
                    
                    return analysis
                else:
                    print("⚠️ API返回字段不完整，使用备用解析")
                    return self.create_default_analysis(result_text)
                    
            except json.JSONDecodeError:
                print("⚠️ JSON解析失败，使用备用解析")
                return self.create_default_analysis(result_text)
                
        except Exception as e:
            print(f"❌ 结果解析失败: {e}")
            return self.create_default_analysis("解析失败")
    
    def create_default_analysis(self, raw_text):
        """创建默认分析结果"""
        return {
            "facial_score": 7.0,
            "body_score": 7.0,
            "facial_suggestions": f"AI分析异常，原始返回: {raw_text[:100]}...",
            "body_suggestions": "建议保持自然的面部表情和专业的坐姿"
        }
    
    def on_message(self, ws, message):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            code = data['header']['code']
            if code != 0:
                print(f'❌ API请求错误: {code}, {data}')
                ws.close()
            else:
                choices = data["payload"]["choices"]
                status = choices["status"]
                content = choices["text"][0]["content"]
                
                ws.parent.api_result += content
                
                if status == 2:  # 完成
                    ws.parent.api_finished = True
                    ws.close()
        except Exception as e:
            print(f"❌ 消息处理错误: {e}")
            ws.close()
    
    def on_error(self, ws, error):
        """处理WebSocket错误"""
        print(f"❌ WebSocket错误: {error}")
        ws.parent.api_finished = True
    
    def on_close(self, ws, close_status_code, close_msg):
        """处理WebSocket关闭"""
        ws.parent.api_finished = True
    
    def on_open(self, ws):
        """处理WebSocket连接建立"""
        thread.start_new_thread(self.run, (ws,))
    
    def run(self, ws, *args):
        """发送数据到WebSocket"""
        try:
            data = json.dumps(gen_params(appid=ws.appid, question=ws.question))
            ws.send(data)
        except Exception as e:
            print(f"❌ 发送数据失败: {e}")
            ws.close()
    
    def start_analysis(self, duration_seconds=300):
        """开始表情肢体分析"""
        print("="*60)
        print("📹 开始面试表情肢体分析")
        print("="*60)
        
        if not self.initialize_camera():
            return False
        
        self.is_analyzing = True
        start_time = time.time()
        
        print(f"⏰ 分析时长: {duration_seconds}秒")
        print(f"📸 拍照间隔: 10秒")
        print(f"🤖 AI分析: 微表情 + 肢体动作")
        print("-" * 60)
        
        try:
            while self.is_analyzing and (time.time() - start_time) < duration_seconds:
                # 拍摄照片
                photo_path = self.capture_photo()
                
                if photo_path:
                    # AI分析
                    print(f"🤖 正在分析 {photo_path}...")
                    analysis = self.analyze_image(photo_path)
                    
                    if analysis:
                        # 添加时间戳
                        analysis['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        analysis['photo_path'] = photo_path
                        self.analysis_results.append(analysis)
                        
                        # 显示分析结果
                        print(f"📊 微表情评分: {analysis['facial_score']}/10")
                        print(f"📊 肢体动作评分: {analysis['body_score']}/10")
                        print(f"💡 微表情建议: {analysis['facial_suggestions']}")
                        print(f"💡 肢体动作建议: {analysis['body_suggestions']}")
                        print(f"📝 已保存第 {len(self.analysis_results)} 次分析记录")
                        print("-" * 60)
                    else:
                        print("⚠️ 分析失败，跳过本次")
                    
                    # 删除临时照片（可选）
                    try:
                        os.remove(photo_path)
                    except:
                        pass
                
                # 等待10秒
                if self.is_analyzing:
                    time.sleep(10)
                    
        except KeyboardInterrupt:
            print("\n👋 用户中断分析")
        except Exception as e:
            print(f"❌ 分析过程出错: {e}")
        finally:
            self.stop_analysis()
        
        return True
    
    def stop_analysis(self):
        """停止分析"""
        self.is_analyzing = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("✅ 表情肢体分析已停止")
        print(f"📊 总共收集了 {len(self.analysis_results)} 次分析记录")
    
    def get_analysis_summary(self):
        """获取分析总结"""
        if not self.analysis_results:
            return None
        
        # 计算平均分
        total_facial = sum(r['facial_score'] for r in self.analysis_results)
        total_body = sum(r['body_score'] for r in self.analysis_results)
        count = len(self.analysis_results)
        
        avg_facial = total_facial / count
        avg_body = total_body / count
        overall_score = (avg_facial + avg_body) / 2
        
        # 收集所有建议（去重）
        facial_suggestions = set()
        body_suggestions = set()
        
        for result in self.analysis_results:
            facial_suggestions.add(result['facial_suggestions'])
            body_suggestions.add(result['body_suggestions'])
        
        # 计算分数分布统计
        facial_scores = [r['facial_score'] for r in self.analysis_results]
        body_scores = [r['body_score'] for r in self.analysis_results]
        
        summary = {
            "analysis_count": count,
            "avg_facial_score": round(avg_facial, 2),
            "avg_body_score": round(avg_body, 2),
            "overall_score": round(overall_score, 2),
            "max_facial_score": max(facial_scores),
            "min_facial_score": min(facial_scores),
            "max_body_score": max(body_scores),
            "min_body_score": min(body_scores),
            "facial_suggestions": list(facial_suggestions),
            "body_suggestions": list(body_suggestions),
            "detailed_results": self.analysis_results,
            "analysis_start_time": self.analysis_results[0]['timestamp'] if self.analysis_results else None,
            "analysis_end_time": self.analysis_results[-1]['timestamp'] if self.analysis_results else None
        }
        
        return summary
    
    def save_analysis_report(self, filename="facial_analysis_report.json"):
        """保存完整的分析报告到JSON文件"""
        try:
            summary = self.get_analysis_summary()
            if summary:
                # 添加详细的分析元数据
                report_data = {
                    "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_analysis_count": summary["analysis_count"],
                    "analysis_duration": f"{summary['analysis_start_time']} 到 {summary['analysis_end_time']}",
                    "performance_summary": {
                        "微表情表现": {
                            "平均分": summary["avg_facial_score"],
                            "最高分": summary["max_facial_score"],
                            "最低分": summary["min_facial_score"],
                            "表现评级": self.get_performance_grade(summary["avg_facial_score"])
                        },
                        "肢体动作表现": {
                            "平均分": summary["avg_body_score"],
                            "最高分": summary["max_body_score"],
                            "最低分": summary["min_body_score"],
                            "表现评级": self.get_performance_grade(summary["avg_body_score"])
                        },
                        "综合表现": {
                            "综合平均分": summary["overall_score"],
                            "综合评级": self.get_performance_grade(summary["overall_score"])
                        }
                    },
                    "改进建议汇总": {
                        "微表情建议": summary["facial_suggestions"],
                        "肢体动作建议": summary["body_suggestions"]
                    },
                    "详细分析记录": summary["detailed_results"]
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 完整分析报告已保存到 {filename}")
                print(f"📊 报告包含 {summary['analysis_count']} 次分析记录")
                print(f"😊 微表情平均分: {summary['avg_facial_score']}/10")
                print(f"🤝 肢体动作平均分: {summary['avg_body_score']}/10") 
                print(f"🎯 综合平均分: {summary['overall_score']}/10")
                return True
            else:
                print("❌ 没有分析数据可保存")
                return False
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return False
    
    def get_performance_grade(self, score):
        """根据评分获取表现等级"""
        if score >= 9:
            return "优秀"
        elif score >= 7:
            return "良好"
        elif score >= 5:
            return "一般"
        elif score >= 3:
            return "较差"
        else:
            return "很差"


class Ws_Param(object):
    """WebSocket参数类"""
    def __init__(self, APPID, APIKey, APISecret, imageunderstanding_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(imageunderstanding_url).netloc
        self.path = urlparse(imageunderstanding_url).path
        self.ImageUnderstanding_url = imageunderstanding_url

    def create_url(self):
        """生成WebSocket连接URL"""
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        signature_sha = hmac.new(
            self.APISecret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }

        url = self.ImageUnderstanding_url + '?' + urlencode(v)
        return url


def gen_params(appid, question):
    """生成API请求参数"""
    data = {
        "header": {
            "app_id": appid
        },
        "parameter": {
            "chat": {
                "domain": "imagev3",
                "temperature": 0.5,
                "top_k": 4,
                "max_tokens": 2028,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


def main():
    """主函数"""
    analyzer = FacialAnalysis()
    
    print("🎯 AI面试表情肢体分析系统")
    print("功能: 每10秒拍照分析微表情和肢体动作")
    
    # 询问分析时长
    try:
        duration = int(input("请输入分析时长(秒，默认300秒): ") or "300")
    except ValueError:
        duration = 300
    
    # 开始分析
    success = analyzer.start_analysis(duration)
    
    if success and analyzer.analysis_results:
        # 显示详细总结
        summary = analyzer.get_analysis_summary()
        if summary:
            print("\n" + "="*80)
            print("📊 面试表情肢体分析总结报告")
            print("="*80)
            print(f"📸 总分析次数: {summary['analysis_count']}")
            print(f"⏰ 分析时段: {summary['analysis_start_time']} - {summary['analysis_end_time']}")
            print()
            print("📈 微表情分析结果:")
            print(f"  😊 平均得分: {summary['avg_facial_score']}/10 ({analyzer.get_performance_grade(summary['avg_facial_score'])})")
            print(f"  📊 得分范围: {summary['min_facial_score']} - {summary['max_facial_score']}")
            print()
            print("📈 肢体动作分析结果:")
            print(f"  🤝 平均得分: {summary['avg_body_score']}/10 ({analyzer.get_performance_grade(summary['avg_body_score'])})")
            print(f"  📊 得分范围: {summary['min_body_score']} - {summary['max_body_score']}")
            print()
            print("🎯 综合表现:")
            print(f"  🏆 综合平均分: {summary['overall_score']}/10 ({analyzer.get_performance_grade(summary['overall_score'])})")
            print()
            print("💡 改进建议汇总:")
            if summary['facial_suggestions']:
                print("  微表情方面:")
                for i, suggestion in enumerate(summary['facial_suggestions'], 1):
                    print(f"    {i}. {suggestion}")
            if summary['body_suggestions']:
                print("  肢体动作方面:")
                for i, suggestion in enumerate(summary['body_suggestions'], 1):
                    print(f"    {i}. {suggestion}")
            print("="*80)
            
            # 保存完整报告
            analyzer.save_analysis_report()
    else:
        print("❌ 分析未成功完成或没有收集到数据")


if __name__ == "__main__":
    main() 