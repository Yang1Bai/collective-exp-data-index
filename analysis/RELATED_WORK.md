# Related work and novelty boundary

This note fixes the claims that the manuscript may and may not make. It is
deliberately stricter than a conventional related-work section: every cited
precedent removes a possible priority claim, and every remaining novelty claim
is tied to a result that is reproduced in this repository.

## 1. Experimental memory and AI-assisted scientific inspiration

FAIR materials-data infrastructure, OPTIMADE, and recent calls for a shared
experimental memory establish that reported measurements are valuable only
when their identities, conditions, provenance, and reuse constraints remain
available. Smit and Garcia sharpen this point as the "data-only illusion":
materials discovery cannot be reduced to scaling labels while synthesis
complexity and chemical knowledge remain outside the model. The present study
therefore cannot claim that experimental-first materials intelligence, FAIR
experimental context, or a shared materials memory is a new aspiration.

AI-assisted scientific inspiration is also established prior art. Tshitoyan
*et al.* showed that unsupervised literature embeddings encode materials
relationships and can recommend functional candidates before their later
report. Marwitz *et al.* subsequently combined language models, temporal
concept graphs, and link prediction to suggest emerging research directions;
domain experts rated a subset of the generated concept combinations as
interesting. The present study therefore cannot claim to introduce the idea
that machine-readable neighboring knowledge can inspire new materials
research.

**Defensible distinction.** This work treats experimental-first as an
operational design constraint, not a data-source adjective. A proposed source
edge carries reported material identity, conditions, provenance, endpoint, and
falsifier. Literature or chemical adjacency may nominate an edge, but only
leakage-safe target evidence, practical thresholds, wrong-source controls, and
transport tests can admit it. The resulting shortlist is tied to an explicit
source-derived hypothesis card. This closes a different part of the workflow
than semantic link prediction: it asks whether an inspired relation survives
contact with measured target outcomes and whether it expands distinct OOD
regions rather than merely predicting a future literature connection.

The distinction is not yet complete validation. The Caltech family-first
analysis was outcome-informed, and no source-derived hypothesis has been tested
prospectively. The present contribution is therefore an experimental
falsification layer and retrospective proof of feasibility, not a demonstrated
autonomous science-discovery system.

## 2. Cross-property, cross-domain, and task-transfer learning

Cross-property transfer learning in materials science is established prior
art. Yamada *et al.* pretrained property models and transferred learned
representations to small-data targets spanning polymers and inorganic
materials. Jha *et al.* transferred models from large computed
formation-energy datasets to smaller computational and experimental targets.
An author correction to the latter study reported duplicates in the
experimental target, reduced its size from 1,963 to 1,643 observations, and
revised the errors. That history is directly relevant here: canonical entity
resolution and split-level duplicate audits are validity conditions, not
optional preprocessing details.

Gupta *et al.* subsequently proposed a cross-property deep-transfer framework
for small materials datasets. Kong *et al.* combined composition
representations, multi-property correlation learning, and generative transfer
from a computational density-of-states domain to experimental optical spectra.
Cubuk *et al.* used machine learning and transfer learning for small-data
solid-electrolyte discovery. The present study therefore cannot claim to
introduce cross-property transfer, tangential-domain transfer, or transfer
learning for ionic conductors.

Chang *et al.* further introduced a mixture-of-experts framework that combines
multiple pretrained materials models and automatically learns source-task
relevance, outperforming pairwise transfer on most of its data-scarce property
tasks. This is the closest precedent to automatic source selection. The present
work does not claim a more expressive transfer architecture or broader task
benchmark; its distinction is the endpoint-resolved experimental audit,
wrong-source abstention, and preservation of complementary source rankings for
OOD exploration.

Nor is a computational map of directional task transfer itself new. Taskonomy
mapped first- and higher-order transfer dependencies among 26 computer-vision
tasks and used the map to reduce supervision requirements. It is an important
conceptual precedent even though its data, representations, and validation
problem differ from experimental materials science.

**Defensible distinction.** This work does not propose a new transfer
architecture. It treats source-to-target borrowing as an object of empirical
measurement and falsification. Every candidate edge must survive canonical
identity audits, provenance-aware or temporal evaluation, a fixed target
budget, source-label permutations, multiplicity correction, cluster-aware
uncertainty, and learner sensitivity. Harmful and practically equivalent edges
remain in the evidence base. These endpoint-resolved states instantiate an
artifact-gated knowledge-borrowing map for the tasks tested here. Unlike a
universal taxonomy or transferability score, the map does not claim to predict
utility on untested materials tasks from distance alone.

