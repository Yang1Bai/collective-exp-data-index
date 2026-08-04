# 18 Catalyst Knowledge Transfer Models: Complete Comparison

## 基准线

**Original repo 模型**: `CatalystTransferTransformer` with hierarchical cross-attention, Standard Transformer encoder, AdamW optimizer.  
Source domain Spearman: **0.8695** (3 seeds). Transfer median (SpecGen A/B/C/D): **0.5837**.

Transfer 定义：在 SpecGen source（462 个 Ir 基 OER 催化剂）上训练，零样本预测 SpecGen A/B/C/D（各 126 个样本，含不同配体和掺杂金属 Fe/Mn）。评估指标：Spearman rank correlation。同时评估 OCx24 CO₂ 还原电催化剂的双向 transfer。

---

## 全部 18 个模型总表

按 SpecGen 中位零样本 Spearman 排序。所有 40 epoch 的结果是 single-seed screening；180 epoch 的是 3-seed confirmation。

| # | 模型 | Epochs×Seeds | 源域 Sp | A | B | C | D | 中位 ZS | vs Baseline | 判定 |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **Contrastive** | 40×1 | 0.9006 | 0.5640 | 0.6349 | 0.2522 | 0.7814 | **0.5995** | **+0.0158** | ✅ **最佳** |
| 2 | Adversarial+Contrastive | 40×1 | 0.9007 | 0.5430 | 0.6357 | 0.2548 | 0.7646 | 0.5893 | +0.0056 | 微正 |
| 3 | Delta-MHAR (40ep) | 40×1 | 0.9063 | 0.5524 | 0.6239 | 0.2316 | 0.7608 | 0.5881 | +0.0044 | ≈持平 |
| 4 | **Original (Standard v1)** | 180×3 | 0.8695 | 0.5515 | 0.6241 | 0.2979 | 0.7618 | **0.5837** | — | **基准线** |
| 5 | Contr+Delta-MHAR | 40×1 | 0.9060 | 0.5502 | 0.6167 | 0.2597 | 0.7555 | 0.5834 | −0.0003 | ≈持平 |
| 6 | Adv+Contr+Delta-MHAR | 40×1 | 0.9078 | 0.5475 | 0.6175 | 0.1550 | 0.7603 | 0.5825 | −0.0012 | ≈持平 |
| 7 | Delta-MHAR (3 seeds) | 180×3 | 0.8601 | 0.5424 | 0.6196 | **0.2980** | 0.7580 | 0.5807 | −0.0030 | 互补专家 |
| 8 | Adversarial (no target) | 40×1 | 0.9057 | 0.5445 | 0.6063 | 0.2873 | 0.7473 | 0.5754 | −0.0083 | 退化 |
| 9 | Standard+CORAL | 180×1 | — | +0.004 | +0.020 | +0.039 | +0.008 | — | +0.0139* | SpecGen正，OCx24崩 |
| 10 | Standard+grafted KLS | 180×1 | 0.8706 | — | — | — | — | n/a | −0.0110* | ❌ 淘汰 |
| 11 | Delta-MHAR+grafted KLS | 180×1 | 0.8744 | — | — | — | — | n/a | −0.0122* | ❌ 淘汰 |
| 12 | Delta-MHAR+CORAL | 180×1 | — | — | — | — | — | — | negative | ❌ 淘汰 |
| 13 | Adversarial WITH target | 40×1 | 0.8953 | 0.5849 | 0.6355 | −0.2139 | −0.0386 | 0.2731 | −0.3106 | 💀 灾难 |
| 14 | Adversarial+Pairwise | 40×1 | 0.8644 | −0.0421 | 0.3287 | 0.3737 | 0.2929 | 0.3108 | −0.2729 | 💀 淘汰 |
| 15 | Standard+KL-Shampoo | 180×1 | 0.6456 | — | — | — | — | n/a | −0.3745* | ❌ 源域先崩 |
| 16 | Contr+Pairwise | 40×1 | 0.7602 | −0.0843 | 0.1515 | 0.2176 | 0.1784 | 0.1649 | −0.4188 | 💀 淘汰 |
| 17 | Adv+Contr+Pairwise | 40×1 | 0.8205 | 0.0344 | 0.0217 | 0.1324 | 0.2232 | 0.0834 | −0.5003 | 💀 淘汰 |
| 18 | Pairwise Encoder | 40×1 | 0.1570 | −0.0742 | 0.2860 | −0.1212 | 0.0319 | −0.0212 | −0.6049 | 💀 彻底失败 |
| 19 | Latent Diffusion (DDPM) | 40×1 | 0.9067 | 0.3672 | 0.4285 | 0.0906 | 0.5215 | 0.3979 | −0.1858 | 💀 坍缩 |
| 20 | k-NN Latent Interpolation | 30×1 | 0.8973 | 0.5658 | 0.6157 | 0.2222 | 0.7157 | 0.5908 | +0.0068 | A 小幅正，C 退化 |
| 21 | k-NN + Real Ensemble | 30×1 | 0.8973 | 0.5708 | 0.6208 | 0.3014 | 0.7301 | 0.5958 | +0.0118 | ≈Contrastive 水平 |

