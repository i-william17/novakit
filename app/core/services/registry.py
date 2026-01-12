from fastapi import Request

class Services:
    def __init__(self, request: Request):
        self.app = request.app

    @property
    def db(self):
        return self.app.state.db_sessionmaker

    @property
    def redis(self):
        return self.app.state.redis