The positive methodological distinction is a selective neighborhood-borrowing
strategy rather than another pooled transfer learner. Qualified sources are
matched to their endpoint and preserved as independent predictions or ranked
proposals, allowing complementary neighbors to nominate different OOD
candidates. Portfolio coverage is then compared with each constituent source,
target-only novelty and random references, and matched wrong-domain or shuffled
sources. This design turns cross-domain information into falsifiable candidate
hypotheses without assuming that one latent representation or one target
surrogate must absorb every useful signal.

### Adjacent transferability and multi-information-source frameworks

Learned transferability scores and task distances address a neighboring
question. LEEP estimates the transferability of a pretrained representation
from its predictions on target data, while optimal-transport dataset distance
quantifies task similarity without training a transfer model
[@Nguyen2020LEEP; @AlvarezMelis2020OTDD]. These methods aim to predict which
source or representation will transfer. Our gates instead audit an observed
source→target effect after fixing its endpoint, split, utility threshold, and
controls. The Caltech result shows why the distinction matters: admission based
on composition alignment did not rank source out-of-fold skill and did not
guarantee acquisition utility.

Multi-fidelity Bayesian optimization and multi-information-source optimization
use cheaper, biased, or noisy approximations to accelerate an expensive target
objective [@Kandasamy2017Multifidelity; @Poloczek2017MISO]. Their acquisition
rules jointly model source bias, uncertainty, and cost. Here, neighboring
experimental datasets are not assumed to be calibrated fidelities, costs are
not optimized, and the tested mean-plus-ensemble-spread UCB is not a general
multi-fidelity policy. The contribution is therefore the separation and
falsification of borrowing endpoints, not a replacement for fidelity-aware
Gaussian-process acquisition. A future policy may combine the present gates
with learned task distances and cost-aware multi-source optimization, but it
must be frozen before a genuinely temporal or prospective target is revealed.

## 3. Experimental alloy data and external confirmation

Attari and Arroyave used the BIRDSHOT high-entropy-alloy dataset to compare
deep tabular and conventional machine-learning models. Their March 2025 table
contained 147 rows and included composition, processing descriptors, and
mechanical properties. The pinned v5 file used here has 171 rows and 151 unique
canonical compositions. This study is therefore neither the first analysis of
BIRDSHOT nor evidence that a new model architecture is required.

**Defensible distinction.** BIRDSHOT is used as a time-ordered external target,
not as another randomly split benchmark. A source model trained on Borg alloy
data produces a small but repeatable reduction in BIRDSHOT yield-strength error
across Year 1-to-2 and Years 1--2-to-3 folds, while the explicit Borg
UTS--yield-strength calibration fails badly on the same external target. This paired
comparison supports a narrower claim: a rigid source-domain calibration need not
transport even when a soft source prediction contains useful local information.
The external gain is below the preregistered 5% practical threshold at the
primary target budget, so it is reported as directional replication rather
than full confirmation.

A post hoc sensitivity conditions the target learner on available cold-work,
holding-time and grain-size fields and retains the relative error reduction.
This rules out those recorded process variables as a simple explanation of the
edge, but rolling-time R² remains negative. The study therefore does not claim
that it has already rescued an externally shifting alloy campaign.

Matbench already provides a versioned suite of 13 materials-prediction tasks,
including the 312-sample experimental steel-strength task, with prescribed
evaluation folds and reference algorithms. The underlying steel table was
released by Hacking Materials on Figshare after extraction and deduplication
from Citrine. An author correction changed a Matbench figure label from yield
strength in GPa to MPa; the present normalization uses the corrected MPa unit.
The present study neither introduces this dataset nor proposes a new benchmark.

**Defensible distinction.** Matbench steels is used as an adversarial,
independent negative transfer target. The upstream five folds are retained;
same-row tensile strength and elongation are forbidden target inputs; and exact
target compositions are excluded from source fits. The null result prevents
mechanical-property adjacency from being promoted to a universal transfer rule.

## 4. Temperature-resolved electrolyte data

