"""三个基础读接口：/me、/transactions（空列表）、/stats（空统计）

注意：stats 的空数据校验已在 test_12_stats.py::test_stats_empty 覆盖，
所以本文件不再重复测 stats。
"""
import pytest

from utils.api_client import get
from utils.assertions import assert_status


@pytest.mark.p0
def test_me_ok(auth_headers):
    """带 token 查 /me -> 200，且只返回 user_id 一个字段"""
    res = get("/me", headers=auth_headers)
    assert_status(res, 200)
    body = res.json()
    assert set(body.keys()) == {"user_id"}
    assert isinstance(body["user_id"], int)


@pytest.mark.p0
def test_transactions_list_empty(auth_headers):
    """新用户查列表 -> 200 且是空数组（不是 null、不是 404）"""
    res = get("/transactions", headers=auth_headers)
    assert_status(res, 200)
    assert res.json() == []