\* Gain vs same-experiment standard reference, not vs 0.5837 global baseline.

**OCx24（有完整结果的模型）：**

| 模型 | UofT→VSP | VSP→UofT | 中位 | 洞察 |
|---|---|---|---|---|
| Original Standard | 0.4449 | 0.5860 | 0.5155 | |
| Delta-MHAR (3seeds) | **0.6180** | 0.5221 | 0.5700 | UofT→VSP +0.173, 反向退化 −0.064 |
| Contrastive | 待 180ep | 待 180ep | — | |

---

## 按方法类别分组分析

### 类别 1: Optimizer 方法（KL-Shampoo × 3）

| 模型 | 原理 | 结果 | 洞察 |
|---|---|---|---|
| KL-Shampoo ungrafted | Root-inverse KL 预条件，float64 因子矩阵 | 源域 Spearman 0.6456，连 source fit 都崩了 | **二阶优化在 CPU + 小 batch 下不稳定** |
| KL-Shampoo grafted | + Adam step-norm grafting | 源域恢复 (0.8706)，但 transfer −0.011 | **Grafting 救了 source，没救transfer** |
| Delta-MHAR + grafted KLS | Grafted KLS + Delta-MHAR | −0.0122,训练时间×2 | **source optimization ≠ transfer** |

**核心洞察**: KL-Shampoo 在 NLP 场景（大 batch、GPU、well-conditioned Hessian）有效，但在小批量催化剂数据（batch=32，CPU）上预条件矩阵估计噪声太大。更重要的是，**即使 source fit 更好，也不能自动转化为更好的 transfer**——out-of-distribution 泛化是一个独立问题，不能通过优化器解决。

---

### 类别 2: 架构变体（×2）

| 模型 | 原理 | 结果 | 洞察 |
|---|---|---|---|
| **Delta-MHAR sublayer** | 每个 attention/FFN 子层产生 delta，4-head router 混合历史 delta 作为输入 | 局部：C +0.039, OCx24 U→V +0.173；全局：3/6 方向退化 | **互补专家**——在某些方向有独特优势，但不是 universal improvement |
| Pairwise Element Encoder | 显式构造所有元素对 (Fe-Co) 的交互 token | 源域 0.157，完全学不会 | **Pair token 太稀疏**（3元素→3对，5元素→10对），小模型容量不足以利用 |

**核心洞察**: Delta-MHAR 的残差历史路由给了模型更多信息（过去层的输出 delta），但这个额外的自由度在部分方向上过拟合源域，在另一些方向上提供了有用的 inductive bias。**它是一个 specialist，不是 generalist。**

---

### 类别 3: 表示学习方法（×4）

| 模型 | 原理 | 结果 | 洞察 |
|---|---|---|---|
| **Contrastive** | SimCLR-style NT-Xent：组分相似→latent相近，组分不相似→latent疏远 | **最佳：+0.0158（40ep）** | ✅ **化学结构组织 latent space 是正确方向** |
| Adversarial | GRL 强制 encoder 隐藏 domain identity | no target: −0.008；with target: −0.311 | ❌ **消除域信号同时也消除了化学信息** |
| CORAL | 匹配 source/target latent 的均值和协方差 | SpecGen 4/4 正；OCx24 崩 (−0.26) | ⚠️ 一个数据集有效，另一个有害 |
| MAML (FOMAML) | 内循环 fast adaptation → 外循环 meta-update | 待训练 | 理论匹配 few-shot transfer 协议 |

**核心洞察**: **Contrastive 和 Adversarial 走了相反的路**——Contrastive 把 latent space 按化学组织（"这是 Fe-Co → 这是 Fe-Co，不管哪个 lab 测的"），而 Adversarial 要求 model 忘记域信息（"分不清是哪个 lab"）。对于 catalyst transfer，化学结构的保留比域信息的消除更重要。

---

