# Проверки локальной доработки — 2026-09-21

Образ: `local/openhands-canvas:1.20.0-sdk1.49.1-system-prompt.1`

Image ID: `sha256:79c650eea206223ef17d0716e9b9face7f9df25f16d98b4b1d3eb1f0a7c01074`.
Версии/commits и hashes патчей: `manifest.json`.

## Автоматические проверки

- Canvas: 33 теста редактора и создания разговоров прошли.
- TypeScript typecheck, ESLint затронутых модулей, Ruff Python-патча,
  проверка полноты переводов и production Docker build прошли.
- SDK/Server: **352 passed**, 13 deselected (upstream stress/live exclusions).
  Profiles, settings, profile API и conversation start; итоговый лог
  `artifacts/logs/openhands-verification.log`. Восемь предупреждений upstream —
  устаревшее имя HTTP 422 в FastAPI/Starlette.
- Новые проверки покрывают `null`, `""`, многострочный Unicode-текст с Jinja-подобными
  скобками без интерполяции, сохранение, resolver, settings, Agent, SystemPromptEvent,
  seed, восстановление Agent и отсутствие переноса текста в другой профиль.
- API принимает поле только у OpenHands-профиля; ACP отклоняет его.
- Canvas отклоняет несовпадающую выбранную LLM вместо сброса собственного промпта.
- Скрипт отката проверен на синтетических JSON: dry-run, backup, сохранение остальных
  полей и повторный запуск. Получившийся профиль успешно прочитан исходным SDK;
  исходный SDK также прочитал сохранённый Agent с собственным промптом.

## Firefox и реальный API

Browser plugin not available; использован локальный Playwright + Firefox headless.
Стенд localhost:19100/19101, без production volumes, ключей и MCP-подключений.
Проверяемый путь: Settings → Agent profiles → создать → сохранить → открыть снова
→ пустой промпт → выключить override. Все шаги прошли; API вернул точный текст,
затем пустую строку, затем `null`. Страница не пустая, заголовок/URL правильные,
нет framework overlay. Во время проверки не зарегистрированы pageerror;
отдельная проверка console не зарегистрировала warning/error.
Скриншот: `artifacts/profile-editor-firefox.png`.

Через реальный Agent Server созданы три изолированных разговора. Сообщение отправлено
с `run: false`, чтобы материализовать SystemPromptEvent без запуска LLM:

| Профиль | Статический SystemPromptEvent |
| --- | --- |
| trace-corpus | `EXACT CORPUS BASE {{ verbatim }}` дословно |
| trace-default | штатный промпт OpenHands |
| trace-empty | пустая строка |

Сохранённое доказательство: `artifacts/system-prompt-events.json`.
Наличие отдельного динамического контекста ожидаемо; он не удаляется этим патчем.
Проверка выполнения реальных задач моделью и качества RAG не входила в эту доработку.

## Перенос и границы

`manage.py prepare` проверен на чистом каталоге: загрузка закреплённых commits,
проверка hashes, `git apply --check`, применение и точное сравнение итогового diff.
После финальных изменений тестов все три итоговых patch-файла дополнительно
применены к чистым checkout с проверкой полного совпадения diff.
Compose overlay разрешается в один и тот же custom image для всех трёх сервисов.

Рабочие контейнеры, профили, промпты, секреты и основной Compose не менялись.
Тестовый стенд после проверки остановлен. Применение custom image к рабочей
установке — отдельный шаг по README.
