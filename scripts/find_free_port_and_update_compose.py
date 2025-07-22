import socket
import yaml
import sys

DOCKER_COMPOSE_PATH = '/Users/smeno/Documents/Personal/Projects/cryptosecure-insights/docker-compose.yml'  # Adjust if needed
KAFKA_SERVICE = 'kafka'
KAFKA_PORT = 9092


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def update_docker_compose(port):
    with open(DOCKER_COMPOSE_PATH, 'r') as f:
        compose = yaml.safe_load(f)

    # Update port mapping
    services = compose.get('services', {})
    kafka = services.get(KAFKA_SERVICE, {})
    ports = kafka.get('ports', [])
    new_ports = [f"{port}:9092" if p.endswith(':9092') else p for p in ports]
    kafka['ports'] = new_ports

    # Update advertised listeners
    env = kafka.get('environment', [])
    new_env = []
    for e in env:
        if e.startswith('KAFKA_CFG_ADVERTISED_LISTENERS='):
            new_env.append(f'KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://localhost:{port}')
        else:
            new_env.append(e)
    kafka['environment'] = new_env
    services[KAFKA_SERVICE] = kafka
    compose['services'] = services

    with open(DOCKER_COMPOSE_PATH, 'w') as f:
        yaml.dump(compose, f, default_flow_style=False)
    print(f"Updated docker-compose.yml to use port {port} for Kafka.")


def main():
    port = find_free_port()
    update_docker_compose(port)
    print(f"You can now start Kafka and connect using localhost:{port}")

if __name__ == '__main__':
    main()
