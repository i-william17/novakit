core/
├── security/        # JWT, rate limit, IP block, hashing
├── middlewares/     # auth, rate limit, CORS, request id
├── logging/         # logger config, structlog
├── metrics/         # prometheus, opentelemetry
├── cache/           # redis client, cache helpers
├── db/              # engine, session, alembic helpers
├── events/          # event bus / signals
└── utils/           # framework utils ONLY
