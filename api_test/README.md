# 个人记账 API · 接口自动化测试

对开源项目 **personal-finance-tracker-api**（FastAPI + JWT）的接口层自动化测试。

| 项目 | 说明 |
|---|---|
| 被测系统 | personal-finance-tracker-api（15 个接口） |
| 技术栈 | Python 3.12 / pytest / requests / pytest-html |
| 用例规模 | **149 条**（P0 冒烟 44 / P1 主流程 68 / P2 边界 31 / 缺陷验证 6） |
| 执行结果 | 143 通过，0 失败，**8 个已确认缺陷**（6 条用 xfail 固化） |
| 全量耗时 | 约 2 分 15 秒（瓶颈为 bcrypt 注册开销） |

---

## 一、被测系统

| 模块 | 接口 | 说明 |
|---|---|---|
| 健康 | `GET /` | 服务探活 |
| 用户 | `POST /register` `POST /login` `GET /me` | 注册、登录、当前用户 |
| 交易 | `POST` `GET` `GET/{id}` `PUT/{id}` `DELETE/{id}` `/transactions` | 交易 CRUD + 多条件筛选 |
| 预算 | `POST` `GET` `GET/{id}` `PUT/{id}` `DELETE/{id}` `/budgets` | 预算 CRUD |
| 统计 | `GET /stats` | 合计、笔数、最大单笔，支持按月 |

鉴权方式：JWT，除 `POST /register`、`POST /login`、`GET /` 外均需 `Authorization: Bearer <token>`。

---

## 二、环境准备

```bash
# 1. 依赖
pip install -r requirements-test.txt

# 2. 启动被测服务（另开一个终端）
cd "D:/chatgpt test woke/personal-finance-tracker-api"
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

服务地址默认 `http://127.0.0.1:8000`，如需修改见 `utils/api_client.py` 的 `BASE_URL`。

---

## 三、目录结构

```
api_test/
├── pytest.ini                  配置：testpaths / pythonpath / 标记声明 / 中文 id 不转义
├── requirements-test.txt       测试依赖
├── conftest.py                 夹具层：6 个 fixture
├── clean_test_data.py          清理测试数据（直连 SQLite）
├── 接口测试用例表_标准版.xlsx    用例表 + 缺陷清单（由代码自动生成）
├── report.html                 HTML 测试报告（本地生成）
├── tools/                      辅助脚本
│   ├── probe_boundary.py       边界值探测脚本（先探测再断言）
│   ├── try_token.py            手工取 token 脚本
│   ├── look.http               接口调试用例
│   └── mini_frontend.html      临时联调页面
├── utils/                      工具层
│   ├── api_client.py           get / post / put / delete / call / get_token
│   └── assertions.py           assert_status / assert_detail
└── tests/                      用例层
    ├── test_00_health.py                  1   探活
    ├── test_02_authenticated.py           2   基础读接口
    ├── test_03_register_validation.py    29   注册：字段校验 + 长度边界 + 成功 + 重复
    ├── test_04_transactions.py            1   交易生命周期（7 步）
    ├── test_05_permission.py             10   横向越权 + 数据隔离
    ├── test_06_filter.py                  7   交易筛选
    ├── test_07_negative.py                4   非法查询参数
    ├── test_08_unauthorized.py           12   未授权扫描（12 个端点）
    ├── test_09_login.py                  10   登录：凭证 + 未注册 + 字段校验
    ├── test_10_transactions_validation.py 15  交易创建校验 + 边界
    ├── test_11_budgets.py                26   预算 CRUD
    ├── test_12_stats.py                  15   统计
    ├── test_13_date_boundary.py           7   日期边界
    ├── test_14_known_defects.py           6   已确认缺陷（xfail）
    └── test_15_volume.py                  3   容量 / 分页 / 性能基线
```

---

## 四、执行方式

