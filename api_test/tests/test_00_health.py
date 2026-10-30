"""探活：确认服务是否可用（冒烟第一条）"""
import pytest

from utils.api_client import get
from utils.assertions import assert_status


@pytest.mark.p0
def test_root_health():
    """根路径可用 -> 200 + 固定文案"""
    res = get("/")
    assert_status(res, 200)
    assert res.json() == {"message": "API is working"}
