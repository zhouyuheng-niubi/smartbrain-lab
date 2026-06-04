"""Run engine state-machine test — zero tokens via the fake LLM fixture."""
from sqlmodel import Session

from server.app.engine import run_engine
from server.app.models.database import Methodology, engine


def test_full_decomposition_loop(client, fake_llm):
    mid = client.get("/api/methodologies", params={"q": "拆解"}).json()["methodologies"][0]["id"]

    with Session(engine) as s:
        run = run_engine.start_run(s, mid, "给销售做个能看业绩的东西", "test run")
        assert run.status == "in_progress"
        assert run.current_step_index == 0

        for _ in range(50):  # safety bound
            res = run_engine.ask_gate(s, run)
            if res.get("done"):
                break
            assert res["ai_question"]
            out = run_engine.submit_answer(
                s, run, res["gate"]["id"], "目标是提升销售转化率，指标是月度达成率，作为经理我希望实时查看。"
            )
            assert out["resolved"] is True  # fake judge always passes
            if out["run_done"]:
                break

        final = run_engine.synthesize_artifact(s, run)
        assert final.status == "completed"
        assert "验收标准" in final.artifact_md
        assert final.artifact_score is not None
        assert final.artifact_score["total"] > 0

        m = s.get(Methodology, mid)
        assert m.run_count >= 1
        assert m.avg_artifact_score is not None

        oc = run_engine.record_outcome(s, run.id, usefulness=5, adopted=True)
        assert oc.usefulness == 5 and oc.adopted is True
