from abc import ABC, abstractmethod
from fastapi import UploadFile
from typing import Callable, Awaitable


class Lemmatizer(ABC):
    @abstractmethod
    def lemmatize(self, word: str) -> str:
        pass


class FileProcessor(ABC):
    @abstractmethod
    async def process_line_by_line(
            self,
            file_path: str,
            processor_func: Callable[[int, str], Awaitable[None]]
    ) -> None:
        pass

    @abstractmethod
    async def save_uploaded_file_streaming(
        self,
        upload_file: UploadFile,
        destination_path: str,
        max_size_bytes: int
    ) -> int:
        pass


class ReportRepository(ABC):
    @abstractmethod
    async def save_report(self, stats: dict, filename: str, total_lines: int) -> str:
        pass
