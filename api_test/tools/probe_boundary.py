"""边界探测脚本：先探明系统真实行为，再决定怎么写断言。"""
import sys
import uuid

sys.path.insert(0, r"/")

from utils.api_client import post


def probe(label, payload, unique_email=True):
    body = dict(payload)
    if unique_email and "email" not in body:
        body["email"] = f"p_{uuid.uuid4().hex[:8]}@qq.com"
    try:
        r = post("/register", body)
        print(f"{label:<28} -> {r.status_code}   {r.text[:70]}")
    except Exception as e:
        print(f"{label:<28} -> 异常 {type(e).__name__}: {e}")


print("========== 密码长度边界 ==========")
for n in [7, 8, 9, 72, 73, 100]:
    probe(f"密码 {n} 位", {"password": "a" * n})

print("\n========== 邮箱格式边界 ==========")
probe("邮箱空串", {"email": "", "password": "12345678"}, unique_email=False)
probe("没有 local 部分 @qq.com", {"email": "@qq.com", "password": "12345678"}, unique_email=False)
probe("没有域名后缀 a@b", {"email": f"a{chr(65)}@b", "password": "12345678"}, unique_email=False)
probe("local 恰好 64 字符", {"email": "a" * 64 + "@qq.com", "password": "12345678"}, unique_email=False)
probe("local 65 字符（超限）", {"email": "a" * 65 + "@qq.com", "password": "12345678"}, unique_email=False)
probe("总长 254（上限）", {"email": "a" * 240 + "@qq.com", "password": "12345678"}, unique_email=False)
probe("总长 255+（超限）", {"email": "a" * 250 + "@qq.com", "password": "12345678"}, unique_email=False)
probe("带 + 号", {"email": f"a+{uuid.uuid4().hex[:6]}@qq.com", "password": "12345678"}, unique_email=False)
probe("以点开头", {"email": f".a{uuid.uuid4().hex[:6]}@qq.com", "password": "12345678"}, unique_email=False)
probe("含中文", {"email": "测试@qq.com", "password": "12345678"}, unique_email=False)