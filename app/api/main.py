from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
import tempfile
from typing import Optional
from datetime import datetime

from app.domain import schemas
from app.core import services

app = FastAPI(
    title="Report Generator API",
    description="API para gerar relatórios HTML dinâmicos a partir de dados de doações",
    version="0.1.0"
)

@app.post("/generate-report", response_class=HTMLResponse)
async def generate_report(file: UploadFile, report_type: Optional[str] = "default"):
    """
    Endpoint principal que recebe o arquivo Excel e retorna o HTML do relatório
    """
    try:
        # Validação básica do arquivo
        if not file.filename.endswith(('.parquet')):
            raise HTTPException(400, "Invalid format")
        
        # Processamento do arquivo
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(await file.read())
            df = services.process_excel_file(tmp.name)
        
        # Geração do relatório
        report_data = services.analyze_donation_data(df)
        html_content = services.generate_html_report(report_data, report_type)
        
        return HTMLResponse(content=html_content, status_code=200)
    
    except Exception as e:
        raise HTTPException(500, f"Erro ao processar relatório: {str(e)}")