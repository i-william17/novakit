import json
import logging
import asyncio
from typing import Dict, Any, Callable, Optional
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
from datetime import datetime
import os
from functools import wraps

logger = logging.getLogger("shared.messaging")


class AsyncRabbitMQClient:
    """Async RabbitMQ client with connection pooling"""

    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.exchanges: Dict[str, aio_pika.abc.AbstractExchange] = {}
        self.queues: Dict[str, aio_pika.abc.AbstractQueue] = {}

    async def connect(self):
        """Establish async connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(self.connection_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def publish(
            self,
            exchange: str,
            routing_key: str,
            message: Dict[str, Any],
            persistent: bool = True
    ):
        """Publish message to exchange"""
        if not self.channel:
            await self.connect()

        exchange_obj = await self.get_exchange(exchange)

        message_body = json.dumps(message).encode()

        await exchange_obj.publish(
            aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT if persistent else None,
                content_type='application/json',
                headers={
                    'service': os.getenv('SERVICE_NAME', 'unknown'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'message_type': routing_key
                }
            ),
            routing_key=routing_key
        )
        logger.debug(f"Published message to {exchange}:{routing_key}")

    async def get_exchange(self, exchange_name: str, exchange_type: str = 'topic'):
        """Get or declare an exchange"""
        if exchange_name not in self.exchanges:
            self.exchanges[exchange_name] = await self.channel.declare_exchange(
                exchange_name,
                exchange_type,
                durable=True
            )
        return self.exchanges[exchange_name]

    async def declare_queue(self, queue_name: str, durable: bool = True):
        """Declare a queue"""
        if queue_name not in self.queues:
            self.queues[queue_name] = await self.channel.declare_queue(
                queue_name,
                durable=durable,
                arguments={
                    'x-dead-letter-exchange': 'dead_letter_exchange',
                    'x-dead-letter-routing-key': f'dead_letter.{queue_name}'
                }
            )
        return self.queues[queue_name]

    async def bind_queue(self, queue: str, exchange: str, routing_key: str):
        """Bind queue to exchange with routing key"""
        queue_obj = await self.declare_queue(queue)
        exchange_obj = await self.get_exchange(exchange)
        await queue_obj.bind(exchange_obj, routing_key)

    async def consume(self, queue: str, callback: Callable, auto_ack: bool = False):
        """Start consuming messages from queue"""
        queue_obj = await self.declare_queue(queue)

        async def wrapped_callback(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    event = json.loads(message.body.decode())
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Reject message and send to DLQ
                    await message.reject(requeue=False)

        await queue_obj.consume(wrapped_callback, no_ack=auto_ack)
        logger.info(f"Started consuming from queue: {queue}")

    async def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")


# ---------------------------------------------------------
# Async Event Bus with Pub/Sub
# ---------------------------------------------------------
class AsyncEventBus:
    """Async event bus for microservices communication"""

    def __init__(self, rabbitmq_client: AsyncRabbitMQClient):
        self.client = rabbitmq_client
        self.exchange = "microservices.events"
        self.subscriptions: Dict[str, list] = {}

    async def initialize(self):
        """Initialize event bus with required exchanges"""
        # Main exchange
        await self.client.get_exchange(self.exchange, 'topic')

        # Dead letter exchange for failed messages
        await self.client.get_exchange('dead_letter_exchange', 'direct')
        await self.client.declare_queue('dead_letter_queue')
        await self.client.bind_queue('dead_letter_queue', 'dead_letter_exchange', 'dead_letter')

    async def publish_event(
            self,
            event_type: str,
            payload: Dict[str, Any],
            routing_key: Optional[str] = None,
            correlation_id: Optional[str] = None
    ):
        """Publish event to event bus"""
        if not routing_key:
            routing_key = f"event.{event_type}"

        event = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "service": os.getenv("SERVICE_NAME", "unknown"),
            "correlation_id": correlation_id or f"corr_{datetime.utcnow().timestamp()}"
        }

        await self.client.publish(self.exchange, routing_key, event)

    async def subscribe(
            self,
            event_type: str,
            callback: Callable,
            queue_name: Optional[str] = None,
            routing_key: Optional[str] = None
    ):
        """Subscribe to event type"""
        if not queue_name:
            queue_name = f"{os.getenv('SERVICE_NAME', 'unknown')}.{event_type}"

        if not routing_key:
            routing_key = f"event.{event_type}"

        # Store subscription
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(callback)

        # Setup queue and binding
        await self.client.bind_queue(queue_name, self.exchange, routing_key)

        # Start consumer
        asyncio.create_task(
            self.client.consume(queue_name, callback)
        )

        logger.info(f"Subscribed to {event_type} on queue {queue_name}")

    def event_handler(self, event_type: str):
        """Decorator for event handlers"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            # Register handler
            asyncio.create_task(self.subscribe(event_type, wrapper))
            return wrapper

        return decorator


# ---------------------------------------------------------
# Factory function for dependency injection
# ---------------------------------------------------------
_event_bus: Optional[AsyncEventBus] = None


async def get_event_bus() -> AsyncEventBus:
    """Get singleton event bus instance"""
    global _event_bus

    if _event_bus is None:
        rabbitmq_url = os.getenv(
            "RABBITMQ_URL",
            "amqp://admin:securepassword123@rabbitmq:5672/"
        )
        client = AsyncRabbitMQClient(rabbitmq_url)
        await client.connect()

        _event_bus = AsyncEventBus(client)
        await _event_bus.initialize()

    return _event_bus