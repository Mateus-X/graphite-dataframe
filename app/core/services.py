import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import httpx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import jinja2
from app.core.config import Settings
from app.domain.schemas import Response, NewDonorsDto, ChurnsDto

# Configuração do ambiente de templates
template_loader = jinja2.FileSystemLoader(searchpath=Path(__file__).parent / "templates")
template_env = jinja2.Environment(loader=template_loader)


class ReportService:
    def __init__(self):
        self.http_client = httpx.AsyncClient(base_url=Settings.MAIN_API + "/dataframe-lines")
        self.template_env = template_env

    async def generate_plot_for_churns_vs_new_donors(self, userId: str) -> pd.DataFrame:
        """Processa o arquivo Parquet e retorna um DataFrame limpo"""
        try:
            # Busca dados de novos doadores e churns
            response_new_donors = await self.http_client.get(self.http_client.base_url + "/new-donors", params={"userId": userId})
            response_new_donors.raise_for_status()
            new_donors = Response[NewDonorsDto].model_validate_json(response_new_donors.text)
            new_donors_per_year = [
                {"year": nd.year, "new_donors": nd.new_donors}
                for nd in new_donors.data.new_donors_per_year
            ]

            response_churns = await self.http_client.get(self.http_client.base_url + "/churns", params={"userId": userId})
            response_churns.raise_for_status()
            churns = Response[ChurnsDto].model_validate_json(response_churns.text)
            churns_per_year = [
                {"year": ch.year, "churns": ch.new_donors}
                for ch in churns.data.churns_per_year
            ]

            df_new = pd.DataFrame(new_donors_per_year)
            df_churn = pd.DataFrame(churns_per_year)
            df = pd.merge(df_new, df_churn, on="year", how="outer").fillna(0)
            df = df.sort_values("year")

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df["year"],
                y=df["new_donors"],
                name="Novos Doadores",
                marker_color="green"
            ))
            fig.add_trace(go.Bar(
                x=df["year"],
                y=df["churns"],
                name="Churns",
                marker_color="red"
            ))
            fig.update_layout(
                barmode="group",
                title="Novos Doadores vs Churns por Ano",
                xaxis_title="Ano",
                yaxis_title="Quantidade de Pessoas",
                legend_title="Categoria"
            )

            return fig.to_html()
        
        except Exception as e:
            raise ValueError(f"Erro ao processar arquivo Parquet: {str(e)}")

    def plot_revenue_trend(self, monthly_data: List[Dict[str, Any]]) -> go.Figure:
        df = pd.DataFrame(monthly_data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['yearMonth'],
            y=df['totalRevenue'],
            name="Total Revenue",
            line=dict(color='royalblue', width=2)
        ))
        df['moving_avg'] = df['totalRevenue'].rolling(window=6).mean()
        fig.add_trace(go.Scatter(
            x=df['yearMonth'],
            y=df['moving_avg'],
            name="6-Month Moving Avg",
            line=dict(color='red', width=2, dash='dot')
        ))
        fig.update_layout(
            title="Monthly Revenue Trend with Moving Average",
            xaxis_title="Month",
            yaxis_title="Revenue",
            hovermode="x unified",
            template="plotly_white"
        )
        return fig

    def generate_plotly_figures(self, df: pd.DataFrame) -> Dict[str, str]:
        """Gera todas as visualizações Plotly e retorna como JSON"""
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
        return {
            'trend_plot': fig_trend.to_json(),
            'annual_plot': fig_annual.to_json()
        }

    def generate_html_report(self, report_data: Dict[str, Any], template_name: str = "default") -> str:
        """Renderiza o template HTML com os dados do relatório"""
        template = self.template_env.get_template(f"{template_name}_report.html")
        report_data['currency'] = lambda x: f"R${x:,.2f}"
        report_data['percentage'] = lambda x: f"{x:.2f}%"
        return template.render(**report_data)
