"""
消息发布-订阅系统核心模块

模块用途:
    实现线程安全的发布-订阅模式，支持同步/异步消息处理和批量发布

作者: [刘晓青]
版本: 1.0.0
创建日期: [2025-07-09]

主要功能:
    - 单例模式的消息器(Messager)
    - 支持泛型的消息接收接口(IReceiver)
    - 线程安全的订阅/取消订阅机制（基于 threading.Lock）
    - 高性能批量消息发布（单次锁获取优化）
    - 内置异步消息处理支持

使用示例:
    >>> from messager import messager
    >>> messager.subscribe(my_handler)
"
"""

import inspect
from typing import Callable, Dict, Type, Protocol
import threading
import asyncio

from typing import TypeVar

T = TypeVar("T")


class IReceiver(Protocol[T]):
    """
    泛型消息接收者接口，支持接收指定类型的消息

    类型参数:
        T: 消息类型，可以是任意类型

    属性:
        token (object): 接收者标识符，用于区分不同的订阅者

    方法:
        receive(message: T) -> None: 接收并处理消息的核心方法
    """

    token: object

    def receive(self, message: T) -> None:
        """
        接收并处理指定类型的消息

        参数:
            message (T): 需要处理的消息对象

        返回值:
            None

        注意:
            实现此方法时应当处理可能的消息处理异常
        """
        ...


