"""End-to-end smoke test with a REAL LLM — proves the Phase 1 closed loop.

Requires SILICONFLOW_API_KEY in the environment (or .env). Runs the whole loop
in-process via TestClient against the real LLM. Exit code 0 = loop works.

    python scripts/smoke_run.py
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./_smoke.db")

from fastapi.testclient import TestClient  # noqa: E402

from server.app.main import app  # noqa: E402

RAW = "给销售做个能看业绩的东西"
ANSWER = (
    "业务目标：销售团队看不到实时业绩，月底才发现差距，希望提升月度达成率（指标：达成率、人均转化率）。"
    "用户：作为销售经理，我希望实时看到团队业绩，以便及时调整策略。"
    "分层：目标(业绩可视化)→Epic(业绩看板)→Story(个人/团队视图)→功能点(本月成单金额、达成率)。"
    "每个功能点都具体可量化（按销售展示当月成单总额，单位元）。"
    "验收标准：给定登录的销售经理，当打开看板，那么显示本月每位销售的成单金额与达成率。"
    "边界：本期只做展示，不做提成计算与发放（非目标）。"
    "最大的三个风险/依赖：①CRM 数据口径不一致，应对：先对齐口径，负责人：数据组张三；"
    "②依赖 CRM 开放数据接口，应对：提前与 IT 确认接口，负责人：后端李四；"
    "③历史数据缺失影响趋势，应对：先用近三月数据，负责人：产品王五。"
)


def main() -> int:
    from core.llm_config import list_configured_providers
    if not any(list_configured_providers().values()):
        print("✗ 未检测到任何已配置的 LLM 供应商 key（REDACTED_CREDENTIAL_NAME / SILICONFLOW_API_KEY 等）")
        return 2

    with TestClient(app) as c:
        # 1) suggest
        sug = c.post("/api/methodologies/suggest", json={"raw_input": RAW}).json()
        slugs = [s.get("slug") for s in sug["suggestions"]]
        assert "requirement-decomposition" in slugs, f"suggest 未命中拆解方法论: {slugs}"
        print(f"[1] suggest ({sug['mode']}) → {slugs}")

        mid = next(m["id"] for m in c.get("/api/methodologies", params={"q": "拆解"}).json()["methodologies"])

        # 2) create run
        run_id = c.post("/api/runs", json={"methodology_id": mid, "raw_input": RAW, "title": "smoke"}).json()["run"]["id"]
        print(f"[2] run created: {run_id}")

        # 3) loop ask/answer
        for i in range(30):
            ask = c.post(f"/api/runs/{run_id}/ask").json()
            if ask.get("done"):
                break
            gid = ask["gate"]["id"]
            print(f"    gate {gid}: {ask['ai_question'][:50]}…")
            res = c.post(f"/api/runs/{run_id}/answer", json={"gate_id": gid, "answer": ANSWER}).json()
            print(f"      → resolved={res['resolved']}  {res.get('reason', '')[:40]}")
            if res["run_done"]:
                break

        # 4) synthesize
        syn = c.post(f"/api/runs/{run_id}/synthesize").json()
        art = syn["run"]["artifact_md"]
        score = syn["run"]["artifact_score"]
        assert "验收标准" in art, "产出物缺少验收标准章节"
        assert score and score["total"] > 0, f"质量分异常: {score}"
        print(f"[4] synthesized: {len(art)} chars, score={score['total']}")

        # 5) outcome
        c.post(f"/api/runs/{run_id}/outcome", json={"usefulness": 5, "adopted": True})

        # 6) methodology stats rolled up
        m = c.get(f"/api/methodologies/{mid}").json()
        assert m["run_count"] >= 1 and m["avg_artifact_score"] is not None
        print(f"[6] methodology stats: run_count={m['run_count']} avg={m['avg_artifact_score']}")

    print("\n✓ SMOKE PASSED — Phase 1 闭环跑通")
    return 0


if __name__ == "__main__":
    sys.exit(main())
