import asyncio
import tempfile
import os
import time
import logging
from typing import Dict
from src.domain.entities import WordStats
from src.domain.interfaces import Lemmatizer, FileProcessor, ReportRepository
from src.application.services import LemmatizerService

logger = logging.getLogger(__name__)


class GenerateReportUseCase:
    def __init__(
            self,
            lemmatizer: Lemmatizer,
            file_processor: FileProcessor,
            report_repository: ReportRepository,
            max_file_size_bytes: int = 3 * 1024 * 1024 * 1024
    ):
        self.lemmatizer = lemmatizer
        self.file_processor = file_processor
        self.report_repository = report_repository
        self.lemmatizer_service = LemmatizerService(lemmatizer)
        self.max_file_size_bytes = max_file_size_bytes

    async def execute(self, upload_file, original_filename: str) -> str:
        start_time = time.perf_counter()
        temp_file_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
                temp_file_path = tmp_file.name

            logger.info(f"Начинаем сохранение файла {original_filename}")
            file_size = await self.file_processor.save_uploaded_file_streaming(
                upload_file,
                temp_file_path,
                self.max_file_size_bytes
            )
            logger.info(f"Файл сохранен. Размер: {file_size / (1024 ** 2):.2f} МБ")

            stats: Dict[str, WordStats] = {}
            total_lines = 0

            async def process_line(line_num: int, line: str):
                nonlocal total_lines
                total_lines = line_num + 1
                await asyncio.to_thread(
                    self.lemmatizer_service.process_line,
                    line, line_num, stats
                )

            logger.info("Начинаем лемматизацию и подсчет статистики")
            process_start = time.perf_counter()
            await self.file_processor.process_line_by_line(temp_file_path, process_line)
            process_time = time.perf_counter() - process_start

            logger.info(
                f"Обработка завершена. "
                f"Строк: {total_lines}, "
                f"Уникальных слов: {len(stats)}, "
                f"Время обработки: {process_time:.2f} сек, "
                f"Скорость: {total_lines / process_time:.0f} строк/сек"
            )

            result_path = await self.report_repository.save_report(
                stats, original_filename, len(stats)
            )

            total_time = time.perf_counter() - start_time
            logger.info(f"Общее время выполнения: {total_time:.2f} сек")

            return result_path

        except ValueError as e:
            logger.error(f"Ошибка валидации: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка обработки файла: {e}", exc_info=True)
            raise
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Временный файл удален: {temp_file_path}")
                except Exception as e:
                    logger.error(f"Не удалось удалить временный файл: {e}")
