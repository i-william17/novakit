app/
└── core/
    ├── __init__.py
    ├── config/                <-- ENV, Settings, configuration loading
    │     ├── __init__.py
    │     ├── base.py
    │     ├── database.py
    │     ├── redis.py
    │     ├── logging.py
    │     └── settings.py
    │
    ├── kernel/                <-- App bootstrapping (hooks before app starts)
    │     ├── __init__.py
    │     ├── boot.py
    │     ├── providers/
    │     │     ├── cache_provider.py
    │     │     ├── database_provider.py
    │     │     ├── websocket_provider.py
    │     │     └── logging_provider.py
    │     └── events.py
    │
    ├── cache/                 <-- Redis, caching, pub/sub
    │     ├── __init__.py
    │     ├── redis_client.py
    │     ├── redis_pubsub.py   <-- PUT YOUR CLASS HERE
    │     └── cache_manager.py
    │
    ├── logging/               <-- Logging configuration, formatters, handlers
    │     ├── __init__.py
    │     ├── formatters.py
    │     ├── handlers.py
    │     └── logging_config.py
    │
    ├── cli/                   <-- your powerful console (like Yii2 or Laravel)
    │     ├── __init__.py
    │     ├── main.py          <-- "novakit" command entrypoint
    │     ├── commands/
    │     │     ├── migrate.py
    │     │     ├── queue.py
    │     │     ├── make_module.py
    │     │     └── make_model.py
    │     └── utils.py
    │
    └── utils/                 <-- shared internal utilities
          ├── __init__.py
          ├── time.py
          ├── strings.py
          ├── exceptions.py
          └── decorators.py
