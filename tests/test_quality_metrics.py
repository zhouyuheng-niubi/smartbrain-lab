"""Unit tests for the score_decomposition VENDOR-PATCH."""
from core.quality_metrics import score_artifact, score_decomposition

GOOD = """# 看板
## 1. 业务目标与背景
- 业务问题：看不到业绩。
- 成功指标：转化率提升。
## 2. 用户故事
- 作为销售经理，我希望看到业绩，以便调整。
## 3. 分层拆解
- 目标 - Epic - Story - 功能点
## 4. 功能点 SMART 明细表
| 功能点 | 描述 |
|---|---|
| 成单金额 | 展示当月金额 |
## 5. 验收标准
| 功能点 | 给定登录，当打开，那么显示金额 |
|---|---|
## 6. 范围边界与非目标
- 本期不做：提成计算。
## 7. 风险
| 风险 | 应对 |
|---|---|
| 数据口径 | 先对齐 |
"""

VAGUE = "## 需求\n做个更好用的、尽量友好的、体验更优的系统，优化一下流程。"


def test_score_decomposition_good_artifact_scores_positive():
    res = score_decomposition(GOOD)
    assert res["phase"] == "decomposition"
    assert res["total"] > 0
    for dim in ("goal_clarity", "layering", "smartness", "acceptance", "boundary_risk"):
        assert dim in res["dimensions"]
    assert res["dimensions"]["acceptance"] > 0


def test_vague_terms_lower_smartness():
    good = score_decomposition(GOOD)["dimensions"]["smartness"]
    vague = score_decomposition(VAGUE)["dimensions"]["smartness"]
    assert vague < good


def test_score_artifact_dispatches_decomposition():
    res = score_artifact("decomposition", GOOD)
    assert res is not None and res["phase"] == "decomposition"
