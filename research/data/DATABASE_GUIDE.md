# Database guide

This page is the collaborator-facing map of every database or data resource currently connected to the project. It is generated from the broad discovery catalog and the analysed-resource ledger; edit those source files rather than this page.

## Scope accounting

| Inventory | Records | Meaning |
|---|---:|---|
| Broad discovery catalog | 127 | Experimental or mixed resources curated for scientific scope, access, licence, provenance, and an original-home link |
| Analysed-resource ledger | 32 | Resources that entered an audit, donor or recipient model, control, readiness screen, or AI-generated research path |
| Exact overlap | 14 | Analysed resources already present under the same identifier in the broad catalog |
| Task-specific additions | 18 | Project resources, subsets, extensions, or external recipients not represented by the same identifier in the broad catalog |
| Union of project resource identifiers | 145 | Index records, not necessarily physically independent archives |

A resource can be catalogued without being analysed, analysed without supporting a positive transfer edge, or represented by a task-specific subset of a larger upstream archive. These distinctions are retained rather than collapsed into one inflated database count.

## Broad catalog at a glance

The catalog contains **98 experimental** and **29 mixed experimental/computational** resources. Access is recorded as **118 open**, **5 registration-gated**, and **4 restricted**. **22** records have an unresolved data licence. Open access must not be interpreted as permission to redistribute.

Every broad-catalog entry has a one-paragraph scientific summary, domain and subdomain, data type, access route, licence, source link, and DOI where available in the [full catalog](../../CATALOG.md).

### Metadata limitations

- **22 licences remain unresolved.** Those entries must not be described as openly licensed or redistributed without an upstream rights check.
- **85 entries currently use the resource homepage as the curator evidence URL.** This records where the metadata was checked, but it is not an independent live-link or file-level audit.
- Repository-scale resources can contain files under different licences and versions. The entry-level licence is a discovery aid, not a substitute for checking the exact downloaded file.
- Dataset sizes and repository contents can change after this snapshot; claim-bearing analyses use pinned commits, hashes, or archived records where available.

### Scientific coverage

