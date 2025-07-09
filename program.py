import unittest
import asyncio
from messager import Messager, IReceiver


class TestReceiver(IReceiver[str]):
    def __init__(self, token=None):
        self.token = token
        self.received = []
    
    def receive(self, message: str) -> None:
        self.received.append(message)


class TestMessager(unittest.TestCase):
    def setUp(self):
        self.messager = Messager()

    def test_subscribe_and_publish(self):
        """测试订阅和发布功能"""
        received = []

        def subscriber(message: str):
            received.append(message)

        self.messager.subscribe(subscriber, "test_token")
        self.messager.publish("test_message", "test_token")
        self.assertEqual(received, ["test_message"])

    def test_duplicate_subscription(self):
        """测试重复订阅时的异常处理"""
        def subscriber(message: str):
            pass

        self.messager.subscribe(subscriber, "test_token")
        with self.assertRaises(ValueError):
            self.messager.subscribe(subscriber, "test_token")

    def test_unsubscribe(self):
        """测试取消订阅功能"""
        received = []

        def subscriber(message: str):
            received.append(message)

        self.messager.subscribe(subscriber, "test_token")
        self.messager.unsubscribe(subscriber)
        self.messager.publish("test_message", "test_token")
        self.assertEqual(received, [])

    def test_subscribe_receiver(self):
        """测试接收者订阅功能"""
        receiver = TestReceiver("test_token")
        self.messager.subscribeReceiver(receiver)
        self.messager.publish("test_message", "test_token")
        self.assertEqual(receiver.received, ["test_message"])

    def test_unsubscribe_receiver(self):
        """测试取消接收者订阅"""
        receiver = TestReceiver("test_token")
        self.messager.subscribeReceiver(receiver)
        self.messager.unsubscribeReceiver(receiver)
        self.messager.publish("test_message", "test_token")
        self.assertEqual(receiver.received, [])

    def test_batch_publish(self):
        """测试批量发布功能"""
        received = []

        def subscriber(message: str):
            received.append(message)

        self.messager.subscribe(subscriber, "test_token")
        self.messager.batch_publish(["msg1", "msg2", "msg3"], "test_token")
        self.assertEqual(received, ["msg1", "msg2", "msg3"])

    def test_async_subscriber(self):
        """测试异步消息处理"""
        received = []

        async def async_subscriber(message: str):
            received.append(message)

        self.messager.subscribe(async_subscriber, "test_token")
        self.messager.publish("async_message", "test_token")
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.1))
        self.assertEqual(received, ["async_message"])

    def test_batch_publish(self):
        """测试批量发布功能"""
        received = []

        def subscriber(message: str):
            print(f"[Batch Subscriber] 收到消息: {message}")
            received.append(message)

        print("=== 开始测试批量发布功能 ===")
        self.messager.subscribe(subscriber, "batch_token")
        print("已订阅批量消息接收器")
        self.messager.batch_publish(["msg1", "msg2", "msg3"], "batch_token")
        print(f"最终接收到的消息列表: {received}")
        print("=== 验证批量消息 ===")
        self.assertEqual(received, ["msg1", "msg2", "msg3"])

    def test_async_subscriber(self):
        """测试异步订阅者"""
        received = []

        async def async_subscriber(message: str):
            print(f"异步收到消息: {message}")
            received.append(message)

        print("开始测试异步订阅者...")
        self.messager.subscribe(async_subscriber, "async_token")
        self.messager.publish("async_message", "async_token")
        # 需要等待异步任务完成
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.sleep(0.1))
            print(f"异步接收到的消息列表: {received}")
            self.assertEqual(received, ["async_message"])
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
