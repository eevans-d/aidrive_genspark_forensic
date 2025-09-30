import pytest
from unittest.mock import AsyncMock

from shared import retail_metrics as rm


@pytest.mark.asyncio
async def test_export_metrics_prometheus_returns_str():
    # Mock DB factory/session
    session = AsyncMock()
    # Each calculate_* does one or more execute calls; return empty iterables
    session.execute = AsyncMock(return_value=[])

    async def factory():
        return session

    collector = rm.RetailMetricsCollector(factory)

    result = await collector.export_metrics_prometheus()
    assert isinstance(result, str)

    # Content assertion depends on Prometheus client availability
    if rm.PROMETHEUS_AVAILABLE:
        # Should include at least one of our metric names or HELP/TYPE preamble
        assert "retail_system_info" in result or "# HELP" in result
    else:
        assert "Prometheus client not available" in result
