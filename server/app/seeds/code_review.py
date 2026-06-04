"""Seed: 代码评审法 (Code Review Discipline)."""

METHODOLOGY = {
    "slug": "code-review",
    "name": "代码评审法",
    "summary": "把资深评审者的'看哪里、问什么、怎么提'固化成可复用的评审套路，让新人也能评出 80 分、并保持评审是建设性的。",
    "tags": ["代码评审", "工程", "质量", "管理赋能", "日常"],
    "trigger": {
        "scenarios": ["review 一个 PR/MR", "新人不知如何评审", "评审质量参差/沦为走过场", "评审变成吵架"],
        "keywords": ["评审", "review", "PR", "代码质量", "合并", "MR"],
    },
    "principles": [
        {"title": "先理解意图再挑毛病", "detail": "看懂这段代码想解决什么问题，再评——否则容易评错重点。"},
        {"title": "正确性 > 设计 > 风格", "detail": "按优先级看：先确认对不对，再看设计合不合理，最后才是命名/格式（能交给工具的别人工挑）。"},
        {"title": "对代码不对人", "detail": "评论针对代码，给出'为什么'和'建议怎么改'，把'你写错了'换成'这里在X情况下会Y'。"},
        {"title": "区分'必须改'和'建议'", "detail": "明确标注阻塞项与可选优化，别让作者猜哪条是硬要求。"},
    ],
    "steps": [
        {"id": "S1", "name": "理解意图", "intent": "看懂要解决什么", "guidance": "读 PR 描述/关联需求，搞清目标再读代码。"},
        {"id": "S2", "name": "查正确性", "intent": "对不对、有没有坑", "guidance": "边界条件、错误处理、并发、空值、回归风险。"},
        {"id": "S3", "name": "看设计", "intent": "合不合理、好不好维护", "guidance": "抽象是否恰当、是否过度设计、是否有更简单的做法。"},
        {"id": "S4", "name": "看测试", "intent": "覆盖关键路径没", "guidance": "关键逻辑/边界是否有测试，测试是否真在验证行为。"},
        {"id": "S5", "name": "给建设性反馈", "intent": "可执行、分轻重", "guidance": "每条评论带原因+建议，标注阻塞/建议。"},
    ],
    "gates": [
        {"id": "G1", "step_id": "S1", "question": "你能用一句话说清这个改动要解决什么问题吗？",
         "why": "没理解意图的评审会挑错重点。", "pass_criteria": "能复述改动意图。"},
        {"id": "G2", "step_id": "S2", "question": "边界条件、错误处理、空值、并发、回归——有没有逐项过一遍？最担心哪个？",
         "why": "正确性是评审第一职责。", "pass_criteria": "正确性维度逐项检查，指出最大风险点。"},
        {"id": "G3", "step_id": "S4", "question": "关键逻辑和边界有对应测试吗？测试是在验证行为还是只为覆盖率？",
         "why": "无测试的改动是定时炸弹。", "pass_criteria": "确认了关键路径测试是否充分。"},
        {"id": "G4", "step_id": "S5", "question": "你的每条评论是否带了'为什么'和'建议怎么改'，并标了'必须改'还是'建议'？",
         "why": "光说'不好'不可执行，且伤人。", "pass_criteria": "评论可执行 + 区分阻塞/建议。"},
    ],
    "anti_patterns": [
        {"name": "风格警察", "symptom": "通篇在挑命名/格式", "fix": "把风格交给 linter/formatter，人力看正确性与设计。"},
        {"name": "橡皮图章", "symptom": "扫一眼就 LGTM", "fix": "强制过 G2 正确性检查。"},
        {"name": "打击式评论", "symptom": "'这写的什么'", "fix": "改成'这里在X会Y，建议Z'。"},
        {"name": "意图不明就评", "symptom": "没看需求直接挑刺", "fix": "先过 G1。"},
    ],
    "artifacts": [
        {"name": "评审结论", "format": "markdown",
         "template": "# 评审：{PR标题}\n\n## 改动意图（一句话）\n\n## 阻塞项（必须改）\n- [ ] \n\n## 建议项（可选）\n- [ ] \n\n## 测试评估\n\n## 结论：通过 / 需修改后再审\n"}],
    "metrics": [
        {"name": "缺陷拦截率", "how_to_measure": "评审拦下的问题 / 该模块线上问题趋势", "target": "上升"},
        {"name": "阻塞/建议是否分清", "how_to_measure": "评论是否标注轻重", "target": "是"},
        {"name": "返工轮次", "how_to_measure": "一个 PR 来回修改的轮数", "target": "下降"},
    ],
    "applicability": {
        "when_to_use": ["所有合并前的代码评审", "想把资深评审标准传给新人", "评审质量需要拉齐"],
        "when_not_to_use": ["原型/一次性脚本（按需轻评即可）", "纯格式化改动（交给工具）"],
    },
    "examples": [
        {"kind": "positive", "title": "Google 工程实践", "content": "Google 的 code review 准则强调：评审看正确性与可维护性，风格靠自动化；评论要建设性、可执行。"},
        {"kind": "negative", "title": "反例", "content": "评审 30 条评论全是变量命名，却漏了一个没处理的空指针——重点彻底搞反。"},
    ],
    "provenance": {"source_type": "builtin", "origin": "Google Engineering Practices", "note": "综合业界代码评审最佳实践"},
    "related": [
        {"slug": "requirement-decomposition", "relation": "upstream", "note": "需求拆得清，评审才有验收锚点"},
        {"slug": "five-whys-postmortem", "relation": "downstream", "note": "评审漏掉的问题，事后用 5Why 复盘补强评审清单"},
    ],
}