Rahmanian *et al.* created the high-throughput PC/EC/EMC/LiPF6 electrolyte
campaign used here, measured conductivity from −30 to 60 °C in 10 °C steps,
provided repeated experiments, and released the data and MADAP analysis
software. Their article explicitly identifies machine-learning use and notes
that fractions of the dataset had already supported ML models. The present
study therefore cannot claim the first conductivity model, first automated
analysis, first low-temperature electrolyte study, or creation of this
dataset.

**Defensible distinction.** The novelty is the frozen *borrowing test*, not the
electrolyte data or model. Formulations are the independent units; outer-test
formulations are absent from all source fits; target-training source features
are cross-fitted; temperature-series-derived Arrhenius and EIS quantities are
forbidden; increasing temperature distances and a shuffled source are frozen
controls; and success requires both absolute R² and target-label equivalence.
The result passes the frozen local, within-campaign point rules and is
deliberately not described as independent-dataset rescue. Its 37.35% label-
saving point estimate has a post-outcome diagnostic interval of
21.84--49.91%; the error reduction and positive absolute utility are stronger
than the exact magnitude of saved labels.

de Blasio *et al.* subsequently published CALiSol-23, a literature-curated
atlas of 13,825 non-aqueous electrolyte-conductivity measurements from 27
articles, spanning 38 solvents, 14 reported lithium-salt labels,
concentrations, and temperatures. Their Data Descriptor explicitly proposes
the dataset for chemistry-agnostic and temperature-dependent conductivity
models. The present study therefore cannot claim the first aggregated liquid-
electrolyte conductivity dataset, the first CALiSol machine-learning use, or
the first model across salts and solvents.

**Defensible distinction for CALiSol.** CALiSol is used as an adversarial
transport test for the frozen borrowing logic. Outer folds hold out complete
source articles; all rows from test articles and exact held-out chemistry
identities are absent from source fits; target-training priors are
leave-one-article-out; article DOI and temperature-series-derived quantities
are forbidden features; and uncertainty resamples articles. The unresolved
result is retained as evidence that the KIT rescue does not automatically
survive experimental-campaign heterogeneity.

Segal *et al.* showed that anchor-and-difference transduction can improve
out-of-support property prediction, although its principal materials tests
define OOD from high response values. Yahagi *et al.* instead used
chemistry-informed transformations to map calculated quantities into
experimental space with fewer than ten calibration measurements. Together,
these studies motivate transferring a relation or transformation rather than
assuming that raw features or pretrained weights are portable.

**Additional distinction for the CALiSol contrast test.** The present
post-outcome reanalysis combines that principle with an experimental
provenance boundary. It learns formulation-response contrasts only within
source articles and uses one outcome-independent target-article anchor to
restore the absolute scale. Its primary comparator uses the same donor and
anchor but transfers an absolute function. The 6.91% macro-RMSE advantage
therefore isolates the transfer object under a held-article-out contract.
Unlike MatEx, this is not an output-tail OOD test or a zero-shot claim; unlike
the simulation-to-experiment study, both donor and recipient are reported
experimental measurements. The method was formulated after the original
CALiSol null and thus requires unchanged external replication.

## 5. Data aggregation and materials-data infrastructure

MDF, OPTIMADE, and controlled vocabularies and metadata schemas already
establish the need for findable, interoperable, machine-readable materials
data. The repository therefore should not claim to be the first materials
database index, federated interface, common schema, or data-integration effort.

More directly, Ottomano *et al.* tested several materials-dataset aggregation
strategies and found that classical-machine-learning performance often
degraded, while most deep-learning changes were not significant. That work
already rejects the assumption that simply adding heterogeneous materials data
must improve prediction.

**Defensible distinction.** The contribution is the combination of (i) a
catalog focused on resources containing experimental measurements, with access
and license limitations left visible; (ii) a commit-pinned local integration
that retains row provenance, conditions, raw and canonical identity, and
quality flags; and (iii) a resource-to-claim audit in which aggregate laws,
transfer edges, negative controls, and external confirmation are evaluated
under one reproducible framework. The novelty is not a universal schema or the
generic lesson that more data can hurt.

## 6. Compensation laws and statistical artifacts

