from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import date

class DonationMetrics(BaseModel):
    total_raised: float
    total_refunded: float
    unique_donors: int
    total_donations: int
    avg_ticket: float
    ltv: float

class MonthlyMetrics(BaseModel):
    year: int
    month: int
    total: float
    unique_donors: int
    avg_ticket: float
    retention_rate: Optional[float]

class AnnualMetrics(BaseModel):
    year: int
    total: float
    growth_rate: Optional[float]
    unique_donors: int
    new_donors: int
    churned_donors: int

class RFMSegment(BaseModel):
    segment: str
    count: int
    avg_recency: float
    avg_frequency: float
    avg_monetary: float

class ReportData(BaseModel):
    overall_metrics: DonationMetrics
    monthly_metrics: List[MonthlyMetrics]
    annual_metrics: List[AnnualMetrics]
    rfm_analysis: List[RFMSegment]
    top_donors: List[Dict[str, float]]
    recent_donations: List[Dict[str, float]]