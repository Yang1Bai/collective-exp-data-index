# Edison Playground 报告评估（vs 本仓库 clean-sheet 纲领）

**评估日期：** 2026-07-29
**评估对象：** `Edison Playground.pdf`（23 页，Edison Scientific "Literature (High)" 任务，执行同一份 `EDISON_CLEAN_SHEET_RESEARCH_PROMPT_2026-07-29.md`）
**对照物：** `analysis/review_packages/claude/CLAUDE_SCIENCE_REVIEW_2026-07-29.md` 与今日已执行的 crosslab_fade 实验链

---

## 1. 定位：Edison 看到了什么、没看到什么

Edison 只拿到了 prompt 文本，**没有访问仓库**。因此它不知道：provenance ladder 证据链、within-specimen 机制（MPEA/KIT 正例的共同结构）、已执行的 abstain-everywhere 电池结果、pending 的 strength→fatigue（71905）、以及 `SAFE_CONTRACT_ROUTED_BORROWING_LITERATURE_AUDIT.md` 已经审计过 bilinear transduction 这一事实。它的输出是一份**纯文献驱动**的从零方案。这既是它的盲区（方案与仓库数据资产完全脱钩），也是它的价值（与我们的结论形成独立收敛检验）。

## 2. 引用核实

- **Li et al., "Probing out-of-distribution generalization in machine learning for materials", *Commun. Mater.* (2025), 10.1038/s43246-024-00731-w — 已核实为真**（Hattrick-Simpers 组，700+ OOD 任务，"多数启发式 OOD 测试实为插值"）。这是 Edison 报告最有价值的单篇引用。
- **Yahagi et al., "Transfer learning from first-principles calculations to experiments with chemistry-informed domain transformation", *Mach. Learn.: Sci. Technol.* (2025), 10.1088/2632-2153/adcdc0（arXiv:2504.02848）— 已核实为真**（<10 个实验标定点、误差降一个量级、以 BEP 型转换律为迁移对象）。
- Segal et al. "Known Unknowns"（bilinear transduction）— 本次审查早已核实其 npj Comput. Mater. 版（10.1038/s41524-025-01808-x）；Edison 引 arXiv:2502.05970，同一工作。
- BOOM benchmark（Antoniuk et al., arXiv:2505.01912）— 真实（LLNL）；其 "pretraining 提升 ID 31–35% 却使 OOD binned R² 降 39–53%" 与本仓库 Chemprop −28.12% 的发现**独立收敛**。
- SevenNet-Omni（Nat. Commun. 2026）与 Zhang et al.（arXiv:2601.08486，multi-task fine-tuning 表征塌缩）— 合理但**本次未独立核实**；引用前需查证。
- 数据表小错：Starrydata2 标 "~30K entries"（本仓库冻结提取为 7,403 目标实体）；ICSD 标 "partially open"（实为订阅制，Edison 自己在验证注记里也承认）。

## 3. 收敛点（两份独立分析得到同一结论）

| 结论 | Edison 的依据 | 本仓库的依据 |
|---|---|---|
| **必须更换迁移对象**：不迁移原始特征/预训练权重，迁移机理关系/修正律/参数 | BOOM、表征塌缩、Yahagi | 40-edge null、Chemprop −28%、within-specimen 正例 |
| 泛型 donor-feature injection 应停止 | Stop 建议 #1 | `multi_target_ood_summary.json` 0/7 programme |
| 泛型预训练不是 OOD 策略 | BOOM 39–53% | `optical_supervised_borrowing_summary.json` |
| 随机切分/名义 OOD 不可作为迁移成功证据 | Li 2025 pseudo-OOD | 本次审查的 M1（Q4 是相对距离而非固定新颖区） |

这四点的独立收敛是 Digital Discovery 论文引言的现成论证结构。**Li 2025 必须补引**：它为"把 provenance（article/campaign/lab）作为第一 OOD 轴、组成距离降为第二轴"的重构提供了外部权威依据——组成型 Q4 按 Li 的判据很可能属 pseudo-OOD，而文献/实验室边界才是本仓库数据里被反复证实的真实分布移。

## 4. 分歧：Edison 的两个旗舰实验不应跟随

1. **Experiment A（OC20→OC22 bilinear transduction）**：donor 与 recipient **都是 DFT 数据**。它完全离开了本项目的固定科学目标（相邻**实验**领域知识弥补数据贫乏区），且 5–7 GPU-days、GemNet-OC、250M 结构的基础设施是另一个研究项目。OCP 社区正活跃开发该方向，差异化低。
2. **Experiment B（DFT→实验带隙修正桥）**：方向有价值（Yahagi 型 Sim2Real），但 (a) recipient 依赖 ICSD 订阅或 ~2,700 条文献带隙，本仓库对该类 corpus 的 provenance 风险有惨痛经验；(b) DFT→实验带隙修正是拥挤领域；(c) 它同样绕开了实验→实验的核心命题。
3. **控制标准低于本仓库自身门槛**：Edison 的设计只有 composition holdout + bootstrap，没有 DOI/campaign 级分割、没有 shuffled/wrong-domain matched falsifier 家族、没有 abstention 三态、没有 outcome-blind freeze。按本仓库的 gate 体系，这两个设计属于"未达 eligibility 的边"。

