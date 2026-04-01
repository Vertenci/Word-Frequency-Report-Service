from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    max_file_size_bytes: int = 3 * 1024 ** 3
    chunk_size_bytes: int = 1024 * 1024
    allowed_extensions: tuple = (".txt", ".text")
