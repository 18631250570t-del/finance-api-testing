# -*- coding: utf-8 -*-
"""清理测试数据（会清空 users / transactions / budgets 三张表）

用途：跑了很多轮测试后，数据库里会累积上千个测试账号。
      清空后环境干净，避免"新用户无数据"这类用例被老数据干扰。

注意：这是**直接操作数据库**，不是在测接口。
     只在本地测试环境用，绝不要对生产库执行。
"""
import sqlite3
from pathlib import Path

DB = Path(r"D:\chatgpt test woke\personal-finance-tracker-api\finance.db")


def main():
    if not DB.exists():
        print(f"数据库不存在：{DB}")
        return

    con = sqlite3.connect(DB)
    print("清理前：")
    for t in ("users", "transactions", "budgets"):
        n = con.execute(f"select count(*) from {t}").fetchone()[0]
        print(f"  {t}: {n} 行")

    # 先删子表再删主表（虽然没有外键约束，顺序仍按依赖来）
    con.execute("delete from transactions")
    con.execute("delete from budgets")
    con.execute("delete from users")
    con.commit()
    con.execute("vacuum")
    con.commit()

    print("清理后：")
    for t in ("users", "transactions", "budgets"):
        n = con.execute(f"select count(*) from {t}").fetchone()[0]
        print(f"  {t}: {n} 行")
    con.close()


if __name__ == "__main__":
    main()
