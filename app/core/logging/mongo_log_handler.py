import logging
from pymongo import MongoClient, errors
from datetime import datetime
from config.config import settings  


class MongoLogHandler(logging.Handler):
    """
    Logging handler that automatically creates the collection if missing,
    and writes log records to MongoDB.
    """
    def __init__(self, level=logging.NOTSET):
        super().__init__(level=level)

        try:
            self.client = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=5000)
            self.db = self.client[settings.LOG_DB_NAME]
            self.collection_name = settings.MONGO_LOG_COLLECTION

            # Ensure connection works
            self.client.admin.command("ping")

            # Ensure collection exists
            if self.collection_name not in self.db.list_collection_names():
                self.db.create_collection(self.collection_name)

            # Optional index
            self.db[self.collection_name].create_index("created_at")

            print(f"[MongoLogHandler] Connected to MongoDB: {settings.MONGO_URL}")
            print(f"[MongoLogHandler] Logging to collection: {self.collection_name}")

        except errors.ServerSelectionTimeoutError as e:
            print(f"[MongoLogHandler] MongoDB connection failed: {e}")
            self.client = None
        except Exception as e:
            print(f"[MongoLogHandler] Initialization error: {e}")
            self.client = None

    def emit(self, record: logging.LogRecord) -> None:
        if not self.client:
            return  # Skip logging if Mongo connection failed

        try:
            log_doc = {
                "created_at": datetime.utcfromtimestamp(record.created),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "pathname": record.pathname,
                "lineno": record.lineno,
                "funcName": record.funcName,
                "process": record.process,
                "thread": record.threadName,
                "stack": self.format(record) if record.exc_info else None
                          if record.exc_info else None,
            }

            self.db[self.collection_name].insert_one(log_doc)

        except Exception as e:
            print(f"[MongoLogHandler] Failed to insert log: {e}")
            self.handleError(record)
