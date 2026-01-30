from taskiq import TaskiqScheduler
from taskiq_redis import ListQueueBroker, RedisScheduleSource
from src.core.config import settings

broker = ListQueueBroker(
    url=settings.REDIS_URL,
)

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[RedisScheduleSource(settings.REDIS_URL)],
)

@broker.task
async def dummy_task():
    print("Hello from TaskIQ worker!")
