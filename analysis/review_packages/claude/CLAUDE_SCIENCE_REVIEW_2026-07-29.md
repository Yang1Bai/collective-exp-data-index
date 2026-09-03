# Clean-sheet scientific review and programme redesign

**日期：** 2026-07-29
**依据：** `CLAUDE_SCIENCE_REVIEW_PROMPT_2026-07-29.md`；仓库实际文件与结果 JSON 的独立重算；全网数据库与文献核实（所有链接均已逐一验证，无杜撰引用）
**Evidence-state guard 执行情况：**
- **Verified completed**：仅使用带 `VERIFIED`/`COMPLETE` 记录的结果。
- **Pending**：Balam job **71905**（strength→fatigue）已确认 `PD (Resources)`，`strength_fatigue_ood_status.log` 显示无结果文件；**不推断其结果**。Battery-conductivity 的 `formal_summary/complete/checksums` 三个文件在 `analysis/results/` 中**不存在**；**按 unknown 处理**。
- **Blocked**：XRD→synthesis 按 `xrd_to_synthesis_readiness.json` 的 `status: hold-recipient-attempt-table-not-verified` 维持 HOLD。

---

## 1. Executive scientific verdict（≤300 字）

已验证的证据不支持"相邻领域性质可跨数据库迁移"，但清晰支持一个更强的规律：**唯一可靠的正迁移都发生在供体标签与受体标签共享同一试样/批次/campaign 的场合**（MPEA UTS→YS Q4 +9.21%、KIT −20→−30 °C +15.02%），而一旦跨越文献/数据库边界，效应塌缩至 ±1–2%（40 边 programme 均值 +0.92%、CALiSol +1.61%、OPV +0.41% 且输给 shuffled、深度光学供体 −28%）。可迁移的不是性质，而是**"同一试样内部廉价测量→昂贵结果的映射"及其参数先验**。建议：论文以 provenance ladder + within-specimen bridge 为主轴，major revision；新旗舰实验采用跨实验室电池衰减参数迁移（§10），它把已被证实的机制第一次变成可部署的跨数据库方法。

---

## 2. Shared fact table

| # | 主张 | 证据指针 | 状态 |
|---|---|---|---|
| 1 | Pooled 规律不可直接搬运：Borg UTS–YS 系数在 BIRDSHOT 上 R²=−3.006 [−4.154,−2.185] | `PHASE1_FINDINGS.md`；`results/strength_law_summary.json` | **supported** |
| 2 | 同-campaign 邻近条件迁移成立：KIT −20→−30 °C +15.02% [8.61,21.10]，14/14 gate 通过，距离衰减 ρ=−1.0，shuffled 有害 | `results/kit_temperature_summary.json` | **supported**（限 within-campaign） |
| 3 | 同-数据库 state-matched 跨性质迁移成立：UTS→YS Q4 +9.21% [4.43,14.37]，aug R²=0.103，real−shuffled +9.47 pp | `results/state_matched_mpea_balam_v2_bootstrap_summary.json`（本人已从 `..._v2_predictions.csv` 独立复算一致） | **supported**（post-selection；Q4−Q1 与 R² 区间均跨零；Q4 每 draw 仅 14 系统） |
| 4 | 该 +9.21% 是"邻近端点的物理信息"而非"相关标签样本扩增" | 无同属性等信息量对照（design v2 `methods` 列表中无 YS→YS 供体） | **unsupported**（可用现有数据判决） |
| 5 | Generic donor-feature injection 跨 8 目标 / 40 边修复 OOD | `results/multi_target_ood_summary.json`: 均值 +0.92% [−0.35,2.92]，0/7 programme 通过 | **unsupported**（干净的 null） |
| 6 | 跨文献同性质迁移：CALiSol −30→−40 °C | +1.61% [−2.14,4.21]，R²=−0.014，距离序 ρ=0 | **unsupported** |
| 7 | 跨数据库预测迁移（任一 outcome-unseen 边） | Starrydata +0.88% Holm p=0.071 R²=−0.485；TRI −0.079%，4/4 plate R²<0；OPV real−shuffled = −0.11% [−0.31,+0.08]；photocatalysis 深度供体 −28.12% | **unsupported**（0/5） |
| 8 | 跨数据库**排序**信号（Caltech static） | 本人重算 shuffled-ranking 经验分布：external OBELiX AUC20=33 → 单侧 p=0.089；ESTM 45 → 0.030；hard-OOD 38 → 0.040、51 → 0.0099；Holm 后仅 ESTM hard-OOD 存活；分母 4/2 个 provenance component | **weak** |
| 9 | "更强 source 模型可拯救跨域迁移" | `results/optical_supervised_borrowing_summary.json`：8/8 source task 过 skill gate，仍 −28.12%，比 shuffled 差 25.23 pp | **unsupported**（已被干净否证——这是全文最有力的单个证据之一） |
| 10 | Strength→fatigue 物理归一化边 | job 71905 `PD`；`strength_fatigue_preoutcome_VERIFIED.json` 通过（62 curves / 17 components / 36 DOIs，`numeric_fatigue_outcome_cells_read=0`） | **pending** |
| 11 | Conductivity→battery capacity 边 | formal 输出缺失；`battery_conductivity_preoutcome_audit.json` `eligible-preoutcome`，但全部五个 property 的 `temperature_coverage_fraction=0.0` | **pending** |
| 12 | XRD→synthesis 边 | `xrd_to_synthesis_readiness.json` HOLD：A-Lab 355 attempts 的失败/部分结果表未验证 | **blocked**（HOLD 决定正确） |

