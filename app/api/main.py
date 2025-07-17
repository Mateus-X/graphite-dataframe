from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
import tempfile
from typing import Optional
from datetime import datetime

from app.domain import schemas
from app.core.services import ReportService
from fastapi.responses import Response



app = FastAPI(
    title="Report Generator API",
    description="API para gerar relatórios HTML dinâmicos a partir de dados de doações",
    version="0.1.0"
)

@app.post("/generate-report", response_class=HTMLResponse)
async def generate_report(userId: str):
    """
    Endpoint principal que recebe o arquivo Excel e retorna o HTML do relatório
    """    
    # Geração do relatório
    try:
        html_content = await ReportService().generate_plot_for_churns_vs_new_donors(userId=userId)
        
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        raise HTTPException(500, f"Erro ao processar relatório: {str(e)}")