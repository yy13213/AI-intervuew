# -*- encoding:utf-8 -*-
import json

def parse_rtasr_result(result_json):
    """
    解析讯飞实时语音转写的JSON结果
    """
    try:
        result = json.loads(result_json)
        
        if result.get("action") == "started":
            return "连接成功，开始转写..."
        
        elif result.get("action") == "result":
            # 直接处理result中的data字段
            data = result.get("data", "")
            if data:
                # 尝试解析data字段
                try:
                    data_obj = json.loads(data)
                    # 提取转写文本
                    text = ""
                    if "cn" in data_obj and "st" in data_obj["cn"]:
                        st = data_obj["cn"]["st"]
                        if "rt" in st:
                            for rt_item in st["rt"]:
                                if "ws" in rt_item:
                                    for ws_item in rt_item["ws"]:
                                        if "cw" in ws_item:
                                            for cw_item in ws_item["cw"]:
                                                text += cw_item.get("w", "")
                    return text.strip()
                except:
                    # 如果data不是JSON格式，直接返回
                    return data
        
        elif result.get("action") == "error":
            return f"错误: {result_json}"
        
        else:
            # 处理没有action字段的情况，可能是直接的转写结果
            if "cn" in result and "st" in result["cn"]:
                st = result["cn"]["st"]
                if "rt" in st:
                    text = ""
                    for rt_item in st["rt"]:
                        if "ws" in rt_item:
                            for ws_item in rt_item["ws"]:
                                if "cw" in ws_item:
                                    for cw_item in ws_item["cw"]:
                                        text += cw_item.get("w", "")
                    return text.strip()
            
            return f"未知结果: {result_json}"
            
    except Exception as e:
        return f"解析错误: {e}"

def format_result(result_json):
    """
    格式化显示转写结果
    """
    parsed = parse_rtasr_result(result_json)
    if parsed and parsed != "连接成功，开始转写...":
        return f"转写结果: {parsed}"
    return parsed

if __name__ == "__main__":
    # 测试解析器
    test_result = '{"seg_id":9,"cn":{"st":{"rt":[{"ws":[{"cw":[{"sc":0.00,"w":"床","wp":"n","rl":"0","wb":1,"wc":0.00,"we":24}],"wb":1,"we":24},{"cw":[{"sc":0.00,"w":"前","wp":"n","rl":"0","wb":25,"wc":0.00,"we":44}],"wb":25,"we":44},{"cw":[{"sc":0.00,"w":"明","wp":"n","rl":"0","wb":45,"wc":0.00,"we":64}],"wb":45,"we":64},{"cw":[{"sc":0.00,"w":"月光","wp":"n","rl":"0","wb":65,"wc":0.00,"we":116}],"wb":65,"we":116}]}],"bg":"0","type":"0","ed":"4790"}},"ls":true}'
    print(format_result(test_result)) 