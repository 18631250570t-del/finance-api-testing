"""交易列表筛选：按分类、金额下限、月份筛选，返回条数必须符合预期"""
import pytest

from utils.api_client import get
from utils.assertions import assert_status


@pytest.mark.p1
def test_seeded_has_three(seeded_headers):
    """造数据自检：这个账号应该有 3 笔交易"""
    res = get("/transactions", headers=seeded_headers)
    assert_status(res, 200)
    assert len(res.json()) == 3, f"造数据失败，只有 {len(res.json())} 笔"


@pytest.mark.p1
@pytest.mark.parametrize(
    "query, expected_count",
    [
        ("", 3),
        ("?category=food", 2),
        ("?category=foo", 0),
        ("?min_amount=250", 1),
        ("?month=2026-05", 2),
        ("?month=2026-06", 1),
    ],
    ids=[
        "不加条件",
        "按分类-food",
        "按分类-foo不存在",
        "金额下限250",
        "月份-2026-05",
        "月份-2026-06",
    ],
)
def test_filter(seeded_headers, query, expected_count):
    """各类筛选条件 -> 返回条数必须符合预期"""
    res = get(f"/transactions{query}", headers=seeded_headers)
    assert_status(res, 200)
    assert len(res.json()) == expected_count, (
        f"查询 {query}  期望 {expected_count} 条，实际 {len(res.json())} 条  响应：{res.text[:200]}"
    )