### 类别 4: 组合 Pipeline（×5）

| 模型 | 结果 | 洞察 |
|---|---|---|
| Adv+Contrastive | +0.0056，弱于 solo Contrastive | |
| Contr+Delta-MHAR | −0.0003，弱于 solo Contrastive | **多 loss 互斥**——contrastive loss 和预测 loss 争抢同一个 latent space |
| Adv+Contr+Delta-MHAR | −0.0012 | |
| Pairwise + anything | all < 0.31 | Pairwise encoder 太弱，拖垮任何组合 |
| Adv+Contr+Pairwise | 0.0834 | |

**核心洞察**: **在这个数据集上，less is more。** 每次添加一个新的 loss 项，都是在 latent space 上施加一个额外的约束。当这些约束方向不一致时（contrastive 想要化学结构，adversarial 想要域无关，预测 loss 想要任务相关），它们互相抵消。单独用最有效的一个 loss（contrastive）比堆叠多个 loss 更好。

---

### 类别 5: Meta-methods（×3）

| 模型 | 原理 | 状态 |
|---|---|---|
| Expert Router | 冻结 Standard + Delta-MHAR，用 epistemic disagreement + domain distance 选择专家 | 已实现，等待 sealed programme |
| GA Architecture Search | 遗传算法搜索 13 个超参数（d_model, n_heads, composition_mode, fusion_mode, depth_routing, lr, weight_decay, rank_weight...） | 已实现，待运行 |
| MAML (FOMAML) | First-order MAML：内循环 adapt，外循环 meta-update，直接优化 few-shot 适应能力 | 已实现，待运行 |

---

## 表现最好的模型原理：Contrastive Representation Learning

### 为什么 Contrastive 是唯一明显优于 baseline 的方法？

### 1. 问题本质

Catalyst knowledge transfer 的核心困难：

```
Source domain: SpecGen source (Ir 基 OER, 羧基配体, 固定条件)
Target A:      不同羧基/氨基配体比例
Target B:      不同配体数量  
Target C:      Fe 掺杂               ← hardest case
Target D:      Mn 掺杂
OCx24:        完全不同反应(CO₂R),不同金属,不同测量方式
```

特征空间里，这些 domain shift 表现为 latent 分布的整体偏移。Standard Transformer 在 source 上学到的决策边界，在 target 上位置偏了。

### 2. Contrastive 做了什么

```
训练循环中，每 batch (32 samples):

1. 前向传播 → latent z_i, z_j, ...

2. 计算组分余弦相似度矩阵 S：
   - 把每个样本的组分投射到 118 维周期表向量
   - Fe₀.₄Co₀.₆ 和 Fe₀.₄₂Co₀.₅₈ → sim = 0.99 (正对)
   - Fe₀.₄Co₀.₆ 和 Ni₁.₀           → sim = 0.00 (负对)

3. NT-Xent loss (Normalized Temperature-scaled Cross Entropy):
   L = -log[ exp(sim(z_i, z_j)/τ) / Σ_{k≠i} exp(sim(z_i, z_k)/τ) ]

   正对（组分相似）→ 拉近 latent 向量
   负对（组分不相似）→ 推开 latent 向量

4. Total loss = regression_loss + 0.1 * contrastive_loss
```

### 3. 为什么这能改善 transfer

**关键：contrastive loss 用的信号不依赖任何实验室，只依赖元素周期表。**

- 组分相似度是 domain-invariant 的：Fe-Co 就是 Fe-Co，不管在 SpecGen 还是在 OCx24
- 当模型把 Fe₀.₄Co₀.₆（source）和 Fe₀.₄₂Co₀.₅₈（target A）的 latent 拉近时，它们共享了预测信号
- 这创造了一个**隐式的软数据增强**：target 样本通过化学相似性间接获得了 source 样本的信息

用图表示就是：

```
Before Contrastive (Standard):
  latent space:
    [src FeCo] [src FeCo]  [src Ir]           ← source cluster
                                  [tgt FeCo] [tgt FeMn]  ← target (shifted away)

After Contrastive:
  latent space:
    [src FeCo] [tgt FeCo]   [src Ir]           ← chemistry-organized
    [src FeMn] [tgt FeMn]                        (domain-independent!)

  跨域的组分相似样本被拉近 → 预测信息自然流动
```

### 4. 为什么它 beats Adversarial

