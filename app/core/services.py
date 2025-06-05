import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import jinja2

# Configuração do ambiente de templates
template_loader = jinja2.FileSystemLoader(searchpath=Path(__file__).parent / "templates")
template_env = jinja2.Environment(loader=template_loader)

def process_excel_file(file_path: str) -> pd.DataFrame:
    """Processa o arquivo Excel e retorna um DataFrame limpo"""
    try:
        df = pd.read_parquet(file_path)
        
        # Renomear colunas para padrão
        df = df.rename(columns={
            'usuario_id': 'donor_id',
            'valor de doacao': 'amount',
            'data': 'date'
        })
        
        # Converter tipos
        df['date'] = pd.to_datetime(df['date'])
        df['amount'] = pd.to_numeric(df['amount'])
        
        # Ordenar por data
        df = df.sort_values('date')
        
        return df
    
    except Exception as e:
        raise ValueError(f"Erro ao processar arquivo Excel: {str(e)}")

def analyze_donation_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Executa todas as análises nos dados de doação"""
    # Métricas gerais
    analysis = {
        'overall_metrics': calculate_overall_metrics(df),
        'monthly_metrics': calculate_monthly_metrics(df),
        'annual_metrics': calculate_annual_metrics(df),
        'rfm_analysis': calculate_rfm_segments(df),
        'plots': generate_plotly_figures(df),
        'current_year': datetime.now().year,
        'generation_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return analysis

def calculate_overall_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcula métricas gerais"""
    return {
        'total_raised': df['amount'].sum(),
        'total_refunded': df[df['amount'] < 0]['amount'].sum(),
        'unique_donors': df['donor_id'].nunique(),
        'total_donations': len(df),
        'avg_ticket': df['amount'].mean(),
        'ltv': df.groupby('donor_id')['amount'].sum().mean()
    }

def calculate_monthly_metrics(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Agrega métricas por mês"""
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    monthly = df.groupby(['year', 'month']).agg(
        total=('amount', 'sum'),
        unique_donors=('donor_id', 'nunique'),
        avg_ticket=('amount', 'mean')
    ).reset_index()
    
    monthly['retention_rate'] = calculate_retention(df)
    
    return monthly.to_dict('records')

def calculate_annual_metrics(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Agrega métricas por ano com crescimento"""
    annual = df.groupby(df['date'].dt.year).agg(
        total=('amount', 'sum'),
        unique_donors=('donor_id', 'nunique')
    ).reset_index()
    annual.columns = ['year', 'total', 'unique_donors']
    
    # Calcular crescimento anual
    annual['growth_rate'] = annual['total'].pct_change() * 100
    
    # Calcular novos vs doadores que deixaram (simplificado)
    annual['new_donors'] = calculate_new_donors(df)
    annual['churned_donors'] = calculate_churned_donors(df)
    
    return annual.to_dict('records')

def calculate_rfm_segments(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Implementa análise RFM (Recência, Frequência, Valor Monetário)"""
    # Agregação por doador
    snapshot_date = df['date'].max() + timedelta(days=1)
    
    rfm = df.groupby('donor_id').agg({
        'date': lambda x: (snapshot_date - x.max()).days,
        'donor_id': 'count',
        'amount': 'sum'
    }).rename(columns={
        'date': 'recency',
        'donor_id': 'frequency',
        'amount': 'monetary'
    })
    
    # Segmentação (exemplo simplificado)
    rfm['r_score'] = pd.qcut(rfm['recency'], q=3, labels=[3, 2, 1])
    rfm['f_score'] = pd.qcut(rfm['frequency'], q=3, labels=[1, 2, 3])
    rfm['m_score'] = pd.qcut(rfm['monetary'], q=3, labels=[1, 2, 3])
    
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    
    # Definir segmentos
    segment_map = {
        r'111|112|121|131|211|221|311': 'inativo',
        r'123|132|213|222|231|321|312': 'em risco',
        r'113|122|133|212|223|232|233|322': 'potencial',
        r'323|332|333': 'leal'
    }
    
    rfm['segment'] = rfm['rfm_score'].replace(segment_map, regex=True)
    
    # Métricas por segmento
    segments = rfm.groupby('segment').agg({
        'recency': 'mean',
        'frequency': 'mean',
        'monetary': 'mean',
        'donor_id': 'count'
    }).reset_index().rename(columns={'donor_id': 'count'})
    
    return segments.to_dict('records')

def generate_plotly_figures(df: pd.DataFrame) -> Dict[str, str]:
    """Gera todas as visualizações Plotly e retorna como JSON"""
    # 1. Arrecadação ao longo do tempo
    df['year_month'] = df['date'].dt.to_period('M').astype(str)
    monthly_trend = df.groupby('year_month')['amount'].sum().reset_index()
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly_trend['year_month'],
        y=monthly_trend['amount'],
        mode='lines+markers',
        name='Arrecadação Mensal'
    ))
    fig_trend.update_layout(
        title='Arrecadação ao Longo do Tempo',
        xaxis_title='Mês',
        yaxis_title='Valor Arrecadado (R$)'
    )
    
    # 2. Métricas anuais
    annual_data = df.groupby(df['date'].dt.year).agg(
        total=('amount', 'sum'),
        donors=('donor_id', 'nunique')
    ).reset_index()
    
    fig_annual = make_subplots(specs=[[{"secondary_y": True}]])
    fig_annual.add_trace(
        go.Bar(
            x=annual_data['date'],
            y=annual_data['total'],
            name='Arrecadação Anual'
        ),
        secondary_y=False
    )
    fig_annual.add_trace(
        go.Scatter(
            x=annual_data['date'],
            y=annual_data['donors'],
            name='Doadores Únicos',
            mode='lines+markers'
        ),
        secondary_y=True
    )
    fig_annual.update_layout(
        title='Performance Anual',
        xaxis_title='Ano'
    )
    
    # Converter para JSON
    return {
        'trend_plot': fig_trend.to_json(),
        'annual_plot': fig_annual.to_json()
    }

def generate_html_report(report_data: Dict[str, Any], template_name: str = "default") -> str:
    """Renderiza o template HTML com os dados do relatório"""
    template = template_env.get_template(f"{template_name}_report.html")
    
    # Adicionar formatação de moeda
    report_data['currency'] = lambda x: f"R${x:,.2f}"
    report_data['percentage'] = lambda x: f"{x:.2f}%"
    
    return template.render(**report_data)