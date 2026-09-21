# Рабочая установка: 2026-09-21

Развёрнут комплект `local-system-prompt-v1` на `/home/ae/services/openhands`.
Все три сервиса используют `local/openhands-canvas:1.20.0-sdk1.49.1-system-prompt.1`,
image ID `sha256:79c650eea206223ef17d0716e9b9face7f9df25f16d98b4b1d3eb1f0a7c01074`.

Перед заменой сервисы остановлены, согласованная резервная копия проверена:
`/home/ae/services/openhands/backups/before-system-prompt-20260921-231456/installation.tar.gz`.
Копия локальная, содержит секреты, в Git не входит.

Проверено после запуска:
- server, canvas, automation: healthy; readiness/health endpoints HTTP 200;
- Canvas через tailnet: HTTP 200, новые строки редактора доступны;
- тестовый Agent Profile сохранил промпт дословно, новый разговор сформировал
  соответствующий SystemPromptEvent; LLM не запускалась;
- тестовый профиль и разговор удалены; сохранилось 9 прежних разговоров;
- существующие агентские и LLM-профили, secrets.env не изменились.

Промпты существующих профилей автоматически не перенастраивались.
Для дальнейших операций Compose использовать оба файла, из каталога сервиса:

```sh
docker compose -f compose.yaml -f customization/compose.custom.yaml up -d
```

Обычный `docker compose up -d` без overlay вернёт upstream image; порядок
безопасного отката описан в README. Push новых коммитов сам по себе ничего
не развёртывает. Данная запись фиксирует результат проверки на указанную дату.