---

## 3. Reviewer 1 — 材料学 / 物理解释视角

**3.1 中心现象到底是什么。** 把全部已验证的边按供体—受体共享的 provenance 层级排列，出现一条近单调的剂量—反应曲线：

| 层级 | 共享结构 | 代表边 | 效应 |
|---|---|---|---|
| L0 同一测量事件 | 同一条应力—应变曲线 | Borg UTS→YS（495/539 配对行） | +9.21%（+ measured-UTS ceiling +47.7%） |
| L1 同一批试样/campaign | 同 108 个配方的相邻温度 | KIT −20→−30 °C | +15.02% |
| L2 同性质跨文献 | 同物理量、不同 article | CALiSol −30→−40 °C；Matbench | +1.61% / −1.23% |
| L3 跨数据库跨性质 | 仅"物理相邻性" | 40-edge、Starrydata、TRI、OPV、photocat | +0.92% ~ −28% |

物理解读：实验标签不是材料的属性，而是**材料 × 加工历史 × 试样几何 × 仪器 × 操作者**的属性。同一试样内部，这些 nuisance 变量对供体和受体标签是**共同的**，因此相减/相除后消去——UTS 与 YS 之比在 Borg 内部稳定（中位 1.36），跨到 BIRDSHOT 变成 2.72；−20 °C 与 −30 °C 电导率之比由激活能决定，在同一配方内近常数。跨文献后 nuisance 不再消去，边就死了。**这不是"迁移学习效果不佳"，这是一个关于实验知识本体论的发现。**

**3.2 机理桥 vs 统计捷径的判别。** 现有证据无法区分 UTS→YS 的收益是（a）端点间物理关系，还是（b）338 条几乎同义标签的样本扩增（Borg 内 UTS≈1.36×YS）。shuffled 对照只否证"任意协变量"。判决实验（零新数据）：构造样本量、系统数、cross-fitting 完全匹配的 **YS→YS 同属性供体**；若 UTS 供体不显著优于它，正确命名是 auxiliary-task label efficiency。§7-Action 1。

**3.3 对 pending strength→fatigue（71905）的物理评估——设计冻结，仅作赛前预测。**
- **物理上是合理的**：σa/UTS 是经典的 Basquin 无量纲变量，钢的 endurance ratio ≈0.35–0.5；用预测 UTS 归一化循环应力是"传递应力尺度"而非"贴一个特征"，这正是本报告主张的参数级迁移方向。协议把 stress-normalization 写成显式 feature（`log10 σa − predicted log10 UTS`）是正确的。
- **但要预先说清三点**：(i) `strength_fatigue_preoutcome_audit.json` 显示 recipient 组成到 Borg 的最近 L1 距离**中位数只有 0.0113**、75 分位 0.121、6/17 组成精确重叠——所以该实验检验的是 **provenance-OOD 而非 chemical-OOD**，通过时不得写成"化学外推成功"；(ii) hardness 控制不是真正的 wrong-property——HV≈3×UTS，它携带同一应力尺度信息。若 real UTS 与 hardness 打平，正确结论是"应力尺度可迁移但非 UTS 特异"，这应现在就写进解释预案，而不是看到结果后再决定；(iii) 17 个 components 支撑 5% gate + CI>0 的功效偏低，null 时不能解读为"物理桥不存在"，只能解读为"该样本下不可检出 ≥5%"。
- **通过/部分通过/失败的解释已预写**：通过 → 第一条 outcome-unseen 的跨数据库、物理归一化边（L2.5 层级）；部分通过（胜 target-only 败 hardness）→ 应力尺度信息可迁移、非端点特异；失败 → provenance ladder 在物理归一化下依然成立，ladder 故事反而更完整。**三种结果都有正面用途，这是这条边设计得好的标志。**

**3.4 XRD→synthesis HOLD 判定正确**，且 readiness 文档已把关键点写对：post-outcome XRD 不能做候选时特征；A-Lab 公开物只保证成功样品的 refined pattern，失败/部分反应未表格化就开跑等于 outcome-selection bias。维持 NO-GO 直到 355-attempt 表通过七项字段检查。

---

