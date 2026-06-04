"""Seed: 5 Why 复盘 (Five Whys Root-Cause Analysis)."""

METHODOLOGY = {
    "slug": "five-whys-postmortem",
    "name": "5-Why 复盘",
    "summary": "对一个问题连续追问 5 层'为什么'，穿过表象抵达根因，并落到可执行的系统性改进。",
    "tags": ["复盘", "根因", "事故", "持续改进", "Toyota"],
    "trigger": {
        "scenarios": ["线上事故后", "项目延期/翻车后", "同类问题反复出现", "质量缺陷复盘"],
        "keywords": ["复盘", "事故", "为什么会", "根因", "又出问题", "故障"],
    },
    "principles": [
        {"title": "对事不对人", "detail": "根因几乎总在流程/系统，而非某个人的'不小心'。指向人就停止了思考。"},
        {"title": "穿过表象", "detail": "第一个原因通常是症状；真正的根因要再追问几层。"},
        {"title": "根因要可被系统性消除", "detail": "好的根因对应一个能防止整类问题再发生的改进，而非一次性补救。"},
    ],
    "steps": [
        {"id": "S1", "name": "客观描述问题", "intent": "讲清发生了什么", "guidance": "时间线 + 影响范围，只陈述事实。"},
        {"id": "S2", "name": "连续追问为什么", "intent": "逐层下钻", "guidance": "每个答案再问一次'为什么'，通常 3-5 层。"},
        {"id": "S3", "name": "锁定根因", "intent": "找到系统性原因", "guidance": "判断哪一层是'消除它就能防止整类问题'的那层。"},
        {"id": "S4", "name": "制定改进项", "intent": "落到可执行", "guidance": "每个根因配一个有负责人、有期限的改进动作。"},
    ],
    "gates": [
        {"id": "G1", "step_id": "S1", "question": "问题的客观时间线和影响是什么？（只讲事实，不要归咎于人）",
         "why": "一上来归咎于人会扼杀根因分析。", "pass_criteria": "有事实性时间线，无指责性表述。"},
        {"id": "G2", "step_id": "S2", "question": "针对每一层原因，你是否又问了一次'为什么'，追到了第 3 层以上？",
         "why": "停在表象就是无效复盘。", "pass_criteria": "至少 3 层的为什么链。"},
        {"id": "G3", "step_id": "S3", "question": "你锁定的根因，消除它能防止这一整类问题再发生吗？",
         "why": "区分根因和症状。", "pass_criteria": "根因对应系统性改进而非一次性补救。"},
        {"id": "G4", "step_id": "S4", "question": "每个改进项是否有明确负责人和截止时间？",
         "why": "没人没期限的改进等于没改进。", "pass_criteria": "每项改进含负责人+期限。"},
    ],
    "anti_patterns": [
        {"name": "归咎于人", "symptom": "根因写成'XX 粗心'", "fix": "问'为什么流程允许这个粗心导致事故'。"},
        {"name": "停在第一层", "symptom": "只问一个为什么就收工", "fix": "G2 强制追到 3 层以上。"},
        {"name": "改进项虚空", "symptom": "'加强意识''下次注意'", "fix": "改成具体的流程/工具/检查项变更。"},
    ],
    "artifacts": [
        {"name": "复盘报告", "format": "markdown",
         "template": "# 复盘：{问题}\n\n## 1. 事实时间线\n\n## 2. 为什么链\n- 为什么1：\n  - 为什么2：\n    - 为什么3：\n\n## 3. 根因\n\n## 4. 改进项\n| 改进 | 负责人 | 期限 |\n|---|---|---|\n"}],
    "metrics": [
        {"name": "为什么链深度", "how_to_measure": "追问层数", "target": "≥3"},
        {"name": "同类问题复发率", "how_to_measure": "改进后同类问题是否再发生", "target": "趋近 0"},
    ],
    "applicability": {
        "when_to_use": ["单一、因果链较清晰的问题", "事故/缺陷复盘", "想找到系统性改进"],
        "when_not_to_use": ["多因素交织、非线性的复杂问题（5Why 会过度简化成单一根因）", "需要数据统计归因的场景"],
    },
    "examples": [
        {"kind": "positive", "title": "丰田经典", "content": "机器停了→保险丝断→轴承没润滑→油泵没抽油→油泵进屑→没装滤网。根因=没滤网，装上就根治。"},
        {"kind": "negative", "title": "误用", "content": "'用户流失'这种多因素问题硬套 5Why，得出单一根因往往是错的——该用数据归因。"},
    ],
    "provenance": {"source_type": "builtin", "origin": "Toyota (Sakichi Toyoda)", "note": "丰田生产方式核心工具"},
    "related": [
        {"slug": "pre-mortem", "relation": "complements", "note": "事前验尸防患于未然，5Why 事后找根因"},
    ],
}
