"""Seed: 第一性原理 (First Principles Thinking)."""

METHODOLOGY = {
    "slug": "first-principles",
    "name": "第一性原理",
    "summary": "把问题拆到不可再拆的基本事实，再从事实自底向上重建方案——而不是靠类比/惯例推理。",
    "tags": ["决策", "创新", "第一性原理", "思维"],
    "trigger": {
        "scenarios": ["大家都说'只能这么做'时", "成本/性能卡在瓶颈", "要做颠覆式创新", "方案陷入路径依赖"],
        "keywords": ["为什么不能", "一直都是", "行业惯例", "突破", "颠覆", "本质"],
    },
    "principles": [
        {"title": "区分'事实'与'惯例'", "detail": "大多数'必须'其实是别人传下来的惯例，不是物理定律。先识别哪些是真约束。"},
        {"title": "拆到不可再拆", "detail": "把问题分解到最基本、最确定的事实层，那里才没有人云亦云。"},
        {"title": "自底向上重建", "detail": "从基本事实出发重新推导方案，而不是在现有方案上修补。"},
    ],
    "steps": [
        {"id": "S1", "name": "陈述问题与现有方案", "intent": "写下默认做法", "guidance": "把'大家都怎么做'明确写出来。"},
        {"id": "S2", "name": "列出所有假设/约束", "intent": "把隐含前提摊开", "guidance": "逐条列出方案背后的假设。"},
        {"id": "S3", "name": "拆解到基本事实", "intent": "区分真约束与惯例", "guidance": "对每条假设问'这是物理/数学事实，还是惯例？'"},
        {"id": "S4", "name": "从事实重建", "intent": "自底向上设计", "guidance": "只用确认的事实，重新推导可能的方案。"},
        {"id": "S5", "name": "对比验证", "intent": "新旧方案对照", "guidance": "新方案与默认做法比，差距和代价在哪。"},
    ],
    "gates": [
        {"id": "G1", "step_id": "S2", "question": "你列的约束里，哪些是真正的物理/数学事实，哪些只是'一直这么做'？",
         "why": "惯例伪装成约束是创新最大的障碍。", "pass_criteria": "每条约束标注了'事实'或'惯例'。"},
        {"id": "G2", "step_id": "S3", "question": "拆到最底层，这个问题真正不可改变的基本事实是什么？",
         "why": "拆得不够深就还在别人的框架里。", "pass_criteria": "给出了几条不可再拆的基本事实。"},
        {"id": "G3", "step_id": "S4", "question": "如果只用这些基本事实从零设计，你会怎么做？",
         "why": "强制跳出现有方案。", "pass_criteria": "提出了至少一个不同于默认做法的方案。"},
    ],
    "anti_patterns": [
        {"name": "类比推理", "symptom": "'别人/竞品都这么做所以我们也这么做'", "fix": "回到 S3，问这个做法基于什么事实。"},
        {"name": "假约束当真约束", "symptom": "把预算/惯例/审批当成物理定律", "fix": "G1 强制区分事实与惯例。"},
        {"name": "拆解不彻底", "symptom": "停在'行业常识'层", "fix": "继续追问'为什么'直到基本事实。"},
    ],
    "artifacts": [
        {"name": "第一性原理分析表", "format": "markdown",
         "template": "# {问题}\n\n## 默认方案\n\n## 假设/约束（标注 事实/惯例）\n| 约束 | 事实? | 依据 |\n|---|---|---|\n\n## 基本事实\n\n## 自底向上重建的方案\n\n## 新旧对比\n"}],
    "metrics": [
        {"name": "被推翻的'伪约束'数", "how_to_measure": "被识别为惯例而非事实的约束数", "target": "≥1"},
        {"name": "是否产出差异化方案", "how_to_measure": "新方案是否实质不同于默认做法", "target": "是"},
    ],
    "applicability": {
        "when_to_use": ["需要突破性方案", "成本/性能遇到看似硬性的天花板", "怀疑现状是路径依赖"],
        "when_not_to_use": ["常规、低风险、已有成熟最佳实践的事（重新发明轮子浪费时间）", "需要快速决策的小事", "纯执行类任务"],
    },
    "examples": [
        {"kind": "positive", "title": "电池成本", "content": "马斯克拆到'电池由什么材料构成、这些材料市价多少'，发现理论成本远低于市价，于是自建供应链。"},
        {"kind": "negative", "title": "误用", "content": "对'要不要给按钮加圆角'这种小事也搞第一性原理，徒增成本——该用惯例的地方别硬拆。"},
    ],
    "provenance": {"source_type": "builtin", "origin": "Aristotle / Elon Musk", "note": "经典思维方法，Musk 推广至工程领域"},
    "related": [
        {"slug": "musk-five-step", "relation": "complements", "note": "五步法的第1步'质疑需求'就是第一性原理的应用"},
        {"slug": "requirement-decomposition", "relation": "upstream", "note": "先用第一性原理定方向，再用需求拆解落地"},
    ],
}
