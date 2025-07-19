# AI语音对话系统

一个基于讯飞星火大模型和TTS的智能语音对话系统，支持流式和一次性两种语音合成模式，以及纯文本转语音功能。

## 🌟 功能特性

### 核心功能
- **AI智能对话**：基于讯飞星火认知大模型
- **实时语音合成**：使用讯飞超拟人语音合成API
- **纯文本转语音**：直接将输入文本转换为语音播放
- **双模式支持**：流式合成和一次性合成
- **音频队列管理**：确保播放顺序正确
- **系统提示词**：支持自定义AI角色和行为

### 三种使用模式

#### 🔴 流式模式 (Stream Mode)
- AI回答时实时显示文字
- 按句子分段合成音频
- 合成一段立即播放一段
- 响应更快，体验更流畅
- 适合实时对话场景

#### 🔵 一次性模式 (Complete Mode)
- AI完整回答后显示全部文字
- 一次性合成完整音频
- 等待时间较长但音频更连贯
- 适合需要完整音频的场景

#### 🟢 纯文本转语音模式 (Text-to-Speech Mode)
- 直接输入文本转换为语音
- 不调用AI对话功能
- 快速响应，适合朗读文本
- 支持批量文本转换

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

### 主要依赖
- `openai` - AI对话接口
- `websocket-client` - WebSocket通信
- `pygame` - 音频播放
- `requests` - HTTP请求

## 🚀 快速开始

### 命令行使用

#### 1. 流式语音对话
```bash
python TTS.py voice_chat
```

#### 2. 一次性语音对话
```bash
python TTS.py voice_chat_complete
```

#### 3. 纯文本转语音模式
```bash
python TTS.py text_to_speech
```

#### 4. 原始流式对话
```bash
python TTS.py ai_chat
```

#### 5. 原始一次性对话
```bash
python TTS.py ai_chat_complete
```

#### 6. 基础TTS测试
```bash
python TTS.py
```

### Python代码使用

#### 基础使用
```python
from TTS import AIVoiceChat

# 创建对话实例
chat = AIVoiceChat()

# 流式语音对话
response = chat.chat_with_voice_stream("你好，请介绍一下你自己")

# 一次性语音对话
response = chat.chat_with_voice_complete("你好，请介绍一下你自己")

# 纯文本转语音
success = chat.text_to_speech("这是一段要转换为语音的文本")
```

#### 交互式文本转语音
```python
chat = AIVoiceChat()

# 启动交互式文本转语音模式
chat.interactive_text_to_speech()
```

#### 批量文本转语音
```python
chat = AIVoiceChat()

texts = [
    "第一段文本：欢迎使用文本转语音系统。",
    "第二段文本：这是一个批量转换的示例。",
    "第三段文本：每段文本都会依次转换为语音并播放。"
]

for text in texts:
    success = chat.text_to_speech(text)
    print(f"转换结果: {'成功' if success else '失败'}")
```

#### 使用系统提示词
```python
system_prompt = "你是一个专业的Python编程助手，请用简洁的语言回答问题。"
chat = AIVoiceChat()

response = chat.chat_with_voice_stream("如何学习Python？", system_prompt)
```

#### 交互式对话
```python
chat = AIVoiceChat()
system_prompt = "你是一个友好的AI助手，请用简洁明了的语言回答问题。"

# 启动交互式流式对话
chat.interactive_chat_stream(system_prompt)

# 启动交互式一次性对话
chat.interactive_chat_complete(system_prompt)
```

#### 自定义配置
```python
# 自定义TTS配置
custom_tts_config = {
    "appid": "your_appid",
    "api_secret": "your_api_secret", 
    "api_key": "your_api_key",
    "url": "your_websocket_url",
    "vcn": "x5_lingfeiyi_flow"
}

chat = AIVoiceChat(tts_config=custom_tts_config)
chat.set_tts_voice("x5_lingfeiyi_flow")
```

