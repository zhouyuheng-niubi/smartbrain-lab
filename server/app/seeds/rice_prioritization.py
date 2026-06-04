"""Seed: RICE 优先级排序 (RICE Scoring)."""

METHODOLOGY = {
    "slug": "rice-prioritization",
    "name": "RICE 优先级",
    "summary": "用 触达(Reach)×影响(Impact)×信心(Confidence)÷工作量(Effort) 给一堆候选打分排序，把直觉变成可对比的数字。",
    "tags": ["优先级", "产品", "决策", "排期"],
    "trigger": {
        "scenarios": ["需求/功能太多排不过来", "资源有限要取舍", "团队对优先级吵不清", "季度规划"],
        "keywords": ["优先级", "先做哪个", "排期", "取舍", "需求池", "排序"],
    },
    "principles": [
        {"title": "把直觉量化", "detail": "RICE 不是要取代判断，而是让判断的依据透明、可对比、可被挑战。"},
        {"title": "信心是诚实的刹车", "detail": "Confidence 强制你承认'这个影响数据有多可靠'，防止拍脑袋高估。"},
        {"title": "除以工作量", "detail": "高价值但巨贵的事未必该先做；性价比（÷Effort）才是排序的关键。"},
    ],
    "steps": [
        {"id": "S1", "name": "列出候选项", "intent": "拉齐清单", "guidance": "把要排序的需求/功能列全。"},
        {"id": "S2", "name": "估 Reach", "intent": "一段时间内触达多少对象", "guidance": "如'每季度影响多少用户'，用真实数据。"},
        {"id": "S3", "name": "估 Impact", "intent": "对每个对象的影响强度", "guidance": "用统一档位（如 3=大,2=中,1=小,0.5=微）。"},
        {"id": "S4", "name": "估 Confidence", "intent": "对上述估计的信心", "guidance": "100%/80%/50%，有数据才给高信心。"},
        {"id": "S5", "name": "估 Effort", "intent": "工作量(人月)", "guidance": "粗估即可，关键是横向可比。"},
        {"id": "S6", "name": "算分排序", "intent": "得出 RICE 分", "guidance": "RICE=R×I×C÷E，降序排。"},
    ],
    "gates": [
        {"id": "G1", "step_id": "S2", "question": "每项的 Reach 是基于真实数据还是拍脑袋？数据来源是什么？",
         "why": "Reach 拍脑袋会让整个排序失真。", "pass_criteria": "Reach 有数据来源或明确估计依据。"},
        {"id": "G2", "step_id": "S4", "question": "哪些项的 Confidence 低于 80%？低信心说明你缺什么信息？",
         "why": "低信心项往往需要先做小验证而非直接排序。", "pass_criteria": "标出了低信心项及缺失信息。"},
        {"id": "G3", "step_id": "S6", "question": "算出来的排序里，有没有和直觉强烈冲突的？冲突说明哪个估值需要复核？",
         "why": "分数与直觉冲突时，往往是某个输入估错了。", "pass_criteria": "复核了与直觉冲突的条目。"},
    ],
    "anti_patterns": [
        {"name": "为想做的事凑高分", "symptom": "倒着调参数让心头好排第一", "fix": "先定估值标准再打分，分开'估值'与'决策'。"},
        {"name": "忽略 Effort", "symptom": "只看价值不看成本", "fix": "强制 ÷Effort，看性价比。"},
        {"name": "假精确", "symptom": "纠结 Impact 是 2.3 还是 2.4", "fix": "用粗档位，RICE 是相对排序不是绝对真理。"},
    ],
    "artifacts": [
        {"name": "RICE 排序表", "format": "markdown",
         "template": "# RICE 优先级\n\n| 候选 | Reach | Impact | Confidence | Effort(人月) | RICE分 | 数据来源 |\n|---|---|---|---|---|---|---|\n\n## 结论与取舍\n"}],
    "metrics": [
        {"name": "排序是否减少争论", "how_to_measure": "评审是否更快达成一致", "target": "是"},
        {"name": "低信心项是否先验证", "how_to_measure": "Confidence<80% 的项是否安排了小验证", "target": "是"},
    ],
    "applicability": {
        "when_to_use": ["候选项多、需横向取舍", "想让优先级有据可依、可被挑战", "季度/迭代规划"],
        "when_not_to_use": ["战略级少数大赌注（数字会掩盖定性判断）", "强依赖/有硬性顺序约束的事", "候选项性质差异太大无法用同一标尺"],
    },
    "examples": [
        {"kind": "positive", "title": "Intercom 提出", "content": "Intercom 产品团队用 RICE 把'谁的声音大谁的需求先做'换成透明可比的分数。"},
        {"kind": "negative", "title": "误用", "content": "拿 RICE 决定'要不要进入一个全新市场'这种战略赌注——定性因素被数字掩盖。"},
    ],
    "provenance": {"source_type": "builtin", "origin": "Intercom", "note": "Sean McBride 提出的产品优先级框架"},
    "related": [
        {"slug": "amazon-working-backwards", "relation": "upstream", "note": "先逆向确认值得做，再用 RICE 在多个值得做的里排序"},
    ],
}
