"""Seed: 马斯克五步法 (The Algorithm)."""

METHODOLOGY = {
    "slug": "musk-five-step",
    "name": "马斯克五步法",
    "summary": "质疑需求→删除→简化→加速→自动化。顺序不可颠倒：先删再优化，否则你在优化本不该存在的东西。",
    "tags": ["精简", "效率", "流程优化", "第一性原理"],
    "trigger": {
        "scenarios": ["流程/系统冗余低效", "上线前的优化阶段", "成本过高需要砍", "团队在做重复劳动"],
        "keywords": ["优化", "精简", "效率", "自动化", "成本", "冗余", "提速", "砍"],
    },
    "principles": [
        {"title": "所有需求都是错的", "detail": "先质疑每条需求/约束，尤其是聪明人提出的——它们最危险，因为没人敢质疑。"},
        {"title": "删到必须加回来为止", "detail": "如果你没有把至少 10% 删掉再加回来，说明你删得不够狠。"},
        {"title": "顺序不可颠倒", "detail": "常见错误是先优化/自动化一个本该被删除的步骤。先删，再简化，最后才自动化。"},
    ],
    "steps": [
        {"id": "S1", "name": "质疑需求", "intent": "让每条需求挂到一个具体的人名上",
         "guidance": "需求必须来自一个有名有姓的人，而非'某部门'，这样才能回溯和质疑。"},
        {"id": "S2", "name": "删除", "intent": "删掉一切非必须的部件/步骤/流程",
         "guidance": "默认删错——如果后来发现删多了，再加回来。没加回过任何东西=删得不够。"},
        {"id": "S3", "name": "简化", "intent": "只对'幸存'下来的项做简化",
         "guidance": "注意：不要先简化再删除，那是在打磨垃圾。"},
        {"id": "S4", "name": "加速", "intent": "加快幸存且简化后的流程", "guidance": "提速时警惕引入新的质量风险。"},
        {"id": "S5", "name": "自动化", "intent": "最后才自动化", "guidance": "只有流程稳定到值得固化时才自动化，否则是把混乱固化。"},
    ],
    "gates": [
        {"id": "G1", "step_id": "S1", "question": "这条需求/约束的责任人具体是谁（姓名）？",
         "why": "挂到部门上的需求无法质疑。", "pass_criteria": "每条关键需求都有具体责任人。"},
        {"id": "G2", "step_id": "S2", "question": "如果把它删掉会发生什么？删错了能否加回来？",
         "why": "强制评估每一项的真实必要性。", "pass_criteria": "明确了删除影响与可逆性。"},
        {"id": "G3", "step_id": "S3", "question": "你正在简化的对象，是否已经通过了'删除'这一关？",
         "why": "防止打磨本该删除的东西。", "pass_criteria": "确认简化对象是幸存项。"},
        {"id": "G4", "step_id": "S4", "question": "加速是否引入了新的质量/安全风险？", "why": "提速常以质量为代价。",
         "pass_criteria": "评估并记录了提速带来的风险。"},
        {"id": "G5", "step_id": "S5", "question": "这个流程是否已经稳定到值得自动化？", "why": "过早自动化=固化混乱。",
         "pass_criteria": "确认流程稳定、重复且值得固化。"},
    ],
    "anti_patterns": [
        {"name": "先自动化再删除", "symptom": "花大力气自动化了一个本该删掉的步骤", "fix": "回到 S2，先评估能否删除。"},
        {"name": "需求挂部门不挂人", "symptom": "'这是合规要求'但找不到具体的人", "fix": "S1 强制落到姓名。"},
        {"name": "删除不彻底", "symptom": "没有任何被删项后来被加回来", "fix": "删得更狠，直到必须加回。"},
    ],
    "artifacts": [
        {"name": "精简决策表", "format": "markdown",
         "template": ("# 精简决策表\n\n| 原需求/步骤 | 责任人 | 保留/删除 | 理由 | 后续动作(简化/加速/自动化) |\n|---|---|---|---|---|\n")},
    ],
    "metrics": [
        {"name": "需求删除率", "how_to_measure": "被删除的需求项 / 原需求项", "target": ">10%"},
        {"name": "步骤数下降比", "how_to_measure": "(原步骤数-新步骤数)/原步骤数", "target": "越高越好"},
        {"name": "Maintainer期缩短比例", "how_to_measure": "(原Maintainer期-新Maintainer期)/原Maintainer期", "target": "可量化的下降"},
    ],
    "applicability": {
        "when_to_use": ["流程/系统冗余低效", "上线前的优化阶段", "成本过高需要砍"],
        "when_not_to_use": ["还在探索'做什么'（先想清楚再精简）", "已经很精简的东西", "需求本身尚未验证"],
    },
    "examples": [
        {"kind": "positive", "title": "SpaceX 减重", "content": "对每个'必须有'的航天惯例件挂上责任人并质疑，删掉大量沿袭件，大幅降本。"},
        {"kind": "negative", "title": "顺序颠倒", "content": "先花大力气把一个步骤自动化，后来才发现这个步骤本就该删——白干。"},
    ],
    "provenance": {"source_type": "builtin", "origin": "Elon Musk (The Algorithm)", "note": "马斯克在多次访谈中阐述的五步法"},
    "related": [
        {"slug": "first-principles", "relation": "complements", "note": "第1步'质疑需求'即第一性原理"},
    ],
}