## 5. 唯一应当吸收的实质内容：anchored Δ-transfer × provenance ladder

Edison 排名第一的机制（bilinear transduction：学 Δx→Δy 而非绝对值）本仓库其实已经 audit 过（`SAFE_CONTRACT_ROUTED_BORROWING_LITERATURE_AUDIT.md`："prespecified secondary tail/rank head, not run"）。但把它与 provenance ladder 结合后，第一次有了**明确的机理理由和判决性用法**：

> Ladder 的机制解释是：同一 provenance 单元内部，试样/仪器/操作者 nuisance 对供受体标签是共同的，作差即消去。那么跨文献迁移的正确对象不是绝对值函数 f(x)，而是**within-provenance 差分函数 Δf**，部署时用目标文献内 1–2 个 anchor 测量恢复绝对尺度。若 article nuisance 近似加性偏移，Δ-transfer 应当在绝对迁移失败（CALiSol +1.61%）的同一数据上成功——这是对 ladder 机制本身的直接检验，而不只是又一种方法。

**建议的 E6（零新数据，CPU 小时级，最合适的下一个 reanalysis）：**

- **数据**：CALiSol-23（已有冻结提取与 article-disjoint split）。
- **训练**：在训练文章内部构造配方对 (i,j)，学习 Δ(formulation features) → Δ(log10 σ at −40 °C)。
- **部署**：对每篇 held-out 文章，取 k ∈ {1, 2, 3} 个已发表测量为 anchor（从该文章内随机抽取，非新实验），预测其余配方：ŷ_t = y_anchor + Δ̂(anchor→t)；多 anchor 取精度加权平均。
- **对照**：(i) 绝对迁移 baseline（即现有 +1.61% [−2.14,4.21] 结果，estimand 完全可比）；(ii) shuffled-Δ（打乱配对后训练）；(iii) 等容量 within-article-only Δ（只用目标文章 anchor 训练，不迁移——分离"anchor 本身"与"迁移的 Δ 函数"的贡献）；(iv) wrong-domain Δ。
- **成功门槛（预注册后冻结）**：article-disjoint RMSE 相对绝对迁移 baseline 改善 ≥5 pp、article-cluster bootstrap CI 下界 >0、绝对 R²>0、胜 shuffled-Δ ≥3 pp、k=1 时已有正效应。
- **解释预案**：正 → ladder 机制（加性 nuisance 消去）获得判决性确认，论文获得 L2 层正例，且 Δ-contract 成为可复用方法；零 → article nuisance 非加性（交互型），ladder 描述性成立但机制需修正——同样是重要结论；负 → Δ 函数本身不跨文献，L2 塌缩比预想更深。
- **MPEA 版本（若 Borg 有 reference 列）**：within-reference Δ(composition, state)→Δ(log YS)，同一模板。

这个实验同时回应了我此前 Action 1 的 E1（provenance 剂量反应）：E1 证明"层级决定衰减"，E6 证明"衰减的机制是可消去的加性 nuisance"。两者合起来，ladder 从观察规律升级为有机制、有修复手段的理论。

## 6. 引文导入清单（并入 RELATED_WORK / M6 表）

必引：Li et al. 2025（10.1038/s43246-024-00731-w，pseudo-OOD）；Yahagi et al. 2025（10.1088/2632-2153/adcdc0，转换律作为迁移对象、<10 标定点）；BOOM（arXiv:2505.01912，预训练损害 OOD——放在 SI S10.2 Chemprop 结果旁）。已在引用清单中的：Segal et al.（npj 版）。查证后再引：SevenNet-Omni、Zhang et al. 2601.08486。

## 7. 底线

Edison 报告的**诊断层与本仓库完全收敛**（换迁移对象、停 generic injection、停 generic pretraining、警惕 pseudo-OOD），这是有力的独立验证，值得写进论文引言的论证链。它的**处方层不应跟随**：两个旗舰实验把项目拖向计算数据与另一套基础设施，且控制标准低于仓库自身门槛。真正该拿走的是一件事：**把 bilinear transduction 从"已 audit 未运行的备选"提升为 ladder 机制的判决性检验（E6：anchored Δ-transfer on CALiSol）**——零新数据、直接可比、三种结果都有明确含义。执行优先级建议排在 E1/E2 之后、等待 71905 与 battery 结果的同时即可完成。
