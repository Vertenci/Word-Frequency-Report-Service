import os
from typing import Callable, Awaitable
import aiofiles
import logging
from fastapi import UploadFile

from src.domain.interfaces import FileProcessor

logger = logging.getLogger(__name__)


class TextFileProcessor(FileProcessor):
    async def process_line_by_line(
            self,
            file_path: str,
            processor_func: Callable[[int, str], Awaitable[None]]
    ) -> None:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            line_num = 0
            async for line in f:
                line = line.strip()
                if line:
                    await processor_func(line_num, line)
                line_num += 1
                if line_num > 0 and line_num % 10000 == 0:
                    logger.info(f"Обработано строк: {line_num}")

    async def save_uploaded_file_streaming(
            self,
            upload_file: UploadFile,
            destination_path: str,
            max_size_bytes: int
    ) -> int:
        total_size = 0
        async with aiofiles.open(destination_path, 'wb') as dest_file:
            while chunk := await upload_file.read(1024 * 1024):
                total_size += len(chunk)

                if total_size > max_size_bytes:
                    if os.path.exists(destination_path):
                        os.unlink(destination_path)
                    raise ValueError(
                        f"Файл превышает максимальный размер "
                        f"{max_size_bytes / (1024 ** 3):.1f} ГБ"
                    )

                await dest_file.write(chunk)

        return total_size
