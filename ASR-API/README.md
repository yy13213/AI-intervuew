# 讯飞实时语音转写API测试

## 项目说明
这是讯飞星火实时语音转写API的Python测试demo，支持将音频文件实时转换为文字。

## 环境要求
- Python 3.6+
- 讯飞开放平台账号和API密钥

## 安装依赖
```bash
pip install -r requirements.txt
```

## 配置说明
在 `python/rtasr_python3_demo.py` 文件中配置您的APPID和APIKey：
```python
app_id = "您的APPID"
api_key = "您的APIKey"
```

## 音频文件要求
- 格式：PCM
- 采样率：16kHz
- 位深度：16bit
- 声道：单声道

## 运行测试
```bash
cd python
python rtasr_python3_demo.py
```

## 测试文件
项目包含测试音频文件 `test_1.pcm`，您也可以使用自己的音频文件进行测试。

## API文档
更多详细信息请参考：[讯飞实时语音转写API文档](https://www.xfyun.cn/doc/asr/rtasr/API.html)

## 注意事项
1. 确保网络连接正常
2. APPID和APIKey需要在讯飞开放平台正确配置
3. 音频文件必须符合格式要求
4. 建议使用WSS协议以提高安全性 