# Catalog

_268 databases · updated 2026-08-16 · 240 experimental · 28 mixed · 0 computational_

> This is a metadata index. Each entry links to the dataset at its original home; nothing is re-hosted here. `data_type` marks whether the underlying data is measured (**experimental**), simulated (**computational**), or **mixed**. Purely computational databases are excluded by policy (see catalog/excluded_computational.json).

> Legend: 🧪 experimental · 🧮 computational · 🔀 mixed · 🔓 open · 🔑 registration · 🔒 restricted

## Contents

- **Chemistry**
  - [Batteries & energy storage](#chemistry-batteries) (1)
  - [ML benchmark datasets](#chemistry-benchmark-ml) (4)
  - [Bioactivity & screening](#chemistry-bioactivity) (4)
  - [Catalysis](#chemistry-catalysis) (1)
  - [Crystallography](#chemistry-crystallography) (1)
  - [Data infrastructure & portals](#chemistry-data-infrastructure) (2)
  - [HTE / synthesis](#chemistry-hte-synthesis) (6)
  - [Ionic liquids](#chemistry-ionic-liquids) (1)
  - [Reaction kinetics](#chemistry-kinetics) (2)
  - [Lab automation & robotic chemistry](#chemistry-lab-automation) (5)
  - [Molecular properties](#chemistry-molecular-properties) (5)
  - [Optical properties & chromophores](#chemistry-optical-properties) (2)
  - [Physical properties](#chemistry-physical-properties) (2)
  - [pKa / dissociation constants](#chemistry-pka) (2)
  - [Polymers](#chemistry-polymers) (1)
  - [Reaction data](#chemistry-reactions) (2)
  - [Self-driving-lab benchmarks](#chemistry-sdl-benchmarks) (3)
  - [Solubility](#chemistry-solubility) (2)
  - [Solvation](#chemistry-solvation) (2)
  - [Experimental spectra (XPS/Raman/XRD)](#chemistry-spectra-exp) (3)
  - [Spectroscopy](#chemistry-spectroscopy) (4)
  - [Thermochemistry](#chemistry-thermochemistry) (1)
- **Materials**
  - [Additive manufacturing](#materials-additive-manufacturing) (1)
  - [Alloys & high-entropy alloys](#materials-alloys) (1)
  - [Alloys & mechanical properties](#materials-alloys-mechanical) (2)
  - [Batteries & energy storage](#materials-batteries) (20)
  - [ML benchmark datasets](#materials-benchmark-ml) (2)
  - [Bioactivity & screening](#materials-bioactivity) (15)
  - [Catalysis](#materials-catalysis) (28)
  - [Crystallography](#materials-crystallography) (2)
  - [Data infrastructure & portals](#materials-data-infrastructure) (3)
  - [Electrocatalysis (experimental HTE)](#materials-electrocatalysis-exp) (2)
  - [General materials properties](#materials-general-properties) (60)
  - [Geophysics & earth sciences](#materials-geophysics) (4)
  - [Glasses](#materials-glasses) (2)
  - [High-throughput experimental](#materials-high-throughput-exp) (3)
  - [HTE / synthesis](#materials-hte-synthesis) (1)
  - [Lab automation & robotic chemistry](#materials-lab-automation) (2)
  - [Magnetic materials](#materials-magnetic) (12)
  - [Mechanical properties](#materials-mechanical) (2)
  - [Membranes & separations](#materials-membranes) (1)
  - [MOFs & porous materials](#materials-mofs-porous) (5)
  - [Nanomaterials & nanosafety](#materials-nanomaterials) (1)
  - [Optical properties & chromophores](#materials-optical-properties) (2)
  - [Organic electronics](#materials-organic-electronics) (2)
  - [Photovoltaics & solar cells](#materials-photovoltaics) (16)
  - [Polymers](#materials-polymers) (6)
  - [Porous materials](#materials-porous-materials) (2)
  - [Experimental spectra (XPS/Raman/XRD)](#materials-spectra-exp) (5)
  - [Spectroscopy](#materials-spectroscopy) (6)
  - [Superconductors](#materials-superconductors) (1)
  - [Thermoelectrics](#materials-thermoelectrics) (2)
  - [Thermophysical properties](#materials-thermophysical) (1)


## Chemistry

<a id="chemistry-batteries"></a>
### Batteries & energy storage

#### 🧪🔓 [5035 Conductivity Experiments for Li-Ion Battery Electrolytes](https://zenodo.org/records/7244939)

Dataset of 5,035 electrochemical impedance spectroscopy conductivity experiments on liquid lithium-ion battery electrolyte formulations (EC/PC/EMC solvents with LiPF6 at varied salt concentrations) across temperatures, with derived activation energies. Generated on a high-throughput formulation-and-measurement platform at KIT/Forschungszentrum Juelich within the BIG-MAP project; single CSV (~39 MB) on Zenodo.

`experimental`· `open`· 2022 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.7244939](https://doi.org/10.5281/zenodo.7244939)· tags: `electrolytes`, `ionic-conductivity`, `lithium-ion`, `high-throughput`, `impedance-spectroscopy`, `big-map`

<a id="chemistry-benchmark-ml"></a>
### ML benchmark datasets

#### 🔀🔓 [MoleculeNet](https://moleculenet.org/)

Curated benchmark suite of 17 public datasets across four property categories (quantum mechanics, physical chemistry, biophysics, physiology) covering >700,000 compounds, with standardized splits and metrics. Distributed via the DeepChem open-source library.

`mixed`· `open`· 2018 · MIT · DeepChem / self-hosted· DOI: [10.1039/C7SC02664A](https://doi.org/10.1039/C7SC02664A)· tags: `benchmark`, `deepchem`, `property-prediction`, `molecular-ml`, `curated-suite`

#### 🔀🔓 [Open Graph Benchmark - Molecular Datasets](https://ogb.stanford.edu/)

Standardized graph-ML benchmark datasets for molecular property prediction, notably ogbg-molhiv (41,127 molecules, HIV-inhibition classification) and ogbg-molpcba (437,929 molecules, 128 PubChem BioAssay tasks). Molecules are RDKit-processed with unified atom/bond features and scaffold splits.

`mixed`· `open`· 2020 · MIT · self-hosted (Stanford)· tags: `graph-neural-networks`, `molhiv`, `molpcba`, `property-prediction`, `benchmark`

#### 🔀🔓 [Therapeutics Data Commons (TDC)](https://tdcommons.ai/)

Unified open platform of 66 ML-ready datasets across 22 learning tasks (~16M data points) spanning target discovery, ADMET, efficacy, safety, and manufacturing for small molecules, antibodies, and vaccines. Provides splits, evaluators, oracles, and leaderboards via an open Python library.

`mixed`· `open`· 2021 · MIT (datasets vary) · GitHub· tags: `benchmark`, `admet`, `drug-discovery`, `ml-ready`, `leaderboards`

#### 🧪🔓 [USPTO-50k Retrosynthesis Benchmark](https://github.com/Hanjun-Dai/GLN)

Benchmark subset of ~50,000 atom-mapped organic reactions in SMILES drawn from Lowe's USPTO patent reactions and labeled into 10 reaction classes (Schneider et al.). The primary standard benchmark for single-step retrosynthesis models.

`experimental`· `open`· 2016 · Other (derived from public USPTO reactions) · GitHub· tags: `retrosynthesis`, `reaction-prediction`, `benchmark`, `atom-mapping`, `uspto`

<a id="chemistry-bioactivity"></a>
### Bioactivity & screening

#### 🧪🔓 [BindingDB](https://www.bindingdb.org/)

Public FAIR knowledgebase of experimentally measured protein-small molecule binding affinities (~2.9M measurements over ~1.3M compounds and thousands of targets), curated chiefly from the literature and patents. Focused on drug-target interactions for SAR/QSAR and computational validation.

`experimental`· `open`· 2024 · CC-BY-4.0 · self-hosted (UCSD)· DOI: [10.1093/nar/gkae1075](https://doi.org/10.1093/nar/gkae1075)· tags: `binding-affinity`, `protein-ligand`, `drug-target`, `Ki`, `SAR`

#### 🧪🔓 [ChEMBL](https://www.ebi.ac.uk/chembl/)

Manually curated database of bioactive drug-like small molecules from the medicinal-chemistry literature, patents, and screening, with measured bioactivities (Ki, Kd, IC50, EC50) against biological targets. Maintained by EMBL-EBI; v34 contains millions of activity records.

`experimental`· `open`· 2024 · CC-BY-SA-3.0 · EMBL-EBI· tags: `bioactivity`, `drug-discovery`, `IC50`, `targets`, `medicinal-chemistry`

#### 🔀🔓 [PubChem](https://pubchem.ncbi.nlm.nih.gov/)

NIH/NCBI public repository of chemical information organized as three linked databases: Substance, Compound (~100M+ unique structures), and BioAssay (experimental screening results). Aggregates deposited experimental data, measured properties, and computed descriptors from hundreds of sources.

`mixed`· `open`· 2004 · Public domain (US Gov) · NCBI· tags: `compounds`, `bioassays`, `screening`, `chemical-structures`, `ncbi`

#### 🧪🔓 [Tox21](https://tripod.nih.gov/tox21/challenge/)

Toxicology-in-the-21st-Century dataset of ~12,000 compounds profiled by quantitative high-throughput in vitro assays across 12 nuclear-receptor and stress-response endpoints (EPA/NIH/FDA collaboration). Basis of the Tox21 Data Challenge and a standard toxicity-prediction benchmark.

`experimental`· `open`· 2014 · Public domain (US Gov) · NIH Tripod· tags: `toxicity`, `high-throughput-screening`, `nuclear-receptor`, `assays`, `benchmark`

<a id="chemistry-catalysis"></a>
### Catalysis

#### 🧪🔓 [CatTestHub](https://chemrxiv.org/engage/chemrxiv/article-details/65b1b5e5e9ebbb4db9e91c68)

Open benchmarking database of experimental heterogeneous catalysis (Univ. Minnesota): initial release compiles >250 experimental data points over 24 solid catalysts for 3 probe chemistries with harmonized conditions, reactor configuration and characterization.

`experimental`· `open`· 2024 · Unknown · ChemRxiv SI / J. Catal.· tags: `heterogeneous-catalysis`, `benchmarking`, `reaction-kinetics`, `catalyst-testing`

<a id="chemistry-crystallography"></a>
### Crystallography

#### 🧪🔒 [Cambridge Structural Database (CSD)](https://www.ccdc.cam.ac.uk/solutions/software/csd/)

Curated repository of experimentally determined small-molecule organic and metal-organic crystal structures (>1,000,000 entries, ~40,000 added/year), maintained by CCDC. NOT fully open: individual depositions are free to view/download via Access Structures, but full search and analytics require a subscription.

`experimental`· `restricted`· 2016 · Other (proprietary; free single-structure viewer) · CCDC· DOI: [10.1107/S2052520616003954](https://doi.org/10.1107/S2052520616003954)· tags: `crystal-structures`, `organometallic`, `x-ray`, `ccdc`, `curated`

<a id="chemistry-data-infrastructure"></a>
### Data infrastructure & portals

#### 🧪🔓 [Chemotion Repository](https://www.chemotion-repository.net/)

Curated open research-data repository for chemistry (KIT; NFDI4Chem): preserves experimental data from syntheses and analytical measurements (NMR, IR, MS, chromatography) for molecules and reactions, ELN-linked with automated plausibility checks; thousands of curated samples/reactions.

`experimental`· `open`· 2021 · CC-BY-4.0 · KIT· tags: `research-data-repository`, `eln`, `synthesis`, `analytical-data`, `fair-data`

#### 🔀🔓 [RADAR4Chem](https://radar.products.fiz-karlsruhe.de/en/radarabout/radar4chem)

Free multidisciplinary repository for publishing FAIR chemistry research data (FIZ Karlsruhe; NFDI4Chem), for datasets that don't fit discipline-specific repositories (up to 10 GB/project). Predominantly experimental deposits; accepts all data types (mixed).

`mixed`· `open`· 2022 · Varies (depositor-chosen CC) · FIZ Karlsruhe· tags: `research-data-repository`, `fair-data`, `nfdi4chem`

<a id="chemistry-hte-synthesis"></a>
### HTE / synthesis

#### 🧪🔓 [AstraZeneca ELN Reaction Dataset (Buchwald-Hartwig)](https://pubs.rsc.org/en/content/articlehtml/2023/sc/d2sc06041h)

First real-world reaction dataset released from a pharma company's electronic lab notebooks: ~1,000 raw Buchwald-Hartwig amination entries (781 passing quality criteria) with reactants, products, catalysts, bases, conditions and yields. Deposited openly and uploaded to the Open Reaction Database.

`experimental`· `open`· 2023 · Other (open; NSF C-CAS) · GitHub / Open Reaction Database· DOI: [10.1039/D2SC06041H](https://doi.org/10.1039/D2SC06041H)· tags: `buchwald-hartwig`, `yield-prediction`, `eln`, `real-world-data`, `amination`

#### 🧪🔓 [Buchwald-Hartwig C-N Cross-Coupling HTE Dataset](https://www.science.org/doi/10.1126/science.aar5169)

High-throughput experimentation dataset of ~3,955 Pd-catalyzed Buchwald-Hartwig C-N cross-coupling reactions measuring yield across combinations of aryl halides, Buchwald ligands, bases, and isoxazole additives. Generated by nanomole-scale HTE in multiwell plates; a canonical benchmark for reaction-yield prediction.

`experimental`· `open`· 2018 · Unknown · Science (AAAS) supplementary· DOI: [10.1126/science.aar5169](https://doi.org/10.1126/science.aar5169)· tags: `cross-coupling`, `catalysis`, `yield-prediction`, `high-throughput`, `buchwald-hartwig`

#### 🧪🔑 [Dark Reactions Project](https://darkreactions.haverford.edu)

Dataset of ~4,000 hydrothermal synthesis reactions (templated vanadium selenites and related inorganic-organic materials), deliberately including failed and partially successful 'dark' reactions mined from lab notebooks, used to train ML that outperformed human intuition (Norquist/Schrier, Haverford).

`experimental`· `registration`· 2016 · Unknown · self-hosted (Haverford)· DOI: [10.1038/nature17439](https://doi.org/10.1038/nature17439)· tags: `failed-reactions`, `hydrothermal-synthesis`, `machine-learning`, `reaction-outcomes`, `materials-discovery`

#### 🧪🔓 [Denmark Chiral Phosphoric Acid Catalyst Selectivity Dataset](https://www.science.org/doi/10.1126/science.aau5631)

Experimental enantioselectivity measurements for CPA-catalyzed thiol addition to N-acylimines across catalyst/substrate combinations, released with conformer-based steric/electronic descriptors (ASO) for 800+ candidate catalysts. A landmark dataset for ML-driven asymmetric catalyst selection.

`experimental`· `open`· 2019 · Other (published SI) · Science SI / Denmark Group· DOI: [10.1126/science.aau5631](https://doi.org/10.1126/science.aau5631)· tags: `enantioselectivity`, `asymmetric-catalysis`, `descriptors`, `machine-learning`

#### 🧪🔓 [Reizman-Jensen Suzuki-Miyaura Flow Optimization Dataset](https://pubs.rsc.org/en/content/articlelanding/2016/re/c6re00153j)

Experimental Suzuki-Miyaura cross-coupling optimization data from an automated droplet-flow microfluidic reactor with feedback, screening palladacycle/ligand combinations plus continuous variables to maximize yield and turnover. Packaged as emulator benchmarks (reizman_suzuki) in the Summit framework.

`experimental`· `open`· 2016 · MIT (Summit) · GitHub (sustainable-processes/summit)· DOI: [10.1039/C6RE00153J](https://doi.org/10.1039/C6RE00153J)· tags: `suzuki-miyaura`, `flow-chemistry`, `reaction-optimization`, `self-optimization`, `benchmark`

#### 🧪🔓 [Suzuki-Miyaura Coupling HTE Dataset (Perera/AstraZeneca)](https://github.com/rxn4chemistry/rxn_yields)

Dataset of 5,760 Pd-catalyzed Suzuki-Miyaura couplings screened on an automated nanomole-scale flow platform, varying electrophile, nucleophile, ligand, base, and solvent with LC-MS yield readouts (>1500 reactions/day). Widely used flow-chemistry HTE benchmark for yield prediction.

`experimental`· `open`· 2018 · Unknown · GitHub / Science SI· DOI: [10.1126/science.aap9112](https://doi.org/10.1126/science.aap9112)· tags: `suzuki-miyaura`, `flow-chemistry`, `cross-coupling`, `yield-prediction`, `high-throughput`

<a id="chemistry-ionic-liquids"></a>
### Ionic liquids

#### 🧪🔓 [ILThermo (NIST Ionic Liquids Database, SRD 147)](https://ilthermo.boulder.nist.gov/)

Free web database of experimentally measured thermodynamic, thermochemical and transport properties of pure ionic liquids and their binary/ternary mixtures, developed by NIST with IUPAC. v2.0 holds nearly 280,000 data points for 1,000+ ionic liquids with method, purity and uncertainty metadata.

`experimental`· `open`· 2013 · NIST SRD (US Gov) · NIST· tags: `ionic-liquids`, `thermodynamic-properties`, `transport-properties`, `mixtures`, `nist`

<a id="chemistry-kinetics"></a>
### Reaction kinetics

#### 🧪🔓 [NIST Chemical Kinetics Database (SRD 17)](https://kinetics.nist.gov/kinetics/)

Comprehensive compilation of published rate constants for thermal gas-phase chemical reactions: ~38,000+ reaction records / ~70,000 rate measurements abstracted from over 12,000 papers. Covers combustion, atmospheric and plasma chemistry; searchable by reactants, products or species.

`experimental`· `open`· 2023 · NIST SRD (US Gov) · NIST· tags: `reaction-kinetics`, `rate-constants`, `gas-phase`, `combustion`, `atmospheric-chemistry`

#### 🧪🔓 [ReSpecTh (Reaction Kinetics, Spectroscopy, Thermochemistry)](https://respecth.hu/)

Open combustion-kinetics data collection (ELTE Budapest): >162,000 experimental data points in >3,600 machine-readable XML files covering ignition delay times (shock tube, RCM), laminar flame speeds, concentration profiles and direct rate coefficients, plus bundled reaction mechanisms.

`experimental`· `open`· 2025 · Unknown · self-hosted (ELTE)· tags: `combustion`, `ignition-delay`, `laminar-flame`, `reaction-kinetics`, `rate-coefficients`

<a id="chemistry-lab-automation"></a>
### Lab automation & robotic chemistry

#### 🧪🔓 [AlphaFlow Self-Driving Fluidic Lab Dataset](https://www.nature.com/articles/s41467-023-37139-y)

Reinforcement-learning-guided self-driving microfluidic lab (Abolhasani, NC State) that autonomously ran thousands of multi-step colloidal ALD reactions over ~30 days to discover core/shell quantum-dot synthesis routes with up to 40 parameters; RL campaign data and code released.

`experimental`· `open`· 2023 · Unknown · GitHub (AbolhasaniLab/AlphaFlow)· DOI: [10.1038/s41467-023-37139-y](https://doi.org/10.1038/s41467-023-37139-y)· tags: `self-driving-lab`, `reinforcement-learning`, `quantum-dots`, `microfluidics`, `nanomaterials`

#### 🧪🔓 [Chemputer/XDL Digitized Synthesis Procedures (Cronin Group)](https://zenodo.org/records/3955103)

Code and data underpinning the Cronin group's universal system for digitizing chemical synthesis: the XDL description language, SynthReader NLP translator and ChemputerXDL execution layer, with an executable reaction database of 100+ validated literature syntheses for the ChemPU robotic platform. Archived on Zenodo.

`experimental`· `open`· 2020 · CC-BY-4.0 (Zenodo archive) · Zenodo / GitLab· DOI: [10.5281/zenodo.3955103](https://doi.org/10.5281/zenodo.3955103)· tags: `chemputer`, `xdl`, `digitized-synthesis`, `robotic-chemistry`, `procedure-database`

#### 🧪🔓 [Closed-Loop General-Conditions Suzuki Dataset (MMLI)](https://moleculemaker.org/datasets/closed-loop-optimization-of-general-reaction-conditions-for-heteroaryl-suzuki-miyaura-coupling/)

Closed-loop robotic HTE campaign (Molecule Maker Lab Institute) combining data-guided matrix down-selection, uncertainty-minimizing ML and robotic experimentation to find general heteroaryl Suzuki-Miyaura conditions, doubling average yield vs benchmarks; all reaction data and code openly released.

`experimental`· `open`· 2022 · Unknown · Molecule Maker Lab Institute· DOI: [10.1126/science.adc8743](https://doi.org/10.1126/science.adc8743)· tags: `closed-loop`, `robotic-experimentation`, `reaction-optimization`, `suzuki-miyaura`, `machine-learning`

#### 🧪🔓 [Mobile Robotic Chemist Photocatalysis Campaign (Burger et al. 2020)](https://github.com/CooperComputationalCaucus/kuka_optimizer)

Data and code from the University of Liverpool's autonomous mobile robot campaign that ran 688 photocatalytic hydrogen-evolution experiments over 8 days in a 10-variable space, discovering photocatalyst formulations six times more active than baseline. Optimizer, campaign data and workflow openly published.

`experimental`· `open`· 2020 · Other (open source; see repo LICENSE) · GitHub / Bitbucket· tags: `mobile-robot`, `autonomous-experimentation`, `photocatalysis`, `hydrogen-evolution`, `bayesian-optimization`

#### 🧪🔓 [Visual Dataset for Anomaly Detection in Self-Driving Laboratories](https://doi.org/10.6084/m9.figshare.29234663.v2)

Annotated first-person RGB image dataset for process anomaly detection in self-driving labs, captured by a mobile robot and a fixed Franka Emika arm across 11 checkpoints and 27 meta-steps of an automated PDMS synthesis workflow (Tsinghua), with anomaly labels, object annotations and image-text pairs.

`experimental`· `open`· 2025 · CC-BY-4.0 · Figshare· DOI: [10.6084/m9.figshare.29234663](https://doi.org/10.6084/m9.figshare.29234663)· tags: `anomaly-detection`, `computer-vision`, `self-driving-labs`, `robotic-chemistry`, `image-dataset`

<a id="chemistry-molecular-properties"></a>
### Molecular properties

#### 🧪🔓 [CALiSol-23](https://www.nature.com/articles/s41597-024-03575-8)

Curated open dataset of 13,825 experimentally measured ionic-conductivity data points for non-aqueous lithium-battery electrolytes, digitized from 27 publications and covering 14 Li-salts, 38 solvents, varied concentrations, and temperatures. Each point is expert-ratified and source-referenced.

`experimental`· `open`· 2024 · CC-BY-4.0 · GitHub / Sci. Data· DOI: [10.1038/s41597-024-03575-8](https://doi.org/10.1038/s41597-024-03575-8)· tags: `electrolytes`, `ionic-conductivity`, `lithium-batteries`, `solvents`, `measured-properties`

#### 🧪🔓 [ESOL (Delaney Aqueous Solubility)](https://acs.figshare.com/articles/dataset/ESOL_Estimating_Aqueous_Solubility_Directly_from_Molecular_Structure/7944677)

Regression dataset of measured aqueous solubility (log mol/L) for 1,128 organic compounds paired with SMILES structures, from Delaney's ESOL study. A small, widely used experimental solubility benchmark (also part of MoleculeNet).

`experimental`· `open`· 2004 · Unknown · Figshare / MoleculeNet· DOI: [10.1021/ci034243x](https://doi.org/10.1021/ci034243x)· tags: `solubility`, `physical-chemistry`, `regression`, `benchmark`, `logS`

#### 🔀🔓 [FreeSolv](https://github.com/MobleyLab/FreeSolv)

Curated database of experimental and calculated hydration (solvation) free energies for 643 neutral small molecules in water, with SMILES, experimental references, and alchemical MD-calculated values plus input files. Maintained by the Mobley Lab.

`mixed`· `open`· 2014 · CC-BY-3.0 · GitHub· DOI: [10.1007/s10822-014-9747-x](https://doi.org/10.1007/s10822-014-9747-x)· tags: `hydration-free-energy`, `solvation`, `physical-chemistry`, `benchmark`, `molecular-dynamics`

#### 🧪🔓 [The Photoswitch Dataset](https://github.com/Ryan-Rhys/The-Photoswitch-Dataset)

Curated molecular ML benchmark of experimentally measured photophysical properties for azobenzene-type molecular photoswitches, including electronic transition wavelengths, thermal isomerization rates, and photostationary states. Built to accelerate data-driven photoswitch discovery.

`experimental`· `open`· 2022 · MIT · GitHub· DOI: [10.1039/D2SC04306H](https://doi.org/10.1039/D2SC04306H)· tags: `photoswitches`, `azobenzene`, `transition-wavelength`, `photophysics`, `benchmark`

#### 🔀🔓 [ZINC20](https://zinc20.docking.org/)

Free ultralarge database of commercially available (purchasable/make-on-demand) compounds in ready-to-dock 3D formats, exceeding 230 million molecules with fast similarity and substructure search. Curated as a real, orderable chemical catalog; 3D conformers and properties are computed.

`mixed`· `open`· 2020 · Free for use (Other) · self-hosted (UCSF)· DOI: [10.1021/acs.jcim.0c00675](https://doi.org/10.1021/acs.jcim.0c00675)· tags: `virtual-screening`, `purchasable-compounds`, `docking`, `chemical-library`, `ligand-discovery`

<a id="chemistry-optical-properties"></a>
### Optical properties & chromophores

#### 🧪🔓 [ChemFluor](https://figshare.com/articles/dataset/ChemFluor/12110619)

Dataset of solvated organic fluorescent dyes with 4,300+ dye/solvent data points across ~3,000 distinct compounds: absorption wavelength, emission wavelength and PL quantum yield collected from published work. Released with ensemble ML models for photophysical property prediction.

`experimental`· `open`· 2021 · Other (open via Figshare/ACS SI) · Figshare· DOI: [10.1021/acs.jcim.0c01203](https://doi.org/10.1021/acs.jcim.0c01203)· tags: `fluorescence`, `dyes`, `emission-wavelength`, `quantum-yield`, `photophysics`

#### 🧪🔓 [Experimental Database of Optical Properties of Organic Compounds (Deep4Chem)](http://deep4chem.korea.ac.kr/)

Experimental optical-property database of 20,236 data points covering 7,016 unique organic chromophores in 365 solvents/host films, curated from 1,358 papers. Properties include absorption/emission maxima, extinction coefficient, PL quantum yield and fluorescence lifetime.

`experimental`· `open`· 2020 · CC-BY-4.0 · Deep4Chem / Sci. Data SI· DOI: [10.1038/s41597-020-00634-8](https://doi.org/10.1038/s41597-020-00634-8)· tags: `chromophores`, `absorption`, `emission`, `quantum-yield`, `fluorescence`

<a id="chemistry-physical-properties"></a>
### Physical properties

#### 🧪🔓 [Bradley Double Plus Good (Highly Curated) Melting Point Dataset](https://figshare.com/articles/dataset/Jean_Claude_Bradley_Double_Plus_Good_Highly_Curated_and_Validated_Melting_Point_Dataset/1031638)

Highly curated and validated subset of the Bradley Open Melting Point Dataset, retaining ~3,000 measurements where multiple independent values agreed within a narrow tolerance. A high-confidence benchmark for melting-point modeling.

`experimental`· `open`· 2014 · CC0 · Figshare· DOI: [10.6084/m9.figshare.1031638](https://doi.org/10.6084/m9.figshare.1031638)· tags: `melting-point`, `curated`, `benchmark`, `physical-properties`

#### 🧪🔓 [Jean-Claude Bradley Open Melting Point Dataset](https://figshare.com/articles/dataset/Jean_Claude_Bradley_Open_Melting_Point_Datset/1031637)

Open-notebook-science compilation of experimental melting points for organic compounds, ~28,000 measurements (including entries flagged as unreliable) with chemical identifiers. A foundational open dataset for melting-point prediction models.

`experimental`· `open`· 2014 · CC0 · Figshare· DOI: [10.6084/m9.figshare.1031637](https://doi.org/10.6084/m9.figshare.1031637)· tags: `melting-point`, `open-notebook-science`, `physical-properties`, `organic-compounds`

<a id="chemistry-pka"></a>
### pKa / dissociation constants

#### 🧪🔓 [IUPAC Digitized pKa Dataset (Dissociation-Constants)](https://github.com/IUPAC/Dissociation-Constants)

FAIR digitization of critically evaluated aqueous acid dissociation constants from IUPAC reference works, curated by the MIT Green Group. High-confidence set of ~24,200 pKa entries for ~10,600 unique molecules with SMILES/InChI, temperature, method and reliability assessment. The largest FAIR open aqueous pKa resource.

`experimental`· `open`· 2022 · CC-BY-NC-4.0 · GitHub / Zenodo· DOI: [10.5281/zenodo.7236452](https://doi.org/10.5281/zenodo.7236452)· tags: `pka`, `dissociation-constants`, `aqueous`, `iupac`, `fair-data`

#### 🧪🔓 [IUPAC Dissociation Constants in Dipolar Aprotic Solvents (Izutsu)](https://github.com/IUPAC/Dissociation-Constants-Izutsu)

Digitized and curated dataset of acid/base dissociation constants (pKa) measured in dipolar aprotic solvents, transcribed from IUPAC reference data compiled by Kosuke Izutsu. Complements the aqueous IUPAC pKa dataset with non-aqueous ionization constants.

`experimental`· `open`· 2022 · CC-BY-NC-4.0 · GitHub· tags: `pka`, `dissociation-constants`, `aprotic-solvents`, `non-aqueous`, `iupac`

<a id="chemistry-polymers"></a>
### Polymers

#### 🧪🔓 [OpenPoly Polymer Benchmark](https://github.com/WangGroupFDU/Openpoly_benchmark)

Literature-derived benchmark dataset of 3,985 polymer entries (PSMILES-encoded backbones) annotated with up to 26 experimentally measured properties, curated by the Wang group (Fudan) for multi-property polymer ML under data-limited conditions. Ships with baselines for 8 model families; pretrained weights on Zenodo (10.5281/zenodo.15551637).

`experimental`· `open`· 2025 · MIT · GitHub / Zenodo· DOI: [10.1007/s10118-025-3402-y](https://doi.org/10.1007/s10118-025-3402-y)· tags: `polymers`, `property-prediction`, `benchmark`, `machine-learning`, `psmiles`, `literature-mining`

<a id="chemistry-reactions"></a>
### Reaction data

#### 🧪🔓 [Open Reaction Database (ORD)](https://open-reaction-database.org/)

Open-access schema, infrastructure, and centralized repository for structured single-step organic reaction data, spanning benchtop reactions, high-throughput experiments, and flow chemistry. Built to support machine learning for reaction prediction and synthesis planning; contains hundreds of thousands of reactions contributed by academic and industrial groups.

`experimental`· `open`· 2021 · CC-BY-SA-4.0 · GitHub· DOI: [10.1021/jacs.1c09820](https://doi.org/10.1021/jacs.1c09820)· tags: `organic-reactions`, `reaction-yields`, `synthesis`, `open-schema`, `machine-learning`

#### 🧪🔓 [USPTO Chemical Reactions (Lowe)](https://figshare.com/articles/dataset/Chemical_reactions_from_US_patents_1976-Sep2016_/5104873)

Text-mined collection of ~1.8 million organic reactions extracted from US patents (1976-Sep 2016) by Daniel M. Lowe, provided as reaction SMILES/CML. The de facto open reaction corpus underlying most retrosynthesis and reaction-prediction ML models.

`experimental`· `open`· 2017 · CC-BY-4.0 · Figshare· DOI: [10.6084/m9.figshare.5104873.v1](https://doi.org/10.6084/m9.figshare.5104873.v1)· tags: `reaction-smiles`, `patents`, `text-mining`, `retrosynthesis`, `reaction-prediction`

<a id="chemistry-sdl-benchmarks"></a>
### Self-driving-lab benchmarks

#### 🔀🔓 [Atlas: A Brain for Self-Driving Laboratories](https://github.com/aspuru-guzik-group/atlas)

Application-agnostic Python package (Aspuru-Guzik group, U Toronto) providing Gaussian-process Bayesian optimization tailored to self-driving labs: mixed/categorical spaces, multi-objective, constrained, multi-fidelity and meta-learning optimization. Exposes benchmarks via the Olympus interface with example campaign datasets.

`mixed`· `open`· 2025 · MIT · GitHub· tags: `bayesian-optimization`, `self-driving-labs`, `gaussian-processes`, `benchmarking`, `botorch`

#### 🔀🔓 [Olympus Benchmark Suite](https://github.com/aspuru-guzik-group/olympus)

Collection of experiment-derived benchmark surfaces for testing experiment-planning algorithms used in self-driving labs. Includes 20+ datasets from real chemistry/materials campaigns (HPLC method optimization, Suzuki couplings, photobleaching of OPV films, OER catalysts) emulated via probabilistic deep-learning models, plus planning strategies via a Python interface.

`mixed`· `open`· 2021 · MIT · GitHub· tags: `benchmarking`, `bayesian-optimization`, `experiment-planning`, `self-driving-labs`, `surrogate-models`

#### 🔀🔓 [Summit (Reaction Optimisation Benchmarks)](https://github.com/sustainable-processes/summit)

Open-source framework (Lapkin group, Cambridge) with chemically motivated virtual benchmarks for reaction optimization: mechanistic simulations (SnAr) and data-driven ExperimentalEmulator benchmarks trained on published experimental reaction data. Bundles eight ML/DoE optimization strategies for closed-loop testing.

`mixed`· `open`· 2021 · MIT · GitHub / PyPI· tags: `benchmarking`, `reaction-optimization`, `bayesian-optimization`, `machine-learning`, `flow-chemistry`

<a id="chemistry-solubility"></a>
### Solubility

#### 🧪🔓 [AqSolDB](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/OVHAW8)

Curated reference set of aqueous solubility (logS) for 9,982 unique compounds, merged and standardized from 9 publicly available solubility datasets, with validated molecular representations and calculated 2D descriptors. One of the largest open experimental aqueous solubility collections.

`experimental`· `open`· 2019 · CC0-1.0 · Harvard Dataverse / GitHub· DOI: [10.1038/s41597-019-0151-1](https://doi.org/10.1038/s41597-019-0151-1)· tags: `aqueous-solubility`, `logs`, `descriptors`, `qspr`, `smiles`

#### 🧪🔓 [BigSolDB](https://zenodo.org/records/15094979)

Large dataset of experimental solubility values for organic compounds in organic solvents and water across a wide temperature range, extracted from peer-reviewed literature. v2.0 contains 103,944 measurements for 1,448 compounds in 213 solvents from 1,595 articles, with standardized machine-readable structures.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.1038/s41597-025-05559-8](https://doi.org/10.1038/s41597-025-05559-8)· tags: `solubility`, `organic-solvents`, `temperature-dependent`, `smiles`, `literature-curated`

<a id="chemistry-solvation"></a>
### Solvation

#### 🧪🔓 [CombiSolv-Exp](https://github.com/fhvermei/chemprop_solvation)

Experimental solvation free energy database of 10,145 unique solute/solvent combinations compiled from public sources (MNSol, FreeSolv, CompSol, Abraham et al.). Released alongside the computational CombiSolv-QM set for transfer-learning solvation prediction.

`experimental`· `open`· 2021 · MIT (code) / open data · GitHub (SolProp)· tags: `solvation-free-energy`, `solvents`, `transfer-learning`, `solprop`

#### 🧪🔓 [Minnesota Solvation Database (MNSol)](https://comp.chem.umn.edu/mnsol/)

Collection of 3,037 experimental free energies of solvation and transfer free energies for 790 unique solutes in 92 solvents, with gas-phase optimized geometries. A standard reference set for benchmarking solvation models.

`experimental`· `open`· 2012 · Other (free for academic/non-profit; commercial licence required) · Univ. Minnesota DRUM· DOI: [10.13020/3eks-j059](https://doi.org/10.13020/3eks-j059)· tags: `solvation-free-energy`, `transfer-free-energy`, `solvents`, `benchmark`

<a id="chemistry-spectra-exp"></a>
### Experimental spectra (XPS/Raman/XRD)

#### 🧪🔓 [GNPS - Global Natural Products Social Molecular Networking](https://gnps2.org/)

Open community platform and reference spectral library for tandem MS of natural products and metabolomics (UCSD): ~2.9 million experimental MS/MS spectra, community-contributed and curated, supporting molecular networking and continuous reanalysis.

`experimental`· `open`· 2016 · Other (open; varies) · UCSD· tags: `mass-spectrometry`, `ms-ms`, `natural-products`, `molecular-networking`, `metabolomics`

#### 🔀🔓 [HMDB - Human Metabolome Database](https://hmdb.ca/)

Reference resource for human metabolites: HMDB 5.0 holds ~220,945 metabolite entries with >19,700 experimentally measured concentrations plus experimental and predicted MS/NMR reference spectra (mixed: measured concentrations/spectra alongside predicted).

`mixed`· `open`· 2022 · Other (free for non-commercial) · self-hosted (TMIC)· tags: `metabolomics`, `metabolite-concentrations`, `nmr`, `mass-spectrometry`

#### 🔀🔓 [MoNA - MassBank of North America](https://mona.fiehnlab.ucdavis.edu/)

Metadata-centric, auto-curating mass-spectra repository (UC Davis Fiehn Lab) with >200,000 spectral records aggregated from experimental reference libraries, in-silico libraries and user contributions; the experimental portion is the majority (hence mixed).

`mixed`· `open`· 2024 · Varies by record (CC-BY / CC0) · UC Davis / GitHub· tags: `mass-spectrometry`, `metabolomics`, `spectral-library`, `ms-ms`

<a id="chemistry-spectroscopy"></a>
### Spectroscopy

#### 🧪🔓 [MassBank Europe](https://massbank.eu/MassBank/)

Open, FAIR mass-spectral library for identifying small molecules of metabolomics, exposomics, and environmental relevance, holding ~120,000 (mostly high-resolution) experimental spectra for ~18,500 compounds from dozens of contributors. Cross-integrated with PubChem, MoNA, and the EPA CompTox Dashboard.

`experimental`· `open`· 2010 · CC-BY-4.0 / CC0 (varies by record) · self-hosted / GitHub· DOI: [10.1002/jms.1777](https://doi.org/10.1002/jms.1777)· tags: `mass-spectrometry`, `metabolomics`, `spectral-library`, `compound-identification`, `fair-data`

#### 🧪🔓 [NIST Chemistry WebBook (SRD 69)](https://webbook.nist.gov/chemistry/)

NIST Standard Reference Database of evaluated experimental thermochemical, ion-energetics, and spectroscopic data: reaction thermochemistry for >8000 reactions, IR spectra for >16,000 compounds, mass spectra for >33,000 compounds, plus UV/Vis and other data. Free to browse and search.

`experimental`· `open`· 1997 · Other (NIST SRD, free to use) · NIST· tags: `thermochemistry`, `ir-spectra`, `mass-spectra`, `reference-data`, `nist`

#### 🧪🔓 [nmrshiftdb2](https://nmrshiftdb.nmr.uni-koeln.de/)

Open-data, open-source web database of organic structures with assigned experimental NMR chemical-shift lists (13C, 1H, and other nuclei) and metadata, supporting spectrum prediction and structure/substructure search. Data downloadable under an open-content license.

`experimental`· `open`· 2003 · Open content (CC) · self-hosted (Univ. Cologne)· tags: `nmr`, `chemical-shifts`, `spectrum-prediction`, `open-data`, `structure-elucidation`

#### 🧪🔓 [Spectral Database for Organic Compounds (SDBS)](https://sdbs.db.aist.go.jp/)

Free searchable spectral database from Japan's AIST covering ~34,000 organic compounds with six measured spectrum types: EI mass spectra, FT-IR, 1H-NMR, 13C-NMR, laser Raman, and EPR. Access is free but requires agreeing to a usage disclaimer.

`experimental`· `open`· 1997 · Other (free with disclaimer) · AIST (Japan)· tags: `ir`, `nmr`, `mass-spectra`, `raman`, `organic-compounds`

<a id="chemistry-thermochemistry"></a>
### Thermochemistry

#### 🔀🔓 [Active Thermochemical Tables (ATcT)](https://atct.anl.gov/)

Argonne National Laboratory resource deriving accurate, internally consistent enthalpies of formation, Gibbs energies and bond dissociation energies for 3,400+ species by statistically solving a Thermochemical Network of experimental and high-level theoretical determinations. A DOE public reusable data resource.

`mixed`· `open`· 2025 · US Gov / open · Argonne National Laboratory· tags: `thermochemistry`, `enthalpy-of-formation`, `bond-dissociation-energy`, `thermochemical-network`


## Materials

<a id="materials-additive-manufacturing"></a>
### Additive manufacturing

#### 🧪🔓 [NIST AM Bench (Additive Manufacturing Benchmark Test Series)](https://www.nist.gov/ambench)

NIST-led series of highly controlled additive manufacturing benchmark measurements (2018/2022/2025) for validating AM process simulations: laser powder bed fusion of Ni superalloys and stainless steel, DED and polymer AM, with in-situ melt-pool, microstructure, residual strain and mechanical data. Permanently archived for public use with blind modeling challenges.

`experimental`· `open`· 2018 · NIST public data (US Gov) · NIST· tags: `additive-manufacturing`, `laser-powder-bed-fusion`, `benchmark`, `in-situ`, `microstructure`

<a id="materials-alloys"></a>
### Alloys & high-entropy alloys

#### 🧪🔓 [Sustainability indicators in high entropy alloy design: an economic, environmental, and societal database](https://springernature.figshare.com/articles/dataset/Sustainability_indicators_in_high_entropy_alloy_design_an_economic_environmental_and_societal_database/28235162/1)

This dataset contains 9 sustainability indicators for 18 elements (Al, Co, Cr, Cu, Fe, Hf, Mn, Mo, Nb, Ni, Re, Ru, Si, Ta, Ti, V, W, Zr) commonly used in High Entropy Alloys (HEAs).

`experimental`· `open`· 2025 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.28235162.v1](https://doi.org/10.6084/m9.figshare.28235162.v1)

<a id="materials-alloys-mechanical"></a>
### Alloys & mechanical properties

#### 🧪🔓 [Expanded MPEA Dataset (Borg et al., high-entropy alloys)](https://figshare.com/articles/dataset/Expanded_dataset_of_mechanical_properties_and_observed_phases_of_multi-principal_element_alloys/12642953)

Literature-compiled dataset of mechanical properties (hardness, yield strength, elongation) and observed phases for 630 multi-principal element / high-entropy alloys, from papers published through 2020. Machine-readable files on Figshare accompanying a Scientific Data descriptor.

`experimental`· `open`· 2020 · Unknown · Figshare· DOI: [10.1038/s41597-020-00768-9](https://doi.org/10.1038/s41597-020-00768-9)· tags: `high-entropy-alloys`, `mpea`, `mechanical-properties`, `phases`, `literature-curated`

#### 🔀🔑 [NIMS MatNavi (incl. Creep/Fatigue/Corrosion Data Sheets)](https://mits.nims.go.jp/en/)

NIMS Materials Database platform spanning polymer, inorganic and metallic databases, notably the NIMS Structural Materials Data Sheets: decades-long creep, fatigue, corrosion and space-use strength test series on steels and alloys. Free after DICE registration; bulk download prohibited.

`mixed`· `registration`· 2001 · NIMS MatNavi Terms (free registration; bulk download prohibited) · NIMS DICE / MatNavi· tags: `alloys`, `creep`, `fatigue`, `corrosion`, `structural-materials`, `nims`

<a id="materials-batteries"></a>
### Batteries & energy storage

#### 🧪🔓 [A Scalable, Biopolymer-Based Microenvironment for Electrochemical CO2 Conversion to Multicarbon Products with Current Densities Over 2 A/cm2](https://springernature.figshare.com/articles/dataset/A_Scalable_Biopolymer-Based_Microenvironment_for_Electrochemical_CO2_Conversion_to_Multicarbon_Products_with_Current_Densities_Over_2_A_cm2/30630491)

The data consists of experimental results underlying our study. Dataset size: 132 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30630491](https://doi.org/10.6084/m9.figshare.30630491)

#### 🧪🔓 [Additional file 3 of Classification of battery compounds using structure-free Mendeleev encodings](https://springernature.figshare.com/articles/dataset/Additional_file_3_of_Classification_of_battery_compounds_using_structure-free_Mendeleev_encodings/26713166)

Additional file 3. Periodic table csv file to undertake cleaning of the experimental data set, in combination with Additional file 2.

`experimental`· `open`· 2024 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.26713166](https://doi.org/10.6084/m9.figshare.26713166)

#### 🧪🔓 [Battery Materials Database (ChemDataExtractor, Huang & Cole)](https://springernature.figshare.com/articles/Metadata_record_for_A_database_of_battery_materials_auto-generated_using_ChemDataExtractor/12646277/1)

Literature-mined database of experimentally reported battery material properties auto-generated with ChemDataExtractor: ~292,000 records (capacity, voltage, conductivity, Coulombic efficiency, energy density) extracted from ~229,000 papers. Scientific Data (2020).

`experimental`· `open`· 2020 · CC0-1.0 · Figshare· DOI: [10.6084/m9.figshare.12646277.v1](https://doi.org/10.6084/m9.figshare.12646277.v1)· tags: `battery-materials`, `text-mining`, `literature-curated`, `capacity`, `conductivity`

#### 🧪🔓 [BatteryArchive.org](https://batteryarchive.org/)

Public repository for visualization, analysis and comparison of experimental battery cycling data across institutions, aggregating datasets (e.g. from Sandia, NREL, CALCE, Oxford) converted to a common format with cycle- and time-series data. Data are experimental cell-testing measurements.

`experimental`· `open`· 2021 · CC-BY-4.0 · self-hosted· tags: `lithium-ion`, `cycling-data`, `degradation`, `experimental`, `cell-testing`

#### 🧪🔓 [CALCE Battery Datasets (University of Maryland)](https://calce.umd.edu/battery-data)

Open experimental Li-ion battery test data from the Center for Advanced Life Cycle Engineering: continuous full/partial cycling, storage, dynamic driving profiles, OCV and impedance measurements across LCO, LFP and NMC chemistries in multiple form factors. Standard reference data for state estimation and degradation modeling.

`experimental`· `open`· 2011 · Other (free for research; citation requested) · CALCE, Univ. Maryland· tags: `lithium-ion`, `degradation`, `cycling-data`, `state-of-charge`, `state-of-health`

#### 🧪🔓 [Direct Evidence of Metal-Ligand Redox in Li-ion Battery Cathodes](https://springernature.figshare.com/articles/dataset/Direct_Evidence_of_Metal-Ligand_Redox_in_Li-ion_Battery_Cathodes/28915994)

Experimental data from diamond I09 and B07 regarding X-ray absorption and RPES to understand redox mechanisms. Dataset size: 39 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.28915994](https://doi.org/10.6084/m9.figshare.28915994)

#### 🧪🔓 [Flow-Synchronized Ring-shaped Electrochemical Ion Pumping for Redox-Free Desalination without Terminal Electrodes](https://springernature.figshare.com/articles/dataset/Flow-Synchronized_Ring-shaped_Electrochemical_Ion_Pumping_for_Redox-Free_Desalination_without_Terminal_Electrodes/30279262/1)

data for figures in main text and SI. Dataset size: 3 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30279262.v1](https://doi.org/10.6084/m9.figshare.30279262.v1)

#### 🧪🔓 [Hydration entropy of cations regulates chloride ion diffusion during electrochemical chlorine evolution](https://springernature.figshare.com/articles/dataset/Hydration_entropy_of_cations_regulates_chloride_ion_diffusion_during_electrochemical_chlorine_evolution/28158095)

- Numerical data are provided for all Supplementary Figures (.xlsx). - Python scripts (.py) are included in Supplementary Figs. 28 and 29. No proprietary code were used. - All data are managed by T.L. Dataset size: 310 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.28158095](https://doi.org/10.6084/m9.figshare.28158095)

#### 🧪🔓 [Metadata record for: Discharge profile of a zinc-air flow battery at various electrolyte flow rates and discharge currents](https://springernature.figshare.com/articles/Metadata_record_for_Discharge_profile_of_a_zinc-air_flow_battery_at_various_electrolyte_flow_rates_and_discharge_currents/12423878/1)

This dataset contains key characteristics about the data described in the Data Descriptor Discharge profile of a zinc-air flow battery at various electrolyte flow rates and discharge currents. Contents: 1. human readable metadata summary table in CSV format 2. machine readable metadata file in JSON format

`experimental`· `open`· 2020 · CC0-1.0 · figshare· DOI: [10.6084/m9.figshare.12423878.v1](https://doi.org/10.6084/m9.figshare.12423878.v1)

#### 🧪🔓 [Metadata record for: Quantum chemical calculations of lithium-ion battery electrolyte and interphase species](https://springernature.figshare.com/articles/dataset/Metadata_record_for_Quantum_chemical_calculations_of_lithium-ion_battery_electrolyte_and_interphase_species/14915256/1)

This dataset contains key characteristics about the data described in the Data Descriptor Quantum chemical calculations of lithium-ion battery electrolyte and interphase species. Contents: 1. human readable metadata summary table in CSV format 2. machine readable metadata file in JSON format

`experimental`· `open`· 2021 · CC0-1.0 · figshare· DOI: [10.6084/m9.figshare.14915256.v1](https://doi.org/10.6084/m9.figshare.14915256.v1)

#### 🧪🔓 [Molecularly aligned electron-channels for ultrafast-charging practical lithium metal batteries](https://springernature.figshare.com/articles/dataset/Molecularly_aligned_electron-channels_for_ultrafast-charging_practical_lithium_metal_batteries/29257265/1)

Molecular design for ultrafast-charging practical lithium metal batteries. Dataset size: 2 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29257265.v1](https://doi.org/10.6084/m9.figshare.29257265.v1)

#### 🧪🔓 [Molecularly aligned electron-channels for ultrafast-charging practical lithium metal batteries](https://springernature.figshare.com/articles/dataset/Molecularly_aligned_electron-channels_for_ultrafast-charging_practical_lithium_metal_batteries/29257265)

Molecular design for ultrafast-charging practical lithium metal batteries. Dataset size: 2 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29257265](https://doi.org/10.6084/m9.figshare.29257265)

#### 🧪🔓 [Multi-Stage Lithium-Ion Battery Aging Dataset](https://figshare.com/articles/dataset/Multi-Stage_Lithium_Ion_Battery_Aging_Study/25975315/1)

Experimental Li-ion aging dataset built with multiple design-of-experiment methodologies: 280 files (10.3 GB) of cycling/aging measurements across stages and conditions. Deposited with the Scientific Data descriptor (2024).

`experimental`· `open`· 2024 · CC-BY-4.0 · Figshare· DOI: [10.6084/m9.figshare.25975315.v1](https://doi.org/10.6084/m9.figshare.25975315.v1)· tags: `lithium-ion`, `aging`, `cycling-data`, `design-of-experiments`

#### 🧪🔓 [NASA Prognostics Center of Excellence (PCoE) Battery Datasets](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/)

Li-ion battery aging datasets from NASA Ames' Prognostics Data Repository: 18650 cells cycled through charge/discharge and impedance (EIS) profiles at multiple temperatures until 30% capacity fade, plus a randomized battery usage dataset. Widely used benchmarks for state-of-health and remaining-useful-life prediction.

`experimental`· `open`· 2007 · NASA open data (US Gov) · NASA Prognostics Data Repository· tags: `lithium-ion`, `degradation`, `prognostics`, `cycling-data`, `impedance`, `rul`

#### 🧪🔓 [NREL/NASA Battery Failure Databank](https://www.nrel.gov/transportation/battery-failure)

Open database of Li-ion cell abuse-test results (NREL + NASA): hundreds of thermal-runaway tests (nail penetration, thermal, internal short) measured with fractional thermal runaway calorimetry, including heat/mass-ejection fractions and high-speed synchrotron radiography.

`experimental`· `open`· 2024 · CC-BY-NC-ND-4.0 (per publication) · NREL· tags: `lithium-ion`, `thermal-runaway`, `abuse-testing`, `calorimetry`, `safety`

#### 🧪🔓 [OBELiX (Open solid Battery Electrolytes with Li)](https://github.com/NRC-Mila/OBELiX)

Curated dataset of 599 synthesized lithium solid-state electrolyte materials with experimentally measured room-temperature ionic conductivities, space groups, lattice parameters and compositions, including full CIF crystal structures for 321 entries. Hand-curated from the experimental literature by NRC/Mila with a leakage-avoiding train/test split and ML baselines; pip-installable as obelix-data.

`experimental`· `open`· 2025 · CC-BY-4.0 · GitHub· DOI: [10.1039/D5DD00441A](https://doi.org/10.1039/D5DD00441A)· tags: `solid-state-electrolytes`, `ionic-conductivity`, `lithium`, `crystal-structures`, `benchmark`, `machine-learning`

#### 🧪🔓 [Oxford Battery Degradation Dataset 1](https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac)

Long-term ageing tests of 8 Kokam 740 mAh lithium-ion pouch cells cycled in the Howey group lab at Oxford (2015-2016) with periodic characterization; ~254 MB of MATLAB data in the Oxford University Research Archive. A canonical open dataset for battery degradation diagnostics.

`experimental`· `open`· 2017 · ODbL · Oxford University Research Archive· DOI: [10.5287/bodleian:KO2kdmYGg](https://doi.org/10.5287/bodleian:KO2kdmYGg)· tags: `lithium-ion`, `degradation`, `ageing`, `pouch-cells`, `cycling-data`

#### 🧪🔓 [Source Data](https://springernature.figshare.com/articles/dataset/Source_Data/29231339/1)

Experimental battery and electrochemical systems dataset: Source Data. Published alongside a Nature Energy study (2026). Deposited on figshare. Dataset size: 1 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29231339.v1](https://doi.org/10.6084/m9.figshare.29231339.v1)

#### 🧪🔓 [TRI/MIT/Stanford Fast-Charging Battery Dataset (Severson & Attia)](https://data.matr.io/1/)

Widely used experimental dataset of 124 commercial LFP/graphite cells (plus a follow-on 45-cell set) cycled under 72 fast-charging protocols, with cycle lives from ~150 to 2,300 cycles. Provided in CSV/MATLAB/JSON formats by the Toyota Research Institute D3BATT collaboration.

`experimental`· `open`· 2019 · CC-BY-4.0 · self-hosted· DOI: [10.1038/s41560-019-0356-8](https://doi.org/10.1038/s41560-019-0356-8)· tags: `lithium-ion`, `fast-charging`, `cycle-life-prediction`, `experimental`, `lfp`

#### 🧪🔓 [Unveiling Solid Electrolyte Interphase Dynamics in Electrochemical Lithium-Mediated Ammonia Synthesis via Operando Raman Spectroscopy](https://springernature.figshare.com/articles/dataset/Unveiling_Solid_Electrolyte_Interphase_Dynamics_in_Electrochemical_Lithium-Mediated_Ammonia_Synthesis_via_Operando_Raman_Spectroscopy/32262747)

Statistical source data of Raman spectra, LSV, and SEI intensities Statistical source data of Raman spectra, potential, SEI intensities, and FE(NH3) Statistical source data of Raman spectra, potential, SEI intensities, and FE(NH3) Statistical source data of Raman spectra, perchlorate/solvent peak analysis, and SEI intensities Statistical source data of potential, FE(NH3), yield rates, Raman spectr…

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.32262747](https://doi.org/10.6084/m9.figshare.32262747)

<a id="materials-benchmark-ml"></a>
### ML benchmark datasets

#### 🔀🔓 [Matbench](https://matbench.materialsproject.org/)

Curated benchmark suite of 13 supervised ML tasks (312 to ~132,000 samples) for materials property prediction, drawing on 10 DFT-derived and experimental data sources, with an automated public leaderboard. Maintained by the Materials Project.

`mixed`· `open`· 2020 · Other · self-hosted· DOI: [10.1038/s41524-020-00406-3](https://doi.org/10.1038/s41524-020-00406-3)· tags: `machine-learning`, `benchmark`, `property-prediction`, `leaderboard`, `featurization`

#### 🔀🔓 [matminer Datasets](https://hackingmaterials.lbl.gov/matminer/)

Collection of standardized, benchmark-ready materials datasets bundled with the matminer data-mining toolkit and hosted on Figshare, spanning experimental and DFT-derived properties loadable directly as pandas dataframes. Aggregated from published sources for ML benchmarking.

`mixed`· `open`· 2018 · Other · Figshare· DOI: [10.1016/j.commatsci.2018.05.018](https://doi.org/10.1016/j.commatsci.2018.05.018)· tags: `machine-learning`, `datasets`, `data-mining`, `featurization`, `benchmark`

<a id="materials-bioactivity"></a>
### Bioactivity & screening

#### 🧪🔓 [A long-term (2000–2022), high-resolution (0.005°) aboveground biomass dataset of global grasslands](https://zenodo.org/doi/10.5281/zenodo.18044162)

Grasslands are critical to the global carbon cycle and support livestock production, yet long-term, high-resolution global datasets of grassland aboveground biomass (AGB) remain scarce, since existing products are often spatially coarse, temporally discontinuous, or regionally limited. Here, we present a global grassland AGB dataset spanning 2000–2022 at 0.005° spatial resolution.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18044162](https://doi.org/10.5281/zenodo.18044162)

#### 🧪🔓 [A long-term (2000–2022), high-resolution (0.005°) aboveground biomass dataset of global grasslands](https://zenodo.org/doi/10.5281/zenodo.18044163)

Grasslands are critical to the global carbon cycle and support livestock production, yet long-term, high-resolution global datasets of grassland aboveground biomass (AGB) remain scarce, since existing products are often spatially coarse, temporally discontinuous, or regionally limited. Here, we present a global grassland AGB dataset spanning 2000–2022 at 0.005° spatial resolution.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18044163](https://doi.org/10.5281/zenodo.18044163)

#### 🧪🔓 [A secreted endosymbiont protein essential for colonizing host cells](https://springernature.figshare.com/articles/dataset/A_secreted_endosymbiont_protein_essential_for_colonizing_host_cells/32257284)

These data were used to support the results and include data used in bioinformatic analyses, image analyses, and experiments on knockdown of the syeA gene. The tables also include accessions for the data used in analyses.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.32257284](https://doi.org/10.6084/m9.figshare.32257284)

#### 🧪🔓 [A tumour-derived organoid biobank maps cancer gene dependencies](https://springernature.figshare.com/articles/dataset/A_tumour-derived_organoid_biobank_maps_cancer_gene_dependencies/28339340/1)

Additional files needed to reproduce analyses included in this manuscript using CRISPR and genomic data from cancer patient-derived organoids. Dataset size: 287 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.28339340.v1](https://doi.org/10.6084/m9.figshare.28339340.v1)

#### 🧪🔓 [Biophysical and Molecular mechanisms that control active wetting and tissue fluidification in epithelial tissues](https://springernature.figshare.com/articles/dataset/Biophysical_and_Molecular_mechanisms_that_control_active_wetting_and_tissue_fluidification_in_epithelial_tissues/31231516/1)

contains the raw data underlying any graphs and charts presented as Excel file

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31231516.v1](https://doi.org/10.6084/m9.figshare.31231516.v1)

#### 🧪🔓 [Cho and Prabowo-etal-Source data](https://springernature.figshare.com/articles/dataset/Cho_and_Prabowo-etal-Source_data/29264624/1)

Source data for all the results presented in the submitted paper.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29264624.v1](https://doi.org/10.6084/m9.figshare.29264624.v1)

#### 🧪🔓 [Construction of synthetic non-genetic DNA-protein systems in living cells](https://springernature.figshare.com/articles/dataset/Construction_of_synthetic_non-genetic_DNA-protein_systems_in_living_cells/26161684)

The zip file includes raw image data obtained from fluorescence microscopy. Dataset size: 17 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.26161684](https://doi.org/10.6084/m9.figshare.26161684)

#### 🧪🔓 [Construction of synthetic non-genetic DNA-protein systems in living cells](https://springernature.figshare.com/articles/dataset/Construction_of_synthetic_non-genetic_DNA-protein_systems_in_living_cells/26161684/1)

The zip file includes raw image data obtained from fluorescence microscopy. Dataset size: 17 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.26161684.v1](https://doi.org/10.6084/m9.figshare.26161684.v1)

#### 🧪🔓 [Efficient and reversible chirality induction between protein and achiral plasmonic assemblies](https://springernature.figshare.com/articles/dataset/Efficient_and_reversible_chirality_induction_between_protein_and_achiral_plasmonic_assemblies/28429202/1)

Experimental and simulation data. Dataset size: 20 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.28429202.v1](https://doi.org/10.6084/m9.figshare.28429202.v1)

#### 🧪🔓 [Efficient and reversible chirality induction between protein and achiral plasmonic assemblies](https://springernature.figshare.com/articles/dataset/Efficient_and_reversible_chirality_induction_between_protein_and_achiral_plasmonic_assemblies/28429202)

Experimental and simulation data. Dataset size: 20 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.28429202](https://doi.org/10.6084/m9.figshare.28429202)

#### 🧪🔓 [Optimizing biodiversity, multifunctionality and yield when transitioning to organic farming](https://springernature.figshare.com/articles/dataset/Optimizing_biodiversity_multifunctionality_and_yield_when_transitioning_to_organic_farming/27302391)

Experimental biological activity dataset: Optimizing biodiversity, multifunctionality and yield when transitioning to organic farming. Published alongside a Nature Sustainability study (2026). Deposited on figshare.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.27302391](https://doi.org/10.6084/m9.figshare.27302391)

#### 🧪🔓 [Purcell-enhanced two-photon emission from a quantum dot via dark-state biexciton loading](https://springernature.figshare.com/articles/dataset/Purcell-enhanced_two-photon_emission_from_a_quantum_dot_via_dark-state_biexciton_loading/31161145/1)

Source data in .xlsx format for preparing the figures in the main text. Dataset size: 2 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31161145.v1](https://doi.org/10.6084/m9.figshare.31161145.v1)

#### 🧪🔓 [Purcell-enhanced two-photon emission from a quantum dot via dark-state biexciton loading](https://springernature.figshare.com/articles/dataset/Purcell-enhanced_two-photon_emission_from_a_quantum_dot_via_dark-state_biexciton_loading/31161145)

Source data in .xlsx format for preparing the figures in the main text. Dataset size: 2 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31161145](https://doi.org/10.6084/m9.figshare.31161145)

#### 🧪🔓 [Versatile heavy metal ion separation via biological ion-channel-inspired membranes](https://springernature.figshare.com/articles/dataset/Versatile_heavy_metal_ion_separation_via_biological_ion-channel-inspired_membranes/30687980/1)

Raw data of uranium extraction from seawater by TpPa-AO membrane.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30687980.v1](https://doi.org/10.6084/m9.figshare.30687980.v1)

#### 🧪🔓 [Versatile heavy metal ion separation via biological ion-channel-inspired membranes](https://springernature.figshare.com/articles/dataset/Versatile_heavy_metal_ion_separation_via_biological_ion-channel-inspired_membranes/30687980)

Raw data of uranium extraction from seawater by TpPa-AO membrane.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30687980](https://doi.org/10.6084/m9.figshare.30687980)

<a id="materials-catalysis"></a>
### Catalysis

#### 🧪🔓 [CRAFTED: An exploratory database of simulated adsorption isotherms of nanoporous materials](https://zenodo.org/doi/10.5281/zenodo.7106173)

Overview The files in this repository compose the C harge-dependent, R eproducible, A ccessible, F orcefield-dependent, and T emperature-dependent E xploratory D atabase ( CRAFTED ) of adsorption isotherms. Dataset size: 55 MB.

`experimental`· `open`· 2023 · CDLA-SHARING-1.0 · Zenodo· DOI: [10.5281/zenodo.7106173](https://doi.org/10.5281/zenodo.7106173)

#### 🧪🔓 [CRAFTED: An exploratory database of simulated adsorption isotherms of nanoporous materials](https://zenodo.org/doi/10.5281/zenodo.10120180)

Overview The files in this repository compose the C harge-dependent, R eproducible, A ccessible, F orcefield-dependent, and T emperature-dependent E xploratory D atabase ( CRAFTED ) of adsorption isotherms. Dataset size: 55 MB.

`experimental`· `open`· 2023 · CDLA-SHARING-1.0 · Zenodo· DOI: [10.5281/zenodo.10120180](https://doi.org/10.5281/zenodo.10120180)

#### 🧪🔓 [CRAFTED: An exploratory database of simulated adsorption isotherms of nanoporous materials](https://zenodo.org/record/8190237)

Overview The files in this repository compose the C harge-dependent, R eproducible, A ccessible, F orcefield-dependent, and T emperature-dependent E xploratory D atabase ( CRAFTED ) of adsorption isotherms. Dataset size: 55 MB.

`experimental`· `open`· 2023 · CDLA-SHARING-1.0 · Zenodo· DOI: [10.5281/zenodo.8190237](https://doi.org/10.5281/zenodo.8190237)

#### 🧪🔓 [Data associated to "An end-to-end framework for reactivity in heterogeneous catalysis"](https://zenodo.org/doi/10.5281/zenodo.17977395)

This repository contains the results associated to the article "An end-to-end framework for reactivity in heterogeneous catalysis" published in Nature Chemical Engineering (DOI: https://doi.org/10.1038/s44286-026-00361-8 ). Dataset size: 1008 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.17977395](https://doi.org/10.5281/zenodo.17977395)

#### 🧪🔓 [Data associated to "An end-to-end framework for reactivity in heterogeneous catalysis"](https://zenodo.org/doi/10.5281/zenodo.17977394)

This repository contains the results associated to the article "An end-to-end framework for reactivity in heterogeneous catalysis" published in Nature Chemical Engineering (DOI: https://doi.org/10.1038/s44286-026-00361-8 ). Dataset size: 1008 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.17977394](https://doi.org/10.5281/zenodo.17977394)

#### 🧪🔓 [Data for the publication "Quantum Fisher information in a strange metal"](https://zenodo.org/doi/10.5281/zenodo.19349955)

Datasets underlying the figures in the publication "Quantum Fisher information in a strange metal"

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.19349955](https://doi.org/10.5281/zenodo.19349955)

#### 🧪🔓 [Data for the publication "Quantum Fisher information in a strange metal"](https://zenodo.org/doi/10.5281/zenodo.19349954)

Datasets underlying the figures in the publication "Quantum Fisher information in a strange metal"

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.19349954](https://doi.org/10.5281/zenodo.19349954)

#### 🧪🔓 [Data set for: Terahertz Time-Domain imaging of feet of diabetic and non-diabetic patients](https://figshare.com/articles/dataset/Data_set_for_Terahertz_Time-Domain_imaging_of_feet_of_diabetic_and_non-diabetic_patients/31052176/9)

This respository contains Terahertz Time-Domain imaging dataset of human plantar surface of the feet acquired from type-2 diabetic and non-diabetic volunteers. The measurements were collected in reflection geometry using a fiber-coupled terahertz system and include spatially resolved terahertz waveforms obtained through raster scanning of both feet soles.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31052176.v9](https://doi.org/10.6084/m9.figshare.31052176.v9)

#### 🧪🔓 [Dataset for the article 'Controlling hydrocarbon chain growth and degree of branching in CO2 electroreduction on fluorine-doped nickel catalysts' (DOI](https://zenodo.org/doi/10.5281/zenodo.15300305)

Dataset for the article 'Controlling hydrocarbon chain growth and degree of branching in CO2 electroreduction on fluorine-doped nickel catalysts' (Nature Catalysis; https://www.nature.com/articles/s41929-025-01370-1). Dataset size: 2 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.15300305](https://doi.org/10.5281/zenodo.15300305)

#### 🧪🔓 [Dataset for the article 'Controlling hydrocarbon chain growth and degree of branching in CO2 electroreduction on fluorine-doped nickel catalysts' (DOI](https://zenodo.org/doi/10.5281/zenodo.15300306)

Dataset for the article 'Controlling hydrocarbon chain growth and degree of branching in CO2 electroreduction on fluorine-doped nickel catalysts' (Nature Catalysis; https://www.nature.com/articles/s41929-025-01370-1). Dataset size: 2 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.15300306](https://doi.org/10.5281/zenodo.15300306)

#### 🧪🔓 [Dataset: Strain boosts propanol electrosynthesis from CO](https://zenodo.org/doi/10.5281/zenodo.18183751)

The two-step electroreduction of CO 2 to CO followed by CO to multi-carbon products is a promising alternative to the direct CO 2 electroreduction for both efficiency and stability. The catalyst features which control selectivity in CO electroreduction (CORR) remain unclear, which limits further advancement in the overall performance.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18183751](https://doi.org/10.5281/zenodo.18183751)

#### 🧪🔓 [Dataset: Strain boosts propanol electrosynthesis from CO](https://zenodo.org/doi/10.5281/zenodo.18183752)

The two-step electroreduction of CO 2 to CO followed by CO to multi-carbon products is a promising alternative to the direct CO 2 electroreduction for both efficiency and stability. The catalyst features which control selectivity in CO electroreduction (CORR) remain unclear, which limits further advancement in the overall performance.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18183752](https://doi.org/10.5281/zenodo.18183752)

#### 🧪🔓 [De novo design and evolution of an artificial metathase for cytoplasmic olefin metathesis.](https://zenodo.org/doi/10.5281/zenodo.17647531)

Data underlying the figures/tables of the publication: Zou, Z., Kalvet, I., Lozhkin, B. et al. De novo design and evolution of an artificial metathase for cytoplasmic olefin metathesis. Nat Catal (2025). https://doi.org/10.1038/s41929-025-01436-0. Dataset size: 23 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.17647531](https://doi.org/10.5281/zenodo.17647531)

#### 🧪🔓 [De novo design and evolution of an artificial metathase for cytoplasmic olefin metathesis.](https://zenodo.org/doi/10.5281/zenodo.17647530)

Data underlying the figures/tables of the publication: Zou, Z., Kalvet, I., Lozhkin, B. et al. De novo design and evolution of an artificial metathase for cytoplasmic olefin metathesis. Nat Catal (2025). https://doi.org/10.1038/s41929-025-01436-0. Dataset size: 23 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.17647530](https://doi.org/10.5281/zenodo.17647530)

#### 🧪🔓 [Direct evaluation of coherence in a Magnon Bose-Einstein Condensate](https://zenodo.org/doi/10.5281/zenodo.20135543)

The spontaneous emergence of coherence is a defining feature of multi-body quantum systems, underlying phenomena from superconductivity to quantum information processing. While Bose-Einstein condensates (BECs) provide a unique setting for exploring this process, yet direct observation of how a condensate acquires a coherent global phase has remained out of reach.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20135543](https://doi.org/10.5281/zenodo.20135543)

#### 🧪🔓 [Direct evaluation of coherence in a Magnon Bose-Einstein Condensate](https://zenodo.org/doi/10.5281/zenodo.20135542)

The spontaneous emergence of coherence is a defining feature of multi-body quantum systems, underlying phenomena from superconductivity to quantum information processing. While Bose-Einstein condensates (BECs) provide a unique setting for exploring this process, yet direct observation of how a condensate acquires a coherent global phase has remained out of reach.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20135542](https://doi.org/10.5281/zenodo.20135542)

#### 🧪🔓 [Emergent Harmonics in Josephson Tunnel Junctions Due to Series Inductance](https://springernature.figshare.com/articles/dataset/Emergent_Harmonics_in_Josephson_Tunnel_Junctions_Due_to_Series_Inductance/29647922/1)

Flux-biased spectroscopy data for fourteeen qubits. Dataset size: 21 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29647922.v1](https://doi.org/10.6084/m9.figshare.29647922.v1)

#### 🧪🔓 [Full-Spectrum Photocatalyst for Radical-Regulated Selective Methane Conversion](https://springernature.figshare.com/articles/dataset/Full-Spectrum_Photocatalyst_for_Radical-Regulated_Selective_Methane_Conversion/28091891/1)

Raw data of the figures conrresponding to the article entitled: Full-Spectrum Photocatalyst for Radical-Regulated Selective Methane Conversion. Dataset size: 15 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.28091891.v1](https://doi.org/10.6084/m9.figshare.28091891.v1)

#### 🧪🔓 [High-resolution multimodal microclimate dataset: thermal, radiative and physiological measurements of a mature linden tree (tilia cordata)](https://zenodo.org/doi/10.5281/zenodo.18039731)

Multi-sensor microclimate dataset from a mature urban linden tree ( Tilia cordata ) collected over 72 hours in June 2025 near Grünstadt, Germany. Dataset size: 7.4 GB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18039731](https://doi.org/10.5281/zenodo.18039731)

#### 🧪🔓 [High-resolution multimodal microclimate dataset: thermal, radiative and physiological measurements of a mature linden tree (tilia cordata)](https://zenodo.org/doi/10.5281/zenodo.18039730)

Multi-sensor microclimate dataset from a mature urban linden tree ( Tilia cordata ) collected over 72 hours in June 2025 near Grünstadt, Germany. Dataset size: 7.4 GB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18039730](https://doi.org/10.5281/zenodo.18039730)

#### 🧪🔓 [Multi-applied field modulation enables efficient multielectron molecular CO2 reduction in strong acid](https://springernature.figshare.com/articles/dataset/Multi-applied_field_modulation_enables_efficient_multielectron_molecular_CO2_reduction_in_strong_acid/29591042/1)

Source data for manuscript in the main text. Dataset size: 4 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29591042.v1](https://doi.org/10.6084/m9.figshare.29591042.v1)

#### 🔀🔓 [Open Catalyst Experiments 2024 (OCx24)](https://fair-chem.github.io/core/datasets/ocx24.html)

First large open experimental electrocatalyst database from Meta FAIR, VSParticle and the University of Toronto: ~572 catalyst samples synthesized by wet-chemistry and dry spark-ablation and tested for HER and CO2 reduction, with XRF, XRD and electrochemical measurements, plus paired DFT screening data to bridge models and experiment.

`mixed`· `open`· 2024 · CC-BY-4.0 (data), MIT (code) · GitHub (FAIR-Chem/fairchem)· DOI: [10.48550/arXiv.2411.11783](https://doi.org/10.48550/arXiv.2411.11783)· tags: `electrocatalysis`, `high-throughput`, `hydrogen-evolution`, `co2-reduction`, `xrd`, `robotic-synthesis`

#### 🧪🔓 [Predictive model for the discovery of sinter-resistant supports for metallic nanoparticle catalysts by interpretable machine learning](https://zenodo.org/doi/10.5281/zenodo.16878886)

Neural Network Potential-driven Molecular Dynamics Database for Catalyst Support Materials This database contains Neural Network Potential driven Molecular Dynamics (NN-MD) simulation results for 3nm Pt nanoparticle supported on various metal oxides supports at 800 °C for 500 ps and high-throughput screening results for catalyst support materials, organized into three datasets for comprehensive an…

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.16878886](https://doi.org/10.5281/zenodo.16878886)

#### 🧪🔓 [Predictive model for the discovery of sinter-resistant supports for metallic nanoparticle catalysts by interpretable machine learning](https://zenodo.org/doi/10.5281/zenodo.16878887)

Neural Network Potential-driven Molecular Dynamics Database for Catalyst Support Materials This database contains Neural Network Potential driven Molecular Dynamics (NN-MD) simulation results for 3nm Pt nanoparticle supported on various metal oxides supports at 800 °C for 500 ps and high-throughput screening results for catalyst support materials, organized into three datasets for comprehensive an…

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.16878887](https://doi.org/10.5281/zenodo.16878887)

#### 🧪🔓 [Resolving Non-Covalent Interactions Between Surface Hydroxyl on Cu and Interfacial Water in Alkaline CO Electroreduction](https://springernature.figshare.com/articles/dataset/Resolving_Non-Covalent_Interactions_Between_Surface_Hydroxyl_on_Cu_and_Interfacial_Water_in_Alkaline_CO_Electroreduction/28531955/1)

Original datas for the manuscript. Dataset size: 1 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.28531955.v1](https://doi.org/10.6084/m9.figshare.28531955.v1)

#### 🧪🔓 [Resolving Non-Covalent Interactions Between Surface Hydroxyl on Cu and Interfacial Water in Alkaline CO Electroreduction](https://springernature.figshare.com/articles/dataset/Resolving_Non-Covalent_Interactions_Between_Surface_Hydroxyl_on_Cu_and_Interfacial_Water_in_Alkaline_CO_Electroreduction/28531955)

Original datas for the manuscript. Dataset size: 1 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.28531955](https://doi.org/10.6084/m9.figshare.28531955)

#### 🧪🔓 [Single cell transcriptome profiling of peripheral blood mononuclear cells in Guillain–Barré syndrome patients](https://springernature.figshare.com/articles/dataset/Single_cell_transcriptome_profiling_of_peripheral_blood_mononuclear_cells_in_Guillain_Barr_syndrome_patients/31975524/1)

We collected a total of 5 human peripheral blood mononuclear cells and performed single-cell RNAseq sequencing. Among them, PBMC1, PBMC2, and PBMC3 were data from three GBS patients, while HPBMC1 and HPBMC2 were data from two healthy controls matched for age and gender. Dataset size: 3.9 GB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31975524.v1](https://doi.org/10.6084/m9.figshare.31975524.v1)

#### 🧪🔓 [Sub-nanometer Alloyed Clusters Sustain High Productivity in Propane Dehydrogenation](https://springernature.figshare.com/articles/dataset/Sub-nanometer_Alloyed_Clusters_Sustain_High_Productivity_in_Propane_Dehydrogenation/31743865/1)

Propane dehydrogenation (PDH) processes typically operate at low weight-hourly space velocities (WHSV) about 10 h⁻¹ to ensure catalyst stability, limiting propylene productivity to around 0.1 molC3H6·gcatalyst-1·h-1. Here, we report that controlling the formation of sub-nm PtSn alloyed clusters encapsulated in silicalite-1 affords a catalyst that can sustain high propylene productivities.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31743865.v1](https://doi.org/10.6084/m9.figshare.31743865.v1)

<a id="materials-crystallography"></a>
### Crystallography

#### 🧪🔓 [American Mineralogist Crystal Structure Database (AMCSD)](https://www.rruff.net/amcsd/)

Freely accessible database of experimentally determined crystal structures of minerals and related materials, drawn from American Mineralogist, The Canadian Mineralogist, European Journal of Mineralogy and other sources. Searchable by mineral, chemistry, cell parameters and symmetry; served via the RRUFF Project.

`experimental`· `open`· 2003 · Other · self-hosted· tags: `minerals`, `crystal-structures`, `cif`, `experimental`, `rruff`

#### 🧪🔓 [Crystallography Open Database (COD)](https://www.crystallography.net/cod/)

Open-access collection of over 520,000 experimentally determined crystal structures of organic, inorganic, metal-organic compounds and minerals (excluding biopolymers), stored as CIF files. Structures are curated from the published literature and community contributions. Used by both the materials and chemistry communities.

`experimental`· `open`· 2012 · CC0 · self-hosted· DOI: [10.1093/nar/gkr900](https://doi.org/10.1093/nar/gkr900)· tags: `crystal-structures`, `cif`, `experimental`, `open-data`, `minerals`, `cross-domain`

<a id="materials-data-infrastructure"></a>
### Data infrastructure & portals

#### 🔀🔓 [Foundry-ML](https://foundry-ml.org/)

Platform and Python API for discovering and loading ML-ready datasets in materials science and chemistry, built on the Materials Data Facility. Serves curated datasets with rich schemas, standardized formats, train/test splits and automatic citation generation.

`mixed`· `open`· 2024 · MIT (software); dataset licenses vary · Foundry-ML / MDF· tags: `ml-ready-datasets`, `materials-science`, `chemistry`, `python-api`, `fair-data`

#### 🔀🔓 [Materials Data Facility (MDF)](https://www.materialsdatafacility.org/)

NIST/CHiMaD-supported data publication and discovery service (UChicago/Globus, NCSA) hosting and indexing materials-science datasets — over 80 TB across ~1,000 datasets, experimental and computational — with citable DOIs, automated metadata extraction and programmatic access.

`mixed`· `open`· 2016 · Other (varies by dataset) · MDF (Globus/NCSA)· tags: `repository`, `data-publication`, `data-discovery`, `fair-data`, `globus`

#### 🧪🔓 [PARADIM Data Collective](https://data.paradim.org/)

Open data portal of the NSF Materials Innovation Platform PARADIM (Cornell/Johns Hopkins), publishing publication-associated datasets from bulk and thin-film crystal growth (MBE, floating zone), electron microscopy, ARPES and theory; datasets browsable publicly and citable with minted DOIs.

`experimental`· `open`· 2019 · Other (varies by dataset) · PARADIM (SciServer)· tags: `crystal-growth`, `thin-films`, `mbe`, `electron-microscopy`, `open-data-portal`

<a id="materials-electrocatalysis-exp"></a>
### Electrocatalysis (experimental HTE)

#### 🧪🔓 [In-Situ PEM Fuel Cell Cathode Catalyst Degradation Dataset](https://figshare.com/articles/dataset/_b_In-Situ_Characterization_of_Cathode_Catalyst_Degradation_in_PEM_Fuel_Cells_b_/25450177/1)

Experimental in-situ characterization of cathode catalyst degradation in proton-exchange-membrane fuel cells: 51 files (851 MB) of electrochemical and characterization data with analysis scripts. Scientific Data descriptor (2024).

`experimental`· `open`· 2024 · CC-BY-4.0 · Figshare· DOI: [10.6084/m9.figshare.25450177.v1](https://doi.org/10.6084/m9.figshare.25450177.v1)· tags: `pem-fuel-cell`, `catalyst-degradation`, `in-situ`, `electrochemistry`

#### 🧪🔓 [Materials Experiment and Analysis Database (MEAD, Caltech HTE/JCAP)](https://solarfuelshub.org/materials-experiment-and-analysis-database)

Raw data, metadata and distilled property/performance metrics from millions of high-throughput materials synthesis and (opto)electrochemical characterization experiments by the Joint Center for Artificial Photosynthesis for solar-fuels discovery — roughly 17 million material states including large OER electrocatalyst composition libraries. Downloadable via CaltechDATA with provenance.

`experimental`· `open`· 2019 · Other (varies by record; open download) · CaltechDATA· tags: `high-throughput-experimentation`, `oer`, `electrocatalysis`, `solar-fuels`, `metal-oxides`, `provenance`

<a id="materials-general-properties"></a>
### General materials properties

#### 🧪🔓 [A quantum resistance memristor for an intrinsically traceable International System of Units standard - Dataset](https://zenodo.org/doi/10.5281/zenodo.16788655)

This is the dataset of "A quantum resistance memristor for an intrinsically traceable International System of Units standard", Nature Nanotechnology, DOI: 10.1038/s41565-025-02037-5, (2025). This work was supported by the European project MEMQuD, code 20FUN06, funder ID: 10.13039/100014132. Dataset size: 2 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.16788655](https://doi.org/10.5281/zenodo.16788655)

#### 🧪🔓 [A quantum resistance memristor for an intrinsically traceable International System of Units standard - Dataset](https://zenodo.org/doi/10.5281/zenodo.16788654)

This is the dataset of "A quantum resistance memristor for an intrinsically traceable International System of Units standard", Nature Nanotechnology, DOI: 10.1038/s41565-025-02037-5, (2025). This work was supported by the European project MEMQuD, code 20FUN06, funder ID: 10.13039/100014132. Dataset size: 2 MB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.16788654](https://doi.org/10.5281/zenodo.16788654)

#### 🧪🔓 [Agricultural Workforce as a Potential Bottleneck of Future Cropland Supply](https://springernature.figshare.com/articles/dataset/Agricultural_Workforce_as_a_Potential_Bottleneck_of_Future_Cropland_Supply/29354609/1)

Here, the main manuscript of a research article is presented, along with supplementary material containing additional figures and tables, and a cover letter introducing the research. Dataset size: 3 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29354609.v1](https://doi.org/10.6084/m9.figshare.29354609.v1)

#### 🧪🔓 [AllpaDB Dataset: Harmonized soil legacy and research data from Peru](https://zenodo.org/doi/10.5281/zenodo.20077332)

This dataset are derived from from historical soil studies conducted throughout Peru. Although soil studies have been carried out in the country since 1962, this information lacked a digital archive and a structured database. This limitation hindered its usefulness for effective land management, scientific research, and education.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20077332](https://doi.org/10.5281/zenodo.20077332)

#### 🧪🔓 [AllpaDB Dataset: Harmonized soil legacy and research data from Peru](https://zenodo.org/doi/10.5281/zenodo.20077331)

This dataset are derived from from historical soil studies conducted throughout Peru. Although soil studies have been carried out in the country since 1962, this information lacked a digital archive and a structured database. This limitation hindered its usefulness for effective land management, scientific research, and education.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20077331](https://doi.org/10.5281/zenodo.20077331)

#### 🧪🔓 [An iontronic reservoir for highly robust neuromorphic prosthesis](https://springernature.figshare.com/articles/dataset/An_iontronic_reservoir_for_highly_robust_neuromorphic_prosthesis/31153141)

This dataset contains the underlying source data for the figures presented in the manuscript. Source_data.xlsx: This spreadsheet includes the numerical data and statistical analysis results for the Main Figures and relevant Extended Data Figures. MATLAB Files (.mat): Due to file size constraints, the large raw datasets corresponding to the Extended Data Figures (e.g., Extended Data Fig. 3, Fig.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31153141](https://doi.org/10.6084/m9.figshare.31153141)

#### 🧪🔓 [An iontronic reservoir for highly robust neuromorphic prosthesis](https://springernature.figshare.com/articles/dataset/An_iontronic_reservoir_for_highly_robust_neuromorphic_prosthesis/31153141/1)

This dataset contains the underlying source data for the figures presented in the manuscript. Source_data.xlsx: This spreadsheet includes the numerical data and statistical analysis results for the Main Figures and relevant Extended Data Figures. MATLAB Files (.mat): Due to file size constraints, the large raw datasets corresponding to the Extended Data Figures (e.g., Extended Data Fig. 3, Fig.…

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31153141.v1](https://doi.org/10.6084/m9.figshare.31153141.v1)

#### 🧪🔓 [Aneuploidy selects for the acquisition of driver genes in breast cancer](https://springernature.figshare.com/articles/dataset/Aneuploidy_selects_for_the_acquisition_of_driver_genes_in_breast_cancer/32144932/1)

Gene-level copy number calls from whole genome sequencing of mouse tumors. Dataset size: 266 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.32144932.v1](https://doi.org/10.6084/m9.figshare.32144932.v1)

#### 🧪🔓 [Charge-Triggered Switching Mechanism in Selenium Select Enabling Ultralow Leakage-Current](https://springernature.figshare.com/articles/dataset/Charge-Triggered_Switching_Mechanism_in_Selenium_Select_Enabling_Ultralow_Leakage-Current/31047436)

This dataset contains the minimum source data for most figures presented in the accompanying manuscript titled "Charge-Triggered Switching Mechanism in Selenium Selector Enabling Ultralow Leakage-Current". Individual data files corresponding to each main figure. Each file contains the raw or primary processed data used to generate the specific panels within that figure.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31047436](https://doi.org/10.6084/m9.figshare.31047436)

#### 🧪🔓 [Charge-Triggered Switching Mechanism in Selenium Select Enabling Ultralow Leakage-Current](https://springernature.figshare.com/articles/dataset/Charge-Triggered_Switching_Mechanism_in_Selenium_Select_Enabling_Ultralow_Leakage-Current/31047436/1)

This dataset contains the minimum source data for most figures presented in the accompanying manuscript titled "Charge-Triggered Switching Mechanism in Selenium Selector Enabling Ultralow Leakage-Current". Individual data files corresponding to each main figure. Each file contains the raw or primary processed data used to generate the specific panels within that figure. The detailed…. Dataset size: 11 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31047436.v1](https://doi.org/10.6084/m9.figshare.31047436.v1)

#### 🔀🔑 [Citrination / Open Citrination (Citrine Informatics)](https://citrination.com)

Large open materials and chemicals data platform aggregating experimental property data contributed by users and auto-extracted from the literature, alongside computational data. The public platform has been decommissioned but datasets remain accessible via their DOIs/URLs.

`mixed`· `registration`· 2016 · Unknown · self-hosted· tags: `experimental-properties`, `literature-extraction`, `informatics`, `property-data`

#### 🧪🔓 [County-Level Environmental and Social Influences on EPA Criminal Prosecutions in the United States](https://springernature.figshare.com/articles/dataset/County-Level_Environmental_and_Social_Influences_on_EPA_Criminal_Prosecutions_in_the_United_States/26180530)

These data can be used to reproduce Extended Data Tables 1-3, Supplementary Tables 1-4 and Figures 1 and 2 in the submitted manuscript, "Social factors shape the geographic pattern of U.S. environmental crime prosecutions". The files contain the Final Data in Stata format (.dta) and .csv format, Stata code (.do) for reproduction of the tables and figures, a .

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.26180530](https://doi.org/10.6084/m9.figshare.26180530)

#### 🧪🔓 [County-Level Environmental and Social Influences on EPA Criminal Prosecutions in the United States](https://springernature.figshare.com/articles/dataset/County-Level_Environmental_and_Social_Influences_on_EPA_Criminal_Prosecutions_in_the_United_States/26180530/1)

These data can be used to reproduce Extended Data Tables 1-3, Supplementary Tables 1-4 and Figures 1 and 2 in the submitted manuscript, "Social factors shape the geographic pattern of U.S. environmental crime prosecutions". The files contain the Final Data in Stata format (.dta) and .csv format, Stata code (.do) for reproduction of the tables and figures, a .xls codebook with a description of…. Dataset size: 2 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.26180530.v1](https://doi.org/10.6084/m9.figshare.26180530.v1)

#### 🧪🔓 [Crossover of quasi-localized dynamics and diffusion in supercooled liquids](https://springernature.figshare.com/articles/dataset/Crossover_of_quasi-localized_dynamics_and_diffusion_in_supercooled_liquids/31814242/1)

This figshare repository contains the raw data used to generate Figures 1–4 of the associated publication: "At the crossover between quasi-localized dynamics and diffusion in deeply supercooled liquids." Repository structure The repository is organized into folders corresponding to the individual figures and subplots.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31814242.v1](https://doi.org/10.6084/m9.figshare.31814242.v1)

#### 🧪🔓 [Crossover of quasi-localized dynamics and diffusion in supercooled liquids](https://springernature.figshare.com/articles/dataset/Crossover_of_quasi-localized_dynamics_and_diffusion_in_supercooled_liquids/31814242)

This figshare repository contains the raw data used to generate Figures 1–4 of the associated publication: "At the crossover between quasi-localized dynamics and diffusion in deeply supercooled liquids." Repository structure The repository is organized into folders corresponding to the individual figures and subplots. Each folder contains the raw data used for the preparation of the relevant…

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31814242](https://doi.org/10.6084/m9.figshare.31814242)

#### 🧪🔓 [Data and code for: The dual impact of trade on the water-energy-food nexus globally](https://springernature.figshare.com/articles/dataset/Data_and_code_for_The_dual_impact_of_trade_on_the_water-energy-food_nexus_globally/29155031)

This contains all the necessary data and code used in the study by Yin et al. (2026) for data preprocessing, network analysis, counterfactual scenario analysis, and machine learning. Dataset size: 7 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29155031](https://doi.org/10.6084/m9.figshare.29155031)

#### 🧪🔓 [Data files associated with A Dependency Map Enhanced with Next-Generation 3D Cancer Models](https://springernature.figshare.com/articles/dataset/Data_files_associated_with_A_Dependency_Map_Enhanced_with_Next-Generation_3D_Cancer_Models/29472362)

This file set includes metadata files (6 files) and analysis result files (29 files) associated with Neiswender, Maffa, Brenan et al. "A Dependency Map Enhanced with Next-Generation 3D Cancer Models" (Nature, 2026). The custom analysis code used for generating these results is available at a GitHub repository (https://github.com/broadinstitute/DepMap-NextGen-Public). In addition, raw profiling…. Dataset size: 106 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29472362](https://doi.org/10.6084/m9.figshare.29472362)

#### 🧪🔓 [Data for: An entangling gate for dual-rail erasure qubits](https://zenodo.org/doi/10.5281/zenodo.20433753)

Datasets for characterization and benchmarking experiments for manuscript: An entangling gate for dual-rail erasure qubits See README.md for description for each dataset. Dataset size: 0 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20433753](https://doi.org/10.5281/zenodo.20433753)

#### 🧪🔓 [Data for: An entangling gate for dual-rail erasure qubits](https://zenodo.org/doi/10.5281/zenodo.20433754)

Datasets for characterization and benchmarking experiments for manuscript: An entangling gate for dual-rail erasure qubits See README.md for description for each dataset. Dataset size: 0 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20433754](https://doi.org/10.5281/zenodo.20433754)

#### 🧪🔓 [Data used in The Linkage between Microbial Community Dynamics and Urbanization Age](https://springernature.figshare.com/articles/dataset/Data_used_in_The_Linkage_between_Microbial_Community_Dynamics_and_Urbanization_Age/24680199)

Raw data used in this study. Full information about data and code is available at https://doi.org/10.6084/m9.figshare.24782817. Dataset size: 61 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.24680199](https://doi.org/10.6084/m9.figshare.24680199)

#### 🧪🔓 [Data used in The Linkage between Microbial Community Dynamics and Urbanization Age](https://springernature.figshare.com/articles/dataset/Data_used_in_The_Linkage_between_Microbial_Community_Dynamics_and_Urbanization_Age/24680199/1)

Raw data used in this study. Full information about data and code is available at https://doi.org/10.6084/m9.figshare.24782817. Dataset size: 61 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.24680199.v1](https://doi.org/10.6084/m9.figshare.24680199.v1)

#### 🧪🔓 [Dataset](https://springernature.figshare.com/articles/dataset/Dataset/30670601)

Dataset of Pypsa-China, an open optimisation model of the Chinese energy system, with aluminum asset data added. Dataset size: 106 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30670601](https://doi.org/10.6084/m9.figshare.30670601)

#### 🧪🔓 [Dataset](https://springernature.figshare.com/articles/dataset/Dataset/30670601/1)

Dataset of Pypsa-China, an open optimisation model of the Chinese energy system, with aluminum asset data added. Dataset size: 106 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30670601.v1](https://doi.org/10.6084/m9.figshare.30670601.v1)

#### 🧪🔓 [Detecting Linear Dichroism with Atomic Resolution](https://springernature.figshare.com/articles/dataset/Detecting_Linear_Dichroism_with_Atomic_Resolution/31998285)

Source data for Detecting Linear Dichroism with Atomic Resolution. Dataset size: 36 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31998285](https://doi.org/10.6084/m9.figshare.31998285)

#### 🧪🔓 [Detecting Linear Dichroism with Atomic Resolution](https://springernature.figshare.com/articles/dataset/Detecting_Linear_Dichroism_with_Atomic_Resolution/31998285/1)

Source data for Detecting Linear Dichroism with Atomic Resolution. Dataset size: 36 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31998285.v1](https://doi.org/10.6084/m9.figshare.31998285.v1)

#### 🧪🔓 [Electron-Phonon Coupling and Symmetry-Breaking in Superconducting Oxide Interfaces Near Ferroelectric Quantum Criticality](https://springernature.figshare.com/articles/dataset/Electron-Phonon_Coupling_and_Symmetry-Breaking_in_Superconducting_Oxide_Interfaces_Near_Ferroelectric_Quantum_Criticality/32324148/1)

Source data for Electron-Phonon Coupling and Symmetry-Breaking in Superconducting Oxide Interfaces Near Ferroelectric Quantum Criticality. Dataset size: 354 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.32324148.v1](https://doi.org/10.6084/m9.figshare.32324148.v1)

#### 🧪🔓 [Generating extended foldamer dye stacks and unravelling their evolving exciton dynamics](https://zenodo.org/doi/10.5281/zenodo.15690639)

Additional Data to report: https://doi.org/10.1038/s41557-026-02082-0 In biomacromolecules, many amino acids or nucleotides are needed to obtain defined secondary structures and concomitant advanced functionalities. Dataset size: 7 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.15690639](https://doi.org/10.5281/zenodo.15690639)

#### 🧪🔓 [Generating extended foldamer dye stacks and unravelling their evolving exciton dynamics](https://zenodo.org/doi/10.5281/zenodo.15690640)

Additional Data to report: https://doi.org/10.1038/s41557-026-02082-0 In biomacromolecules, many amino acids or nucleotides are needed to obtain defined secondary structures and concomitant advanced functionalities. Dataset size: 7 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.15690640](https://doi.org/10.5281/zenodo.15690640)

#### 🧪🔓 [HCMI model-tumour DNA methylation beta matrices, restricted to the flagship epigenetic-concordance probe sets](https://zenodo.org/doi/10.5281/zenodo.21838909)

What this is. Per-cancer-type DNA methylation beta-value matrices for Human Cancer Models Initiative (HCMI) patient-derived cancer models and their matched parental tumours, restricted to the probe sets used by the HCMI flagship paper's epigenetic-concordance analysis. 23 Parquet files, one per cancer type, 42.3 MB total. Each file is probes (rows) x samples (columns), Float32, with a leading…

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.21838909](https://doi.org/10.5281/zenodo.21838909)

#### 🧪🔓 [HCMI model-tumour DNA methylation beta matrices, restricted to the flagship epigenetic-concordance probe sets](https://zenodo.org/doi/10.5281/zenodo.21838908)

What this is. Per-cancer-type DNA methylation beta-value matrices for Human Cancer Models Initiative (HCMI) patient-derived cancer models and their matched parental tumours, restricted to the probe sets used by the HCMI flagship paper's epigenetic-concordance analysis. 23 Parquet files, one per cancer type, 42.3 MB total. Each file is probes (rows) x samples (columns), Float32, with a leading…

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.21838908](https://doi.org/10.5281/zenodo.21838908)

#### 🔀🔓 [Materials Cloud Archive](https://archive.materialscloud.org)

FAIR, open-access archive hosting hundreds of community-contributed materials-science datasets (often with full provenance via AiiDA), spanning DFT calculations, workflows and some experimental data. Each dataset receives a persistent DOI.

`mixed`· `open`· 2020 · Other · Materials Cloud· DOI: [10.1038/s41597-020-0637-x](https://doi.org/10.1038/s41597-020-0637-x)· tags: `fair-data`, `repository`, `aiida`, `provenance`, `doi`

#### 🧪🔓 [Metadata for a global atlas of soil microbial genetic resources](https://springernature.figshare.com/articles/dataset/Metadata_for_a_global_atlas_of_soil_microbial_genetic_resources/29482997)

We compiled a global database of 1,609 soil metagenomes and found that hotspots exhibiting both high functional gene richness and dissimilarity are rare. Overall, fewer than 25% of hotspots of soil microbial genetic resources fell within designated protected areas. Meanwhile, global patterns of microbial gene richness and dissimilarity were largely decoupled from those in taxonomic biodiversity. Dataset size: 1 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29482997](https://doi.org/10.6084/m9.figshare.29482997)

#### 🧪🔓 [Microscopic signatures of imaginary charge density wave in a kagome metal](https://springernature.figshare.com/articles/dataset/Microscopic_signatures_of_imaginary_charge_density_wave_in_a_kagome_metal/32251713/1)

Source data for Microscopic signatures of an imaginary charge density wave in a kagome metal. Dataset size: 7 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.32251713.v1](https://doi.org/10.6084/m9.figshare.32251713.v1)

#### 🧪🔓 [Microscopic signatures of imaginary charge density wave in a kagome metal](https://springernature.figshare.com/articles/dataset/Microscopic_signatures_of_imaginary_charge_density_wave_in_a_kagome_metal/32251713)

Source data for Microscopic signatures of an imaginary charge density wave in a kagome metal. Dataset size: 7 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.32251713](https://doi.org/10.6084/m9.figshare.32251713)

#### 🔀🔓 [NOMAD (Novel Materials Discovery) Repository & Archive](https://nomad-lab.eu)

Large FAIR repository and archive of raw and processed computational materials-science data (millions of DFT and beyond-DFT calculations from many codes), with growing support for experimental data uploads. Community-contributed and code-agnostic.

`mixed`· `open`· 2019 · CC-BY-4.0 · NOMAD· DOI: [10.1088/2515-7639/ab13bb](https://doi.org/10.1088/2515-7639/ab13bb)· tags: `fair-data`, `dft`, `repository`, `electronic-structure`, `ai-toolkit`

#### 🧪🔓 [Observation of angular momentum transfer among crystal lattice modes - Experimental data](https://zenodo.org/doi/10.5281/zenodo.19087102)

Experimental data for the paper " Observation of angular momentum transfer among crystal lattice modes ", published with open-access in Nature Physics under https://doi.org/10.1038/s41567-026-03274-8 The data was measured at the Department of Physical Chemistry, Fritz Haber Institute of the Max Planck Society in Berlin. Contents: Data from Fig. 1 c-f Data from Fig. 2 a-d Data from Fig.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.19087102](https://doi.org/10.5281/zenodo.19087102)

#### 🧪🔓 [Observation of angular momentum transfer among crystal lattice modes - Experimental data](https://zenodo.org/doi/10.5281/zenodo.19087101)

Experimental data for the paper " Observation of angular momentum transfer among crystal lattice modes ", published with open-access in Nature Physics under https://doi.org/10.1038/s41567-026-03274-8 The data was measured at the Department of Physical Chemistry, Fritz Haber Institute of the Max Planck Society in Berlin. Contents: Data from Fig. 1 c-f Data from Fig. 2 a-d Data from Fig.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.19087101](https://doi.org/10.5281/zenodo.19087101)

#### 🧪🔓 [Observing disorder-induced average topological order in an atom array](https://springernature.figshare.com/articles/dataset/Observing_disorder-induced_average_topological_order_in_an_atom_array/30752111/1)

We have deposited the source data underlying all four figures of the manuscript in figshare. The dataset consists of four Excel files, each corresponding to one figure in the main text

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30752111.v1](https://doi.org/10.6084/m9.figshare.30752111.v1)

#### 🧪🔓 [Observing disorder-induced average topological order in an atom array](https://springernature.figshare.com/articles/dataset/Observing_disorder-induced_average_topological_order_in_an_atom_array/30752111)

We have deposited the source data underlying all four figures of the manuscript in figshare. The dataset consists of four Excel files, each corresponding to one figure in the main text. Dataset size: 0 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30752111](https://doi.org/10.6084/m9.figshare.30752111)

#### 🧪🔓 [OdonTraits Europe. A comprehensive traits dataset for European dragonflies and damselflies](https://zenodo.org/doi/10.5281/zenodo.17248815)

Description Species traits are an important facet of biodiversity and are useful for testing many ecological hypotheses. Many initiatives to centralize species traits have emerged in recent years, but there are still large gaps in species traits’ knowledge in the literature.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.17248815](https://doi.org/10.5281/zenodo.17248815)

#### 🧪🔓 [OdonTraits Europe. A comprehensive traits dataset for European dragonflies and damselflies](https://zenodo.org/doi/10.5281/zenodo.20134320)

Description Species traits are an important facet of biodiversity and are useful for testing many ecological hypotheses. Many initiatives to centralize species traits have emerged in recent years, but there are still large gaps in species traits’ knowledge in the literature.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20134320](https://doi.org/10.5281/zenodo.20134320)

#### 🧪🔓 [Original Data of "Scalable Generation of Massive Schrödinger Cat States via Quantum Tunneling"](https://springernature.figshare.com/articles/dataset/Original_Data_of_Scalable_Generation_of_Massive_Schr_dinger_Cat_States_via_Quantum_Tunneling_/29643506)

This file provides the original experimental data associated with our massive quantum tunneling study, formatted as a .xls spreadsheet. Dataset size: 1 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29643506](https://doi.org/10.6084/m9.figshare.29643506)

#### 🧪🔓 [Ovarian Stainology: Database of evidence-based immunohistochemical antigen expression in ovarian tumors](https://zenodo.org/doi/10.5281/zenodo.20692986)

Ovarian Stainology is a structured, openly accessible database of evidence-based immunohistochemical (IHC) antigen and protein expression profiles in ovarian tumors, aggregated from the published literature. The final harmonized dataset comprises 12,212 tumor–stain frequency records derived from 1,450 studies, curated from 100,149 raw tumor–stain pairs gathered across 5,961 screened publications.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20692986](https://doi.org/10.5281/zenodo.20692986)

#### 🧪🔓 [Ovarian Stainology: Database of evidence-based immunohistochemical antigen expression in ovarian tumors](https://zenodo.org/doi/10.5281/zenodo.21227034)

Ovarian Stainology is a structured, openly accessible database of evidence-based immunohistochemical (IHC) antigen and protein expression profiles in ovarian tumors, aggregated from the published literature. The final harmonized dataset comprises 12,212 tumor–stain frequency records derived from 1,450 studies, curated from 100,149 raw tumor–stain pairs gathered across 5,961 screened publications.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.21227034](https://doi.org/10.5281/zenodo.21227034)

#### 🧪🔓 [Principles of optics in Fock space for the scalable manipulation of large quantum states](https://springernature.figshare.com/articles/dataset/Principles_of_optics_in_Fock_space_for_the_scalable_manipulation_of_large_quantum_states/30892724)

Data for Figures in the main text of “Principles of Optics in the Fock Space: Scalable Manipulation of Giant Quantum States”. Dataset size: 1 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30892724](https://doi.org/10.6084/m9.figshare.30892724)

#### 🧪🔓 [Programming Local Confinements in Crystalline Frameworks through Reticular Chemistry](https://springernature.figshare.com/articles/dataset/Programming_Local_Confinements_in_Crystalline_Frameworks_through_Reticular_Chemistry/30593789/1)

PXRD, VT-PXRD, CO2 isotherm, breakthrough curves, DRIFT spectra data for NU-6000 and NU-6001. Dataset size: 130 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30593789.v1](https://doi.org/10.6084/m9.figshare.30593789.v1)

#### 🧪🔓 [Protected Rivers Assessment of the United States (PRA-US) Version 1.2.](https://zenodo.org/doi/10.5281/zenodo.17279334)

Conservation Science Partners, in partnership with American Rivers, has developed the Protected Rivers Assessment of the United States , a data-driven nationwide inventory of present-day river protection status. Dataset size: 4.5 GB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.17279334](https://doi.org/10.5281/zenodo.17279334)

#### 🧪🔓 [Protected Rivers Assessment of the United States (PRA-US) Version 1.2.](https://zenodo.org/doi/10.5281/zenodo.17279333)

Conservation Science Partners, in partnership with American Rivers, has developed the Protected Rivers Assessment of the United States , a data-driven nationwide inventory of present-day river protection status. Dataset size: 4.5 GB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.17279333](https://doi.org/10.5281/zenodo.17279333)

#### 🧪🔓 [Real-Space Imaging of the Electron-Pair Density Hole in Molecular Auger-Meitner Decay](https://springernature.figshare.com/articles/dataset/Real-Space_Imaging_of_the_Electron-Pair_Density_Hole_in_Molecular_Auger-Meitner_Decay/32316573)

Data for the figures and extended data figures in the manuscript "Real-Space Imaging of the Electron-Pair Density Hole in Molecular Auger-Meitner Decay" in Nature Physics (2026). In addition, Molpro in- and output files, as well as simulated scattering signals are provided. A Wolfram Mathematica notebook file is included for generating the figures and inspecting the electronic structure data.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.32316573](https://doi.org/10.6084/m9.figshare.32316573)

#### 🧪🔓 [Real-Space Imaging of the Electron-Pair Density Hole in Molecular Auger-Meitner Decay](https://springernature.figshare.com/articles/dataset/Real-Space_Imaging_of_the_Electron-Pair_Density_Hole_in_Molecular_Auger-Meitner_Decay/32316573/1)

Data for the figures and extended data figures in the manuscript "Real-Space Imaging of the Electron-Pair Density Hole in Molecular Auger-Meitner Decay" in Nature Physics (2026). In addition, Molpro in- and output files, as well as simulated scattering signals are provided. A Wolfram Mathematica notebook file is included for generating the figures and inspecting the electronic structure data.…. Dataset size: 41 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.32316573.v1](https://doi.org/10.6084/m9.figshare.32316573.v1)

#### 🧪🔓 [Romanetz Driving Force Supporting Data](https://zenodo.org/doi/10.5281/zenodo.18135191)

Source data to support the findings of manuscript entitled, "Photoinduced electron transfer distance is controlled by the driving force in solid-state organic donor-acceptors.". Dataset size: 262 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18135191](https://doi.org/10.5281/zenodo.18135191)

#### 🧪🔓 [Romanetz Driving Force Supporting Data](https://zenodo.org/doi/10.5281/zenodo.18135192)

Source data to support the findings of manuscript entitled, "Photoinduced electron transfer distance is controlled by the driving force in solid-state organic donor-acceptors.". Dataset size: 262 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18135192](https://doi.org/10.5281/zenodo.18135192)

#### 🧪🔓 [Scalable large-area ZIF-8 membranes for industrial propylene/propane separations](https://springernature.figshare.com/articles/dataset/Scalable_large-area_ZIF-8_membranes_for_industrial_propylene_propane_separations/29456279)

This dataset includes experimental and characterization data supporting the findings reported in the manuscript entitled “Enabling scalable fabrication of large-area ZIF-8 membranes for industrial side-stream separation.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29456279](https://doi.org/10.6084/m9.figshare.29456279)

#### 🧪🔓 [Supporting data: Soft-X-ray momentum microscopy of nonlinear magnon interactions](https://zenodo.org/doi/10.5281/zenodo.19471018)

Supporting data for the research article “Soft X-ray momentum microscopy of nonlinear magnon interactions below 100 nm wavelength.” This repository contains the raw experimental data and a Jupyter notebook used to generate all data-driven figures presented in the study. Detailed information on data structure and processing can be found in the included README.md .

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.19471018](https://doi.org/10.5281/zenodo.19471018)

#### 🧪🔓 [Supporting data: Soft-X-ray momentum microscopy of nonlinear magnon interactions](https://zenodo.org/doi/10.5281/zenodo.19471019)

Supporting data for the research article “Soft X-ray momentum microscopy of nonlinear magnon interactions below 100 nm wavelength.” This repository contains the raw experimental data and a Jupyter notebook used to generate all data-driven figures presented in the study. Detailed information on data structure and processing can be found in the included README.md .

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.19471019](https://doi.org/10.5281/zenodo.19471019)

#### 🧪🔓 [The Active Young-Dupré Equation](https://springernature.figshare.com/articles/dataset/The_Active_Young-Dupr_Equation/31148908)

These data allow to reproduce all figures and movies included in our article. Dataset size: 75 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31148908](https://doi.org/10.6084/m9.figshare.31148908)

#### 🧪🔓 [The Active Young-Dupré Equation](https://springernature.figshare.com/articles/dataset/The_Active_Young-Dupr_Equation/31148908/1)

These data allow to reproduce all figures and movies included in our article. Dataset size: 75 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31148908.v1](https://doi.org/10.6084/m9.figshare.31148908.v1)

#### 🧪🔓 [Towards Single-Crystalline Two-Dimensional Poly(arylene vinylene) Covalent Organic Frameworks](https://springernature.figshare.com/articles/dataset/Towards_Single-Crystalline_Two-Dimensional_Poly_arylene_vinylene_Covalent_Organic_Frameworks/30631367)

Source data for main text figure. Dataset size: 6 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30631367](https://doi.org/10.6084/m9.figshare.30631367)

#### 🧪🔓 [Towards Single-Crystalline Two-Dimensional Poly(arylene vinylene) Covalent Organic Frameworks](https://springernature.figshare.com/articles/dataset/Towards_Single-Crystalline_Two-Dimensional_Poly_arylene_vinylene_Covalent_Organic_Frameworks/30631367/1)

Source data for main text figure. Dataset size: 6 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30631367.v1](https://doi.org/10.6084/m9.figshare.30631367.v1)

#### 🧪🔓 [Tuning Phonon Transmission via Single-Atom Substituents](https://springernature.figshare.com/articles/dataset/Tuning_Phonon_Transmission_via_Single-Atom_Substituents/31383004)

Experimental materials properties dataset: Tuning Phonon Transmission via Single-Atom Substituents. Published alongside a Nature Materials study (2026). Deposited on figshare. Dataset size: 16 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31383004](https://doi.org/10.6084/m9.figshare.31383004)

<a id="materials-geophysics"></a>
### Geophysics & earth sciences

#### 🧪🔓 [Dataset: The past and future impact of climate change on childhood malaria in Africa](https://zenodo.org/doi/10.5281/zenodo.20399793)

Data files necessary to reproduce the figures in the manuscript "The past and future impact of climate change on childhood malaria in Africa". Nature (2026). https://doi.org/10.1038/s41586-026-10840-w Abstract : Despite recent advances in climate change attribution, many health impacts remain unmeasured (Carlson et al., 2025). Here we leverage over a century of clinical data (Snow et al., 2017)…. Dataset size: 12.2 GB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20399793](https://doi.org/10.5281/zenodo.20399793)

#### 🧪🔓 [Dataset: The past and future impact of climate change on childhood malaria in Africa](https://zenodo.org/doi/10.5281/zenodo.20399792)

Data files necessary to reproduce the figures in the manuscript "The past and future impact of climate change on childhood malaria in Africa". Nature (2026). https://doi.org/10.1038/s41586-026-10840-w Abstract : Despite recent advances in climate change attribution, many health impacts remain unmeasured (Carlson et al., 2025). Here we leverage over a century of clinical data (Snow et al., 2017)…. Dataset size: 12.2 GB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20399792](https://doi.org/10.5281/zenodo.20399792)

#### 🧪🔓 [Recalculated (depth and temperature consistent) surface ocean CO₂ atlas (SOCAT) version 2026](https://zenodo.org/doi/10.5281/zenodo.20757578)

Product Information SOCAT dataset version v2026 Recalculated SOCAT dataset version V0-1 Changelog at end of repository FluxEngine version v4.2.0 Contacts Daniel J. Ford d.ford@exeter.ac.uk Jamie D. Shutler j.d.shutler@exeter.ac.uk Introduction The Surface Ocean CO₂ Atlas (SOCAT) version 2026 dataset (Bakker et al., 2016; https://doi.org/10.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20757578](https://doi.org/10.5281/zenodo.20757578)

#### 🧪🔓 [Recalculated (depth and temperature consistent) surface ocean CO₂ atlas (SOCAT) version 2026](https://zenodo.org/doi/10.5281/zenodo.20757579)

Product Information SOCAT dataset version v2026 Recalculated SOCAT dataset version V0-1 Changelog at end of repository FluxEngine version v4.2.0 Contacts Daniel J. Ford d.ford@exeter.ac.uk Jamie D. Shutler j.d.shutler@exeter.ac.uk Introduction The Surface Ocean CO₂ Atlas (SOCAT) version 2026 dataset (Bakker et al., 2016; https://doi.org/10.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20757579](https://doi.org/10.5281/zenodo.20757579)

<a id="materials-glasses"></a>
### Glasses

#### 🧪🔒 [INTERGLAD Ver. 8 (International Glass Database System)](https://www.newglass.jp/interglad_n/gaiyo/info_e.html)

International Glass Database System (New Glass Forum, Japan) with property and structural data for ~405,000 glasses compiled from literature, patents and manufacturer catalogs, plus property-prediction and composition-optimization tools. Paid licence; limited free trial after registration.

`experimental`· `restricted`· 2019 · Proprietary (paid licence; free trial) · New Glass Forum (Japan)· tags: `glass`, `glass-properties`, `compositions`, `property-prediction`

#### 🧪🔓 [SciGlass (open release via EPAM)](https://github.com/epam/SciGlass)

Formerly commercial glass property database released openly on GitHub: property data for ~422,000 glass compositions (oxide, halide, chalcogenide) compiled from 40,000+ literature sources and patents, plus ~15,000 optical spectra and 3,800 ternary glass-formation diagrams. Distributed as Microsoft Access (.mdb) files.

`experimental`· `open`· 2019 · MIT · GitHub· tags: `glass`, `glass-properties`, `compositions`, `literature-curated`, `viscosity`

<a id="materials-high-throughput-exp"></a>
### High-throughput experimental

#### 🧪🔓 [BIRDSHOT High-Entropy Alloy HTE Dataset (Texas A&M)](https://zenodo.org/records/16396374)

Bayesian-guided high-throughput experimental campaign (BIRDSHOT center, Texas A&M) that designed, synthesized and mechanically tested ~147 non-equimolar Cantor-family high-entropy alloys, reporting composition, processing and measured mechanical properties (strength, elongation, hardness).

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo / GitHub· DOI: [10.5281/zenodo.16396374](https://doi.org/10.5281/zenodo.16396374)· tags: `high-entropy-alloys`, `mechanical-properties`, `bayesian-optimization`, `combinatorial`, `alloy-discovery`

#### 🧪🔓 [CAMEO Autonomous Combinatorial Materials Dataset (NIST)](https://www.nature.com/articles/s41467-020-19597-w)

Closed-loop autonomous materials exploration (CAMEO; NIST/Kusne) driving synchrotron XRD across combinatorial thin-film libraries (Fe-Ga-Pd, Ge-Sb-Te) with Bayesian active learning, discovering a novel phase-change material; full autonomous experiment trajectories released by NIST.

`experimental`· `open`· 2020 · NIST Public Domain · NIST (data.nist.gov)· DOI: [10.1038/s41467-020-19597-w](https://doi.org/10.1038/s41467-020-19597-w)· tags: `autonomous-experimentation`, `combinatorial`, `synchrotron-xrd`, `active-learning`, `phase-mapping`

#### 🧪🔓 [High-Throughput Experimental Materials Database (HTEM-DB, NREL)](https://htem.nrel.gov/)

First large publicly available collection of experimental data for inorganic thin-film materials synthesized by combinatorial high-throughput methods at NREL, covering synthesis conditions, chemical composition, crystal structure and optoelectronic property measurements for tens of thousands of samples. Data are experimental, accessible via web UI and API.

`experimental`· `open`· 2018 · Other · NREL· DOI: [10.1038/sdata.2018.53](https://doi.org/10.1038/sdata.2018.53)· tags: `thin-films`, `combinatorial`, `experimental`, `optoelectronic`, `nrel`

<a id="materials-hte-synthesis"></a>
### HTE / synthesis

#### 🧪🔓 [A-Lab Autonomous Solid-State Synthesis Dataset](https://www.nature.com/articles/s41586-023-06734-w)

Autonomous robotic laboratory (Ceder group, UC Berkeley/LBNL) that over 17 days attempted 58 target inorganic compounds via 355 solid-state synthesis recipes, realizing 41 novel oxides/phosphates identified from Materials Project and GNoME; released outcomes include recipes, refined XRD patterns and CIFs.

`experimental`· `open`· 2023 · Unknown · GitHub (CederGroupHub/alabos)· DOI: [10.1038/s41586-023-06734-w](https://doi.org/10.1038/s41586-023-06734-w)· tags: `autonomous-lab`, `solid-state-synthesis`, `inorganic-materials`, `active-learning`, `robotics`, `xrd`

<a id="materials-lab-automation"></a>
### Lab automation & robotic chemistry

#### 🧪🔓 [Ada Self-Driving Lab Thin-Film Dataset](https://www.science.org/doi/10.1126/sciadv.aaz8867)

Ada self-driving laboratory (Berlinguette, UBC) that autonomously synthesized and characterized thin-film materials, including spray-combustion palladium films and spiro-OMeTAD hole-transport materials, closing the design-make-measure loop; campaign data (conductivity, film properties) on GitHub.

`experimental`· `open`· 2020 · Unknown · GitHub (berlinguette/ada)· DOI: [10.1126/sciadv.aaz8867](https://doi.org/10.1126/sciadv.aaz8867)· tags: `self-driving-lab`, `thin-films`, `hole-transport-materials`, `palladium`, `bayesian-optimization`

#### 🧪🔓 [Argonne PolyBot Electronic-Polymer Dataset](https://www.nature.com/articles/s41467-024-55655-3)

PolyBot self-driving lab (Argonne CNM) autonomously navigated a 7-dimensional processing space for PEDOT:PSS electronic-polymer thin films via importance-guided Bayesian optimization, generating hundreds of characterized films (conductivity >4500 S/cm); experiment table and code released.

`experimental`· `open`· 2025 · CC-BY-4.0 · GitHub (polybot-nexus)· DOI: [10.1038/s41467-024-55655-3](https://doi.org/10.1038/s41467-024-55655-3)· tags: `self-driving-lab`, `electronic-polymers`, `pedot-pss`, `thin-films`, `bayesian-optimization`

<a id="materials-magnetic"></a>
### Magnetic materials

#### 🧪🔓 [Altermagnetic photonic crystals](https://springernature.figshare.com/articles/dataset/Altermagnetic_photonic_crystals/32229984/1)

Altermagnetic photonic crystals. Dataset size: 13 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.32229984.v1](https://doi.org/10.6084/m9.figshare.32229984.v1)

#### 🧪🔓 [An Electrospinography Database of Spinal Cord Activity During Gait-Related Tasks and Motor Imagery Exercises](https://zenodo.org/doi/10.5281/zenodo.14615202)

Description The electroespinography (ESG) signals dataset comprises recordings from fourteen able-bodied participants. A total 10 sessions were recorded for experiment 1 (age: 30.30 ± 8.60, 40 % female participants), 10 sessions for experiment 2 (age: 30.00 ± 8.99, 40 % female participants) and 5 sessions for experiment 3 (age: 26.00 ± 4.24, 40 % female participants).

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.14615202](https://doi.org/10.5281/zenodo.14615202)

#### 🧪🔓 [An Electrospinography Database of Spinal Cord Activity During Gait-Related Tasks and Motor Imagery Exercises](https://zenodo.org/doi/10.5281/zenodo.19065545)

Description The electroespinography (ESG) signals dataset comprises recordings from fourteen able-bodied participants. A total 10 sessions were recorded for experiment 1 (age: 30.30 ± 8.60, 40 % female participants), 10 sessions for experiment 2 (age: 30.00 ± 8.99, 40 % female participants) and 5 sessions for experiment 3 (age: 26.00 ± 4.24, 40 % female participants).

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.19065545](https://doi.org/10.5281/zenodo.19065545)

#### 🧪🔓 [Covalency control of photomagnetic relaxation in a manganese(II) photoswitch](https://zenodo.org/doi/10.5281/zenodo.20025667)

Experimental magnetic materials dataset: Covalency control of photomagnetic relaxation in a manganese(II) photoswitch. Published alongside a II study (2026). Deposited on Zenodo. Dataset size: 4 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20025667](https://doi.org/10.5281/zenodo.20025667)

#### 🧪🔓 [Covalency control of photomagnetic relaxation in a manganese(II) photoswitch](https://zenodo.org/doi/10.5281/zenodo.20025668)

Experimental magnetic materials dataset: Covalency control of photomagnetic relaxation in a manganese(II) photoswitch. Published alongside a II study (2026). Deposited on Zenodo. Dataset size: 4 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20025668](https://doi.org/10.5281/zenodo.20025668)

#### 🧪🔓 [Exchange-mediated Spin-Electric Control of Single Molecules on Surfaces](https://springernature.figshare.com/articles/dataset/Exchange-mediated_Spin-Electric_Control_of_Single_Molecules_on_Surfaces/31554586)

Data and Evaluation to "Exchange-mediated Spin-Electric Control of Single Molecules on Surfaces". Sorted by the paper Figures. Dataset size: 98 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31554586](https://doi.org/10.6084/m9.figshare.31554586)

#### 🧪🔓 [Exchange-mediated Spin-Electric Control of Single Molecules on Surfaces](https://springernature.figshare.com/articles/dataset/Exchange-mediated_Spin-Electric_Control_of_Single_Molecules_on_Surfaces/31554586/1)

Data and Evaluation to "Exchange-mediated Spin-Electric Control of Single Molecules on Surfaces". Sorted by the paper Figures. Dataset size: 98 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31554586.v1](https://doi.org/10.6084/m9.figshare.31554586.v1)

#### 🧪🔓 [Homochiral Toroidal Spin State in Dy(III)-based Single-Molecule Toroics](https://springernature.figshare.com/articles/dataset/Homochiral_Toroidal_Spin_State_in_Dy_III_-based_Single-Molecule_Toroics/30937706)

This folder contains the raw experimental data for the micro-SQUID and MChD measurements presented in the above publication. The data are separated into separate files corresponding to Figs. 3-6 described in the main text. Dataset size: 2 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30937706](https://doi.org/10.6084/m9.figshare.30937706)

#### 🧪🔓 [Homochiral Toroidal Spin State in Dy(III)-based Single-Molecule Toroics](https://springernature.figshare.com/articles/dataset/Homochiral_Toroidal_Spin_State_in_Dy_III_-based_Single-Molecule_Toroics/30937706/1)

This folder contains the raw experimental data for the micro-SQUID and MChD measurements presented in the above publication. The data are separated into separate files corresponding to Figs. 3-6 described in the main text. Dataset size: 2 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30937706.v1](https://doi.org/10.6084/m9.figshare.30937706.v1)

#### 🧪🔓 [MAGNDATA (Bilbao Crystallographic Server)](https://www.cryst.ehu.es/magndata/)

Collection of more than 2,000 published commensurate and incommensurate magnetic structures (mostly from neutron diffraction), described with magnetic space/superspace group symmetry and downloadable as magCIF files compatible with VESTA, Jmol, JANA and FullProf.

`experimental`· `open`· 2016 · Other (free; citation requested) · Bilbao Crystallographic Server· tags: `magnetic-structures`, `neutron-diffraction`, `magnetic-symmetry`, `mcif`

#### 🧪🔓 [Source data for Planckian scattering and parallel conduction channels in an iron chlacogenide superconductor](https://springernature.figshare.com/articles/dataset/Source_data_for_Planckian_scattering_and_parallel_conduction_channels_in_an_iron_chlacogenide_superconductor/29042909)

Experimental magnetic materials dataset: Source data for Planckian scattering and parallel conduction channels in an iron chlacogenide superconductor. Published alongside a Nature Physics study (2026). Deposited on figshare. Dataset size: 1 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29042909](https://doi.org/10.6084/m9.figshare.29042909)

#### 🧪🔓 [Source data for Planckian scattering and parallel conduction channels in an iron chlacogenide superconductor](https://springernature.figshare.com/articles/dataset/Source_data_for_Planckian_scattering_and_parallel_conduction_channels_in_an_iron_chlacogenide_superconductor/29042909/1)

Experimental dataset associated with a figshare publication. Data covers: Source data for Planckian scattering and parallel conduction channels in an iron chlacogenide superconductor. Dataset size: 1 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29042909.v1](https://doi.org/10.6084/m9.figshare.29042909.v1)

<a id="materials-mechanical"></a>
### Mechanical properties

#### 🧪🔓 [Nonmonotonic Magnetic Friction from Collective Rotor Dynamics (Data)](https://zenodo.org/doi/10.5281/zenodo.18487115)

Raw data of the manuscript Nonmonotonic Magnetic Friction from Collective Rotor Dynamics by H. Gu, A. Lüders, and C. Bechinger Reference: Gu, H., Lüders, A. & Bechinger, C. Non-monotonic magnetic friction from collective rotor dynamics. Nat. Mater. (2026). https://doi.org/10.1038/s41563-026-02538-1. Dataset size: 15.1 GB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18487115](https://doi.org/10.5281/zenodo.18487115)

#### 🧪🔓 [Nonmonotonic Magnetic Friction from Collective Rotor Dynamics (Data)](https://zenodo.org/doi/10.5281/zenodo.18487116)

Raw data of the manuscript Nonmonotonic Magnetic Friction from Collective Rotor Dynamics by H. Gu, A. Lüders, and C. Bechinger Reference: Gu, H., Lüders, A. & Bechinger, C. Non-monotonic magnetic friction from collective rotor dynamics. Nat. Mater. (2026). https://doi.org/10.1038/s41563-026-02538-1. Dataset size: 15.1 GB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18487116](https://doi.org/10.5281/zenodo.18487116)

<a id="materials-membranes"></a>
### Membranes & separations

#### 🧪🔓 [Membrane Database - Polymer Gas Separation (MSA/CSIRO)](https://research.csiro.au/virtualscreening/membrane-database-polymer-gas-separation-membranes/)

Database of experimentally measured polymer gas-separation permeabilities covering ~1,500 polymers with permeability/selectivity for N2, O2, H2, CH4 and CO2 compiled from the literature (1950-2018); underpins Robeson upper-bound analysis.

`experimental`· `open`· 2019 · Unknown · CSIRO / Membrane Society of Australasia· tags: `gas-separation`, `permeability`, `polymers`, `robeson-plot`, `membranes`

<a id="materials-mofs-porous"></a>
### MOFs & porous materials

#### 🔀🔓 [CoRE MOF 2024 Database](https://zenodo.org/records/15055758)

2024 release of the Computation-Ready Experimental MOF database: 8,300 experimentally reported MOF crystal structures (2,664 computation-ready) with precomputed geometric, charge, stability and hydrophobicity properties, plus pointers to 32,537 additional CSD-derived structures; full DB spans 40,837 structures. Major expansion of the CoRE MOF 2019 release already in this catalog, with a web interface at mof-db.pusan.ac.kr.

`mixed`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.15055758](https://doi.org/10.5281/zenodo.15055758)· tags: `mofs`, `crystal-structures`, `adsorption`, `porous-materials`, `computation-ready`, `screening`

#### 🔀🔓 [CoRE MOF Database (Computation-Ready, Experimental MOFs)](https://zenodo.org/records/3677685)

Curated set of ~14,000 computation-ready experimental metal-organic framework crystal structures (2019 release) derived from the CSD and literature, with solvent removed and disorder resolved for direct use in simulation. Includes computed pore analytics (LCD, PLD, surface area, void fraction); distributed as CIFs and CSVs on Zenodo.

`mixed`· `open`· 2019 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.3677685](https://doi.org/10.5281/zenodo.3677685)· tags: `mofs`, `porous-materials`, `crystal-structures`, `adsorption`, `computation-ready`, `cif`

#### 🧪🔒 [CSD MOF Subset (Cambridge Structural Database)](https://support.ccdc.cam.ac.uk/support/solutions/articles/103000306242-how-many-mofs-are-there-in-the-csd-)

CCDC-curated subsets of the CSD identifying ~100,000+ MOF/coordination-polymer entries, updated with each CSD release. Full access requires a CSD licence, but a freely accessible collection of 10,636 CIFs of 3D non-disordered porous MOFs (solvent removed) is provided for research use.

`experimental`· `restricted`· 2017 · CCDC/CSD licence; free MOF CIF collection for research · CCDC· tags: `mofs`, `crystal-structures`, `csd`, `ccdc`, `coordination-polymers`

#### 🔀🔓 [CURATED COFs](https://github.com/danieleongari/CURATED-COFs)

Hundreds of experimentally reported covalent-organic framework crystal structures collected from the literature with git-tracked corrections, paper provenance and CIFs. DFT-optimized structures with DDEC charges are published on Materials Cloud for adsorption screening.

`mixed`· `open`· 2019 · MIT · GitHub / Materials Cloud· tags: `cofs`, `porous-materials`, `crystal-structures`, `literature-curated`, `adsorption`

#### 🧪🔓 [NIST/ARPA-E Adsorbent Database (ISODB)](https://adsorption.nist.gov/isodb/index.php)

Free, continuously updated NIST database of experimentally measured gas/vapor adsorption isotherms curated from the literature: ~37,700 isotherms across ~8,265 adsorbent materials and 449 adsorbates from ~4,367 articles, digitized from published tables/figures plus interlaboratory reference isotherms.

`experimental`· `open`· 2023 · Public domain (NIST/US Gov) · NIST / GitHub (NIST-ISODB)· tags: `adsorption`, `isotherms`, `mofs`, `gas-storage`, `porous-materials`

<a id="materials-nanomaterials"></a>
### Nanomaterials & nanosafety

#### 🧪🔑 [eNanoMapper / NanoCommons Knowledge Base](https://www.nanocommons.eu/)

EU nanoinformatics resource for nanosafety: experimental physicochemical and (eco)toxicological characterization for >1,400 nanomaterials aggregated from projects (nanoMILE, NanoFASE, SmartNanoTox) with harmonized metadata.

`experimental`· `registration`· 2023 · Unknown · eNanoMapper· tags: `nanosafety`, `nanomaterials`, `toxicology`, `physicochemical`

<a id="materials-optical-properties"></a>
### Optical properties & chromophores

#### 🧪🔓 [Data for "Degree-of-polarization modulation for high-dimensional optical computing"](https://zenodo.org/doi/10.5281/zenodo.20775839)

This repository contains the MATLAB (.mat) files with the experimental and numerical data supporting the figures presented in the article: Alessandro Petrini, Claudio Conti, and Davide Pierangeli, Degree-of-polarization modulation for high-dimensional optical computing , Nature (2026). https://doi.org/10.1038/s41586-026-10891-z. Dataset size: 30.6 GB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20775839](https://doi.org/10.5281/zenodo.20775839)

#### 🧪🔓 [Data for "Degree-of-polarization modulation for high-dimensional optical computing"](https://zenodo.org/doi/10.5281/zenodo.20775840)

This repository contains the MATLAB (.mat) files with the experimental and numerical data supporting the figures presented in the article: Alessandro Petrini, Claudio Conti, and Davide Pierangeli, Degree-of-polarization modulation for high-dimensional optical computing , Nature (2026). https://doi.org/10.1038/s41586-026-10891-z. Dataset size: 30.6 GB.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.20775840](https://doi.org/10.5281/zenodo.20775840)

<a id="materials-organic-electronics"></a>
### Organic electronics

#### 🔀🔓 [HOPV15 (Harvard Organic Photovoltaic Dataset)](https://figshare.com/articles/dataset/HOPV15_Dataset/1610063)

Experimental photovoltaic performance data (HOMO/LUMO, PCE, Voc, Jsc) from the literature for ~350 organic donor molecules, paired with quantum-chemical calculations over multiple conformers using several DFT functionals. An experiment-theory calibration resource for organic electronics; on Figshare.

`mixed`· `open`· 2016 · Unknown · Figshare· DOI: [10.1038/sdata.2016.86](https://doi.org/10.1038/sdata.2016.86)· tags: `organic-photovoltaics`, `opv`, `dft`, `calibration`, `molecules`

#### 🔀🔓 [OCELOT Database (Organic Crystals in Electronic and Light-Oriented Technologies)](https://oscar.as.uky.edu/)

Open archive (Risko group, Univ. Kentucky) of 56,000+ experimentally determined organic semiconductor crystal structures from ~47,000 distinct molecules, enriched with high-throughput DFT-computed optoelectronic descriptors and ML tools. Web interface and Python API.

`mixed`· `open`· 2021 · Other (see OCELOT Terms of Use) · University of Kentucky· tags: `organic-semiconductors`, `crystal-structures`, `dft-descriptors`, `optoelectronics`, `api`

<a id="materials-photovoltaics"></a>
### Photovoltaics & solar cells

#### 🧪🔒 [AMANDA / AMADAP Automated OPV-Perovskite Platform (Erlangen)](https://link.springer.com/article/10.1007/s10853-021-06281-7)

AMANDA/AMADAP automated research platform (Brabec, FAU Erlangen) fabricates and characterizes OPV and perovskite devices, screening 100+ OPV processing variations for efficiency/photostability within ~70 h and 160 perovskite compositions for photothermal stability. No consolidated open repository located; data reported within papers.

`experimental`· `restricted`· 2021 · Unknown· tags: `materials-acceleration-platform`, `organic-photovoltaics`, `perovskite`, `device-aging`, `high-throughput`

#### 🧪🔓 [Bulk heterojunction contact doping for low-resistance metal–perovskite interfaces](https://springernature.figshare.com/articles/dataset/Bulk_heterojunction_contact_doping_for_low-resistance_metal_perovskite_interfaces/30957728/1)

Source data for Fig. 1d, Figs. 2b-d,f, Figs. 3a-e, and Figs. 4a-f

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30957728.v1](https://doi.org/10.6084/m9.figshare.30957728.v1)

#### 🧪🔓 [Data Accompanying 'Molecular Factors Controlling Charge Pair Generation in Organic Photovoltaic Materials'](https://zenodo.org/doi/10.5281/zenodo.18151704)

Data used to create the figures in the main text of Hart, L.J.F., Medranda, D.G., Yuan, S.W. et al. Molecular factors controlling charge pair generation in organic photovoltaic materials. Nat. Mater. (2026). https://doi.org/10.1038/s41563-026-02509-6.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18151704](https://doi.org/10.5281/zenodo.18151704)

#### 🧪🔓 [Data Accompanying 'Molecular Factors Controlling Charge Pair Generation in Organic Photovoltaic Materials'](https://zenodo.org/doi/10.5281/zenodo.18151703)

Data used to create the figures in the main text of Hart, L.J.F., Medranda, D.G., Yuan, S.W. et al. Molecular factors controlling charge pair generation in organic photovoltaic materials. Nat. Mater. (2026). https://doi.org/10.1038/s41563-026-02509-6.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18151703](https://doi.org/10.5281/zenodo.18151703)

#### 🧪🔓 [E2M2s model and input data of the European energy system](https://springernature.figshare.com/articles/dataset/E2M2s_model_and_input_data_of_the_European_energy_system/29646350)

Contains the full code, data, and workflows used to analyse the solar rebound effect in a sector-coupled European energy system model, including all scenario definitions. Dataset size: 99 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.29646350](https://doi.org/10.6084/m9.figshare.29646350)

#### 🧪🔓 [Emerging-PV Reports Database](https://emerging-pv.org/)

Community-curated online database of research-cell device performance for emerging photovoltaics — OPV, perovskites, dye-sensitized and other next-generation devices — collected from literature and researcher submissions, with interactive efficiency graphs and annual 'Emerging PV Reports' in Adv. Energy Mater.

`experimental`· `open`· 2021 · Unknown · emerging-pv.org (HI ERN / FZ Jülich)· tags: `opv`, `organic-solar-cells`, `perovskite`, `device-performance`, `efficiency-tables`

#### 🧪🔓 [High-Throughput Robotic Perovskite Stability Dataset (MIT)](https://www.nature.com/articles/s41467-021-22472-x)

High-throughput robotic synthesis and accelerated degradation testing of multi-cation halide perovskite compositions across temperatures (Buonassisi group, MIT), producing optical/stability measurements that revealed a temperature-induced stability reversal between MA and Cs cations.

`experimental`· `open`· 2021 · CC-BY-4.0· DOI: [10.1038/s41467-021-22472-x](https://doi.org/10.1038/s41467-021-22472-x)· tags: `perovskite`, `degradation`, `stability`, `high-throughput`, `robotic`, `machine-learning`

#### 🧪🔓 [Hole-Transfer Cascade–Engineered Donor Polymer for Moisture-Stable Unencapsulated Perovskite Solar Cells](https://springernature.figshare.com/articles/dataset/Hole-Transfer_Cascade_Engineered_Donor_Polymer_for_Moisture-Stable_Unencapsulated_Perovskite_Solar_Cells/30405232)

This file provides the raw data underlying the four main figures presented in the manuscript "Hybrid kink PeSC." It includes original measurement datasets and source values used for data plotting and analysis.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30405232](https://doi.org/10.6084/m9.figshare.30405232)

#### 🧪🔓 [Hole-Transfer Cascade–Engineered Donor Polymer for Moisture-Stable Unencapsulated Perovskite Solar Cells](https://springernature.figshare.com/articles/dataset/Hole-Transfer_Cascade_Engineered_Donor_Polymer_for_Moisture-Stable_Unencapsulated_Perovskite_Solar_Cells/30405232/1)

This file provides the raw data underlying the four main figures presented in the manuscript "Hybrid kink PeSC." It includes original measurement datasets and source values used for data plotting and analysis. Dataset size: 0 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30405232.v1](https://doi.org/10.6084/m9.figshare.30405232.v1)

#### 🧪🔓 [Layer Photovoltaic Effect in a Two-dimensional Parity-Time Symmetric Antiferromagnet](https://springernature.figshare.com/articles/dataset/Layer_Photovoltaic_Effect_in_a_Two-dimensional_Parity-Time_Symmetric_Antiferromagnet/31827727/1)

All source data files for the main text figures, extended data figures and supplementary figures (saved as individual excel files). Dataset size: 1 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31827727.v1](https://doi.org/10.6084/m9.figshare.31827727.v1)

#### 🧪🔓 [Layer Photovoltaic Effect in a Two-dimensional Parity-Time Symmetric Antiferromagnet](https://springernature.figshare.com/articles/dataset/Layer_Photovoltaic_Effect_in_a_Two-dimensional_Parity-Time_Symmetric_Antiferromagnet/31827727)

All source data files for the main text figures, extended data figures and supplementary figures (saved as individual excel files). Dataset size: 1 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.31827727](https://doi.org/10.6084/m9.figshare.31827727)

#### 🧪🔓 [NREL Photovoltaic Data Acquisition (PVDAQ) Public Datasets](https://data.openei.org/submissions/4568)

Large-scale time-series database of field performance data (15-minute resolution and finer) and system metadata from experimental and commercial PV sites, including environmental sensor streams; over 500 GB in the DOE Open Energy Data Initiative data lake, used for PV performance and degradation analysis.

`experimental`· `open`· 2021 · CC-BY-4.0 · OEDI / AWS Open Data· DOI: [10.25984/1846021](https://doi.org/10.25984/1846021)· tags: `solar`, `pv-performance`, `degradation`, `time-series`, `field-data`, `nrel`

#### 🧪🔓 [Perovskite Solar Cells Ageing Dataset (HZB)](https://zenodo.org/records/8185883)

2,245 cleaned maximum-power-point-tracking ageing traces (efficiency vs time) for perovskite solar cells spanning many device stacks, collected on a high-throughput ageing system (Abate group, Helmholtz-Zentrum Berlin); CC-BY-4.0 on Zenodo, underlying the 'stability follows efficiency' analysis.

`experimental`· `open`· 2023 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.8185883](https://doi.org/10.5281/zenodo.8185883)· tags: `perovskite`, `solar-cells`, `device-ageing`, `stability`, `high-throughput`, `mppt`

#### 🧪🔓 [Simultaneous measurements of solar wind from L1, shocked solar wind from Magnetosheath, and measures of geomagnetic response from ground-based indices](https://zenodo.org/doi/10.5281/zenodo.17546718)

These data are compiled from other sources and are used in the calculations and simulations for the paper Sivadas et al., 2026 "Regression to the Mean can Explain the Saturation of Geomagnetic Storms". Data.zip contains the curated data set of simultaneous measurements from L1 satellites and ground-based measurements.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.17546718](https://doi.org/10.5281/zenodo.17546718)

#### 🧪🔓 [Simultaneous measurements of solar wind from L1, shocked solar wind from Magnetosheath, and measures of geomagnetic response from ground-based indices](https://zenodo.org/doi/10.5281/zenodo.18291615)

These data are compiled from other sources and are used in the calculations and simulations for the paper Sivadas et al., 2026 "Regression to the Mean can Explain the Saturation of Geomagnetic Storms". Data.zip contains the curated data set of simultaneous measurements from L1 satellites and ground-based measurements.

`experimental`· `open`· 2026 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.18291615](https://doi.org/10.5281/zenodo.18291615)

#### 🧪🔓 [The Perovskite Database Project](https://www.perovskitedatabase.com/)

Open-access, FAIR database of experimental perovskite solar cell devices, covering more than 42,000 cells with up to ~100 parameters each (device stack, composition, J-V metrics, stability), curated from over 16,000 publications. Every entry is linked to its source DOI; searchable and downloadable, now also hosted in NOMAD.

`experimental`· `open`· 2022 · CC-BY-4.0 · self-hosted· DOI: [10.1038/s41560-021-00941-3](https://doi.org/10.1038/s41560-021-00941-3)· tags: `perovskite-solar-cells`, `photovoltaics`, `device-data`, `experimental`, `fair-data`

<a id="materials-polymers"></a>
### Polymers

#### 🔀🔓 [Khazana / Polymer Genome (Ramprasad Group)](https://khazana.gatech.edu/)

Khazana is a searchable repository of downloadable published computational materials data (DFT datasets for polymers and dielectrics) with ML utilities; Polymer Genome is the associated polymer property-prediction platform trained on DFT and experimental literature data. Thousands of polymer/organic-material property records for polymer informatics.

`mixed`· `open`· 2018 · Unknown · Khazana (Georgia Tech)· tags: `polymers`, `polymer-informatics`, `dft`, `machine-learning`, `dielectrics`

#### 🧪🔓 [Metadata record for: Efficient compressed database of equilibrated configurations of ring-linear polymer blends for MD simulations](https://springernature.figshare.com/articles/dataset/Metadata_record_for_Efficient_compressed_database_of_equilibrated_configurations_of_ring-linear_polymer_blends_for_MD_simulations/18742097/1)

This dataset contains key characteristics about the data described in the Data Descriptor Efficient compressed database of equilibrated configurations of ring-linear polymer blends for MD simulations. Contents: 1. human readable metadata summary table in CSV format 2. machine readable metadata file in JSON format

`experimental`· `open`· 2022 · CC0-1.0 · figshare· DOI: [10.6084/m9.figshare.18742097.v1](https://doi.org/10.6084/m9.figshare.18742097.v1)

#### 🧪🔓 [NanoMine / MaterialsMine](https://materialsmine.org/)

Open FAIR knowledge graph of polymer nanocomposite data (Duke/RPI/Northwestern): experimental structure-property data from >1,700 nanocomposite samples extracted from the literature and contributed by labs, with microstructure characterization.

`experimental`· `open`· 2020 · Unknown · self-hosted· tags: `polymer-nanocomposites`, `structure-property`, `knowledge-graph`, `fair-data`

#### 🧪🔑 [PoLyInfo (NIMS Polymer Database)](https://polymer.nims.go.jp/)

NIMS database of polymer properties extracted from scientific literature, covering ~100 property classes (thermal, electrical, mechanical) with chemical structures, monomers, polymerization and processing conditions. Holds ~19,000 homopolymers, ~175,000 polymer samples and ~552,000 property data points from ~22,000 literature sources. Manually curated; bulk download is prohibited.

`experimental`· `registration`· 2011 · NIMS MatNavi Terms (free registration; bulk download prohibited) · NIMS DICE / MatNavi· tags: `polymers`, `polymer-properties`, `literature-curated`, `nims`, `matnavi`, `polymer-informatics`

#### 🧪🔓 [Polymer Property Predictor and Database (NIST/CHiMaD)](https://pppdb.uchicago.edu/)

NIST/CHiMaD resource (UChicago) curating experimentally measured Flory-Huggins interaction parameters and glass-transition temperatures extracted from the literature, with tools to predict polymer phase diagrams.

`experimental`· `open`· 2018 · Unknown · UChicago· tags: `polymers`, `flory-huggins`, `glass-transition`, `informatics`

#### 🧪🔓 [Transient pH changes drive vacuole formation in enzyme-polymer condensates](https://springernature.figshare.com/articles/dataset/Transient_pH_changes_drive_vacuole_formation_in_enzyme-polymer_condensates/30038194)

This contains the source data - including raw, uncropped images and videos corresponding to cropped images shown in the main text and supporting information. Dataset size: 412 MB.

`experimental`· `open`· 2026 · CC-BY-4.0 · figshare· DOI: [10.6084/m9.figshare.30038194](https://doi.org/10.6084/m9.figshare.30038194)

<a id="materials-porous-materials"></a>
### Porous materials

#### 🧪🔓 [Dataset: Statistics makes a difference: Machine learning adsorption dynamics of functionalized cyclooctyne on Si(001) at DFT accuracy](https://zenodo.org/doi/10.5281/zenodo.16836065)

Raw Data for the publication Statistics makes a difference: Machine learning adsorption dynamics of functionalized cyclooctyne on Si(001) at DFT accuracy. Dataset size: 35.7 GB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.16836065](https://doi.org/10.5281/zenodo.16836065)

#### 🧪🔓 [Dataset: Statistics makes a difference: Machine learning adsorption dynamics of functionalized cyclooctyne on Si(001) at DFT accuracy](https://zenodo.org/doi/10.5281/zenodo.17523493)

Raw Data for the publication Statistics makes a difference: Machine learning adsorption dynamics of functionalized cyclooctyne on Si(001) at DFT accuracy. Dataset size: 35.7 GB.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.17523493](https://doi.org/10.5281/zenodo.17523493)

<a id="materials-spectra-exp"></a>
### Experimental spectra (XPS/Raman/XRD)

#### 🧪🔓 [LIBS Benchmark Classification Dataset](https://springernature.figshare.com/articles/Training_dataset/11316578/1)

Benchmark dataset of measured laser-induced breakdown spectroscopy (LIBS) spectra for classification: 7.6 GB HDF5 training set (plus test set) covering many sample classes, released as a Scientific Data descriptor (2020). CC0.

`experimental`· `open`· 2020 · CC0-1.0 · Figshare· DOI: [10.6084/m9.figshare.11316578.v1](https://doi.org/10.6084/m9.figshare.11316578.v1)· tags: `libs`, `spectroscopy`, `benchmark`, `classification`, `hdf5`

#### 🧪🔓 [Multidimensional Photoemission Spectra of WSe2](https://zenodo.org/record/2704787)

Measured multidimensional (time/angle-resolved) photoemission spectroscopy data of tungsten diselenide: 6.2 GB HDF5 volumes released with an open-source end-to-end workflow for multidimensional photoemission spectroscopy. Scientific Data (2020).

`experimental`· `open`· 2020 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.2704787](https://doi.org/10.5281/zenodo.2704787)· tags: `arpes`, `photoemission`, `2d-materials`, `hdf5`, `trarpes`

#### 🧪🔓 [NIST X-ray Photoelectron Spectroscopy Database (SRD 20)](https://srdata.nist.gov/xps/)

Critically evaluated collection of over 22,000 XPS line positions, chemical shifts, doublet splittings and energy separations of photoelectron and Auger-electron lines, compiled from published literature (v5.0, updated 2023). Interactive search by element, line type and energy.

`experimental`· `open`· 2023 · NIST SRD (free public access) · NIST· DOI: [10.18434/T4T88K](https://doi.org/10.18434/T4T88K)· tags: `xps`, `binding-energies`, `surface-analysis`, `nist`, `reference-data`

#### 🧪🔓 [opXRD - Open Experimental Powder XRD Database](https://xrd.aimat.science/)

Open experimental powder X-ray diffraction database aggregating patterns from 18+ labs (KIT AiMat and collaborators): 92,552 measured diffractograms (2,179 phase-labeled) across many materials classes, on Zenodo under CC-BY-4.0 for training/benchmarking ML on real XRD data.

`experimental`· `open`· 2025 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.15298026](https://doi.org/10.5281/zenodo.15298026)· tags: `xrd`, `powder-diffraction`, `crystallography`, `machine-learning`, `characterization`

#### 🧪🔓 [RRUFF Project Database](https://rruff.info/)

Integrated database of high-quality Raman spectra, X-ray powder diffraction patterns, infrared spectra and measured chemistry for thousands of well-characterized mineral samples, measured at the University of Arizona from documented specimens. A reference standard for mineral identification.

`experimental`· `open`· 2005 · Other (free for research/educational use) · University of Arizona· tags: `raman`, `xrd`, `infrared`, `minerals`, `reference-spectra`

<a id="materials-spectroscopy"></a>
### Spectroscopy

#### 🧪🔓 [Datasets for the computational workflow of multidimensional photoemission spectroscopy](https://zenodo.org/record/3987303)

Recorded single-electron event data of bulk 2H-WSe 2 photoemission from a commercial momentum microscope (SPECS METIS 1000).These data are used for demonstration of the computational workflow explained in the following publication. R. P. Xian, Y. Acremann, S. Y. Agustsson, M. Dendzik, K. Bühlmann, D. Curcio, D. Kutnyakhov, F. Pressacco, M. Heber, S. Dong, T. Pincelli, J.

`experimental`· `open`· 2020 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.3987303](https://doi.org/10.5281/zenodo.3987303)

#### 🧪🔓 [Datasets for the computational workflow of multidimensional photoemission spectroscopy](https://zenodo.org/record/3987304)

Recorded single-electron event data of bulk 2H-WSe 2 photoemission from a commercial momentum microscope (SPECS METIS 1000).These data are used for demonstration of the computational workflow explained in the following publication. R. P. Xian, Y. Acremann, S. Y. Agustsson, M. Dendzik, K. Bühlmann, D. Curcio, D. Kutnyakhov, F. Pressacco, M. Heber, S. Dong, T. Pincelli, J.

`experimental`· `open`· 2020 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.3987304](https://doi.org/10.5281/zenodo.3987304)

#### 🧪🔓 [K-edge XANES spectra data](https://springernature.figshare.com/articles/dataset/K-edge_XANES_spectra_data/5678998/1)

K-edge XANES spectra data computed using FEFF9. Dataset size: 5.4 GB.

`experimental`· `open`· 2018 · CC0-1.0 · figshare· DOI: [10.6084/m9.figshare.5678998.v1](https://doi.org/10.6084/m9.figshare.5678998.v1)

#### 🧪🔓 [Multidimensional photoemission spectra of tungsten diselenide](https://zenodo.org/record/4266202)

Pump-probe multidimensional photoemission spectroscopy (MPES) of tungsten diselenide (WSe2) measured using an electron momentum microscope at the FLASH Free Electron Laser. This is an example file for data standardization of MPES and has been linked to the publication, D. Kutnyakhov, R. P. Xian, M. Dendzik, M. Heber, F. Pressacco, S. Y. Agustsson, L. Wenthaus, H. Meyer, S. Gieschen, G.

`experimental`· `open`· 2020 · CC-BY-4.0 · Zenodo· DOI: [10.5281/zenodo.4266202](https://doi.org/10.5281/zenodo.4266202)

#### 🧪🔓 [Support tables](https://springernature.figshare.com/articles/Support_tables/11316572/1)

Excel sheets providing the sample compositions with estimated uncertainties.

`experimental`· `open`· 2020 · CC0-1.0 · figshare· DOI: [10.6084/m9.figshare.11316572.v1](https://doi.org/10.6084/m9.figshare.11316572.v1)

#### 🧪🔓 [Testing dataset](https://springernature.figshare.com/articles/Testing_dataset/11316575/1)

Testing dataset in hdf5 file format without the class labels. Scripts are provided for reading in the dataset in R, Python, and Matlab. Dataset size: 3.1 GB.

`experimental`· `open`· 2020 · CC0-1.0 · figshare· DOI: [10.6084/m9.figshare.11316575.v1](https://doi.org/10.6084/m9.figshare.11316575.v1)

<a id="materials-superconductors"></a>
### Superconductors

#### 🧪🔓 [SuperCon (NIMS / MDR)](https://mdr.nims.go.jp/concern/datasets/mw22v8634?locale=en)

Curated database of experimental superconducting materials recording chemical composition and critical temperature (Tc) for tens of thousands of conventional and unconventional superconductors. Re-edited and released as MDR SuperCon (~26,000 records) via the NIMS Materials Data Repository.

`experimental`· `open`· 2022 · CC-BY-4.0 · NIMS MDR· tags: `superconductors`, `critical-temperature`, `experimental`, `nims`, `tc`

<a id="materials-thermoelectrics"></a>
### Thermoelectrics

#### 🧪🔓 [ESTM — Experimentally Synthesized Thermoelectric Materials Dataset](https://github.com/KRICT-DATA/SIMD)

Public dataset of 5,205 experimental observations covering 880 unique experimentally synthesized thermoelectric materials, with measured Seebeck coefficient, electrical conductivity, thermal conductivity, power factor and figure of merit (ZT). Released with the SIMD data-driven discovery toolkit.

`experimental`· `open`· 2022 · Unknown · GitHub· DOI: [10.1038/s41524-022-00897-2](https://doi.org/10.1038/s41524-022-00897-2)· tags: `thermoelectrics`, `zt`, `seebeck`, `experimental`, `data-driven`

#### 🧪🔓 [Starrydata2](https://www.starrydata2.org/)

Open, web-based database that crowdsources experimental material-property data digitized from published plot images, containing 190,000+ curves from 80,000+ physical samples across 13,000+ papers, heavily weighted toward experimental thermoelectric materials. All data are openly downloadable.

`experimental`· `open`· 2019 · Other · self-hosted· tags: `thermoelectrics`, `experimental`, `plot-digitization`, `crowdsourced`, `property-curves`

<a id="materials-thermophysical"></a>
### Thermophysical properties

#### 🧪🔓 [NIST TRC ThermoML Archive](https://trc.nist.gov/ThermoML/)

Archive of experimental thermophysical, thermochemical and transport property data in the IUPAC-standard ThermoML XML format, produced by the NIST Thermodynamics Research Center in cooperation with five major journals. Machine-readable files carry data points with uncertainties, methods and full bibliographic metadata.

`experimental`· `open`· 2006 · Other (free with journal publishers' permission) · NIST TRC· tags: `thermophysical-properties`, `thermochemistry`, `thermoml`, `xml`, `nist`
