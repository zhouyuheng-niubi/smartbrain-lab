"""Prompt templates for the run engine and the distillation engine.

The bracketed markers ([JUDGE] / [SYNTHESIZE] / [DISTILL_*]) let tests'
deterministic fake LLM discriminate the call type without any real tokens.
"""
from __future__ import annotations

# ── Distillation: the JSON shape every extract/synthesize must return ────────
METHODOLOGY_JSON_SCHEMA = """{
  "name": "方法论名称",
  "summary": "一句话精炼概括",
  "tags": ["标签"],
  "trigger": {"scenarios": ["什么情境下该用"], "keywords": ["触发关键词"]},
  "principles": [{"title": "信条", "detail": "为什么这么看问题"}],
  "steps": [{"id": "S1", "name": "步骤名", "intent": "目的", "guidance": "怎么做"}],
  "gates": [{"id": "G1", "step_id": "S1", "question": "每步必答的硬问题", "why": "为何重要", "pass_criteria": "怎样算通过"}],
  "anti_patterns": [{"name": "反模式", "symptom": "症状", "fix": "纠正"}],
  "artifacts": [{"name": "产出物", "format": "markdown", "template": "# 输出骨架"}],
  "metrics": [{"name": "效果度量", "how_to_measure": "如何衡量", "target": "目标"}],
  "applicability": {"when_to_use": ["适用场景"], "when_not_to_use": ["什么时候千万别用它"]},
  "examples": [{"kind": "positive", "title": "案例名", "content": "正例/反例描述"}],
  "related": []
}"""

DISTILL_EXTRACT_TMPL = """[DISTILL_EXTRACT] 你是一位方法论分析专家。下面是某位资深同事在「{topic}」上的真实工作材料。
请**反向归纳**出他隐含遵循的方法论——他看哪里、问什么、按什么步骤、避免什么、什么时候不该这么做。

补充说明：{hint}

真实材料：
\"\"\"{materials}\"\"\"

请只返回一个严格符合下述结构的 JSON（不要任何额外文字），字段尽量填实、可执行，
特别重视 gates(决策闸门) 和 applicability.when_not_to_use(什么时候别用)：
{schema}"""

DISTILL_Q_TMPL = """[DISTILL_Q] 你是一位善于挖掘隐性经验的访谈者，正在采访一位资深的「{topic}」专家，
目标是把他脑子里的方法论结构化出来。

已经聊过的内容：
{transcript}

还需要补强的方面：{gaps}

请基于以上，提出**一个**简短、具体、能挖出隐性经验的问题（优先问：判断依据、踩过的坑、
什么时候不该这么做、如何判断做得好不好）。只输出这一个问题本身。"""

DISTILL_SYNTH_TMPL = """[DISTILL_SYNTH] 你是一位方法论分析专家。下面是与一位「{topic}」资深专家的完整访谈记录。
请把它合成为一套结构化方法论。

访谈记录：
{transcript}

请只返回一个严格符合下述结构的 JSON（不要任何额外文字），把专家的隐性经验落成可复用的
步骤与决策闸门，特别重视 applicability.when_not_to_use：
{schema}"""

GATE_QUESTION_TMPL = """你是一位资深的方法论教练，正在带一位同事走「{methodology_name}」。

当前步骤：{step_name}（{step_intent}）
本步骤要通过的决策闸门：
  问题：{gate_question}
  为什么重要：{gate_why}
  通过标准：{gate_pass_criteria}

同事的原始诉求：
\"\"\"{raw_input}\"\"\"

到目前为止已澄清的内容：
{prior_context}

请基于以上，向这位同事提出**一个**简短、具体、直击要害的追问，帮助他满足这个决策闸门。
只输出这一个问题本身，不要解释、不要寒暄。"""


GATE_JUDGE_TMPL = """[JUDGE] 你是一位严格的方法论评审者。请判断同事的回答是否满足决策闸门。

决策闸门问题：{gate_question}
通过标准：{gate_pass_criteria}

同事的回答：
\"\"\"{user_answer}\"\"\"

请只返回一个 JSON 对象，不要任何额外文字：
{{"resolved": true 或 false, "reason": "一句话判定理由", "followup": "若未通过，给出一句继续追问；通过则留空"}}"""


SYNTHESIZE_TMPL = """[SYNTHESIZE] 你是一位资深方法论教练。请把同事走完「{methodology_name}」全过程的所有问答，
合成为一份结构化产出物。

同事的原始诉求：
\"\"\"{raw_input}\"\"\"

逐个决策闸门的问答记录：
{qa_transcript}

请严格按照下面的产出物骨架填充，输出完整 Markdown（不要省略任何章节，
表格请填入真实内容而非占位符）：

{artifact_template}"""


# ── Lens: 透镜诊断 ────────────────────────────────────────────────────────────
LENS_DIAGNOSIS_JSON_SCHEMA = """{
  "overall": "一句话总评：这份材料用该方法论看，整体如何",
  "score": {"total": 7.5},
  "gate_findings": [
    {"gate_id": "G1", "question": "该闸门的问题", "verdict": "pass|concern|fail",
     "evidence": "材料中的依据（可引用原文）", "suggestion": "具体改进建议"}
  ],
  "anti_pattern_hits": [{"name": "命中的反模式", "evidence": "材料中的体现"}],
  "strengths": ["材料里做得好的点"],
  "top_fixes": ["最该先改的 3 件事"]
}"""

LENS_DIAGNOSE_TMPL = """[LENS_DIAGNOSE] 你是一位严格而建设性的评审专家。请**戴上「{methodology_name}」这副眼镜**，
给下面这份现成材料做一次体检——不是替它重写，而是诊断它在这套方法论下哪里站得住、哪里有问题。

方法论（你的诊断标准）：
{methodology_context}

被诊断的材料（标题：{title}）：
\"\"\"{material}\"\"\"

请只返回一个严格符合下述结构的 JSON（不要任何额外文字）。对每个决策闸门给出 pass/concern/fail
判定并**引用材料中的依据**，命中的反模式要指出具体体现，最后给出最该先改的几件事：
{schema}"""


# ── Advisor: 顾问陪练 ─────────────────────────────────────────────────────────
ADVISOR_SYSTEM_TMPL = """[ADVISOR] 你是一位资深顾问，**完全戴着「{methodology_name}」这套方法论的世界观**
和同事一对一讨论他正纠结的问题。你不是百科全书，而是这套方法论的化身。

这套方法论的内核：
{methodology_context}

同事想讨论的纠结点：{topic}

要求：
- 用这套方法论的**信条和决策闸门**来拷问他、引导他想清楚，而不是直接替他下结论。
- 一次只聚焦一两个最关键的问题，像真人对话一样简洁、犀利、有温度。
- 当他想偷懒跳过关键判断时，温和但坚定地把他拉回来。
- 适时指出他可能正踩的反模式。
先用一两句话开场，并抛出第一个最关键的拷问。"""
