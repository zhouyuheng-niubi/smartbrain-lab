"""Seed: 需求评审/拆解方法论 (Phase 1 主角).

分层需求法 + SMART + 验收标准(Given-When-Then) + 边界定义 + 风险识别。
把一句模糊需求，变成可开发、可验收、有边界的结构化拆解书。
"""

METHODOLOGY = {
    "slug": "requirement-decomposition",
    "name": "需求评审 / 拆解方法论",
    "summary": "把一句模糊需求拆成可开发、可验收、有边界的结构化任务——分层需求法 + SMART + 验收标准 + 边界 + 风险。",
    "tags": ["需求", "拆解", "评审", "产品", "管理层"],
    "trigger": {
        "scenarios": [
            "收到一句话的模糊需求",
            "需求评审会前的拆解准备",
            "把客户/老板的诉求变成可开发任务",
            "下属拿到需求不知如何下手",
        ],
        "keywords": ["需求", "拆解", "评审", "模糊", "不清楚", "做个", "想要", "搞一个", "功能"],
    },
    "principles": [
        {"title": "先对齐 Why 再谈 What",
         "detail": "目标不清，不许进入拆解。任何功能都必须能回答'解决什么业务问题'。"},
        {"title": "分层而非分块",
         "detail": "目标→场景→Epic→Story→功能点，逐层下钻；不要一上来就罗列零散功能。"},
        {"title": "边界即定义",
         "detail": "讲清'不做什么'和讲清'做什么'同样重要；模糊边界是 scope creep 的温床。"},
        {"title": "无验收标准等于没需求",
         "detail": "每个功能点都要有可判定的'怎样算做完'，否则它只是一句愿望。"},
    ],
    "steps": [
        {"id": "S1", "name": "澄清目标与背景",
         "intent": "锁定真实业务问题与成功指标", "guidance": "问清楚：为什么现在要做？成功后哪个业务指标会变好？"},
        {"id": "S2", "name": "识别用户与场景",
         "intent": "明确为谁解决、在什么场景", "guidance": "写出至少一条'作为X，我希望Y，以便Z'的用户故事。"},
        {"id": "S3", "name": "分层拆解",
         "intent": "目标→Epic→Story→功能点", "guidance": "拆到 3 层以上，检查是否无重叠、无遗漏（MECE）。"},
        {"id": "S4", "name": "SMART 化每个功能点",
         "intent": "消除模糊词，使每项具体可衡量", "guidance": "把'尽量/优化/更好/友好'替换成具体、可量化的描述或标注待定。"},
        {"id": "S5", "name": "定义验收标准",
         "intent": "每个功能点怎样算做完", "guidance": "用 Given-When-Then（给定…当…那么…）写出可判定的 AC。"},
        {"id": "S6", "name": "划定范围与非目标",
         "intent": "明确不做什么", "guidance": "列出非目标清单，标清本期边界，避免 scope creep。"},
        {"id": "S7", "name": "风险与依赖识别",
         "intent": "暴露未知与依赖", "guidance": "列出最大 3 个风险/依赖/未知，每个配应对或负责人。"},
    ],
    "gates": [
        {"id": "G1", "step_id": "S1",
         "question": "这个需求要解决的真实业务问题是什么？成功之后，哪个可量化指标会变好？",
         "why": "目标缺失会导致后续拆解全是镀金功能。",
         "pass_criteria": "给出明确业务目标，且至少 1 个会改善的指标。"},
        {"id": "G2", "step_id": "S2",
         "question": "主要用户是谁？在什么场景下使用？用一条'作为…我希望…以便…'描述。",
         "why": "脱离用户和场景的功能没有价值锚点。",
         "pass_criteria": "至少 1 条结构完整的用户故事。"},
        {"id": "G3", "step_id": "S3",
         "question": "能否把需求拆成 3 层以上（目标→Epic→Story→功能点）且彼此无重叠、无遗漏？",
         "why": "不分层就会遗漏或重复。",
         "pass_criteria": "出现层级化的拆解结构。"},
        {"id": "G4", "step_id": "S4",
         "question": "每个功能点是否 SMART？还有哪些含'尽量/优化/更好/友好'等模糊词？",
         "why": "模糊词是返工和扯皮的根源。",
         "pass_criteria": "模糊词清零，或被明确标注为待定项。"},
        {"id": "G5", "step_id": "S5",
         "question": "每个功能点的验收标准是什么？怎样算做完（Given-When-Then）？",
         "why": "没有 AC 的需求无法验收。",
         "pass_criteria": "每个主要功能点至少 1 条可判定的验收标准。"},
        {"id": "G6", "step_id": "S6",
         "question": "本期明确'不做'哪些？范围边界画在哪里？",
         "why": "边界含糊会导致 scope creep。",
         "pass_criteria": "给出非目标清单。"},
        {"id": "G7", "step_id": "S7",
         "question": "最大的 3 个风险/依赖/未知是什么？各自如何应对、谁负责？",
         "why": "未识别的风险会在交付期爆炸。",
         "pass_criteria": "风险表含应对措施或负责人。"},
    ],
    "anti_patterns": [
        {"name": "需求镀金", "symptom": "加了一堆'锦上添花'功能但与目标无关",
         "fix": "回到 G1，对每个功能追问'解决什么业务问题'。"},
        {"name": "目标缺失直接拆功能", "symptom": "跳过 Why，上来就列功能清单",
         "fix": "强制先过 G1，目标不清不许进入 S3。"},
        {"name": "验收写成'用户满意'", "symptom": "AC 不可判定",
         "fix": "改写为 Given-When-Then 的客观条件。"},
        {"name": "边界含糊致 scope creep", "symptom": "没有非目标清单，需求不断膨胀",
         "fix": "在 S6 显式列出'本期不做'。"},
        {"name": "把假设当事实", "symptom": "未验证的假设直接进入拆解",
         "fix": "在 S7 把假设列为风险并标注验证方式。"},
    ],
    "artifacts": [
        {"name": "结构化需求拆解书", "format": "markdown",
         "template": (
             "# {标题}\n\n"
             "## 1. 业务目标与背景 (S1)\n- 业务问题：\n- 成功指标：\n\n"
             "## 2. 用户与场景 / 用户故事 (S2)\n- 作为…我希望…以便…\n\n"
             "## 3. 分层拆解 (S3)\n- 目标\n  - Epic\n    - Story\n      - 功能点\n\n"
             "## 4. 功能点 SMART 明细表 (S4)\n| 功能点 | 具体描述 | 可衡量 | 优先级 | 待定项 |\n|---|---|---|---|---|\n\n"
             "## 5. 验收标准 (S5)\n| 功能点 | 验收标准 (Given-When-Then) |\n|---|---|\n\n"
             "## 6. 范围边界与非目标 (S6)\n- 本期做：\n- 本期不做（非目标）：\n\n"
             "## 7. 风险 / 依赖 / 未知 (S7)\n| 风险 | 影响 | 应对 | 负责人 |\n|---|---|---|---|\n"
         )},
    ],
    "metrics": [
        {"name": "功能点含明确 AC 占比", "how_to_measure": "有验收标准的功能点 / 总功能点", "target": "100%"},
        {"name": "评审会被打回条目数", "how_to_measure": "评审会上被要求返工的需求条目数", "target": "尽可能少（趋势下降）"},
        {"name": "开发期 scope-creep 变更数", "how_to_measure": "开发中新增/变更的范围条目数", "target": "趋势下降"},
    ],
    "applicability": {
        "when_to_use": ["拿到一句话的模糊需求", "需求评审会前拆解", "把客户/老板的诉求变成可开发任务"],
        "when_not_to_use": ["需求已非常明确、只差排期", "探索性原型阶段（过早结构化会扼杀探索）", "纯 bug 修复"],
    },
    "examples": [
        {"kind": "positive", "title": "销售业绩看板", "content": "把'给销售做个能看业绩的东西'拆成带 SMART 明细、Given-When-Then 验收、范围边界与风险表的规格书。"},
        {"kind": "negative", "title": "过度流程", "content": "对一个一句话能说清的小改动也硬走全套 7 步——拆解成本超过收益。"},
    ],
    "provenance": {"source_type": "builtin", "origin": "内部沉淀 · 分层需求法 + SMART", "note": "本系统 Phase 1 主角方法论"},
    "related": [
        {"slug": "rice-prioritization", "relation": "downstream", "note": "拆出功能点后用 RICE 排优先级"},
        {"slug": "code-review", "relation": "downstream", "note": "验收标准是评审的锚点"},
    ],
}
