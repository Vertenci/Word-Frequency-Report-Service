import time
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from src.application.use_cases import GenerateReportUseCase
from functools import lru_cache
from src.domain.config import AppConfig
from src.infrastructure.lemmatizer import Pymorphy3Lemmatizer
from src.infrastructure.file_processor import TextFileProcessor
from src.infrastructure.excel_repository import ExcelReportRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/report", tags=["report"])


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()


@lru_cache
def get_report_use_case(config: AppConfig = Depends(get_config)) -> GenerateReportUseCase:
    lemmatizer = Pymorphy3Lemmatizer()
    file_processor = TextFileProcessor()
    report_repository = ExcelReportRepository()

    return GenerateReportUseCase(
        lemmatizer,
        file_processor,
        report_repository,
        max_file_size_bytes=config.max_file_size_bytes,
        batch_size=config.batch_size,
        max_workers=config.max_workers
    )


@router.post("/export")
async def export_report(
    file: UploadFile = File(...),
    use_case: GenerateReportUseCase = Depends(get_report_use_case)
):
    if not any(file.filename.lower().endswith(ext) for ext in get_config().allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Только текстовые файлы: {', '.join(get_config().allowed_extensions)}"
        )

    try:
        start_time = time.perf_counter()
        result_path = await use_case.execute(file, file.filename)
        elapsed = time.perf_counter() - start_time
        logger.info(f"Запрос обработан за {elapsed:.2f} сек")

        return FileResponse(
            path=result_path,
            filename=result_path.split('/')[-1],
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                "X-Processing-Time": str(elapsed),
                "X-File-Size": "streamed",
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
