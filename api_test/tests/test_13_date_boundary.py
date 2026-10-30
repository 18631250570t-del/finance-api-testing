"""交易日期边界测试

实测结论：date 字段没有任何范围校验
  - 公元 1 年、1900 年、1970 年都能记账
  - 未来日期（2027、2036、9999）也能记账
本文件锁定当前行为；「应该限制范围」作为缺陷 #5 记在 known_defects。
"""
import pytest

from utils.api_client import get, post
from utils.assertions import assert_status


@pytest.mark.p2
@pytest.mark.parametrize(
    "date_str",
    [
        "0001-01-01T00:00:00",
        "1900-01-01T00:00:00",
        "1970-01-01T00:00:00",
        "2999-12-31T23:59:59",
        "9999-12-31T23:59:59",
    ],
    ids=["公元1年", "1900年", "纪元1970", "2999年", "9999年"],
)
def test_create_with_extreme_date(auth_headers, date_str):
    """记录：任意极端日期都能记账（无范围校验，见缺陷 #5）"""
    res = post("/transactions",
               {"amount": 10, "category": "dt", "date": date_str},
               headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["date"].startswith(date_str[:10])


@pytest.mark.p2
def test_create_with_future_date(auth_headers):
    """未来日期（十年后）也能记账 —— 记录现状"""
    res = post("/transactions",
               {"amount": 10, "category": "future", "date": "2036-03-01T00:00:00"},
               headers=auth_headers)
    assert_status(res, 201)


@pytest.mark.p1
def test_old_transaction_in_stats(auth_headers):
    """1900 年的账能按月份查到，也计入全部统计"""
    post("/transactions",
         {"amount": 777, "category": "old", "date": "1900-01-01T00:00:00"},
         headers=auth_headers)

    month = get("/stats?month=1900-01", headers=auth_headers)
    assert_status(month, 200)
    assert month.json()["total_expenses"] == 777

    everything = get("/stats", headers=auth_headers)
    assert everything.json()["total_expenses"] == 777
