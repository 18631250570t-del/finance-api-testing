"""数据量测试：列表有没有条数上限 / 分页 / 性能基线

实测结论（探测脚本结论）：
  - 没有条数上限：300 笔全部返回
  - 没有分页：传 page/limit 被忽略，仍返回全部
  - 性能线性下降：300 笔 41ms / 39.5KB，推算 1 万笔约 1.4s / 1.3MB，10 万笔约 14s / 13MB

这三条用例的价值是「锁定当前能力边界」：
  若哪天接口加了条数上限或分页，用例会立刻变红，提醒更新。
"""
import time

import pytest

from utils.api_client import get, post
from utils.assertions import assert_status


@pytest.mark.p2
def test_list_returns_all_without_limit(auth_headers):
    """创建 50 笔 -> 列表一次性返回全部 50 条（说明没有条数上限）"""
    for i in range(50):
        post("/transactions", {"amount": i + 1, "category": "vol"}, headers=auth_headers)

    res = get("/transactions", headers=auth_headers)
    assert_status(res, 200)
    assert len(res.json()) == 50, (
        f"只返回了 {len(res.json())} 条，说明存在隐含条数上限（或默认分页）"
    )


@pytest.mark.p2
def test_pagination_params_ignored(auth_headers):
    """传 page/limit 参数 -> 被忽略，仍返回全部（记录：未实现分页）"""
    for i in range(10):
        post("/transactions", {"amount": i + 1, "category": "p"}, headers=auth_headers)

    res = get("/transactions?page=1&limit=3", headers=auth_headers)
    assert_status(res, 200)
    assert len(res.json()) == 10, (
        "分页参数似乎生效了？请确认接口是否已支持分页，若已支持需改写此用例"
    )


@pytest.mark.p2
def test_list_performance_baseline(auth_headers):
    """性能基线：50 笔数据下，列表响应应 < 2 秒"""
    for i in range(50):
        post("/transactions", {"amount": i + 1, "category": "perf"}, headers=auth_headers)

    started = time.monotonic()
    res = get("/transactions", headers=auth_headers)
    elapsed = time.monotonic() - started

    assert_status(res, 200)
    assert len(res.json()) == 50
    assert elapsed < 2.0, f"50 笔数据下列表耗时 {elapsed * 1000:.0f} ms，超过 2 秒基线"