## 4. Reviewer 2 — ML / 统计 / OOD 有效性视角

**4.1 已确认的统计问题（多数沿用我 07-27 审查，此处只列会改变结论的）：**
- **Caltech static ranking 的 null 用错**：确定性排序（100 seed SD=0）必须对 shuffled-ranking **分布**检验。重算后 external OBELiX p=0.089（不显著）、Holm 后仅 ESTM hard-OOD (p=0.0099) 存活；recall20 陈述（hard-OOD shuffled q95=1.000）零信息。这是当前稿件唯一的跨数据库正信号，必须降级表述。
- **MPEA Q4 有效聚类数是 14/draw（并集 56），不是 59**；bootstrap 把 60 个 model-by-draw run 当独立重采样维度，与 §2.8 自述"seeds 不作为独立数据集"矛盾。改 leave-one-system-out + 单独报告 draw 方差。
- **estimand 混用**：pooled-SSE 口径 9.21% vs mean-of-runs 口径 7.87%（`v2_summary.json` `summaries` 中 `state_plus_crossfitted_predicted_uts/q4` 的 `mean_relative_rmse_gain=0.07867`）。两个都报。
- 40-edge 表中 `te_zt ← Seebeck` 的 aug Q4 R²=−621 属 non-evaluable，应剔除后做敏感性。
- n=2 的随机效应元分析（I²=76.7%）不可解释，删。

**4.2 OOD 定义的科学性。** 现有 Q4 是"相对每次 draw 的已标注系统的最远四分位"——**相对**距离，非固定科学新颖区。CALiSol/Caltech/TRI 的 article/plate 分割才是真正的科学复制单元。建议全文统一：**OOD 的第一轴是 provenance（article/campaign/lab），第二轴才是组成距离**——这与 ladder 主张自洽，也与 MatFold（Witman & Schindler, *Digital Discovery* 2025, 10.1039/D4DD00250D）的分级 split 谱系接轨。

**4.3 方法体系的解构（保留/冗余/事后）。**
- **必要且已被证据支撑**：cross-fitting；DOI/campaign 级分割；matched shuffled + wrong-domain 双 falsifier；绝对效用（R²>0）gate；abstention 三态输出。
- **冗余**：97-edge 面板中的多重 wrong-property 变体（一个 shuffled + 一个 wrong-domain 已足够判别）；CCA meta-gate 的 9 特征学习层（`cca_leave_one_program_summary.json`：不敌 adjacency-only，且 `admitted_point_harm_rate=0.588` 未被引用——若保留必须披露）。
- **事后且应明标**：family-first portfolio、hard-OOD OBELiX、knowledge-deficit surface、CS13 battery diagnostic。
- **建议的最小 ablation**（一次 run 完成，不需要矩阵爆炸）：在 MPEA 与 KIT 两个正例上做 4-arm 分解——{full contract} / {−cross-fitting} / {−state features} / {−provenance split}——每 arm 与 full 的差就是该组件的边际贡献。这直接回答"哪个 gate 在做功"。

**4.4 三个与 scalar injection 实质不同的迁移机制**（详细设计见 §10；此处给判别性摘要）：

| 机制 | 迁移对象 | 为何比端点更不变 | abstain 方式 | 最简否证实验 | 可行性 |
|---|---|---|---|---|---|
| A. 参数级迁移 + hierarchical partial pooling | 物理模型系数的**人群先验**及"早期自测→系数"映射 | 系数（衰减指数、激活能、Basquin b）消去了试样级 nuisance；每个受体样本保留**自己的**早期数据作锚 | 先验后验重叠度低 → 收缩到 recipient-only | shuffled 供体先验 vs 真先验无差 → 否证 | **高**（公开电池数据全套 CC-BY） |
| B. Provenance 噪声地板测量 | 不迁移任何东西——**测量跨实验室方差分量**，给出任何迁移边的理论天花板 | 方差分量是实验体系的属性，不依赖模型 | n/a（它就是 abstention 的定量依据） | 若 σ²_lab≈0 而跨库迁移仍失败 → ladder 理论被否证 | **高**（Perovskite Database 42,400 devices 每条带 DOI） |
| C. 失败模式/process-window 迁移 | 反应发生/不发生的**分类边界**而非连续性质 | 相图与反应窗口由热力学决定，比性质数值更稳健 | 候选落在供体前驱体/工艺 support 外 → target-only | Precursor Genome 内 element-family holdout 上 shuffled=real → 否证 | **中**（recipient 表 blocked，见 §3.4） |

---

## 5. Reviewer 3 — Novelty 与 *Digital Discovery* 意义视角

