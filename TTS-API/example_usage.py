#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS API 使用示例
演示如何使用纯文本转语音功能
"""

from TTS import AIVoiceChat, quick_text_to_speech

def example_single_text_to_speech():
    """示例：单个文本转语音"""
    print("=" * 50)
    print("示例：单个文本转语音")
    print("=" * 50)
    
    # 方法1：使用便捷函数
    text = "你好，这是一个文本转语音的测试。"
    print(f"转换文本: {text}")
    success = quick_text_to_speech(text)
    print(f"转换结果: {'成功' if success else '失败'}")
    
    print("\n" + "=" * 50)
    
    # 方法2：使用AIVoiceChat类
    chat = AIVoiceChat()
    text2 = "这是第二个测试，使用AIVoiceChat类进行文本转语音。"
    print(f"转换文本: {text2}")
    success2 = chat.text_to_speech(text2)
    print(f"转换结果: {'成功' if success2 else '失败'}")

def example_interactive_text_to_speech():
    """示例：交互式文本转语音"""
    print("=" * 50)
    print("示例：交互式文本转语音")
    print("=" * 50)
    
    chat = AIVoiceChat()
    chat.interactive_text_to_speech()

def example_custom_voice():
    """示例：自定义发音人"""
    print("=" * 50)
    print("示例：自定义发音人")
    print("=" * 50)
    
    # 创建聊天实例
    chat = AIVoiceChat()
    
    # 设置不同的发音人（可选）
    # chat.set_tts_voice("x5_lingfeiyi_flow")  # 默认发音人
    
    # 转换文本
    text = "这是使用自定义发音人的测试。"
    print(f"转换文本: {text}")
    success = chat.text_to_speech(text)
    print(f"转换结果: {'成功' if success else '失败'}")

def example_batch_text_to_speech():
    """示例：批量文本转语音"""
    print("=" * 50)
    print("示例：批量文本转语音")
    print("=" * 50)
    
    texts = [
        "第一段文本：欢迎使用文本转语音系统。",
        "第二段文本：这是一个批量转换的示例。",
        "第三段文本：每段文本都会依次转换为语音并播放。"
    ]
    
    chat = AIVoiceChat()
    
    for i, text in enumerate(texts, 1):
        print(f"\n处理第{i}段文本: {text}")
        success = chat.text_to_speech(text)
        print(f"第{i}段转换结果: {'成功' if success else '失败'}")
        
        # 等待一下，避免音频重叠
        import time
        time.sleep(1)

if __name__ == "__main__":
    print("TTS API 使用示例")
    print("=" * 60)
    
    while True:
        print("\n请选择示例:")
        print("1. 单个文本转语音")
        print("2. 交互式文本转语音")
        print("3. 自定义发音人")
        print("4. 批量文本转语音")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == "1":
            example_single_text_to_speech()
        elif choice == "2":
            example_interactive_text_to_speech()
        elif choice == "3":
            example_custom_voice()
        elif choice == "4":
            example_batch_text_to_speech()
        elif choice == "5":
            print("再见！")
            break
        else:
            print("无效选择，请重新输入。") 