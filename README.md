# 消息发布-订阅系统核心模块

## 模块用途
实现线程安全的发布-订阅模式，支持同步/异步消息处理和批量发布。

## 作者
刘晓青

## 版本
1.0.0

## 创建日期
2025-07-09

## 主要功能
- 单例模式的消息器（Messager）
- 支持泛型的消息接收接口（IReceiver）
- 线程安全的订阅/取消订阅机制（基于 `threading.Lock`）
- 高性能批量消息发布（单次锁获取优化）
- 内置异步消息处理支持

## 使用示例
```python
from messager import Messager
messager.subscribe(my_handler)
```

---

# 测试 `messager.py` 的功能

```python
import pytest
from messager import Messager, IReceiver

def test_singleton_pattern():
    """测试 Messager 是否为单例"""
    messager1 = Messager()
    messager2 = Messager()
    assert messager1 is messager2

def test_subscribe_and_publish():
    """测试订阅与发布功能"""
    messager = Messager()
    received_messages = []

    def handler(msg: str):
        received_messages.append(msg)

    messager.subscribe(handler)
    messager.publish("Hello, World!")
    assert "Hello, World!" in received_messages

def test_batch_publish():
    """测试批量发布功能"""
    messager = Messager()
    received_messages = []

    def handler(msg: str):
        received_messages.append(msg)

    messager.subscribe(handler)
    messages = ["Message 1", "Message 2", "Message 3"]
    messager.batch_publish(messages)
    assert len(received_messages) == 3
    assert all(msg in received_messages for msg in messages)

def test_unsubscribe():
    """测试取消订阅功能"""
    messager = Messager()
    received_messages = []

    def handler(msg: str):
        received_messages.append(msg)

    messager.subscribe(handler)
    messager.publish("Test Message")
    messager.unsubscribe(handler)
    received_messages.clear()
    messager.publish("Another Message")
    assert len(received_messages) == 0

class MockReceiver(IReceiver[str]):
    """模拟接收者类"""
    def __init__(self):
        self.token = object()
        self.received_messages = []

    def receive(self, message: str) -> None:
        self.received_messages.append(message)

def test_receiver_interface():
    """测试 IReceiver 接口"""
    messager = Messager()
    receiver = MockReceiver()
    messager.subscribeReceiver(receiver)
    messager.publish("Receiver Test")
    assert len(receiver.received_messages) == 1
```

---

以上内容为消息发布-订阅系统核心模块的文档和使用示例，以及相应的功能测试代码。该模块旨在提供线程安全的发布-订阅功能，并支持同步和异步消息处理。