**已核实的先行工作**（全部 DOI 已验证；缺引将招致直接的 novelty 反对）：
- 有向多边迁移矩阵 + null 报告：Devi, Butler & Sai Gautam, *npj Comput. Mater.* **10** (2024), 10.1038/s41524-024-01486-1（7×6 pretrain→finetune 网格，含 negative transfer）；Gupta et al. 2021 的 234 边。
- 实验合金 negative-transfer 审计：Kang, arXiv:2512.22740（54,028 样本、显著性检验、迁移无效 null）。
- 泄漏分级 split：**MatFold**（*Digital Discovery* **4**, 625, 2025, 10.1039/D4DD00250D）；Meredig LOCO-CV + 1NN null（10.1039/C8ME00012C）；Durdy random-projection null（10.1039/D2DD00039C）。
- UTS/YS 作供体：Wei et al., *Acta Mater.* **235**, 118103 (2022)。
- 参数级/物理结构化迁移已有先例：Bradford et al., ACS Cent. Sci. 2023（Arrhenius/VTF 结构模型，10.1021/acscentsci.2c01123）；Zhou & Howey, IFAC 2023（电池寿命 hierarchical Bayes，10.1016/j.ifacol.2023.10.708）；Xie et al., *Nat. Commun.* **13**:7562 (2022) 数据驱动无量纲数（10.1038/s41467-022-35084-w）。
- 跨实验室方差：all-solid-state battery round-robin, *Nat. Energy* 2024, 10.1038/s41560-024-01634-3。
- 失败实验学习：Raccuglia, *Nature* 533:73 (2016)；Sci. Adv. 2025 negative-data LM（10.1126/sciadv.adt5578）。

**什么是真正新的：**
1. **Provenance ladder 作为跨 5 个学科、9 个 programme 的受控剂量—反应结果**——现有文献里没有任何一篇把"同试样/同 campaign/跨文献/跨数据库"作为实验变量系统扫描。这是本仓库独有的资产，且 30+ 个 null 恰恰是它的证据而非累赘。
2. **Edge-level 三态决策合同（admit / rank-only / abstain）在冻结 falsifier 下的多次 outcome-unseen 执行**——sample-level abstention 已有（Jacobs、conformal 谱系），edge-level 没有。
3. **"更强 source 模型不能拯救跨域迁移"的干净否证**（−28.12%，8/8 source skill 达标）——对当前 foundation-model 叙事是稀缺的反证，*Digital Discovery* 读者会记住这一条。

**什么不新，必须让位**：多边矩阵、UTS→YS、泄漏 split、matched null baseline、参数级迁移本身。§10 的旗舰方案的新颖性因此必须定位在"**跨实验室 OOD + 冻结 falsifier + abstention** 的参数迁移"，并显式引用并区别 Zhou & Howey（他们是单数据集内的 pooling，无跨库 OOD、无对照家族）。

---

## 6. Cross-review synthesis

**共识（三个视角一致）：**
1. 证据支持的中心现象是 provenance ladder，不是"相邻领域可选择性迁移"。
2. 仓库的方法学资产（冻结、falsifier、abstention、验证链）是真实的、超过领域平均水平的贡献，应保留为论文骨架。
3. 当前唯一跨数据库正信号（Caltech static）经正确 null 检验后只剩 ESTM hard-OOD 一条，不足以承重；论文需要一条新的、诚实的跨库正结果，或者把跨库部分明确写成"测得的天花板"。
4. 两个 pending 实验设计质量高，无论正负都有位置；不得因结果修改冻结项。

**分歧：**
- R1 倾向把 strength→fatigue 通过后作为主轴正例；R2 提醒其组成重叠（中位 L1=0.011）使它只能算 provenance-OOD，且 17 components 功效有限；R3 认为即便通过，其新颖性弱于 §10 的电池参数迁移方案（Wei 2022 已有 UTS 供体先例）。综合裁决：71905 无论结果如何都进论文，但**不作为唯一旗舰**；§10 方案并行启动。
- R2 主张删除全部 Caltech portfolio 叙事；R3 主张保留 ESTM hard-OOD 单条 + 正确 p 值作为"rank-only 通道存在"的最小证据。综合：按 R3，但移出 Abstract。

---

## 7. 三个最高杠杆 next actions（按优先级）

**Action 1 — 同属性等信息量对照 + provenance 三级剂量反应（合并为一次 reanalysis 包）**
- **精确分析**：(a) MPEA：YS→YS 供体（338 行 / 60 系统精确匹配 UTS 供体），四方配对（target-only / UTS / same-property / 各自 shuffled），沿用 `state_matched_mpea_balam_design_v2.json` 的全部 split、seed、budget；估计量 = gain(UTS)−gain(YS-donor)，elemental-system cluster bootstrap（不含 run 维度）。(b) CALiSol：固定 −30→−40 °C 供体，split 三级（within-article formulation-out / formulation-cluster-out / article-out），加 donor-skill-matched 降采样（KIT 供体降到 OOF R²≈0.119）解耦供体技能与 provenance。
- **决策价值**：一次判决两个 fatal——hero result 的机制归属 + ladder 的因果性。这是全仓库信息增益最高的单笔计算。
- **数据/算力**：零新数据；≤6 CPU·h。
- **停止规则**：预注册两个估计量与阈值（UTS−YS-donor ≥3 pp；最深−最浅层级差 ≥5 pp 且 CI>0），跑一次，不迭代。
- **结果分支**：正 → Abstract 保留 9.21% 并升级 ladder 为受控规律；null → hero result 改名 auxiliary-task label efficiency，ladder 降为观察性描述；harmful（YS-donor 更强）→ 明写供体机制是标签扩增，L0 层重新定义。

