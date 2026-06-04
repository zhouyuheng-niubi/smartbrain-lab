"""Seed: 亚马逊逆向工作法 (Working Backwards / PR-FAQ)."""

METHODOLOGY = {
    "slug": "amazon-working-backwards",
    "name": "亚马逊逆向工作法",
    "summary": "从客户结果倒推，而非从能力正推。先写新闻稿(PR)和FAQ，再决定是否开发。",
    "tags": ["立项", "客户价值", "PRFAQ", "产品决策"],
    "trigger": {
        "scenarios": ["新产品/新功能立项", "判断一件事是否值得做", "需要对齐客户价值"],
        "keywords": ["立项", "新产品", "新功能", "客户价值", "PRFAQ", "逆向", "值不值得做"],
    },
    "principles": [
        {"title": "从客户结果倒推", "detail": "先定义客户最终得到什么，再反推要做什么；不要从'我们有什么能力'正推。"},
        {"title": "先写新闻稿再开发", "detail": "在动工前写好发布新闻稿——如果它不令人兴奋，产品多半也不会。"},
        {"title": "FAQ 暴露真问题", "detail": "用内外部 FAQ 逼出最难回答的硬问题，而不是回避它们。"},
    ],
    "steps": [
        {"id": "S1", "name": "写一页新闻稿(PR)", "intent": "用客户视角描述'已发布'的产品",
         "guidance": "标题+副标题+发布段+客户引述，像产品已经上线那样写。"},
        {"id": "S2", "name": "写 FAQ", "intent": "内外部各 5 问", "guidance": "外部 FAQ 面向客户，内部 FAQ 面向团队的硬问题。"},
        {"id": "S3", "name": "定义客户与痛点", "intent": "用客户原话描述痛点", "guidance": "客户是谁？他现在怎么痛？"},
        {"id": "S4", "name": "反推最小可行体验", "intent": "从结果倒推最小要做什么", "guidance": "达成那个客户结果，最少要交付什么？"},
        {"id": "S5", "name": "设定成功指标", "intent": "可量化的成功定义", "guidance": "什么数字达到多少，算这件事成功？"},
    ],
    "gates": [
        {"id": "G1", "step_id": "S3", "question": "客户是谁？用他自己的原话描述痛点是什么？",
         "why": "脱离真实客户的产品是自嗨。", "pass_criteria": "有具体客户画像与原话级痛点。"},
        {"id": "G2", "step_id": "S1", "question": "这篇新闻稿能否让目标客户读完就想'我要这个'？",
         "why": "不令人兴奋的 PR 预示失败的产品。", "pass_criteria": "PR 有清晰的客户价值与兴奋点。"},
        {"id": "G3", "step_id": "S2", "question": "最难回答的那个 FAQ 是什么？你怎么回答？",
         "why": "回避硬问题=把风险推后。", "pass_criteria": "正面回答了至少一个尖锐 FAQ。"},
        {"id": "G4", "step_id": "S4", "question": "如果不做这件事，客户会怎样？机会成本是多少？",
         "why": "评估真实必要性。", "pass_criteria": "讲清了不做的后果与机会成本。"},
        {"id": "G5", "step_id": "S5", "question": "成功的可量化指标是什么？", "why": "无指标=无法判断成败。",
         "pass_criteria": "给出明确、可量化的成功指标。"},
    ],
    "anti_patterns": [
        {"name": "技术驱动逆向", "symptom": "从'我们能做什么'出发而非客户结果", "fix": "回到 S3，先锁定客户与痛点。"},
        {"name": "PR 写成功能清单", "symptom": "新闻稿罗列功能而非客户收益", "fix": "改写为客户视角的收益叙事。"},
        {"name": "FAQ 回避硬问题", "symptom": "只问容易的问题", "fix": "强制 G3 正面回答尖锐问题。"},
    ],
    "artifacts": [
        {"name": "PR-FAQ 文档", "format": "markdown",
         "template": ("# {产品名} — 发布新闻稿\n\n## 标题\n\n## 副标题\n\n## 发布段\n\n## 客户引述\n\n"
                      "---\n\n# FAQ\n\n## 外部 FAQ（面向客户）\n1. \n\n## 内部 FAQ（面向团队）\n1. \n")},
    ],
    "metrics": [
        {"name": "PR 共鸣评分", "how_to_measure": "盲投 1-5 分，目标读者读 PR 后的兴奋度", "target": "≥4"},
        {"name": "未解决硬问题数", "how_to_measure": "FAQ 中仍无答案的尖锐问题数", "target": "趋近 0"},
        {"name": "Go/No-Go 是否明确", "how_to_measure": "评审后是否得出清晰决策", "target": "明确"},
    ],
    "applicability": {
        "when_to_use": ["新产品/新功能立项", "判断一件事值不值得做", "需要对齐客户价值"],
        "when_not_to_use": ["已确定要做、只差执行", "内部小工具/小优化（写 PR-FAQ 是过度投入）"],
    },
    "examples": [
        {"kind": "positive", "title": "AWS", "content": "亚马逊新服务先写一页发布新闻稿 + FAQ，读起来不令人兴奋就不立项。"},
        {"kind": "negative", "title": "技术驱动", "content": "从'我们有这个能力'出发倒推产品，PR 写成功能清单，最终没人要。"},
    ],
    "provenance": {"source_type": "builtin", "origin": "Amazon", "note": "亚马逊 Working Backwards / PR-FAQ 文化"},
    "related": [
        {"slug": "pre-mortem", "relation": "complements", "note": "立项时一起用：先逆向定义价值，再事前验尸排雷"},
        {"slug": "rice-prioritization", "relation": "downstream", "note": "多个值得做的项目之间用 RICE 排序"},
    ],
}

