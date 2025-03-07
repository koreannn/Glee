class OcrCache:
    def __init__(self):
        self.cache = {}

    def get_hash(self, filedata: bytes) -> str:
        return hashlib.md5(filedata).hexdigest()

    def get(self, key: str):
        return self.cache.get(key)

    def set(self, key: str, value: str):
        self.cache[key] = value