**Action 2 — 等待并如实纳入 71905 与 battery（零干预）**
- **精确分析**：不做任何事，直到结果落地；落地后只运行已冻结的 verifier。同时**现在**把两条 a priori 预言写入带时间戳的附录：(i) battery corpus 温度覆盖率=0 → 按 state-matching 原则预测**不通过**完整 gate；(ii) strength→fatigue 若通过而 hardness 控制同样通过 → 解释为"应力尺度可迁移、非 UTS 特异"。
- **决策价值**：把两个 pending 变成对中心假设的 out-of-sample 检验；预言写在前面，正负都是理论的数据点。
- **停止规则**：n/a。**结果分支**：battery 通过 → "state coverage 非必要"需进 Discussion（重要修正）；不通过 → ladder 的一次前瞻确认。71905 通过 → 论文获得第一条 outcome-unseen 跨库正边（provenance-OOD 限定语必加）；null → L2 层再添一条受控 null。
- **新数据/算力**：零（已在队列）。

**Action 3 — 启动 §10 旗舰：跨实验室电池衰减参数迁移（新实验，公开数据）**
- **精确分析**：见 §10 冻结设计。**决策价值**：论文从"审计 + 一个受限正例"升级为"理论（ladder）+ 机制（within-specimen bridge）+ 可部署方法（参数先验迁移）+ 前瞻验证"。
- **新数据/算力**：全公开（CC-BY）；下载 ~10 GB；模型为层级贝叶斯/经验贝叶斯，单机数小时。
- **停止规则**：outcome-blind audit gate（§10.8）不过即 abstain 归档；formal run 一次，不得因结果改 gate。
- **结果分支**：正 → 旗舰正例 + 标题级主张；null → "参数空间也受 provenance 地板约束"，与 ladder 自洽，论文仍成立（audit-methods 框架 + 天花板测量）；harmful → 收缩校准失败案例，如实报告并触发 §10.9 的解释预案。

---

## 8. Keep / Cut / Reframe / Run 决策表

| 证据 programme | 决定 | 理由与去处 |
|---|---|---|
| Borg→BIRDSHOT 系数搬运失败（R²=−3.006） | **Keep**（正文，压缩为一段） | Ladder 的 L2 反面锚点 |
| ISODB / Meyer–Neldel 补偿律 | **Reframe → SI** | 与主轴（迁移）关系弱；保留为 "association≠transport" 引言注脚 |
| KIT −20→−30 °C | **Keep**（正文，L1 正例） | 措辞改为 within-campaign condition transfer；37.35% 标签节省必须与 post-outcome CI [21.84,49.91] 并排 |
| CALiSol | **Keep**（正文，L2 关键 null） | 加 Action 1(b) 的三级 split 后升级为受控证据 |
| MPEA state-matched UTS→YS | **Keep**（正文，L0 正例） | 以 Action 1(a) 的判决结果决定命名；修 14-系统聚类数与双 estimand 报告 |
| 40-edge generic benchmark | **Keep**（正文，L3 null 面板） | 剔 non-evaluable cell 后重报均值；是 ladder 的 L3 数据点 |
| Chemprop 光学供体 −28% | **Reframe → 从 SI 提入正文** | "source skill 不是瓶颈"的判决性否证，主轴证据 |
| OPV optical external | **Keep**（正文一句 + SI） | real−shuffled CI 已含零，作为 L3 的 outcome-blind null |
| Starrydata / TRI outcome-unseen | **Keep**（正文，abstention 演示） | 删 n=2 元分析统计量，仅列各自结论 |
| Caltech adaptive residual 全 null | **Keep**（正文一句） | 与 OBELiX UCB null 合并为"target-refit 通道死亡"一段 |
| Caltech static ranking | **Reframe** | 重算 shuffled-null p 值；只保留 ESTM hard-OOD；移出 Abstract |
| Caltech family-first portfolio | **Cut（正文）→ SI 短段** | 分母 4/2、outcome-informed、不敌 best single source（estm_family_first 49/4/4） |
| OBELiX UCB + random 对照 | **Keep**（正文） | 加入 wrong-domain alloy_control saved 0.57 > 提名供体 0.25 这句（诚实且有力） |
| CCA leave-one-programme meta-gate | **Cut → SI** | 不敌 adjacency-only；若保留必须披露 `admitted_point_harm_rate=0.588` |
| CS13 multistage battery diagnostic (+6.12%) | **Cut（作为证据）→ SI 方法开发注记** | outcome-guided；冻结 primary non-evaluable |
| Knowledge-deficit surface / hard-OOD OBELiX | **Cut → SI** | post-outcome，不改变结论 |
| 118/233 catalog 叙事 | **Reframe** | 按 `CATALOG_TO_PAPER_OPPORTUNITY_AUDIT.md`：118 为冻结快照，115 TDM 记录明标为 discovery queue |
| Strength→fatigue（71905） | **Run（已在队列，勿动）** | 落地后按 §3.3 预案解释 |
| Battery conductivity | **Run(pending)（勿动）** | 按 Action 2 预言化 |
| XRD→synthesis | **HOLD** | 维持 NO-GO 规则；解锁条件 = 355-attempt 表七项检查 |
| §10 新旗舰 | **Run** | 唯一新增计算投入 |