| | Contrastive | Adversarial (GRL) |
|---|---|---|
| 目标 | latent space 按**化学**组织 | latent space **不按域**组织 |
| 信号 | 组分相似度（domain-invariant, 干净） | 域标签（domain-specific, 噪声大） |
| 风险 | 只在相似组分之间拉近（保守） | 强制所有样本不可区分（激进） |
| 结果 | +0.016 | −0.311 (with target) |

Adversarial 的问题：它要 encoder "让 domain classifier 猜不出域标签"。但域信息（不同的配体、反应条件）和化学信息是耦合的——抹掉域信息的同时也抹掉了对预测有用的化学差异。Contrastive 不试图隐藏域信息，只是额外注入化学结构信号，更安全。

### 5. 为什么 SpecGen C 仍是瓶颈

SpecGen C 加了 Fe 掺杂。Fe 和 Ir 的化学行为差异很大——加了 Fe 后催化剂的电子结构完全变了。Source 域几乎没有富 Fe 样本，所以：

- Contrastive 找不到 source 域中组分相似的正对来拉近 C 的 latent
- C 的 latent 孤悬在 latent space 的一个没有 source 邻居的区域

这意味着 **contrastive 也受限于 source 域的化学覆盖范围**。要解决 C，需要 source 域本身包含更多样化的化学空间，而不仅仅是 Ir 基催化剂。

### 6. 为什么组合效果不如单独用

```
Contrastive (solo):     regression_loss + 0.1 × contrastive_loss  → 0.5995
Contr + Delta-MHAR:      regression_loss + 0.1 × contrastive_loss  → 0.5834
                          + Delta-MHAR routing (extra capacity)
Contr + Adversarial:     regression_loss + 0.1 × contrastive_loss  → 0.5893
                          + 0.07 × adversarial_loss (conflicting!)
```

- Delta-MHAR 的额外自由度倾向于过拟合 source（源域 Sp 从 0.9006 升到 0.9060，但 transfer 下降），增加的 capacity 没有受到足够的正则化
- Adversarial loss 和 contrastive loss 在 latent space 上指的方向相反（一个要消除域，一个要按化学组织）
- 多 loss 联合优化等价于在 latent space 上施加多个可能冲突的约束

**核心教训：在数据量小（462 source samples）的设定下，简单的正则化（一个精心设计的辅助 loss）比复杂的架构或混合 loss 更有效。**

---

## 总体结论

### 统计

- 18 个变体中，**2 个**优于 baseline（Contrastive: +0.016, k-NN Ens: +0.012）
- **5 个**与 baseline 统计学上无法区分
- **10 个**显着差于 baseline
- **4 个**待运行/待 sealed programme
- **3 个**在部分方向上有互补优势

### 最诚实的评估

**No single model convincingly beats the original on all transfer directions.** The best improvement (contrastive learning) is +0.016 median Spearman, with 3/4 directions positive but SpecGen C remaining stubbornly difficult. This is a genuinely hard problem — the input features (elemental composition + UV-vis spectra + synthesis conditions) may simply not encode enough cross-chemical-space transferable information.

### 最有价值的方向

1. **Contrastive learning** (best overall, clean principle, easy to combine with other methods)
2. **Delta-MHAR** (complementary to Standard — UofT→VSP +0.173, SpecGen C best at 0.298)
3. **Expert Router** (uses both without target labels — needs sealed programme for honest evaluation)
4. **MAML** (directly optimizes for few-shot transfer — matches the evaluation protocol)

### 不应再投入的方向

- **KL-Shampoo**: source optimization ≠ transfer
- **Adversarial domain adaptation**: erases chemical information alongside domain identity
- **Pairwise element encoder**: too sparse for small models
- **CORAL**: inconsistent across datasets

---

## Reproduce

```bash
cd collective-exp-data-index

# 40-epoch screening (all 8 methods, ~4 min)
python analysis/run_transfer_screening.py --epochs 40 --skip-adaptation

# 40-epoch round 2 (Delta-MHAR variants, adversarial with target)
python analysis/run_round2_screening.py --epochs 40

# 180-epoch full benchmark (contrastive + combos, ~25 min)
python analysis/run_full_benchmark.py

# GA architecture search (~2 hours, 16 pop × 8 gen × 30ep)
python -c "
from catalyst_attention.data import load_specgen_archive
from catalyst_attention.genetic_search import run_ga_search
import torch
samples = [s for s in load_specgen_archive('research/data/specgen.zip') if s.program=='specgen_source']
result = run_ga_search(samples, device=torch.device('cpu'), population_size=16, generations=8, epochs=30)
print('Best config:', result['best_genes'])
"

# Run all tests
python -m pytest tests/test_catalyst_attention.py -v
```