#### 便捷函数
```python
from TTS import quick_chat_stream, quick_chat_complete, quick_text_to_speech

# 快速流式对话
response = quick_chat_stream("请给我讲个笑话", "你是一个幽默的AI助手")

# 快速一次性对话
response = quick_chat_complete("请给我讲个笑话", "你是一个幽默的AI助手")

# 快速文本转语音
success = quick_text_to_speech("这是一段要转换为语音的文本")
```

## 📋 API接口说明

### AIVoiceChat 类

#### 初始化
```python
AIVoiceChat(api_key=None, base_url=None, tts_config=None)
```

#### 主要方法

| 方法 | 描述 | 参数 |
|------|------|------|
| `chat_with_voice_stream()` | 流式语音对话 | message, system_prompt=None |
| `chat_with_voice_complete()` | 一次性语音对话 | message, system_prompt=None |
| `text_to_speech()` | 纯文本转语音 | text |
| `interactive_text_to_speech()` | 交互式文本转语音 | 无 |
| `interactive_chat_stream()` | 交互式流式对话 | system_prompt=None |
| `interactive_chat_complete()` | 交互式一次性对话 | system_prompt=None |
| `set_tts_voice()` | 设置TTS发音人 | vcn |
| `set_ai_model()` | 设置AI模型 | model |

### 便捷函数

| 函数 | 描述 | 参数 |
|------|------|------|
| `quick_chat_stream()` | 快速流式对话 | message, system_prompt=None |
| `quick_chat_complete()` | 快速一次性对话 | message, system_prompt=None |
| `quick_text_to_speech()` | 快速文本转语音 | text |
| `create_ai_voice_chat()` | 创建对话实例 | api_key=None, system_prompt=None, tts_config=None |

## ⚙️ 配置说明

### TTS配置参数
```python
tts_config = {
    "appid": "your_appid",           # 讯飞应用ID
    "api_secret": "your_api_secret", # 讯飞API密钥
    "api_key": "your_api_key",       # 讯飞API Key
    "url": "your_websocket_url",     # WebSocket连接地址
    "vcn": "x5_lingfeiyi_flow"       # 发音人ID
}
```

### 支持的发音人
- `x5_lingfeiyi_flow` - 灵飞一（默认）
- `x5_lingxiaorong_flow` - 灵小蓉
- `x5_lingyuzhao_flow` - 灵玉照
- `x5_lingxiaoxuan_flow` - 灵小萱
- 更多发音人请参考讯飞官方文档

## 🔧 技术架构

### 核心组件
1. **AI对话模块** - 基于讯飞星火大模型
2. **TTS合成模块** - 基于讯飞超拟人语音合成
3. **音频队列管理** - 使用优先级队列确保播放顺序
4. **线程池管理** - 并行合成提高效率
5. **音频播放模块** - 基于pygame实现稳定播放

### 工作流程

#### 流式模式
1. AI开始回答，实时显示文字
2. 检测句子结束标记（。！？等）
3. 将句子加入并行合成队列
4. 合成完成后加入音频播放队列
5. 按序号顺序播放音频

#### 一次性模式
1. AI完整回答，显示全部文字
2. 将完整回答一次性合成音频
3. 播放完整音频文件

## 📝 使用示例

运行示例代码：
```bash
python example_usage.py
```

示例包含：
- 基础流式和一次性对话
- 系统提示词使用
- 交互式对话
- 自定义配置
- 便捷函数使用
- 两种模式对比

## 🐛 常见问题

### Q: 音频播放失败怎么办？
A: 确保已安装pygame，并检查音频设备是否正常工作。

### Q: 合成速度慢怎么办？
A: 可以调整合成参数，或使用一次性模式获得更好的音频质量。

### Q: 如何更换发音人？
A: 使用`set_tts_voice()`方法，或修改TTS配置中的`vcn`参数。

### Q: 如何自定义AI角色？
A: 使用`system_prompt`参数设置AI的行为和角色。

## 📄 许可证

本项目基于MIT许可证开源。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**注意**：使用前请确保已正确配置讯飞API密钥和TTS服务权限。 