class Messager:
    """
    消息器核心实现类(单例模式)

    特性:
    - 线程安全的消息订阅/发布机制
    - 支持同步和异步消息处理
    - 支持批量消息发布
    - 内置接收者管理功能

    使用示例:
    >>> messager = Messager()
    >>> def handler(msg: str): print(f"收到消息: {msg}")
    >>> messager.subscribe(handler)
    >>> messager.publish("测试消息")
    """

    _INSTANCE = None
    _LOCK = threading.RLock()  # 使用可重入锁

    def __new__(cls):
        """单例模式"""
        with cls._LOCK:
            if cls._INSTANCE is None:
                cls._INSTANCE = super().__new__(cls)
        return cls._INSTANCE

    def __init__(self):
        """初始化"""
        if not hasattr(self, "subscribers"):
            with self._LOCK:
                self.subscribers: Dict[Type, Dict[object, set[Callable]]] = {}
                self.subscriberSet = set()

    def _get_parameter_type(self, subscriber: Callable) -> Type:
        """
        获取参数类型
        @param subscriber: 订阅者函数
        @return: 参数类型
        """
        signature = inspect.signature(subscriber)
        parameters = signature.parameters
        if len(parameters) != 1:
            raise ValueError(
                "订阅者函数必须只有一个参数。"
                "示例: def my_subscriber(message: MessageType):"
            )
        first_param = next(iter(parameters.values()))
        parameter_type = first_param.annotation
        if parameter_type is inspect.Parameter.empty:
            raise ValueError(
                "订阅者函数的参数必须包含类型注解。"
                "示例: def my_subscriber(message: MessageType):"
            )
        return parameter_type

    def subscribe(self, subscriber: Callable, token: object = None) -> None:
        """
        订阅消息

        参数:
            subscriber (Callable): 订阅者函数或IReceiver实例，必须包含类型注解
            token (object, optional): 订阅者标识符，用于分组管理

        异常:
            ValueError: 当重复订阅或参数不符合要求时抛出

        示例:
            >>> def handler(msg: str): print(f"收到: {msg}")
            >>> messager.subscribe(handler)
        """
        with self._LOCK:
            if subscriber in self.subscriberSet:
                raise ValueError(
                    f"订阅者函数 {subscriber.__name__} 已存在。"
                    "如需重新订阅，请先取消订阅。"
                )
            parameter_type = self._get_parameter_type(subscriber)
            if parameter_type not in self.subscribers:
                self.subscribers[parameter_type] = {}
            if token not in self.subscribers[parameter_type]:
                self.subscribers[parameter_type][token] = set()
            subscribers = self.subscribers[parameter_type][token]
            self.subscriberSet.add(subscriber)
            subscribers.add(subscriber)

    def subscribeReceiver(self, receiver: IReceiver[T]) -> None:
        """
        订阅消息
        @param receiver: IReceiver实例
        """
        with self._LOCK:
            if receiver in self.subscriberSet:
                raise ValueError(
                    f"接收者实例 {receiver.__class__.__name__} 已存在。"
                    "如需重新订阅，请先取消订阅。"
                )
            parameter_type = self._get_parameter_type(receiver.receive)
            if parameter_type not in self.subscribers:
                self.subscribers[parameter_type] = {}
            token = receiver.token if hasattr(receiver, "token") else None
            if token not in self.subscribers[parameter_type]:
                self.subscribers[parameter_type][token] = set()
            subscribers = self.subscribers[parameter_type][token]
            self.subscriberSet.add(receiver)
            subscribers.add(receiver.receive)

    def publish(self, message: object, token: object = None) -> None:
        """
        发布消息

        参数:
            message (object): 消息对象，类型决定分发给哪些订阅者
            token (object, optional): 目标订阅者分组标识

        实现说明:
            - 自动匹配消息类型对应的订阅者
            - 支持同步和异步处理模式
            - 线程安全的消息分发
        """
        message_type = type(message)

        # 最小化锁的范围，仅获取订阅者列表
        with self._LOCK:
            subscriberMap = self.subscribers.get(message_type, {})
            subscribers = subscriberMap.get(token, set()).copy()

        # 在锁外执行实际的消息分发
        for subscriber in subscribers:
            if asyncio.iscoroutinefunction(subscriber):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(subscriber(message))
                finally:
                    loop.close()
            else:
                subscriber(message)

    def batch_publish(self, messages: list[object], token: object = None) -> None:
        """
        批量发布消息

        参数:
            messages (list[object]): 消息对象列表
            token (object, optional): 目标订阅者分组标识

        性能优化:
            - 使用单次锁获取提高吞吐量
            - 自动合并相同类型的消息处理

        注意:
            列表中的消息类型应当尽量统一以提高性能

        @param token: 可选的标识符，用于指定要通知的订阅者
        """
        if not messages:
            return

        # 使用defaultdict简化分组逻辑
        from collections import defaultdict

        message_groups = defaultdict(list)
        for msg in messages:
            message_groups[type(msg)].append(msg)

        # 为每种消息类型获取订阅者
        for msg_type, msgs in message_groups.items():
            with self._LOCK:
                subscriberMap = self.subscribers.get(msg_type, {})
                subscribers = subscriberMap.get(token, set()).copy()

            # 分发消息
            for subscriber in subscribers:
                for msg in msgs:
                    if asyncio.iscoroutinefunction(subscriber):
                        asyncio.create_task(subscriber(msg))
                    else:
                        subscriber(msg)

    def unsubscribe(self, subscriber: Callable) -> None:
        """
        取消订阅

        参数:
            subscriber (Callable): 订阅者函数或IReceiver实例

        注意:
            - 如果订阅者不存在会静默失败
            - 线程安全的取消操作

        示例:
            >>> messager.unsubscribe(my_handler)

        @param token: 可选的标识符，用于指定要取消订阅的订阅者
        """
        with self._LOCK:
            parameter_type = self._get_parameter_type(subscriber)
            if parameter_type in self.subscribers:
                for _, subscribers in self.subscribers[parameter_type].items():
                    if subscriber in subscribers:
                        subscribers.discard(subscriber)
            self.subscriberSet.discard(subscriber)

    def unsubscribeReceiver(self, receiver: IReceiver[T]) -> None:
        """
        取消订阅
        @param receiver: IReceiver实例
        """
        with self._LOCK:
            parameter_type = self._get_parameter_type(receiver.receive)
            if parameter_type in self.subscribers:
                for _, subscribers in self.subscribers[parameter_type].items():
                    if receiver.receive in subscribers:
                        subscribers.discard(receiver.receive)
            self.subscriberSet.discard(receiver)