Meyer--Neldel and enthalpy--entropy compensation have long histories across
materials, kinetics, adsorption, and chemistry. Krug, Hunter and Grieger
formalized the statistical coupling that can produce apparent compensation
when slope and intercept are estimated from the same limited temperature
range. Cornish-Bowden later emphasized that excellent compensation
correlations can be largely artefactual. Bond *et al.* distinguished apparent
from statistically established isokinetic behavior in heterogeneous catalysis
and catalogued mechanism changes, diffusion limitation, and parameter error as
sources of false compensation. Mianowski and Urbanczyk specifically examined
isosteric adsorption compensation near ambient temperature. The
isokinetic/Krug comparison used here is therefore an inherited diagnostic, not
a new test and not proof of mechanism.

The NIST/ARPA-E Database of Novel and Emerging Adsorbent Materials (ISODB) is
also an established public data resource. This study streams a pinned ISODB
snapshot for matched-loading isosteric fits; it does not claim to have created
or fully normalized the adsorption data.

**Defensible distinction.** The thermoelectric analysis uses
reference-separated series construction, Arrhenius quality gates,
heteroskedasticity-consistent inference, family-size rules, multiplicity
correction, and threshold sensitivity. Its pooled association is weak. In
contrast, the large ISODB association survives an independent-parameter Krug
null but requires adsorbate-family intercepts. These results rule out the
overly simple statement that either all pooled regularities are universal or
all are Krug artifacts. The defensible contribution is an artifact-gatekeeping
workflow that can return weak, artifactual, or strong-but-conditional outcomes.

## 7. Claims the manuscript must avoid

- first cross-property, cross-domain, or tangential-domain transfer learning
  in materials;
- first transfer-learning study of solid electrolytes;
- first computational map of task transfer;
- first machine-learning analysis of BIRDSHOT;
- first Matbench steel benchmark or first release of the steel-strength data;
- first machine-learning analysis, automated analysis, or temperature-resolved
  measurement of the KIT liquid-electrolyte campaign;
- first warning that heterogeneous data aggregation can reduce performance;
- first materials metadata schema, database federation, or integrated data
  resource;
- first use of AI to expose latent materials relationships, recommend future
  candidates, or suggest new research directions;
- the claim that using experimental labels alone incorporates chemical
  knowledge or resolves the data-only illusion;
- a universal, ordinal physical-distance law for borrowing: the 0--3 ordering
  is not significant in the present map;
- a domain-general or independently replicated rescue map: the strongest
  preregistered positive edge remains within one electrolyte campaign, the
  CALiSol paper-disjoint repair is a post-outcome anchored-contrast
  reanalysis, BIRDSHOT lacks absolute utility, and Matbench is null;
- proof that Meyer--Neldel or organic transfer effects are physically absent;
- proof that the ISODB compensation relation has one universal mechanism;
- prospective discovery acceleration from retrospective pool simulations.

## 8. Verified reference set

