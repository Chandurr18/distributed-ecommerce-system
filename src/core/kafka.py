from aiokafka import AIOKafkaProducer

# Kafka broker address
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

# Kafka topics
ORDER_EVENTS_TOPIC = "order-events"


def create_kafka_producer():
    return AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
    )