---

## 9. 修订后的中心主张与图逻辑

**一句话 thesis：**

> 实验知识以"同一试样内部廉价测量→昂贵结果的映射"形式存在；这一映射的**参数**可以跨数据库迁移并配备可证伪的 falsifier 与 abstention，而端点**数值**本身在跨越文献/实验室边界时按 provenance 层级定量塌缩。

**图逻辑（6 图）：**
- **Fig 1** Provenance ladder 总图：x 轴 = 共享 provenance 层级（L0→L3），y 轴 = 相对增益（点 + CI），全部 9 个 programme 的边落位；右侧小面板 = 每层的 falsifier 结构。这是论文的 money figure，现有数据即可画。
- **Fig 2** L0/L1 正例机制图：MPEA（含 Action 1 的同属性对照判决结果）+ KIT 距离衰减；nuisance-cancellation 示意。
- **Fig 3** L2/L3 塌缩面板：40-edge、CALiSol 三级 split（Action 1b）、Matbench、OPV、Chemprop −28%——统一坐标，让塌缩可视化。
- **Fig 4** 端点分离：prediction 死 / rank-only 弱存活（正确 null 带）/ abstention 三态决策流程图。
- **Fig 5** 两条 outcome-blind 前瞻检验：71905 与 battery 的预言 vs 结果（落地后填入；投稿时若仍 pending，以预言注册图代替）。
- **Fig 6** 旗舰新实验（§10）结果：跨实验室衰减参数迁移的 budget 曲线（recipient-only vs prior-transfer vs shuffled/wrong-chemistry）。

---

## 10. Clean-sheet research programme

### 10.1 三个（+1）新迁移假设

**H1 — 跨实验室衰减参数迁移（hierarchical partial pooling of degradation kinetics）。** 可迁移的对象不是容量数值，而是 (i) 衰减动力学系数（Q_loss=a·nᵝ 的 log a、β、knee 位置）的人群先验，(ii) "本 cell 前 100 循环特征 → 本 cell 系数"的映射。每个受体 cell 保留自己的早期循环作锚——**这正是 KIT/MPEA 成功机制（within-specimen bridge）的可部署化**。数据：MATR/Severson 124 LFP cells（CC-BY 4.0, data.matr.io, 10.1038/s41560-019-0356-8）+ Attia 2020 → BatteryArchive SNL LFP 18650（batteryarchive.org；备选 HUST 77 LFP cells，经 BatteryML MIT 统一预处理，github.com/microsoft/BatteryML）。**新颖性区隔**：Zhou & Howey (2023) 的 hierarchical pooling 在单数据集内、无跨实验室 OOD、无 falsifier 家族、无 abstention——本方案三者齐备。

**H2 — Provenance 噪声地板测量（不迁移任何东西的迁移研究）。** 用 Perovskite Database Project（>42,400 devices，每条带 source DOI；Jacobsson et al., *Nat. Energy* 2022, 10.1038/s41560-021-00941-3；NOMAD 托管）对 PCE 做层级方差分解：给定 device-stack/工艺描述符后，估计 σ²_between-lab 与 σ²_within-lab。**σ²_lab/(σ²_lab+σ²_res) 就是任何跨文献迁移边的理论天花板**——它把本仓库全部 1–2% 的跨库 null 从"失败"变成"被定量预测的必然"。交叉校准：all-solid-state round-robin（*Nat. Energy* 2024, 10.1038/s41560-024-01634-3）提供独立的 between-lab 方差外部锚。执行成本最低（单数据库、无迁移模型），理论承载量最高。
- OOD/单位：DOI 为聚类单位；控制 = 同 stack 同工艺跨 DOI 的重复组成；否证条件：若 σ²_lab≈0 而跨库迁移仍普遍失败 → ladder 理论错误，失败须另找原因。
- 成功标准：σ²_lab 分量显著非零且其量级足以解释 L2/L3 观察到的塌缩幅度（预测区间覆盖实测的 +0.4~+1.6% 边效应）。