1. Yamada, H. *et al.* Predicting materials properties with little data using
   shotgun transfer learning. *ACS Cent. Sci.* **5**, 1717--1730 (2019).
   [https://doi.org/10.1021/acscentsci.9b00804](https://doi.org/10.1021/acscentsci.9b00804)
2. Jha, D. *et al.* Enhancing materials property prediction by leveraging
   computational and experimental data using deep transfer learning. *Nat.
   Commun.* **10**, 5316 (2019).
   [https://doi.org/10.1038/s41467-019-13297-w](https://doi.org/10.1038/s41467-019-13297-w)
3. Jha, D. *et al.* Author Correction: Enhancing materials property prediction
   by leveraging computational and experimental data using deep transfer
   learning. *Nat. Commun.* **11**, 3643 (2020).
   [https://doi.org/10.1038/s41467-020-17054-2](https://doi.org/10.1038/s41467-020-17054-2)
4. Gupta, V. *et al.* Cross-property deep transfer learning framework for
   enhanced predictive analytics on small materials data. *Nat. Commun.*
   **12**, 6595 (2021).
   [https://doi.org/10.1038/s41467-021-26921-5](https://doi.org/10.1038/s41467-021-26921-5)
5. Kong, S., Guevarra, D., Gomes, C. P. & Gregoire, J. M. Materials
   representation and transfer learning for multi-property prediction. *Appl.
   Phys. Rev.* **8**, 021409 (2021).
   [https://doi.org/10.1063/5.0047066](https://doi.org/10.1063/5.0047066)
6. Cubuk, E. D., Sendek, A. D. & Reed, E. J. Screening billions of candidates
   for solid lithium-ion conductors: a transfer learning approach for small data.
   *J. Chem. Phys.* **150**, 214701 (2019).
   [https://doi.org/10.1063/1.5093220](https://doi.org/10.1063/1.5093220)
7. Zamir, A. R. *et al.* Taskonomy: disentangling task transfer learning. In
   *Proc. CVPR* 3712--3722 (2018).
   [https://doi.org/10.1109/CVPR.2018.00391](https://doi.org/10.1109/CVPR.2018.00391)
8. Therrien, F. *et al.* OBELiX: a curated dataset of crystal structures and
   experimentally measured ionic conductivities for lithium solid-state
   electrolytes. *Digital Discovery* **5**, 910 (2026).
   [https://doi.org/10.1039/D5DD00441A](https://doi.org/10.1039/D5DD00441A)
9. Attari, V. & Arroyave, R. Decoding non-linearity and complexity: deep
   tabular learning approaches for materials science. *Digital Discovery*
   **4**, 2765--2780 (2025).
   [https://doi.org/10.1039/D5DD00166H](https://doi.org/10.1039/D5DD00166H)
10. Ottomano, F., De Felice, G., Gusev, V. V. & Sparks, T. D. Not as simple as
    we thought: a rigorous examination of data aggregation in materials
    informatics. *Digital Discovery* **3**, 337--346 (2024).
    [https://doi.org/10.1039/D3DD00207A](https://doi.org/10.1039/D3DD00207A)
11. Blaiszik, B. *et al.* The Materials Data Facility: data services to advance
    materials science research. *JOM* **68**, 2045--2052 (2016).
    [https://doi.org/10.1007/s11837-016-2001-3](https://doi.org/10.1007/s11837-016-2001-3)
12. Andersen, C. W. *et al.* OPTIMADE, an API for exchanging materials data.
    *Sci. Data* **8**, 217 (2021).
    [https://doi.org/10.1038/s41597-021-00974-z](https://doi.org/10.1038/s41597-021-00974-z)
13. Medina-Smith, A. *et al.* A controlled vocabulary and metadata schema for
    materials science data discovery. *Data Sci. J.* **20**, 18 (2021).
    [https://doi.org/10.5334/dsj-2021-018](https://doi.org/10.5334/dsj-2021-018)
14. Siderius, D. NIST/ARPA-E Database of Novel and Emerging Adsorbent
    Materials, version 1.0. National Institute of Standards and Technology
    (2019). [https://doi.org/10.18434/T43882](https://doi.org/10.18434/T43882)
15. Krug, R. R., Hunter, W. G. & Grieger, R. A. Enthalpy--entropy
    compensation. 1. Some fundamental statistical problems associated with
    the analysis of van't Hoff and Arrhenius data. *J. Phys. Chem.* **80**,
    2335--2341 (1976).
    [https://doi.org/10.1021/j100562a006](https://doi.org/10.1021/j100562a006)
16. Cornish-Bowden, A. Enthalpy--entropy compensation: a phantom phenomenon.
    *J. Biosci.* **27**, 121--126 (2002).
    [https://doi.org/10.1007/BF02703768](https://doi.org/10.1007/BF02703768)
17. Bond, G. C., Keane, M. A., Kral, H. & Lercher, J. A. Compensation
    phenomena in heterogeneous catalysis: general principles and a possible
    explanation. *Catal. Rev.* **42**, 323--383 (2000).
    [https://doi.org/10.1081/CR-100100264](https://doi.org/10.1081/CR-100100264)
18. Mianowski, A. & Urbanczyk, W. Enthalpy--entropy compensation for
    isosteric state adsorption at near ambient temperatures. *Adsorption*
    **23**, 831--846 (2017).
    [https://doi.org/10.1007/s10450-017-9900-7](https://doi.org/10.1007/s10450-017-9900-7)
19. Dunn, A., Wang, Q., Ganose, A., Dopp, D. & Jain, A. Benchmarking
    materials property prediction methods: the Matbench test set and
    Automatminer reference algorithm. *npj Comput. Mater.* **6**, 138 (2020).
    [https://doi.org/10.1038/s41524-020-00406-3](https://doi.org/10.1038/s41524-020-00406-3)
20. Dunn, A. *et al.* Author Correction: Benchmarking materials property
    prediction methods: the Matbench test set and Automatminer reference
    algorithm. *npj Comput. Mater.* **6**, 159 (2020).
    [https://doi.org/10.1038/s41524-020-00433-0](https://doi.org/10.1038/s41524-020-00433-0)
21. Hacking Materials. Steel Strength Data. Figshare (2018).
    [https://doi.org/10.6084/m9.figshare.7250453](https://doi.org/10.6084/m9.figshare.7250453)
22. Rahmanian, F. *et al.* Conductivity experiments for electrolyte
    formulations and their automated analysis. *Sci. Data* **10**, 43 (2023).
    [https://doi.org/10.1038/s41597-023-01936-3](https://doi.org/10.1038/s41597-023-01936-3)
23. de Blasio, P. *et al.* CALiSol-23: Experimental electrolyte conductivity
    data for various Li-salts and solvent combinations. *Sci. Data* **11**, 750
    (2024).
    [https://doi.org/10.1038/s41597-024-03575-8](https://doi.org/10.1038/s41597-024-03575-8)
24. Scheffler, M. *et al.* FAIR data enabling new horizons for materials
    research. *Nature* **604**, 635--642 (2022).
    [https://doi.org/10.1038/s41586-022-04501-x](https://doi.org/10.1038/s41586-022-04501-x)
25. Smit, B. & Garcia, S. The data-only illusion in materials discovery.
    *Nat. Mater.* (2026).
    [https://doi.org/10.1038/s41563-026-02578-7](https://doi.org/10.1038/s41563-026-02578-7)
26. Akhound, M. A., Sauer, M. O. & Thygesen, K. S. Two-dimensional materials
    need a shared experimental memory. *Nat. Rev. Mater.* (2026).
    [https://doi.org/10.1038/s41578-026-00938-y](https://doi.org/10.1038/s41578-026-00938-y)
27. Tshitoyan, V. *et al.* Unsupervised word embeddings capture latent
    knowledge from materials science literature. *Nature* **571**, 95--98
    (2019).
    [https://doi.org/10.1038/s41586-019-1335-8](https://doi.org/10.1038/s41586-019-1335-8)
28. Marwitz, T. *et al.* Predicting new research directions in materials
    science using large language models and concept graphs. *Nat. Mach.
    Intell.* **8**, 535--544 (2026).
    [https://doi.org/10.1038/s42256-026-01206-y](https://doi.org/10.1038/s42256-026-01206-y)
29. Chang, R., Wang, Y.-X. & Ertekin, E. Towards overcoming data scarcity in
    materials science: unifying models and datasets with a mixture of experts
    framework. *npj Comput. Mater.* **8**, 242 (2022).
    [https://doi.org/10.1038/s41524-022-00929-x](https://doi.org/10.1038/s41524-022-00929-x)
30. Li, K. *et al.* Exploiting redundancy in large materials datasets for
    efficient machine learning with less data. *Nat. Commun.* **14**, 7283
    (2023).
    [https://doi.org/10.1038/s41467-023-42992-y](https://doi.org/10.1038/s41467-023-42992-y)
31. Li, K. *et al.* Probing out-of-distribution generalization in machine
    learning for materials. *Commun. Mater.* **6**, 9 (2025).
    [https://doi.org/10.1038/s43246-024-00731-w](https://doi.org/10.1038/s43246-024-00731-w)
32. Yahagi, Y., Obuchi, K., Kosaka, F. & Matsui, K. Transfer learning from
    first-principles calculations to experiments with chemistry-informed
    domain transformation. *Mach. Learn.: Sci. Technol.* **6**, 025026 (2025).
    [https://doi.org/10.1088/2632-2153/adcdc0](https://doi.org/10.1088/2632-2153/adcdc0)
33. Segal, N., Netanyahu, A., Greenman, K. P., Agrawal, P. &
    Gómez-Bombarelli, R. Known Unknowns: Out-of-Distribution Property
    Prediction in Materials and Molecules. *npj Comput. Mater.* **11**, 345
    (2025).
    [https://doi.org/10.1038/s41524-025-01808-x](https://doi.org/10.1038/s41524-025-01808-x)
