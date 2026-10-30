import pytest

from utils.api_client import call
from utils.assertions import assert_detail, assert_status


CASES = [
    ("POST",   "/transactions", {"amount": 10, "category": "x"}),
    ("GET",    "/transactions", None),
    ("GET",    "/transactions/1", None),
    ("PUT",    "/transactions/1", {"amount": 10, "category": "x"}),
    ("DELETE", "/transactions/1", None),
    ("POST",   "/budgets", {"name": "x", "limit": 10}),
    ("GET",    "/budgets", None),
    ("GET",    "/budgets/1", None),
    ("PUT",    "/budgets/1", {"name": "x", "limit": 10}),
    ("DELETE", "/budgets/1", None),
    ("GET",    "/stats", None),
    ("GET",    "/me", None),
]


@pytest.mark.p0
@pytest.mark.parametrize(
    "method, path, body",
    CASES,
    ids=[
        "建交易", "交易列表", "交易详情", "改交易", "删交易",
        "建预算", "预算列表", "预算详情", "改预算", "删预算",
        "统计", "当前用户",
    ],
)
def test_unauthorized(method, path, body):
    """不携带任何 token 访问受保护接口 -> 一律 401"""
    res = call(method, path, body=body)
    assert_status(res, 401)
    assert_detail(res, "Not authenticated")