**H3 — 反应发生边界（failure-mode/process-window）迁移。** 迁移对象是"反应发生/不发生"的分类边界（4 类 outcome：unreacted/transformed/partial/complete），不是性质数值。Donor = Precursor Genome（1,035 pairwise 反应、真负结果、arXiv:2607.09903、Zenodo 10.5281/zenodo.21285546）；recipient = A-Lab 355 attempts（**blocked**，解锁条件见 `xrd_to_synthesis_readiness.json`）。Fallback（可立即执行）：Precursor Genome 内部 element-family holdout 作为 process-window 迁移的方法开发，明标 within-programme。物理依据：反应窗口由热力学与扩散控制，比性质数值对试样 nuisance 更稳健；且负结果数据天然免疫 publication bias——这是全仓库缺失的数据类型。

**H4（辅助）— Donor disagreement 作为 OOD 探索信号。** Borg vs BIRDSHOT 双 UTS 卡片的分歧已冻结在 71905 的 applicability gate 中；若 71905 通过，其 disagreement-gated coverage 数据可直接检验"分歧高 → 迁移失败概率高"，零额外成本。不单独立项。

### 10.2 选择判据与裁决

| 判据 | H1 | H2 | H3 |
|---|---|---|---|
| 共享物理 latent 明确 | SEI 动力学系数 ✓✓ | n/a（测天花板） | 反应热力学 ✓ |
| 候选时输入可得 | 前 100 循环，✓✓ | ✓✓ | 前驱体/工艺 ✓ |
| provenance 独立 | 两个实验室 ✓✓ | 单库多 DOI ✓ | 同平台两 campaign（弱）|
| 数据可得性 | 全 CC-BY ✓✓ | ✓✓ | recipient blocked ✗ |
| 负/null 结果可得 | 全轨迹 ✓✓ | ✓ | ✓✓（独有优势） |
| OOD 单位可辩护 | laboratory ✓✓ | DOI ✓ | campaign ✓ |
| 预期效应量级 | 5–10 MAPE pts ✓✓ | 解释性 ✓✓ | 未知 |
| 对论文主轴的承载 | 机制的可部署化 ✓✓ | 失败的定量解释 ✓✓ | 中间层级 ✓ |

**裁决：H1 为旗舰（成功概率最高 × 科学意义最大 × 立即可跑）；H2 为必做伴随分析（成本最低、把全部 null 变成理论证据）；H3 维持 HOLD，fallback 可选。** H1+H2 合起来给论文一个完整闭环：H2 解释为什么端点数值不可迁移，H1 证明参数与映射可以。

### 10.3–10.10 H1 冻结实验设计（可直接实施）

**10.3 角色与数据。**
- **Donor**：MATR-1（Severson 2019，124 × A123 APR18650M1A LFP/graphite，快充协议族，per-cycle 容量/Q(V)/内阻/温度；CC-BY 4.0）+ MATR-2（Attia 2020）作为第二 donor batch。下载源 data.matr.io；以 BatteryML（MIT）的 loader 统一化并锁定其 commit hash（其内置 MATR batch1/2 同 cell 续测勘误必须启用）。
- **Recipient（primary）**：BatteryArchive 中 SNL LFP 18650 cells（不同实验室、不同协议/温度/DOD）。**Recipient（declared backup，audit 不过时启用）**：HUST 77-cell LFP 数据集（BatteryML 内建）。
- **Wrong-chemistry 对照供体**：SNL NCA/NMC cells——预期 abstain/null，必须保留在分母。

**10.4 共享物理机制。** LFP/graphite 早期衰减由 SEI 生长主导 → 容量损失近似 Q_loss=a·nᵝ（β≈0.5 扩散限制时），后期 knee 由析锂/LAM 触发；温度按 Arrhenius 缩放。系数 (log a, β, n_knee) 是 cell 级物理量，消去实验室 nuisance 的程度远高于任意循环数处的容量值。

**10.5 迁移什么、为何更稳定。** 迁移 (i) (log a, β, log n_knee) 的人群先验（含协议协变量的回归先验），(ii) 映射 g: {前 100 循环 ΔQ(V) 分位特征、容量斜率、CE、IR 漂移、协议描述符} → 系数后验。不迁移任何容量数值。稳定性论据：同一 cell 的早期轨迹与晚期寿命之间的映射由同一电化学体系产生（within-specimen bridge）；跨实验室移动的只是映射的先验形状，其误差被每个受体 cell 自己的 100 循环数据持续修正。

**10.6 候选时输入。** 严格 ≤ 第 100 循环：per-cycle 放电容量序列、CE、IR（MATR 有；SNL 用可得子集，特征取交集并在 audit 中冻结）、协议（充电率、DOD、温度）。**禁止**：第 100 循环之后的任何测量；RPT 中在参考条件下的诊断（若其循环序号 >100）；名义容量归一化参数必须仅在 donor 上拟合。