```bash
cd api_test

# 全量（149 条）
python -m pytest -q

# 冒烟（P0，44 条，部署后必跑）
python -m pytest -m p0 -q

# 主流程回归（P0 + P1）
python -m pytest -m "p0 or p1" -q

# 只看边界与异常
python -m pytest -m p2 -q

# 生成 HTML 报告（单文件，可直接发人）
python -m pytest --html=report.html --self-contained-html

# 查看用例覆盖情况
python -m pytest --collect-only -q

# 清理累积的测试数据
python clean_test_data.py
```

预期输出：

```
143 passed, 6 xfailed in 132s
```

> `6 xfailed` 不是失败，是 6 条已确认缺陷的用例（见第五节）。

---

## 五、已确认缺陷（8 条）

| 编号 | 缺陷 | 严重程度 | 自动化固化 |
|---|---|---|---|
| DEF-001 | bcrypt 只处理前 72 字节，超长密码被截断，不同密码可互相登录 | 严重 | ✅ xfail |
| DEF-002 | 密码超过 4096 位时接口返回 500（应为 422） | 严重 | ✅ xfail |
| DEF-003 | 交易金额无上限校验，1e308 可写入 | 一般 | ✅ xfail |
| DEF-004 | 金额累加溢出导致 `/stats` 的 `total_expenses` 返回 null | 严重 | ✅ xfail |
| DEF-005 | 交易日期无范围校验，可记录公元 1 年 / 9999 年 / 未来日期 | 一般 | ✅ xfail |
| DEF-006 | 金额用 float 累加，`0.1 + 0.2 != 0.3` | 一般 | ✅ xfail |
| DEF-007 | 邮箱 local 部分 65 字符超 RFC 5321 上限仍被接受 | 轻微 | 用例锁定 |
| DEF-008 | `month` 参数在 `/transactions` 返回 400、在 `/stats` 返回 200，规则不一致 | 一般 | 用例锁定 |

完整复现步骤与修复建议见 `接口测试用例表_标准版.xlsx` 的「缺陷清单」页。

**缺陷固化的做法**：使用 `@pytest.mark.xfail(strict=True)`。当前显示 `XFAIL`，不拖累回归结果；
缺陷修复后用例变绿会报 `XPASS`，主动提醒移除标记，防止标记腐烂。

---

## 六、框架设计（三层分离）

```
用例层 tests/          只写"发什么请求 + 断言什么"，不关心域名、超时、token
   ↓ 使用
夹具层 conftest.py     负责"准备环境"：造账号、拿 token、造固定数据
   ↓ 使用
工具层 utils/          负责"怎么发"：域名拼接、超时、JSON 体、请求头
```

### 工具层 `utils/api_client.py`

| 方法 | 说明 |
|---|---|
| `get/post/put/delete` | 封装 HTTP 方法，统一 `BASE_URL` 与 `timeout=10` |
| `call(method, path, body, headers)` | 通用入口，供参数化扫描（如未授权扫描）使用 |
| `get_token(email, password)` | 登录并取 `access_token` |

**为什么统一超时**：初版设为 5 秒，全量执行时偶发 `ReadTimeout`（bcrypt 累积开销导致服务器短暂变慢），
排查后提升至 10 秒——而不是加自动重试，因为**重试会掩盖真实的性能退化**。

### 夹具层 `conftest.py`

| fixture | 作用 | 依赖 |
|---|---|---|
| `_new_headers()` | 普通函数：造一个新账号并返回请求头 | — |
| `auth_headers` | 用户 A 的请求头 | `_new_headers` |
| `other_headers` | 用户 B 的请求头（越权测试用） | `_new_headers` |
| `registered_user` | 已注册用户的邮箱与密码 | — |
| `seeded_headers` | 已造好 3 笔固定交易的账号 | `_new_headers` |
| `budget` | 已创建的 1 个预算（id + 请求头） | `auth_headers` |

默认 `scope="function"`：**每条用例独立账号，互不污染**，代价是每轮约 150 次 bcrypt。

### 断言层 `utils/assertions.py`

| 方法 | 作用 |
|---|---|
| `assert_status(res, expected)` | 断言状态码，失败时输出**请求方法 + URL + 期望/实际 + 完整响应体** |
| `assert_detail(res, text)` | 断言 400/401/404 的 `detail` 文案 |

