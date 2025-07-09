"""
测试 messager.py 的功能
"""
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
        self.token = None
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
    assert "Receiver Test" == receiver.received_messages[0]