**10.7 OOD 定义与统计单位。** Primary OOD 轴 = **laboratory/dataset**（MATR→SNL），这是真实的科学新颖性（不同厂牌产线、不同循环仪、不同协议设计哲学）。统计单位 = cell；推断 = cell 级 jackknife + 协议块 cluster bootstrap；secondary 分层 = 温度/DOD 协议块。Chemistry-OOD（LFP→NCA/NMC）为预期-abstain 边界，单独报告。

**10.8 Outcome-blind audit gate（先于任何寿命标签访问）。** 只读元数据与前 100 循环数据，冻结：(1) SNL LFP cell 数 ≥20（不足 → 启用 HUST backup，本决定在开标签前做出）；(2) 每 cell 前 100 循环完整率 ≥90%；(3) donor–recipient 特征交集 ≥ {容量序列、CE、协议}；(4) 寿命标签定义 = cycles to 80% SOH（右删失 cell 保留，删失感知评估）；(5) 全部阈值、seed、对照、成功 gate 的 SHA256 冻结文件。

**10.9 对照家族（Holm 校正的冻结 family）。**
1. **recipient-only**：同层级模型、平先验，仅用受体自己的 ≤10 个已开标签 cell + 各 cell 前 100 循环；
2. **shuffled-donor**：打乱 donor 内 cell 特征↔系数配对后重建先验与映射（架构完全匹配）；
3. **wrong-chemistry prior**：NCA/NMC 供体先验 → LFP 受体；
4. **prior-only（无映射）**：只给人群先验、不给 g——分解"先验"与"映射"各自贡献；
5. **equal-capacity Gaussian prior**：与真先验同维度同宽度的信息无关先验；
6. **oracle ceiling**：受体全数据拟合（只作上界，不入比较）。

**10.10 Primary estimand、成功 gate、算力与失败解释。**
- **Estimand**：held-out 受体 cell 上 log10(cycles-to-80%SOH) 的 RMSE（及 MAPE），受体已标注预算 ∈ {0, 5, 10} cells，200 次配对 draw。
- **成功 gate（全部满足才算正边）**：budget ≤10 时相对 recipient-only 的 RMSE 降低 ≥10%；cell-cluster bootstrap 95% CI 下界 >0；Holm p<0.05（对照家族 5 项）；胜 shuffled 与 wrong-chemistry 各 ≥5 pp；绝对 R²>0；预测区间经验覆盖率不劣于 recipient-only（校准不得恶化）；≥65% 配对 draw 为正。
- **Abstention 规则**：受体 cell 的早期特征落在 donor 特征分布的 support（马氏距离 90 分位）之外，或系数后验与先验的 KL 超过冻结阈值 → 该 cell 回退 recipient-only；abstain 率入报告。
- **算力与阶段**：Stage A 下载+audit（1 天，笔记本）；Stage B donor 内 leave-protocol-out 自检（数小时）；Stage C 冻结后 formal run（数小时，单机；无需 Balam）。**停止条件**：audit gate 任一不过 → 记录 abstain，不改 gate 重试；formal run 只跑一次。
- **失败解释预案**：null → "provenance 地板延伸到参数空间"，与 H2 的方差分解定量对照，论文主轴不受损（ladder + 天花板 + 审计方法）；harmful → 检查先验收缩校准（报告 posterior shrinkage 诊断），如实归档为 hierarchical transfer 的失败案例——这在电池文献中同样稀缺。
- **什么结果支撑强主张**：通过全部 gate 且 prior-only 对照显示映射 g 贡献 ≥ 先验贡献 → 标题级主张成立："同试样廉价—昂贵映射的参数可跨实验室迁移，端点数值不可"——即 Fig 1 ladder 的第一条被工程化跨越的边。

---

### 附：对"是否重访已失败的 optical/OPV/multi-target 实验"的明确回答

**不重访。** 三条理由：(1) `optical_supervised_borrowing_summary.json` 已证明失败与 source 容量无关（8/8 skill 达标仍 −28.12%），换更大模型是重复验证；(2) OPV 的 real−shuffled CI [−0.31,+0.08]% 表明真卡片不含超越随机卡片的信息，方法层面无可挽救——缺的是 device stack 状态变量，而公开 OPV 数据无第二个独立库可做诚实 OOD（本次全网核实：无canonical 开放实验 OPV 器件库；KRICT 库未公开）；(3) 这些 null 在新框架下不是待修复的失败，而是 ladder L3 层与 H2 天花板的**证据**——重访会破坏它们的证据价值。40-edge benchmark 同理：它的作用已经完成（证明 L3 的 generic 通道不存在），加边或换模型都不会改变 programme 级结论。
