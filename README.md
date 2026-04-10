# alertmanager-pachka-router

Шлюз для отправки алертов из Prometheus Alertmanager в мессенджер **Пачка** с **маршрутизацией по чатам** по зоне ответственности (по лейблам алерта).

## Как это работает

- Alertmanager отправляет webhook на этот сервис (`POST /alertmanager/webhook`).
- Сервис группирует алерты из одного webhook‑ивента и **раскладывает** их по чатам Пачки согласно правилам (`routes.yaml`).
- Для каждого подходящего чата отправляет сообщение в Пачку через API:
  - `POST https://api.pachca.com/api/shared/v1/messages`
  - `Authorization: Bearer <BOT_TOKEN>`

## Быстрый старт (Docker Compose)

1) Создайте `routes.yaml` на основе примера:

```bash
cp routes.example.yaml routes.yaml
```

2) Создайте `.env`:

```bash
cp .env.example .env
```

3) Запустите:

```bash
docker compose up --build
```

Проверка health:

```bash
curl -sS http://localhost:8080/health
```

## Деплой в Kubernetes

Манифесты лежат в `k8s/` (kustomize).

1) Замените `PACHCA_TOKEN` в `k8s/secret.yaml`.
2) Настройте правила маршрутизации в `k8s/configmap.yaml` (секция `routes.yaml`).
3) Примените:

```bash
kubectl apply -k k8s
```

Webhook URL для Alertmanager внутри кластера:

- `http://alertmanager-pachka-router:8080/alertmanager/webhook`

Важно: в `k8s/deployment.yaml` нужно указать реальный `image:` (образ, доступный вашему кластеру/registry).

## Настройка Alertmanager

В `alertmanager.yml` добавьте receiver с webhook:

```yaml
receivers:
  - name: pachka-router
    webhook_configs:
      - url: http://alertmanager-pachka-router:8080/alertmanager/webhook
        send_resolved: true
```

Дальше в `route` направляйте нужные алерты в receiver `pachka-router` (как обычно в Alertmanager).

## Правила маршрутизации (`routes.yaml`)

Правило выбирает чат Пачки по matchers (лейблам алерта). Можно:

- роутить по `team`, `service`, `namespace`, `severity` и т.д.
- делать fallback‑чат (default)
- отправлять один и тот же алерт в несколько чатов (если совпало несколько правил)

См. `routes.example.yaml`.

## Переменные окружения

- `PACHCA_TOKEN` (обязательно): bot token Пачки
- `PACHCA_BASE_URL` (необязательно): по умолчанию `https://api.pachca.com/api/shared/v1`
- `ROUTES_PATH` (необязательно): путь до `routes.yaml` (по умолчанию `/config/routes.yaml`)
- `PORT` (необязательно): по умолчанию `8080`
- `MESSAGE_MAX_ALERTS` (необязательно): сколько алертов максимум включать в один пост (по умолчанию `20`)
- `WEBHOOK_TOKEN` (необязательно): если задан, то `/alertmanager/webhook` требует заголовок `X-Webhook-Token: <token>`
- `PACHCA_TIMEOUT_SECONDS` (необязательно): таймаут запросов к Pachca (по умолчанию `15`)
- `PACHCA_MAX_ATTEMPTS` (необязательно): количество попыток отправки в Pachca при сетевых ошибках/429/5xx (по умолчанию `3`)

## Метрики

Доступны Prometheus-метрики:

- `GET /metrics`

## Как получить `entity_id` чата в Пачке

Сообщения отправляются в `discussion` (чат) по `entity_id`.

- Через CLI Пачки: найти чат и взять его id (см. доки Пачки).
- Или (если у вас уже есть ссылка/ID чата) использовать его как `entity_id`.

## Форматирование

Сообщение отправляется простым текстом. Внутри:

- заголовок с `status`, количеством алертов, общей важностью (если есть)
- список алертов (кратко: `alertname`, `instance`, `severity`, `summary`)
- ссылка `generatorURL` (если есть)

