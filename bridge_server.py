from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from typing import Optional, List, Dict

# 기존 브릿지 모듈 임포트
from printer_bridge import RibbonPrinterBridge, PrinterManager


# -----------------------------------------------------
# 로깅 설정
# -----------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("BridgeServer")

app = FastAPI(title="Ribbon Print Bridge Agent")

# CORS 활성화 (로컬 웹앱 테스트를 위함)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: 운영 시 특정 오리진으로 제한 (예: http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------
# 전역 상태 (PrinterManager 인스턴스 싱글톤 유지)
# -----------------------------------------------------
printer_manager = PrinterManager()


# -----------------------------------------------------
# API 모델 (웹앱으로부터 받을 JSON Schema)
# -----------------------------------------------------
class PrintJobRequest(BaseModel):
    printer_name: str
    configs: Dict[str, dict]  # {'경조사': config_dict, '보내는이': config_dict}
    
# -----------------------------------------------------
# HTTP 엔드포인트
# -----------------------------------------------------

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Ribbon Print Bridge Agent is running"}

@app.get("/api/printers")
def list_printers():
    """연결 가능한 지원 프린터 목록을 반환합니다."""
    try:
        printers = printer_manager.get_available_printers()
        return {"status": "success", "data": printers}
    except Exception as e:
        logger.error(f"Failed to get printer list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/print")
def submit_print_job(job: PrintJobRequest):
    """웹 앱으로부터 인쇄 데이터를 수신하여 로컬 프린터로 출력을 실행합니다."""
    logger.info(f"Received print job request for printer: {job.printer_name}")
    
    # 1. 프린터 선택 검증
    if not job.printer_name:
        raise HTTPException(status_code=400, detail="Printer name is required")
        
    try:
        success = printer_manager.select_printer(job.printer_name)
        if not success:
            raise HTTPException(status_code=400, detail=f"Printer '{job.printer_name}' could not be selected or is not a supported model.")
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Error selecting printer: {str(e)}")

    # 2. 인쇄 실행
    try:
        # 기존 main.py의 `_perform_print`와 유사한 동작 수행
        result, error_msg = printer_manager.print_ribbon(job.configs)
        
        if result:
            logger.info("Print job completed successfully.")
            return {"status": "success", "message": "Print job completed successfully"}
        else:
             logger.error(f"Print job failed: {error_msg}")
             raise HTTPException(status_code=500, detail=f"Print failed: {error_msg}")
             
    except Exception as e:
        logger.error(f"Exception during print process: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    logger.info("Starting Print Bridge Agent...")
    # 브릿지 서버를 로컬호스트(127.0.0.1) 8000포트에서 실행
    uvicorn.run(app, host="127.0.0.1", port=8000)
