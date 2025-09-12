"""
Business Intelligence KPI Tracker for Argentine Retail System
Tracks key performance indicators and business metrics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class KPICategory(Enum):
    SALES = "sales"
    INVENTORY = "inventory" 
    FINANCIAL = "financial"
    OPERATIONS = "operations"
    CUSTOMER = "customer"
    COMPLIANCE = "compliance"

@dataclass
class KPIMetric:
    """Represents a KPI metric with metadata"""
    name: str
    category: KPICategory
    value: float
    target: Optional[float]
    unit: str
    description: str
    timestamp: datetime
    period: str  # daily, weekly, monthly, quarterly

    @property
    def performance_ratio(self) -> Optional[float]:
        """Calculate performance ratio against target"""
        if self.target and self.target != 0:
            return self.value / self.target
        return None

    @property
    def status(self) -> str:
        """Get status based on performance"""
        ratio = self.performance_ratio
        if ratio is None:
            return "no_target"
        elif ratio >= 1.0:
            return "on_target"
        elif ratio >= 0.8:
            return "below_target"
        else:
            return "critical"

class BusinessIntelligenceTracker:
    """Main class for tracking business KPIs"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(self.__class__.__name__)

    async def calculate_sales_kpis(self, start_date: datetime, end_date: datetime) -> List[KPIMetric]:
        """Calculate sales-related KPIs"""
        kpis = []

        # Total Revenue
        revenue_query = """
        SELECT SUM(total_amount) as total_revenue
        FROM invoices 
        WHERE created_at BETWEEN :start_date AND :end_date
        AND status = 'approved'
        """
        result = self.db.execute(text(revenue_query), {
            'start_date': start_date, 'end_date': end_date
        }).fetchone()

        total_revenue = result.total_revenue or 0
        kpis.append(KPIMetric(
            name="total_revenue",
            category=KPICategory.SALES,
            value=total_revenue,
            target=1000000.0,  # 1M ARS target
            unit="ARS",
            description="Total revenue from approved invoices",
            timestamp=datetime.now(),
            period="monthly"
        ))

        # Average Order Value
        aov_query = """
        SELECT AVG(total_amount) as avg_order_value
        FROM invoices 
        WHERE created_at BETWEEN :start_date AND :end_date
        AND status = 'approved'
        """
        result = self.db.execute(text(aov_query), {
            'start_date': start_date, 'end_date': end_date
        }).fetchone()

        avg_order_value = result.avg_order_value or 0
        kpis.append(KPIMetric(
            name="average_order_value",
            category=KPICategory.SALES,
            value=float(avg_order_value),
            target=15000.0,  # 15K ARS target
            unit="ARS",
            description="Average value per order",
            timestamp=datetime.now(),
            period="monthly"
        ))

        # Sales Growth Rate
        previous_period_start = start_date - (end_date - start_date)
        previous_revenue_result = self.db.execute(text(revenue_query), {
            'start_date': previous_period_start, 'end_date': start_date
        }).fetchone()

        previous_revenue = previous_revenue_result.total_revenue or 1
        growth_rate = ((total_revenue - previous_revenue) / previous_revenue) * 100

        kpis.append(KPIMetric(
            name="sales_growth_rate",
            category=KPICategory.SALES,
            value=growth_rate,
            target=10.0,  # 10% growth target
            unit="%",
            description="Month-over-month sales growth rate",
            timestamp=datetime.now(),
            period="monthly"
        ))

        return kpis

    async def calculate_inventory_kpis(self) -> List[KPIMetric]:
        """Calculate inventory-related KPIs"""
        kpis = []

        # Inventory Turnover
        turnover_query = """
        SELECT 
            SUM(p.price * s.quantity_sold) / AVG(p.price * s.stock_quantity) as turnover_ratio
        FROM products p
        JOIN stock s ON p.id = s.product_id
        WHERE s.updated_at >= :thirty_days_ago
        """
        thirty_days_ago = datetime.now() - timedelta(days=30)
        result = self.db.execute(text(turnover_query), {
            'thirty_days_ago': thirty_days_ago
        }).fetchone()

        turnover_ratio = result.turnover_ratio or 0
        kpis.append(KPIMetric(
            name="inventory_turnover",
            category=KPICategory.INVENTORY,
            value=float(turnover_ratio),
            target=4.0,  # 4x turnover target
            unit="ratio",
            description="Inventory turnover ratio (monthly)",
            timestamp=datetime.now(),
            period="monthly"
        ))

        # Stock Out Rate
        stockout_query = """
        SELECT 
            COUNT(CASE WHEN stock_quantity <= reorder_point THEN 1 END) * 100.0 / COUNT(*) as stockout_rate
        FROM stock s
        JOIN products p ON s.product_id = p.id
        WHERE p.active = true
        """
        result = self.db.execute(text(stockout_query)).fetchone()
        stockout_rate = result.stockout_rate or 0

        kpis.append(KPIMetric(
            name="stockout_rate",
            category=KPICategory.INVENTORY,
            value=float(stockout_rate),
            target=5.0,  # 5% or less stockout rate
            unit="%",
            description="Percentage of products below reorder point",
            timestamp=datetime.now(),
            period="daily"
        ))

        return kpis

    async def calculate_financial_kpis(self, start_date: datetime, end_date: datetime) -> List[KPIMetric]:
        """Calculate financial KPIs including Argentine-specific metrics"""
        kpis = []

        # Gross Margin
        margin_query = """
        SELECT 
            SUM((il.unit_price - p.cost_price) * il.quantity) / SUM(il.unit_price * il.quantity) * 100 as gross_margin
        FROM invoice_lines il
        JOIN products p ON il.product_id = p.id
        JOIN invoices i ON il.invoice_id = i.id
        WHERE i.created_at BETWEEN :start_date AND :end_date
        AND i.status = 'approved'
        """
        result = self.db.execute(text(margin_query), {
            'start_date': start_date, 'end_date': end_date
        }).fetchone()

        gross_margin = result.gross_margin or 0
        kpis.append(KPIMetric(
            name="gross_margin",
            category=KPICategory.FINANCIAL,
            value=float(gross_margin),
            target=35.0,  # 35% margin target
            unit="%",
            description="Gross profit margin percentage",
            timestamp=datetime.now(),
            period="monthly"
        ))

        # AFIP Tax Compliance Rate
        compliance_query = """
        SELECT 
            COUNT(CASE WHEN afip_status = 'approved' THEN 1 END) * 100.0 / COUNT(*) as compliance_rate
        FROM invoices
        WHERE created_at BETWEEN :start_date AND :end_date
        AND requires_afip = true
        """
        result = self.db.execute(text(compliance_query), {
            'start_date': start_date, 'end_date': end_date
        }).fetchone()

        compliance_rate = result.compliance_rate or 0
        kpis.append(KPIMetric(
            name="afip_compliance_rate",
            category=KPICategory.COMPLIANCE,
            value=float(compliance_rate),
            target=95.0,  # 95% compliance target
            unit="%",
            description="AFIP tax compliance rate",
            timestamp=datetime.now(),
            period="monthly"
        ))

        # Inflation-Adjusted Revenue (Argentina specific)
        inflation_rate_monthly = 0.045  # 4.5% monthly inflation
        periods = (end_date - start_date).days / 30
        inflation_factor = (1 + inflation_rate_monthly) ** periods

        adjusted_revenue = total_revenue / inflation_factor if 'total_revenue' in locals() else 0
        kpis.append(KPIMetric(
            name="inflation_adjusted_revenue",
            category=KPICategory.FINANCIAL,
            value=adjusted_revenue,
            target=850000.0,  # Adjusted target considering inflation
            unit="ARS",
            description="Revenue adjusted for Argentine inflation",
            timestamp=datetime.now(),
            period="monthly"
        ))

        return kpis

    async def calculate_operations_kpis(self) -> List[KPIMetric]:
        """Calculate operational KPIs"""
        kpis = []

        # Invoice Processing Time
        processing_query = """
        SELECT AVG(EXTRACT(EPOCH FROM (processed_at - created_at))/3600) as avg_processing_hours
        FROM invoices
        WHERE processed_at IS NOT NULL
        AND created_at >= :seven_days_ago
        """
        seven_days_ago = datetime.now() - timedelta(days=7)
        result = self.db.execute(text(processing_query), {
            'seven_days_ago': seven_days_ago
        }).fetchone()

        avg_processing_time = result.avg_processing_hours or 0
        kpis.append(KPIMetric(
            name="invoice_processing_time",
            category=KPICategory.OPERATIONS,
            value=float(avg_processing_time),
            target=2.0,  # 2 hours target
            unit="hours",
            description="Average invoice processing time",
            timestamp=datetime.now(),
            period="weekly"
        ))

        # OCR Accuracy Rate
        ocr_query = """
        SELECT 
            COUNT(CASE WHEN ocr_confidence >= 0.9 THEN 1 END) * 100.0 / COUNT(*) as ocr_accuracy
        FROM invoices
        WHERE created_at >= :seven_days_ago
        AND ocr_processed = true
        """
        result = self.db.execute(text(ocr_query), {
            'seven_days_ago': seven_days_ago
        }).fetchone()

        ocr_accuracy = result.ocr_accuracy or 0
        kpis.append(KPIMetric(
            name="ocr_accuracy_rate",
            category=KPICategory.OPERATIONS,
            value=float(ocr_accuracy),
            target=90.0,  # 90% accuracy target
            unit="%",
            description="OCR processing accuracy rate",
            timestamp=datetime.now(),
            period="weekly"
        ))

        return kpis

    async def generate_kpi_dashboard_data(self, period: str = "monthly") -> Dict[str, Any]:
        """Generate complete KPI dashboard data"""
        if period == "monthly":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        elif period == "weekly":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
        else:  # daily
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)

        try:
            # Collect all KPIs
            all_kpis = []
            all_kpis.extend(await self.calculate_sales_kpis(start_date, end_date))
            all_kpis.extend(await self.calculate_inventory_kpis())
            all_kpis.extend(await self.calculate_financial_kpis(start_date, end_date))
            all_kpis.extend(await self.calculate_operations_kpis())

            # Group by category
            kpis_by_category = {}
            for kpi in all_kpis:
                category = kpi.category.value
                if category not in kpis_by_category:
                    kpis_by_category[category] = []

                kpis_by_category[category].append({
                    'name': kpi.name,
                    'value': kpi.value,
                    'target': kpi.target,
                    'unit': kpi.unit,
                    'description': kpi.description,
                    'status': kpi.status,
                    'performance_ratio': kpi.performance_ratio
                })

            # Calculate summary metrics
            total_kpis = len(all_kpis)
            on_target = len([k for k in all_kpis if k.status == 'on_target'])
            critical = len([k for k in all_kpis if k.status == 'critical'])

            dashboard_data = {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'total_kpis': total_kpis,
                    'on_target': on_target,
                    'critical': critical,
                    'overall_health': 'good' if critical == 0 else 'warning' if critical <= 2 else 'critical'
                },
                'kpis_by_category': kpis_by_category,
                'alerts': [
                    {
                        'kpi': kpi.name,
                        'message': f"{kpi.name} is below target: {kpi.value:.2f} {kpi.unit} (target: {kpi.target:.2f})",
                        'severity': 'high' if kpi.status == 'critical' else 'medium'
                    }
                    for kpi in all_kpis 
                    if kpi.status in ['critical', 'below_target']
                ]
            }

            return dashboard_data

        except Exception as e:
            self.logger.error(f"Error generating KPI dashboard: {str(e)}")
            raise

    async def export_kpi_report(self, period: str = "monthly", format: str = "json") -> str:
        """Export KPI report in specified format"""
        dashboard_data = await self.generate_kpi_dashboard_data(period)

        if format == "json":
            import json
            return json.dumps(dashboard_data, indent=2, ensure_ascii=False)

        elif format == "excel":
            # Create Excel report using pandas
            output_file = f"kpi_report_{period}_{datetime.now().strftime('%Y%m%d')}.xlsx"

            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Summary sheet
                summary_df = pd.DataFrame([dashboard_data['summary']])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

                # KPI details by category
                for category, kpis in dashboard_data['kpis_by_category'].items():
                    kpi_df = pd.DataFrame(kpis)
                    kpi_df.to_excel(writer, sheet_name=category.title(), index=False)

                # Alerts sheet
                alerts_df = pd.DataFrame(dashboard_data['alerts'])
                if not alerts_df.empty:
                    alerts_df.to_excel(writer, sheet_name='Alerts', index=False)

            return output_file

        else:
            raise ValueError(f"Unsupported format: {format}")
