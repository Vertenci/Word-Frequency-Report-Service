import asyncio
import tempfile
import os
import time
import logging
from typing import Dict, List, Tuple
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
            max_file_size_bytes: int = 3 * 1024 * 1024 * 1024,
            batch_size: int = 1000,
            max_workers: int = 4
    ):
        self.lemmatizer = lemmatizer
        self.file_processor = file_processor
        self.report_repository = report_repository
        self.lemmatizer_service = LemmatizerService(lemmatizer)
        self.max_file_size_bytes = max_file_size_bytes
        self.batch_size = batch_size
        self.max_workers = max_workers

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

            lines_batch: List[Tuple[int, str]] = []
            batches = []
            total_lines = 0

            async def collect_lines(line_num: int, line: str):
                nonlocal total_lines, lines_batch, batches
                total_lines = line_num + 1
                lines_batch.append((line_num, line))

                if len(lines_batch) >= self.batch_size:
                    batches.append(lines_batch.copy())
                    lines_batch.clear()

            logger.info("Начинаем сбор строк в пакеты")
            await self.file_processor.process_line_by_line(temp_file_path, collect_lines)

            if lines_batch:
                batches.append(lines_batch)

            logger.info(f"Собрано {len(batches)} пакетов, всего строк: {total_lines}")

            logger.info("Начинаем лемматизацию и подсчет статистики")
            process_start = time.perf_counter()

            semaphore = asyncio.Semaphore(self.max_workers)

            async def process_batch_with_semaphore(batch):
                async with semaphore:
                    return await asyncio.to_thread(
                        self.lemmatizer_service.process_line_batch,
                        batch
                    )

            tasks = [process_batch_with_semaphore(batch) for batch in batches]
            batch_results = await asyncio.gather(*tasks)

            logger.info("Объединяем результаты обработки")
            stats: Dict[str, WordStats] = {}

            for batch_stat in batch_results:
                for lemma, word_stat in batch_stat.items():
                    if lemma not in stats:
                        stats[lemma] = WordStats(word=lemma)

                    main_stat = stats[lemma]
                    main_stat.total_count += word_stat.total_count

                    max_len = max(len(main_stat.line_counts), len(word_stat.line_counts))
                    while len(main_stat.line_counts) < max_len:
                        main_stat.line_counts.append(0)

                    for i, count in enumerate(word_stat.line_counts):
                        main_stat.line_counts[i] += count

            process_time = time.perf_counter() - process_start

            logger.info(
                f"Обработка завершена. "
                f"Строк: {total_lines}, "
                f"Уникальных слов: {len(stats)}, "
                f"Время обработки: {process_time:.2f} сек, "
                f"Скорость: {total_lines / process_time:.0f} строк/сек"
            )

            result_path = await self.report_repository.save_report(
                stats, original_filename, total_lines
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
