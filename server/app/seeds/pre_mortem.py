"""Seed: 事前验尸 (Pre-mortem)."""

METHODOLOGY = {
    "slug": "pre-mortem",
    "name": "事前验尸",
    "summary": "在启动前，假设项目已经惨败，倒推'它是怎么失败的'，提前暴露并堵住风险。",
    "tags": ["风险", "立项", "决策", "复盘"],
    "trigger": {
        "scenarios": ["重大项目启动前", "投入大资源前", "团队过度乐观时", "方案评审"],
        "keywords": ["启动", "立项", "风险", "会不会失败", "评审", "上线前"],
    },
    "principles": [
        {"title": "假设已经失败", "detail": "比'有什么风险'更有效的提问是'它已经失败了，复盘为什么'——心理上更敢说真话。"},
        {"title": "先发散再收敛", "detail": "每个人独立写失败原因，避免从众，再汇总。"},
        {"title": "风险要配对策", "detail": "识别风险只是一半，每条高优风险都要有预案和负责人。"},
    ],
    "steps": [
        {"id": "S1", "name": "设定失败场景", "intent": "假设已惨败", "guidance": "宣布'6个月后这个项目彻底失败了'。"},
        {"id": "S2", "name": "独立写失败原因", "intent": "避免从众", "guidance": "每人单独列出'它为什么失败'。"},
        {"id": "S3", "name": "汇总分类排序", "intent": "找出高优风险", "guidance": "合并去重，按概率×影响排序。"},
        {"id": "S4", "name": "制定预案", "intent": "堵住高优风险", "guidance": "Top 风险各配预防/应对措施+负责人。"},
    ],
    "gates": [
        {"id": "G1", "step_id": "S2", "question": "假设它已经失败，最可能的 3 个失败原因是什么？",
         "why": "倒推比正推更能暴露盲点。", "pass_criteria": "列出至少 3 个具体失败原因。"},
        {"id": "G2", "step_id": "S3", "question": "这些风险按'发生概率 × 影响'排序，最该先堵的是哪几个？",
         "why": "不排序就会平均用力。", "pass_criteria": "风险有概率/影响排序。"},
        {"id": "G3", "step_id": "S4", "question": "Top 风险各自的预防措施和负责人是什么？",
         "why": "无预案的风险识别没有价值。", "pass_criteria": "每个高优风险有措施+负责人。"},
    ],
    "anti_patterns": [
        {"name": "走过场", "symptom": "只列'没风险'或泛泛而谈", "fix": "强制每人写 3 个具体失败原因。"},
        {"name": "识别不应对", "symptom": "列了风险就结束", "fix": "G3 要求每条高优风险配预案。"},
        {"name": "乐观偏见", "symptom": "团队一致觉得稳赢", "fix": "用'已经失败'的措辞逼出反面意见。"},
    ],
    "artifacts": [
        {"name": "事前验尸清单", "format": "markdown",
         "template": "# 事前验尸：{项目}\n\n## 失败场景假设\n\n## 失败原因（概率/影响排序）\n| 失败原因 | 概率 | 影响 | 预案 | 负责人 |\n|---|---|---|---|---|\n"}],
    "metrics": [
        {"name": "识别的高优风险数", "how_to_measure": "排序后 Top 风险数量", "target": "≥3"},
        {"name": "带预案的风险占比", "how_to_measure": "有应对措施的风险/总风险", "target": "高优 100%"},
    ],
    "applicability": {
        "when_to_use": ["高投入/高风险项目启动前", "团队明显过度乐观", "决策不可逆"],
        "when_not_to_use": ["低风险可逆的小事", "已在执行中（应改用常规风险跟踪）"],
    },
    "examples": [
        {"kind": "positive", "title": "Gary Klein 提出", "content": "研究表明'假设已失败'的提问方式比'有何风险'多发现约30%的潜在问题。"},
    ],
    "provenance": {"source_type": "builtin", "origin": "Gary Klein (HBR)", "note": "认知心理学家提出的决策工具"},
    "related": [
        {"slug": "five-whys-postmortem", "relation": "complements", "note": "一个事前防、一个事后查"},
        {"slug": "amazon-working-backwards", "relation": "complements", "note": "立项时一起用：先逆向定义价值，再事前验尸排雷"},
    ],
}