封装断言不是为了少写代码，而是为了**降低排查成本**：原生 `assert 500 == 200` 只有数字，
封装后能一眼看出请求了什么、服务端回了什么。

---

## 七、用例设计

### 设计方法

| 方法 | 应用示例 |
|---|---|
| 等价类 | 密码 <8 位无效组、≥8 位有效组 |
| 边界值 | 密码 7/8/9 位、分类 0/1/100/101 字符、金额 0/0.001、邮箱总长 254/255 |
| 错误推测 | 请求体塞 `role=admin`、塞他人 `user_id`、传 `page/limit` |
| 场景法 | 交易 7 步生命周期（创建→查→改→复查→删→复查） |
| 权限矩阵 | 12 个受保护端点的未授权扫描、2 种资源 × 3 种操作的横向越权 |

### 覆盖维度

1. **功能正确性**：CRUD 正常流程、统计口径、字段契约
2. **参数校验**：必填、类型、长度、格式、枚举值
3. **权限安全**：未授权（401）、横向越权（404）、数据隔离、属主篡改
4. **数据一致性**：统计与明细交叉验证、删除后统计同步、更新失败不改数据
5. **容量与性能**：条数上限、分页能力、响应时间基线

### 分级

| 级别 | 判据 | 条数 | 何时跑 |
|---|---|---|---|
| P0 | 挂了产品就不能用（核心链路 + 安全防线） | 44 | 每次部署后 |
| P1 | 主流程功能 | 68 | 每日回归 |
| P2 | 边界值、异常参数、容量 | 31 | 版本回归 |
| — | 已确认缺陷验证（xfail） | 6 | 全量时执行 |

---

## 八、几个关键实践

### 1. 用例必须可重复执行

会写库的用例一律用唯一数据（`uuid` 拼接邮箱），避免第二次跑变成 400「用户已存在」。
需要"固定长度 + 唯一值"时用「固定填充 + 随机后缀」拼出，例如 local 恰 64 字符：`"a" * 56 + uuid4().hex[:8]`。

### 2. 先探测再断言

需求文档没写的边界（密码上限、金额上限、日期范围），先跑探测脚本看真实行为，
再把确定的结果写成用例，避免"凭想象写期望值"导致假失败。详见 `tools/probe_boundary.py`。

### 3. 验证结果，而不是验证动作

- 删除接口返回 200 只说明"应答了"，必须再查一次确认 404，才证明"数据真没了"
- 越权测试返回 404 只说明"被拒绝了"，必须以属主身份复查数据未被篡改

### 4. 校验失败的用例也要验证数据未被改坏

`PUT /budgets/{id}` 传 `limit=0` 返回 422 后，还要复查原值仍是 1000，防止"报了错但事务没回滚"。

### 5. 已知缺陷用 xfail 固化

把缺陷写成"会红的用例"，既保留证据，又不让红灯干扰回归；用 `strict=True` 让修复自动被感知。

---

## 九、维护指南

### 新增用例

1. 在对应模块文件里加 `test_xxx`，并打 `@pytest.mark.p0/p1/p2`
2. 需要登录态就用 `auth_headers`；需要两个用户用 `other_headers`
3. 状态码断言用 `assert_status`，错误文案用 `assert_detail`
4. 跑 `python -m pytest -q` 确认全绿
5. 重新生成用例表（见下）

### 重新生成用例表

用例表由代码自动解析生成，代码改了表就重生成，避免文档与实现不一致。

### 定期清理数据

```bash
python clean_test_data.py
```

每轮全量会新增约 150 个测试账号，累积后建议清理，避免"新用户无数据"类用例被老数据干扰。

---

## 十、当前局限

- 无并发测试（SQLite 写锁限制，需换 PostgreSQL 才能有意义）
- 无服务端日志断言（当前只校验 HTTP 响应层）
- 分页、排序的用例仅有基线断言（被测接口尚未实现分页）
- 未接入 CI（可挂 GitHub Actions：起服务 → `pytest -m p0` → 上传报告）
