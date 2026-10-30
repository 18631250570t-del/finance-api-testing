"""交易列表的非法查询参数：400（业务规则）与 422（格式）"""
import pytest

from utils.api_client import get
from utils.assertions import assert_detail, assert_status


@pytest.mark.p2
@pytest.mark.parametrize(
    "query, expected_detail",
    [
        ("?sort=random", "sort must be 'asc' or 'desc'"),
        ("?month=2026-13", "month must be in YYYY-MM format"),
        ("?month=2026", "month must be in YYYY-MM format"),
    ],
    ids=["sort非法值", "月份13", "月份缺段"],
)
def test_filter_bad_request(seeded_headers, query, expected_detail):
    """非法的查询参数 -> 400 + 明确的 detail 文案"""
    res = get(f"/transactions{query}", headers=seeded_headers)
    assert_status(res, 400)
    assert_detail(res, expected_detail)


@pytest.mark.p2
def test_filter_bad_amount_type(seeded_headers):
    """金额传字母 -> 422，且错误指向 min_amount 字段"""
    res = get("/transactions?min_amount=abc", headers=seeded_headers)
    assert_status(res, 422)
    assert "min_amount" in res.text, f"422 响应里没提到 min_amount，实际：{res.text}"