| Domain | Scientific family | Resources | Examples |
|---|---|---:|---|
| Chemistry | [Batteries & energy storage](../../CATALOG.md#chemistry-batteries) | 1 | [5035 Conductivity Experiments for Li-Ion Battery Electrolytes](https://zenodo.org/records/7244939) |
| Chemistry | [ML benchmark datasets](../../CATALOG.md#chemistry-benchmark-ml) | 4 | [MoleculeNet](https://moleculenet.org/), [Open Graph Benchmark - Molecular Datasets](https://ogb.stanford.edu/), [Therapeutics Data Commons (TDC)](https://tdcommons.ai/), [and 1 more](../../CATALOG.md#chemistry-benchmark-ml) |
| Chemistry | [Bioactivity & screening](../../CATALOG.md#chemistry-bioactivity) | 4 | [BindingDB](https://www.bindingdb.org/), [ChEMBL](https://www.ebi.ac.uk/chembl/), [PubChem](https://pubchem.ncbi.nlm.nih.gov/), [and 1 more](../../CATALOG.md#chemistry-bioactivity) |
| Chemistry | [Catalysis](../../CATALOG.md#chemistry-catalysis) | 1 | [CatTestHub](https://chemrxiv.org/engage/chemrxiv/article-details/65b1b5e5e9ebbb4db9e91c68) |
| Chemistry | [Crystallography](../../CATALOG.md#chemistry-crystallography) | 1 | [Cambridge Structural Database (CSD)](https://www.ccdc.cam.ac.uk/solutions/software/csd/) |
| Chemistry | [Data infrastructure & portals](../../CATALOG.md#chemistry-data-infrastructure) | 2 | [Chemotion Repository](https://www.chemotion-repository.net/), [RADAR4Chem](https://radar.products.fiz-karlsruhe.de/en/radarabout/radar4chem) |
| Chemistry | [HTE / synthesis](../../CATALOG.md#chemistry-hte-synthesis) | 8 | [AstraZeneca ELN Reaction Dataset (Buchwald-Hartwig)](https://pubs.rsc.org/en/content/articlehtml/2023/sc/d2sc06041h), [Buchwald-Hartwig C-N Cross-Coupling HTE Dataset](https://www.science.org/doi/10.1126/science.aar5169), [Dark Reactions Project](https://darkreactions.haverford.edu), [and 5 more](../../CATALOG.md#chemistry-hte-synthesis) |
| Chemistry | [Ionic liquids](../../CATALOG.md#chemistry-ionic-liquids) | 1 | [ILThermo (NIST Ionic Liquids Database, SRD 147)](https://ilthermo.boulder.nist.gov/) |
| Chemistry | [Reaction kinetics](../../CATALOG.md#chemistry-kinetics) | 2 | [NIST Chemical Kinetics Database (SRD 17)](https://kinetics.nist.gov/kinetics/), [ReSpecTh (Reaction Kinetics, Spectroscopy, Thermochemistry)](https://respecth.hu/) |
| Chemistry | [Lab automation & robotic chemistry](../../CATALOG.md#chemistry-lab-automation) | 5 | [AlphaFlow Self-Driving Fluidic Lab Dataset](https://www.nature.com/articles/s41467-023-37139-y), [Chemputer/XDL Digitized Synthesis Procedures (Cronin Group)](https://zenodo.org/records/3955103), [Closed-Loop General-Conditions Suzuki Dataset (MMLI)](https://moleculemaker.org/datasets/closed-loop-optimization-of-general-reaction-conditions-for-heteroaryl-suzuki-miyaura-coupling/), [and 2 more](../../CATALOG.md#chemistry-lab-automation) |
| Chemistry | [Molecular properties](../../CATALOG.md#chemistry-molecular-properties) | 5 | [CALiSol-23](https://www.nature.com/articles/s41597-024-03575-8), [ESOL (Delaney Aqueous Solubility)](https://acs.figshare.com/articles/dataset/ESOL_Estimating_Aqueous_Solubility_Directly_from_Molecular_Structure/7944677), [FreeSolv](https://github.com/MobleyLab/FreeSolv), [and 2 more](../../CATALOG.md#chemistry-molecular-properties) |
| Chemistry | [Optical properties & chromophores](../../CATALOG.md#chemistry-optical-properties) | 2 | [ChemFluor](https://figshare.com/articles/dataset/ChemFluor/12110619), [Experimental Database of Optical Properties of Organic Compounds (Deep4Chem)](http://deep4chem.korea.ac.kr/) |
| Chemistry | [Physical properties](../../CATALOG.md#chemistry-physical-properties) | 2 | [Bradley Double Plus Good (Highly Curated) Melting Point Dataset](https://figshare.com/articles/dataset/Jean_Claude_Bradley_Double_Plus_Good_Highly_Curated_and_Validated_Melting_Point_Dataset/1031638), [Jean-Claude Bradley Open Melting Point Dataset](https://figshare.com/articles/dataset/Jean_Claude_Bradley_Open_Melting_Point_Datset/1031637) |
| Chemistry | [pKa / dissociation constants](../../CATALOG.md#chemistry-pka) | 2 | [IUPAC Digitized pKa Dataset (Dissociation-Constants)](https://github.com/IUPAC/Dissociation-Constants), [IUPAC Dissociation Constants in Dipolar Aprotic Solvents (Izutsu)](https://github.com/IUPAC/Dissociation-Constants-Izutsu) |
| Chemistry | [Polymers](../../CATALOG.md#chemistry-polymers) | 1 | [OpenPoly Polymer Benchmark](https://github.com/WangGroupFDU/Openpoly_benchmark) |
| Chemistry | [Reaction data](../../CATALOG.md#chemistry-reactions) | 2 | [Open Reaction Database (ORD)](https://open-reaction-database.org/), [USPTO Chemical Reactions (Lowe)](https://figshare.com/articles/dataset/Chemical_reactions_from_US_patents_1976-Sep2016_/5104873) |
| Chemistry | [Self-driving-lab benchmarks](../../CATALOG.md#chemistry-sdl-benchmarks) | 3 | [Atlas: A Brain for Self-Driving Laboratories](https://github.com/aspuru-guzik-group/atlas), [Olympus Benchmark Suite](https://github.com/aspuru-guzik-group/olympus), [Summit (Reaction Optimisation Benchmarks)](https://github.com/sustainable-processes/summit) |
| Chemistry | [Solubility](../../CATALOG.md#chemistry-solubility) | 2 | [AqSolDB](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/OVHAW8), [BigSolDB](https://zenodo.org/records/15094979) |
| Chemistry | [Solvation](../../CATALOG.md#chemistry-solvation) | 2 | [CombiSolv-Exp](https://github.com/fhvermei/chemprop_solvation), [Minnesota Solvation Database (MNSol)](https://comp.chem.umn.edu/mnsol/) |
| Chemistry | [Experimental spectra (XPS/Raman/XRD)](../../CATALOG.md#chemistry-spectra-exp) | 3 | [GNPS - Global Natural Products Social Molecular Networking](https://gnps2.org/), [HMDB - Human Metabolome Database](https://hmdb.ca/), [MoNA - MassBank of North America](https://mona.fiehnlab.ucdavis.edu/) |
| Chemistry | [Spectroscopy](../../CATALOG.md#chemistry-spectroscopy) | 5 | [MassBank Europe](https://massbank.eu/MassBank/), [NIST Chemistry WebBook (SRD 69)](https://webbook.nist.gov/chemistry/), [NMRexp](https://zenodo.org/records/17296666), [and 2 more](../../CATALOG.md#chemistry-spectroscopy) |
| Chemistry | [Thermochemistry](../../CATALOG.md#chemistry-thermochemistry) | 1 | [Active Thermochemical Tables (ATcT)](https://atct.anl.gov/) |
| Materials | [Additive manufacturing](../../CATALOG.md#materials-additive-manufacturing) | 3 | [L-PBF Relative Density Dataset for Commercial Metallic Alloys](https://github.com/GermanOmar/data_LPBF), [NIST AM Bench (Additive Manufacturing Benchmark Test Series)](https://www.nist.gov/ambench), [ORNL L-PBF In Situ Imaging + XCT + Fatigue Dataset](https://www.osti.gov/biblio/2524534) |
| Materials | [Alloys & mechanical properties](../../CATALOG.md#materials-alloys-mechanical) | 2 | [Expanded MPEA Dataset (Borg et al., high-entropy alloys)](https://figshare.com/articles/dataset/Expanded_dataset_of_mechanical_properties_and_observed_phases_of_multi-principal_element_alloys/12642953), [NIMS MatNavi (incl. Creep/Fatigue/Corrosion Data Sheets)](https://mits.nims.go.jp/en/) |
| Materials | [Batteries & energy storage](../../CATALOG.md#materials-batteries) | 9 | [Battery Materials Database (ChemDataExtractor, Huang & Cole)](https://springernature.figshare.com/articles/Metadata_record_for_A_database_of_battery_materials_auto-generated_using_ChemDataExtractor/12646277/1), [BatteryArchive.org](https://batteryarchive.org/), [CALCE Battery Datasets (University of Maryland)](https://calce.umd.edu/battery-data), [and 6 more](../../CATALOG.md#materials-batteries) |
| Materials | [ML benchmark datasets](../../CATALOG.md#materials-benchmark-ml) | 2 | [Matbench](https://matbench.materialsproject.org/), [matminer Datasets](https://hackingmaterials.lbl.gov/matminer/) |
| Materials | [Catalysis](../../CATALOG.md#materials-catalysis) | 1 | [Open Catalyst Experiments 2024 (OCx24)](https://fair-chem.github.io/fair-chemistry-papers/#open-catalyst-experiments-2024-ocx24) |
| Materials | [Crystallography](../../CATALOG.md#materials-crystallography) | 2 | [American Mineralogist Crystal Structure Database (AMCSD)](https://www.rruff.net/amcsd/), [Crystallography Open Database (COD)](https://www.crystallography.net/cod/) |
| Materials | [Data infrastructure & portals](../../CATALOG.md#materials-data-infrastructure) | 3 | [Foundry-ML](https://foundry-ml.org/), [Materials Data Facility (MDF)](https://www.materialsdatafacility.org/), [PARADIM Data Collective](https://data.paradim.org/) |
| Materials | [Electrocatalysis (experimental HTE)](../../CATALOG.md#materials-electrocatalysis-exp) | 3 | [CatHubExp (Catalysis-Hub Experimental Electrocatalysis Database)](https://experimental.catalysis-hub.org), [In-Situ PEM Fuel Cell Cathode Catalyst Degradation Dataset](https://figshare.com/articles/dataset/_b_In-Situ_Characterization_of_Cathode_Catalyst_Degradation_in_PEM_Fuel_Cells_b_/25450177/1), [Materials Experiment and Analysis Database (MEAD, Caltech HTE/JCAP)](https://solarfuelshub.org/materials-experiment-and-analysis-database) |
| Materials | [General materials properties](../../CATALOG.md#materials-general-properties) | 3 | [Citrination / Open Citrination (Citrine Informatics)](https://citrination.com), [Materials Cloud Archive](https://archive.materialscloud.org), [NOMAD (Novel Materials Discovery) Repository & Archive](https://nomad-lab.eu) |
| Materials | [Glasses](../../CATALOG.md#materials-glasses) | 2 | [INTERGLAD Ver. 8 (International Glass Database System)](https://www.newglass.jp/interglad_n/gaiyo/info_e.html), [SciGlass (open release via EPAM)](https://github.com/epam/SciGlass) |
| Materials | [High-throughput experimental](../../CATALOG.md#materials-high-throughput-exp) | 3 | [BIRDSHOT High-Entropy Alloy HTE Dataset (Texas A&M)](https://zenodo.org/records/16396374), [CAMEO Autonomous Combinatorial Materials Dataset (NIST)](https://www.nature.com/articles/s41467-020-19597-w), [High-Throughput Experimental Materials Database (HTEM-DB, NREL)](https://htem.nrel.gov/) |
| Materials | [HTE / synthesis](../../CATALOG.md#materials-hte-synthesis) | 1 | [A-Lab Autonomous Solid-State Synthesis Dataset](https://www.nature.com/articles/s41586-023-06734-w) |
| Materials | [Lab automation & robotic chemistry](../../CATALOG.md#materials-lab-automation) | 2 | [Ada Self-Driving Lab Thin-Film Dataset](https://www.science.org/doi/10.1126/sciadv.aaz8867), [Argonne PolyBot Electronic-Polymer Dataset](https://www.nature.com/articles/s41467-024-55655-3) |
| Materials | [Magnetic materials](../../CATALOG.md#materials-magnetic) | 1 | [MAGNDATA (Bilbao Crystallographic Server)](https://www.cryst.ehu.es/magndata/) |
| Materials | [Membranes & separations](../../CATALOG.md#materials-membranes) | 1 | [Membrane Database - Polymer Gas Separation (MSA/CSIRO)](https://research.csiro.au/virtualscreening/membrane-database-polymer-gas-separation-membranes/) |
| Materials | [MOFs & porous materials](../../CATALOG.md#materials-mofs-porous) | 5 | [CoRE MOF 2024 Database](https://zenodo.org/records/15055758), [CoRE MOF Database (Computation-Ready, Experimental MOFs)](https://zenodo.org/records/3677685), [CSD MOF Subset (Cambridge Structural Database)](https://support.ccdc.cam.ac.uk/support/solutions/articles/103000306242-how-many-mofs-are-there-in-the-csd-), [and 2 more](../../CATALOG.md#materials-mofs-porous) |
| Materials | [Nanomaterials & nanosafety](../../CATALOG.md#materials-nanomaterials) | 1 | [eNanoMapper / NanoCommons Knowledge Base](https://www.nanocommons.eu/) |
| Materials | [Organic electronics](../../CATALOG.md#materials-organic-electronics) | 2 | [HOPV15 (Harvard Organic Photovoltaic Dataset)](https://figshare.com/articles/dataset/HOPV15_Dataset/1610063), [OCELOT Database (Organic Crystals in Electronic and Light-Oriented Technologies)](https://oscar.as.uky.edu/) |
| Materials | [Photovoltaics & solar cells](../../CATALOG.md#materials-photovoltaics) | 7 | [AMANDA / AMADAP Automated OPV-Perovskite Platform (Erlangen)](https://link.springer.com/article/10.1007/s10853-021-06281-7), [Autonomous Closed-Loop Perovskite Solar Cell Campaign (PVK_Passivation_ML)](https://github.com/ShuaihuaLu/PVK_Passivation_ML), [Emerging-PV Reports Database](https://emerging-pv.org/), [and 4 more](../../CATALOG.md#materials-photovoltaics) |
| Materials | [Polymers](../../CATALOG.md#materials-polymers) | 4 | [Khazana / Polymer Genome (Ramprasad Group)](https://khazana.gatech.edu/), [NanoMine / MaterialsMine](https://materialsmine.org/), [PoLyInfo (NIMS Polymer Database)](https://polymer.nims.go.jp/), [and 1 more](../../CATALOG.md#materials-polymers) |
| Materials | [Experimental spectra (XPS/Raman/XRD)](../../CATALOG.md#materials-spectra-exp) | 6 | [LIBS Benchmark Classification Dataset](https://springernature.figshare.com/articles/Training_dataset/11316578/1), [Multidimensional Photoemission Spectra of WSe2](https://zenodo.org/record/2704787), [NIST X-ray Photoelectron Spectroscopy Database (SRD 20)](https://srdata.nist.gov/xps/), [and 3 more](../../CATALOG.md#materials-spectra-exp) |
| Materials | [Superconductors](../../CATALOG.md#materials-superconductors) | 1 | [SuperCon (NIMS / MDR)](https://mdr.nims.go.jp/concern/datasets/mw22v8634?locale=en) |
| Materials | [Thermoelectrics](../../CATALOG.md#materials-thermoelectrics) | 3 | [ESTM — Experimentally Synthesized Thermoelectric Materials Dataset](https://github.com/KRICT-DATA/SIMD), [Starrydata2](https://www.starrydata2.org/), [teMatDb / teMatDb272](https://github.com/byungkiryu/teMatDb) |
| Materials | [Thermophysical properties](../../CATALOG.md#materials-thermophysical) | 1 | [NIST TRC ThermoML Archive](https://trc.nist.gov/ThermoML/) |

## Resources used or audited in this project

The following resources materially entered the research process. `Disposition` records their scientific role in this project; it is not a quality judgement on the upstream database.

### Adsorption thermodynamics

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [NIST/ARPA-E ISODB](https://adsorption.nist.gov/isodb/index.php) | artifact-gate analysis | conditional pooled regularity | Streamed from hash-pinned source archive | open; Public domain NIST/US Government |

### Alloy fatigue

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [C45 steel fatigue dataset](https://figshare.com/articles/dataset/FatigueData-C45/23007362) | recipient | null or unqualified external attempt | Associated article DOI 10.1038/s41597-023-02354-1 | open; CC-BY-4.0; [DOI](https://doi.org/10.6084/m9.figshare.23007362.v2) |

### Alloy mechanics

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [BIRDSHOT HTE alloys](https://zenodo.org/records/16396374) | recipient | below-gate external boundary | Temporal alloy campaign | open; CC-BY-4.0; [DOI](https://doi.org/10.5281/zenodo.16396374) |
| [Borg expanded MPEA dataset](https://figshare.com/articles/dataset/Expanded_dataset_of_mechanical_properties_and_observed_phases_of_multi-principal_element_alloys/12642953) | donor and recipient | provenance-specific positive and portability failure | UTS and yield-strength relations | open; Unknown; [DOI](https://doi.org/10.1038/s41597-020-00768-9) |
| [Matbench steels](https://figshare.com/articles/dataset/steels/7250453) | recipient | independent null | Official Matbench steel folds | open; CC-BY-4.0; [DOI](https://doi.org/10.6084/m9.figshare.7250453.v1) |

### Aqueous molecular properties

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [AqSolDB](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/OVHAW8) | donor and recipient | null control | Organic solubility target/source portfolio | open; CC0-1.0; [DOI](https://doi.org/10.1038/s41597-019-0151-1) |
| [FreeSolv](https://github.com/MobleyLab/FreeSolv) | donor and recipient | null control | Hydration free-energy source | open; CC-BY-3.0; [DOI](https://doi.org/10.1007/s10822-014-9747-x) |
| [IUPAC digitized pKa](https://github.com/IUPAC/Dissociation-Constants) | donor | null/control portfolio | Non-commercial upstream licence | open; CC-BY-NC-4.0; [DOI](https://doi.org/10.5281/zenodo.7236452) |

### Battery aging

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [CALCE battery data](https://web.calce.umd.edu/batteries/data/) | wrong-chemistry control | cross-lab control | Control source only | open; site-specific |
| [HUST battery lifecycle](https://data.mendeley.com/datasets/nsc7hnsg4s/2) | recipient | cross-lab abstention | Recipient source used through a constrained mirror in the completed audit | open; verify-upstream |
| [MATR fast-charging battery life](https://data.matr.io) | donor | cross-lab abstention | Raw source required for complete rerun | open; CC-BY-4.0 |
| [Multi-stage lithium-ion battery aging](https://figshare.com/articles/dataset/Multi-Stage_Lithium_Ion_Battery_Aging_Study/25975315) | recipient | non-evaluable frozen primary and diagnostic | 279 cells and 71 aging conditions; associated paper DOI 10.1038/s41597-024-03859-z | open; CC-BY-4.0; [DOI](https://doi.org/10.6084/m9.figshare.25975315.v1) |

### Electrocatalysis

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [Au-Ir-Rh SECCM libraries](https://zenodo.org/records/20439519) | donor and recipient | attention representation boundary | Three complete composition libraries with EDX XPS LSV and fitted kinetics; fitted target is derived from the input LSV | open; CC-BY-4.0; [DOI](https://doi.org/10.5281/zenodo.20439519) |
| [Caltech high-throughput Acid-OER](https://data.caltech.edu/records/tg041-j4g80) | donor/control | null portfolio component | Mn/Sb/Sn/Ti/Co oxide libraries | open; repository record; [DOI](https://doi.org/10.22002/tg041-j4g80) |
| [Caltech metal-oxide ORR](https://data.caltech.edu/records/1km87-52j70) | donor/control | null portfolio component | Mn/Ni/Mg/Ca/Fe/La/Y/In oxide catalysts | open; repository record; [DOI](https://doi.org/10.22002/D1.1632) |
| [OCx24](https://fair-chem.github.io/fair-chemistry-papers/#open-catalyst-experiments-2024-ocx24) | donor/control | null portfolio component | Current official paper entry; legacy direct dataset page retired; experimental and computational catalyst resource | open; CC-BY-4.0 data; MIT code; [DOI](https://doi.org/10.48550/arXiv.2411.11783) |
| [SpecGen robotic derivative OER](https://doi.org/10.1038/s44160-025-00983-5) | donor and recipients | main controlled routing case | Controlled catalyst derivative systems | publisher supplementary; verify-upstream; [DOI](https://doi.org/10.1038/s44160-025-00983-5) |
| [TRI four-plate OER](https://data.caltech.edu/records/7b106-nf257) | recipient | outcome-unseen null | Four experimental composition plates | open; repository record; [DOI](https://doi.org/10.22002/D1.1345) |

### Electrolyte transport

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [BambooMixer electrolyte conductivity](https://huggingface.co/ByteDance-Seed/bamboo_mixer/resolve/main/dataset/data.json) | donor | main positive relation transfer | Source data associated with BambooMixer | open; verify-upstream; [DOI](https://doi.org/10.1038/s42256-025-01173-w) |
| [CALiSol-23](https://www.nature.com/articles/s41597-024-03575-8) | donor and recipient | main and supplementary analyses | Literature-aggregated conductivity programme | open; CC-BY-4.0; [DOI](https://doi.org/10.1038/s41597-024-03575-8) |
| [FINALES electrolyte optimization](https://archive.materialscloud.org/records/61sz9-09m30) | recipient | main boundary | Associated paper DOI 10.1002/aenm.202403263 | open; CC-BY-4.0; [DOI](https://doi.org/10.24435/materialscloud:qt-1s) |
| [KIT/Juelich 5035 conductivity experiments](https://zenodo.org/records/7244939) | donor and recipient | supplement positive and Edison target | Controlled formulation-temperature series | open; CC-BY-4.0; [DOI](https://doi.org/10.5281/zenodo.7244939) |
| [LiAsF6 BambooMixer extension](https://huggingface.co/datasets/PKUAIBDA/Dataset_Bamboomixer_extension/resolve/main/LiAsF6_conductivity.json) | recipient | main positive unseen-salt test | External salt absent from source training | open; verify-upstream; [DOI](https://doi.org/10.1038/s42256-026-01277-x) |
| [SolventSeg LiPF6/EC/EMC](https://github.com/ndrewwang/SolventSeg/tree/beta) | recipient | main positive ranking test | Independent Oxford/Glasgow formulation programme | open; verify-upstream; [DOI](https://doi.org/10.5281/zenodo.6299956) |

### Molecular photochemistry

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [Photoswitch dataset](https://github.com/Ryan-Rhys/The-Photoswitch-Dataset) | donor | null/harmful optical portfolio | Experimental optical properties | open; MIT; [DOI](https://doi.org/10.1039/D2SC04306H) |

### Optoelectronics

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [Organic photovoltaic device database](https://figshare.com/articles/dataset/Database_for_Organic_Photovoltaic_Cells/12045567) | recipient | null external attempt | Associated article DOI 10.1038/s41597-020-00634-8 | open; CC-BY-4.0; [DOI](https://doi.org/10.6084/m9.figshare.12045567.v2) |

### Photocatalysis

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [Photocatalytic HER molecular dataset](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8372320/supplementaryFiles?includeInlineImage=false) | recipient | harmful Chemprop transfer | Blind set remained unopened after development gate failed | open article supplement; verify-upstream; [DOI](https://doi.org/10.1039/D1SC02150H) |

### Polymers

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [OpenPoly polymer benchmark](https://github.com/WangGroupFDU/Openpoly_benchmark) | donor and recipient | null portfolio component | Experimental polymer properties | open; MIT; [DOI](https://doi.org/10.1007/s10118-025-3402-y) |

### Solid ionic transport

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [Caltech experimental Li-ion conductivity](https://data.caltech.edu/records/23mvv-6gk43) | recipient | static ranking limited and adaptive null | 571 Li-containing compounds with DOI and ICSD provenance | open; CC0; [DOI](https://doi.org/10.22002/23mvv-6gk43) |
| [OBELiX](https://github.com/NRC-Mila/OBELiX) | donor and recipient | adaptive-search null | Experimental solid electrolyte conductivity | open; CC-BY-4.0; [DOI](https://doi.org/10.1039/D5DD00441A) |

### Thermoelectric transport

| Resource | Project role | Disposition | What it contributed | Access and licence |
|---|---|---|---|---|
| [ESTM thermoelectrics](https://github.com/KRICT-DATA/SIMD) | donor and recipient | null and ranking controls | Experimental thermoelectric transport | open; Unknown; [DOI](https://doi.org/10.1038/s41524-022-00897-2) |
| [Starrydata2](https://www.starrydata2.org/) | recipient | outcome-unseen null | Reference-separated transport series | open; upstream-specific |

## Task-specific resources outside the broad catalog

These records are included in the analysed-resource ledger but do not share an identifier with the broad catalog. Some are experiment-specific subsets or extensions rather than standalone general-purpose databases.

| Resource | Domain | Why it entered the project | Disposition |
|---|---|---|---|
| [C45 steel fatigue dataset](https://figshare.com/articles/dataset/FatigueData-C45/23007362) | alloy fatigue | Associated article DOI 10.1038/s41597-023-02354-1 | null or unqualified external attempt |
| [Matbench steels](https://figshare.com/articles/dataset/steels/7250453) | alloy mechanics | Official Matbench steel folds | independent null |
| [CALCE battery data](https://web.calce.umd.edu/batteries/data/) | battery aging | Control source only | cross-lab control |
| [HUST battery lifecycle](https://data.mendeley.com/datasets/nsc7hnsg4s/2) | battery aging | Recipient source used through a constrained mirror in the completed audit | cross-lab abstention |
| [MATR fast-charging battery life](https://data.matr.io) | battery aging | Raw source required for complete rerun | cross-lab abstention |
| [Multi-stage lithium-ion battery aging](https://figshare.com/articles/dataset/Multi-Stage_Lithium_Ion_Battery_Aging_Study/25975315) | battery aging | 279 cells and 71 aging conditions; associated paper DOI 10.1038/s41597-024-03859-z | non-evaluable frozen primary and diagnostic |
| [Au-Ir-Rh SECCM libraries](https://zenodo.org/records/20439519) | electrocatalysis | Three complete composition libraries with EDX XPS LSV and fitted kinetics; fitted target is derived from the input LSV | attention representation boundary |
| [Caltech high-throughput Acid-OER](https://data.caltech.edu/records/tg041-j4g80) | electrocatalysis | Mn/Sb/Sn/Ti/Co oxide libraries | null portfolio component |
| [Caltech metal-oxide ORR](https://data.caltech.edu/records/1km87-52j70) | electrocatalysis | Mn/Ni/Mg/Ca/Fe/La/Y/In oxide catalysts | null portfolio component |
| [SpecGen robotic derivative OER](https://doi.org/10.1038/s44160-025-00983-5) | electrocatalysis | Controlled catalyst derivative systems | main controlled routing case |
| [TRI four-plate OER](https://data.caltech.edu/records/7b106-nf257) | electrocatalysis | Four experimental composition plates | outcome-unseen null |
| [BambooMixer electrolyte conductivity](https://huggingface.co/ByteDance-Seed/bamboo_mixer/resolve/main/dataset/data.json) | electrolyte transport | Source data associated with BambooMixer | main positive relation transfer |
| [FINALES electrolyte optimization](https://archive.materialscloud.org/records/61sz9-09m30) | electrolyte transport | Associated paper DOI 10.1002/aenm.202403263 | main boundary |
| [LiAsF6 BambooMixer extension](https://huggingface.co/datasets/PKUAIBDA/Dataset_Bamboomixer_extension/resolve/main/LiAsF6_conductivity.json) | electrolyte transport | External salt absent from source training | main positive unseen-salt test |
| [SolventSeg LiPF6/EC/EMC](https://github.com/ndrewwang/SolventSeg/tree/beta) | electrolyte transport | Independent Oxford/Glasgow formulation programme | main positive ranking test |
| [Organic photovoltaic device database](https://figshare.com/articles/dataset/Database_for_Organic_Photovoltaic_Cells/12045567) | optoelectronics | Associated article DOI 10.1038/s41597-020-00634-8 | null external attempt |
| [Photocatalytic HER molecular dataset](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8372320/supplementaryFiles?includeInlineImage=false) | photocatalysis | Blind set remained unopened after development gate failed | harmful Chemprop transfer |
| [Caltech experimental Li-ion conductivity](https://data.caltech.edu/records/23mvv-6gk43) | solid ionic transport | 571 Li-containing compounds with DOI and ICSD provenance | static ranking limited and adaptive null |

## How to interpret project status

- **Main positive**: supports a claim-bearing prediction or screening result.
- **Main boundary**: defines where an unchanged borrowing route fails or abstains.
- **Supplementary positive**: informative evidence that does not lead the paper.
- **Null, harmful, or non-evaluable**: retained evidence against selective reporting.
- **Control or audit-only**: tests specificity, leakage, readiness, or artefacts.

Edge-level outcomes are recorded separately in the [attempt ledger](../evidence/ATTEMPT_LEDGER.csv), because one database can be useful for one endpoint and harmful for another.

## Data access and redistribution

Third-party raw files are not mirrored here by default. The [analysed-resource ledger](ANALYSED_RESOURCE_LEDGER.csv) records the primary URL, DOI, access route, upstream licence, and repository redistribution decision. The repository retains source-pinned metadata, analysis code, compact derived summaries, hashes, and small validation artefacts needed for the audit trail.

## Updating this guide

1. Add broad resources to `catalog/catalog.json`.
2. Add project-used or audited resources to `research/data/ANALYSED_RESOURCE_LEDGER.csv`.
3. Run `python scripts/build_exports.py`.
4. Run `python scripts/build_database_guide.py`.
5. Run `python scripts/validate_catalog.py` and the repository tests.

Last generated from the repository inventories; see version control for the exact source revisions.
