"""Seed: ADR 技术决策记录 (Architecture Decision Record)."""

METHODOLOGY = {
    "slug": "adr-tech-decision",
    "name": "ADR 技术决策记录",
    "summary": "把一个有分量的技术选型决策，连同'背景-选项-权衡-决定-后果'一并固化下来，让未来的人知道'当时为什么这么选'。",
    "tags": ["架构", "技术决策", "选型", "工程", "文档"],
    "trigger": {
        "scenarios": ["重要技术选型(框架/数据库/架构)", "引入新依赖", "推翻一个旧决策", "团队对方案有分歧"],
        "keywords": ["选型", "技术决策", "用什么", "架构", "ADR", "要不要上"],
    },
    "principles": [
        {"title": "记录'为什么'而非只记'是什么'", "detail": "代码能告诉你做了什么，但只有 ADR 能告诉你当时为什么这么选、放弃了什么。"},
        {"title": "诚实列出被否的选项", "detail": "写清楚还考虑过哪些方案、为什么没选——这是 ADR 最值钱的部分。"},
        {"title": "承认后果与代价", "detail": "每个决策都有代价，写下来才能让后人判断'现在还成立吗'。"},
    ],
    "steps": [
        {"id": "S1", "name": "背景与问题", "intent": "讲清要解决什么", "guidance": "当前处境、约束、需要决策的点。"},
        {"id": "S2", "name": "候选选项", "intent": "列出认真考虑过的方案", "guidance": "至少 2-3 个，含被否的。"},
        {"id": "S3", "name": "权衡对比", "intent": "各选项利弊", "guidance": "按关键维度（成本/团队熟悉度/可维护性/风险）对比。"},
        {"id": "S4", "name": "决定", "intent": "选哪个及理由", "guidance": "明确选择 + 决定性理由。"},
        {"id": "S5", "name": "后果", "intent": "代价与后续", "guidance": "带来的正/负后果、需要承担的代价、何时该复审。"},
    ],
    "gates": [
        {"id": "G1", "step_id": "S2", "question": "你认真考虑过哪些备选方案？至少有没有 2 个？",
         "why": "只有一个选项的'决策'不是决策。", "pass_criteria": "列出 ≥2 个候选。"},
        {"id": "G2", "step_id": "S3", "question": "按哪些关键维度对比的？被否的选项'输'在哪？",
         "why": "没有维度的对比是情绪化选型。", "pass_criteria": "有明确对比维度 + 被否原因。"},
        {"id": "G3", "step_id": "S5", "question": "这个决定带来的代价/负面后果是什么？什么条件下应该重新评估它？",
         "why": "不写代价的决策会被后人误当成'没有代价'。", "pass_criteria": "写明了代价 + 复审触发条件。"},
    ],
    "anti_patterns": [
        {"name": "只记结论", "symptom": "'我们用 X'，没有为什么", "fix": "强制写候选+权衡+后果。"},
        {"name": "事后粉饰", "symptom": "把已定的事补一份漂亮文档，掩盖真实分歧", "fix": "诚实记录当时的不确定与分歧。"},
        {"name": "选项凑数", "symptom": "为显得严谨编两个明显不可能的备选", "fix": "只列真正认真考虑过的。"},
    ],
    "artifacts": [
        {"name": "ADR 文档", "format": "markdown",
         "template": "# ADR-{编号}: {决策标题}\n状态：提议/采纳/废弃\n\n## 背景\n\n## 候选选项\n\n## 权衡对比\n| 维度 | 选项A | 选项B | 选项C |\n|---|---|---|---|\n\n## 决定\n\n## 后果（代价 / 复审条件）\n"}],
    "metrics": [
        {"name": "候选选项数", "how_to_measure": "认真对比的方案数", "target": "≥2"},
        {"name": "是否写明代价", "how_to_measure": "后果章节是否含负面代价与复审条件", "target": "是"},
    ],
    "applicability": {
        "when_to_use": ["有长期影响、难回退的技术决策", "决策涉及多人/未来接手者", "选型有真实分歧"],
        "when_not_to_use": ["可轻易回退的小决策（写 ADR 是过度流程）", "纯个人偏好、无团队影响的事"],
    },
    "examples": [
        {"kind": "positive", "title": "选数据库", "content": "记录'为何选 PostgreSQL 而非 MongoDB'：对比一致性需求/团队经验/运维成本，写明放弃 Mongo 的原因，半年后争议时一查即明。"},
        {"kind": "negative", "title": "误用", "content": "给'用 lodash 还是手写一个 debounce'也写 ADR——小到可回退的事不值得。"},
    ],
    "provenance": {"source_type": "builtin", "origin": "Michael Nygard", "note": "业界广泛采用的轻量架构决策记录法"},
    "related": [
        {"slug": "first-principles", "relation": "upstream", "note": "重大选型先用第一性原理拆，再用 ADR 固化"},
    ],
}
