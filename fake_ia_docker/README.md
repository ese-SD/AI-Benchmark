# A mettre dans le docker-compose si on veux faire tourner le fake_ia_docker:
```
  fake_ia_docker:
    build:
      context: ./fake_ia_docker
      dockerfile: Dockerfile
    container_name: fake_ia_docker
    depends_on:
      - perf_db
      - kafka
    volumes:
      - ./fake_ia_docker:/app
    networks:
      - kafka-test
```