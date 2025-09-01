import hashlib


class HashinatorT1000:
    def __init__(self) -> None:
        self.hashes: dict[str, str] = {}

    def _sha1(self, text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def hash(self, text: str) -> str:
        candidate = self._sha1(text)
        while True:
            if candidate not in self.hashes:
                self.hashes[candidate] = text
                return candidate
            elif self.hashes[candidate] == text:
                return candidate
            else:
                candidate = self._sha1(candidate + ".")

    def unhash(self, hash: str) -> str | None:
        return self.hashes.get(hash, None)
