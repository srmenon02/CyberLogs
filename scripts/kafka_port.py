import os
import yaml

DOCKER_COMPOSE_PATH = os.path.join(os.path.dirname(__file__), '../docker-compose.yml')
KAFKA_SERVICE = 'kafka'


def get_kafka_port():
    with open(DOCKER_COMPOSE_PATH, 'r') as f:
        compose = yaml.safe_load(f)
    kafka = compose.get('services', {}).get(KAFKA_SERVICE, {})
    for port_map in kafka.get('ports', []):
        if port_map.endswith(':9092'):
            return int(port_map.split(':')[0])
    # fallback
    return 9092
