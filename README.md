# HW5: Ontology-based Semantic Grounding

> AI Capstone 2026 — Group 04

## 1. Project Title and Group Members

**Homework 5: Ontology-based Semantic Grounding**

| Member | Student ID |
|--------|------------|
| 謝侑哲 | 112550069 |
| 李佑軒 | 112550011 |
| 江秉璋 | 112550129 |
| 蔡承志 | 112550183 |
| 廖漢軒 | 112550087 |
| 張程翔 | 112550205 |

## 2. Selected Tasks

本組涵蓋作業要求的三個 entry-level 任務，並額外實作一個自定義 advanced task：

**Entry-level（baseline，必做）**
1. **Cup Stacking** — 機器人抓取並堆疊藍色杯與粉紅色杯
2. **Cutlery Arrangement** — 機器人抓取刀叉並相對盤子擺放
3. **Toy Block Collection** — 機器人抓取積木並放入籃子

**Advanced Task（自定義）**
4. **Shell Game（藏球猜杯，kitchen scene）** — 數個**外觀完全相同**的不透明杯子中，
   一顆小球藏在其中一個杯子下並經過洗牌；機器人必須抓起**藏有球的那個杯子**。
   關鍵在於「哪一個杯子是抓取目標」無法由外觀判斷，而是由 reasoner **推理**得出
   （`g04:BallConcealingCup`）。這清楚示範了本專案的核心區分：
   **「可抓取（graspable）」≠「任務目標（task target）」**——三個杯子都可抓，但只有藏球的那一個是該抓的。

## 3. Ontology Design

本體論採用五層語義建模結構：

| Layer | Description | Example |
|-------|-------------|---------|
| **Object Type** | 共用的物件類別 | `cap:Cup`, `cap:Knife`, `cap:Fork`, `cap:Plate`, `cap:ToyBlock`, `cap:Basket`, `g04:Ball` |
| **Task Role** | 物件在任務中的角色 | `cap:TargetObject`, `cap:ReferenceObject`, `cap:ContainerTarget`, `cap:CollectableObject`, `g04:CandidateContainer`, `g04:HiddenItem` |
| **Affordance** | 物件的操作可能性 | `cap:GraspingAffordance`, `cap:SupportAffordance`, `cap:ContainmentAffordance`, `cap:StackabilityAffordance`, `g04:ConcealmentAffordance` |
| **Instance** | 組別專屬的具體物件個體 | `g04:blueCup01`, `g04:knife01`, `g04:block01`, `g04:shellCup02`, `g04:ball01` |
| **Inferred Class** | 推理器推導出的類別成員 | `g04:blueCup01 a cap:GraspableObject`；`g04:shellCup02 a g04:BallConcealingCup` |

### 核心推理模式（兩個推理目標）

**(1) GraspableObject**（baseline + advanced 共用）

```
cap:GraspableObject ≡ cap:PhysicalObject ⊓ ∃cap:hasAffordance.cap:GraspingAffordance
```

物件若是 `cap:PhysicalObject` 且具有至少一個 `cap:GraspingAffordance`，即被推理為 `cap:GraspableObject`。

**(2) BallConcealingCup**（advanced task，shell-game 抓取目標）

```
g04:BallConcealingCup ≡ cap:Cup ⊓ ∃g04:conceals.g04:Ball
```

某個杯子若藏著（`g04:conceals`）一顆球，即被推理為 `g04:BallConcealingCup`——也就是機器人該抓的杯子。
`g04:conceals shellCup02 → ball01` 是感知/追蹤得到的**事實斷言**；「哪一杯是目標」則是**推理結果**。

<!-- > **匯入依賴說明**：`ontology/imports/course-affordance.ttl` 與 `course-alignment.ttl`
> 為官方提供的課程資源。經與原始檔比對與 RDFLib 解析確認，原始 TTL 可正常解析；
> 本 repository 內的 imports 版本僅作為可重現執行所需的匯入依賴。 -->

## 4. Modeled Objects and Affordances

**Baseline 物件**

| Object | Type | Color | Task Role | Affordances | Graspable |
|--------|------|-------|-----------|-------------|------------|
| `g04:blueCup01` | `cap:Cup` | blue | `cap:TargetObject` | Grasping, Stackability | ✅ Yes (inferred) |
| `g04:pinkCup01` | `cap:Cup` | pink | `cap:TargetObject` | Grasping, Stackability | ✅ Yes (inferred) |
| `g04:knife01` | `cap:Knife` | silver | `cap:TargetObject` | Grasping | ✅ Yes (inferred) |
| `g04:fork01` | `cap:Fork` | silver | `cap:TargetObject` | Grasping | ✅ Yes (inferred) |
| `g04:plate01` | `cap:Plate` | white | `cap:ReferenceObject` | Support | ❌ No |
| `g04:block01` | `cap:ToyBlock` | red | `cap:CollectableObject` | Grasping | ✅ Yes (inferred) |
| `g04:basket01` | `cap:Basket` | brown | `cap:ContainerTarget` | Containment | ❌ No |

**Advanced task 物件（Shell Game）** — 三個杯子刻意設為**同類別、同顏色、同 label、皆不透明**，僅靠 identity / pose frame 區分。

| Object | Type | Color | Opaque | Task Role | Affordances | Graspable | BallConcealingCup |
|--------|------|-------|--------|-----------|-------------|------------|--------------------|
| `g04:shellCup01` | `cap:Cup` | pink | true | `g04:CandidateContainer` | Grasping, Concealment | ✅ Yes (inferred) | ❌ No |
| `g04:shellCup02` | `cap:Cup` | pink | true | `g04:CandidateContainer` | Grasping, Concealment | ✅ Yes (inferred) | ✅ **Yes (inferred)** |
| `g04:shellCup03` | `cap:Cup` | pink | true | `g04:CandidateContainer` | Grasping, Concealment | ✅ Yes (inferred) | ❌ No |
| `g04:ball01` | `g04:Ball` | white | — | `g04:HiddenItem` | （無）| ❌ No | — |

**設計決策**：
- baseline 物件不逐一宣告具名 affordance individual；`reasoning.py` 會根據 class-level `owl:someValuesFrom` restrictions materialize 匿名 affordance blank nodes。
- `plate01`、`basket01` 不被推理為 GraspableObject（擔任參考物/容器；其 class restriction 只導出 Support/Containment，而非 `GraspingAffordance`）。
- `ball01` 的 class 不導出 `GraspingAffordance`：機器只抓杯子、間接取球，故球不可抓。
- 三個 shell cup 都可抓（由 `cap:Cup` 的 `GraspingAffordance` restriction 導出），但只有藏球的 `shellCup02` 被推理為 `BallConcealingCup`（抓取目標）。
- 顏色與不透明拆成兩個正交屬性：`cap:hasColor "pink"` 記顏色、`g04:isOpaque true` 記不透明，**不**合併成混合字串。不透明是 concealment 成立的感知前提——正因看不穿，目標杯才須靠推理而非觀察。

## 5. Namespace Policy

| Prefix | Namespace URI | 用途 |
|--------|--------------|------|
| `cap:` | `https://hcis.io/ontology/aicapstone/2026/` | 課程共用詞彙（classes, properties, affordances） |
| `g04:` | `https://hcis.io/ontology/aicapstone/2026/group04/` | Group 04 專屬詞彙（instances, advanced 新類別/屬性/角色） |

- **`cap:`** namespace 下的 term 來自官方 `course-affordance.ttl`，加上 `cap:GraspableObject`。
- **`g04:`** namespace 下的 term 由本組定義，包括所有 instances，以及 advanced task 新增的
  class（`g04:Ball`、`g04:BallConcealingCup`）、affordance（`g04:ConcealmentAffordance`）、
  task role（`g04:CandidateContainer`、`g04:HiddenItem`）、object property（`g04:conceals`、`g04:concealedBy`）、
  datatype property（`g04:isOpaque`）。
- 本組**不**在 `cap:` namespace 下放置 group-specific 的物件類別或實例（`cap:GraspableObject` 推理目標除外）。

## 6. Instructions for Running the Query

### 環境建置

```bash
# 建立 conda 虛擬環境
conda create -n hw5-ontology python=3.11 -y
conda activate hw5-ontology

# 安裝依賴（rdflib + pyshacl）
pip install -r requirements.txt
```

### 執行推理與查詢

```bash
# 從專案根目錄執行
python src/reasoning.py
```

這會：
1. 載入 `ontology/imports/course-affordance.ttl` 和 `ontology/group-ontology.ttl`
2. 執行推理流程（subClassOf 閉包 → type 繼承 → class-level affordance materialization → GraspableObject 分類 → BallConcealingCup 分類）
3. 執行三個 SPARQL 查詢（`graspable_objects.rq`、`task_objects.rq`、`concealing_cup.rq`）
4. 匯出推理結果至 `ontology/inferred-results.ttl`
5. 儲存查詢結果至 `results/*_output.txt`

### SHACL 結構驗證

```bash
python shacl/validate.py
```

用 `shacl/shapes.ttl` 驗證圖是否滿足結構約束（每個 PhysicalObject 有 objectLabel、
每個任務目標有 taskRole + affordance），結果為 **Conforms: True**，報告存
`shacl/shacl_validation_report.txt`。驗證前會沿用 `reasoning.py` 的 class-level affordance materialization，
讓 SHACL 能看見由 restriction 導出的匿名 affordance blank nodes。這示範了「OWL 推理（infer）」與「SHACL 驗證（validate）」的分工。
所有 SHACL 相關檔案集中於選用的 `shacl/` 資料夾。

<!-- > Windows 提示：腳本啟動時會強制 stdout 使用 UTF-8，狀態標示一律純 ASCII（`[INFERRED]`/`[YES]`/`[NO]`），
> 助教不需設定任何環境變數即可直接執行。 -->

## 7. Expected Query Output

### `graspable_objects.rq` — 8 個 inferred GraspableObject

| obj | label | role |
|-----|-------|------|
| `g04:block01` | toy_block | `cap:CollectableObject` |
| `g04:blueCup01` | blue_cup | `cap:TargetObject` |
| `g04:fork01` | fork | `cap:TargetObject` |
| `g04:knife01` | knife | `cap:TargetObject` |
| `g04:pinkCup01` | pink_cup | `cap:TargetObject` |
| `g04:shellCup01` | shell_cup | `g04:CandidateContainer` |
| `g04:shellCup02` | shell_cup | `g04:CandidateContainer` |
| `g04:shellCup03` | shell_cup | `g04:CandidateContainer` |

`g04:plate01`、`g04:basket01`、`g04:ball01` **不會**出現在結果中。

### `concealing_cup.rq` — 1 個 inferred 抓取目標（advanced task）

| cup | cupLabel | ball | ballLabel | poseFrame |
|-----|----------|------|-----------|-----------|
| `g04:shellCup02` | shell_cup | `g04:ball01` | ball | world/object_cup02 |

只回傳 `shellCup02`（同時是 GraspableObject 且為 BallConcealingCup）；空杯 `shellCup01`、`shellCup03` 不在結果中。

## 8. What is Inferred vs Asserted

### Asserted（直接斷言）
- 物件類型：`g04:blueCup01 a cap:Cup`、`g04:shellCup02 a cap:Cup`、`g04:ball01 a g04:Ball`
- Advanced 描述性 affordance：shell-game 杯使用匿名 blank node 斷言 `cap:hasAffordance [ a g04:ConcealmentAffordance ]`
- Task Role：`g04:blueCup01 cap:hasTaskRole cap:TargetObject`
- 感知事實：`g04:shellCup02 g04:conceals g04:ball01`（球在哪個杯子下，由感知/追蹤得到）
- Class 階層：`cap:Cup rdfs:subClassOf cap:PhysicalObject`

### Inferred（推理得出）
- **Type 繼承**：`g04:blueCup01 a cap:PhysicalObject`（透過 subClassOf）
- **匿名 affordance materialization**：`cap:Cup` 的 `∃cap:hasAffordance.cap:GraspingAffordance` restriction 使 `g04:blueCup01` 取得匿名 `GraspingAffordance` blank node
- **GraspableObject 分類**：`g04:blueCup01 a cap:GraspableObject`（透過 `owl:equivalentClass` 定義）
- **BallConcealingCup 分類**：`g04:shellCup02 a g04:BallConcealingCup`（透過 `owl:equivalentClass` + `g04:conceals` 事實推理出的抓取目標）

兩個 inferred class 都完全由 OWL 定義驅動，**不是**手動寫入。特別是 shell game 的答案（哪一杯）
不是被斷言的，而是從 `conceals` 事實推理出來——避免手動斷言所有結果。

## 9. How `inferred-results.ttl` Was Generated

`ontology/inferred-results.ttl` 由 `src/reasoning.py` 自動生成，流程如下：

1. **載入**：RDFLib 解析 course-affordance.ttl 和 group-ontology.ttl 到同一個 RDF graph
2. **階段 1**：計算 `rdfs:subClassOf` 的傳遞性閉包
3. **階段 2**：根據 subClassOf 繼承推入缺失的 `rdf:type` triples（如 `g04:blueCup01 a cap:PhysicalObject`）
4. **階段 2b**：讀取 class-level `cap:hasAffordance some ...` restrictions，為物件 materialize 匿名 affordance blank nodes
5. **階段 3**：解析 `cap:GraspableObject` 的 `owl:equivalentClass` 定義，對滿足條件的 individual 推入 `rdf:type cap:GraspableObject`
6. **階段 4**：解析 `g04:BallConcealingCup` 的 `owl:equivalentClass` 定義，對「是 Cup 且 conceals 某 Ball」的杯子推入 `rdf:type g04:BallConcealingCup`
7. **序列化**：將完整的推理後 graph（原始 + 推理新增的 triples）序列化為 Turtle

由於 RDFLib 不內建完整 OWL 推理器，本腳本實作自訂的推理規則層來完成所需的 class classification。
推理摘要：11 個 PhysicalObject → 8 個 GraspableObject、1 個 BallConcealingCup（shellCup02）。

## 10. File Links

### Ontology Files
| File | Description | Authored By |
|------|-------------|-------------|
| [group-ontology.ttl](ontology/group-ontology.ttl) | Group 04 ontology | Group 04 |
| [inferred-results.ttl](ontology/inferred-results.ttl) | 推理後的完整 graph | reasoning.py |
| [course-affordance.ttl](ontology/imports/course-affordance.ttl) | 課程共用 ontology | Course |
| [course-alignment.ttl](ontology/imports/course-alignment.ttl) | SKOS 對齊 | Course |

### Query Files
| File | Description |
|------|-------------|
| [graspable_objects.rq](queries/graspable_objects.rq) | 查詢推理後的 GraspableObject |
| [task_objects.rq](queries/task_objects.rq) | 查詢所有任務物件與 affordance |
| [concealing_cup.rq](queries/concealing_cup.rq) | 查詢 advanced task 的藏球抓取目標杯 |

### Source Code
| File | Description |
|------|-------------|
| [reasoning.py](src/reasoning.py) | Python RDFLib 自訂推理 + SPARQL 查詢腳本 |

### Result Files
| File | Description |
|------|-------------|
| [graspable_objects_output.txt](results/graspable_objects_output.txt) | GraspableObject 查詢結果 |
| [task_objects_output.txt](results/task_objects_output.txt) | 任務物件查詢結果 |
| [concealing_cup_output.txt](results/concealing_cup_output.txt) | 藏球目標杯查詢結果 |

### SHACL Validation
| File | Description |
|------|-------------|
| [shapes.ttl](shacl/shapes.ttl) | SHACL 結構驗證 shapes |
| [validate.py](shacl/validate.py) | pyshacl SHACL 結構驗證腳本 |
| [shacl_validation_report.txt](shacl/shacl_validation_report.txt) | SHACL 驗證報告 |

### Documentation
| File | Description |
|------|-------------|
| [report.md](report.md) | 作業報告 |


## Repository Structure

```
semantic-affordance-grounding/
├── README.md                         ← 本文件
├── report.md                         ← 設計報告
├── requirements.txt                  ← Python 依賴（rdflib + pyshacl）
├── ontology/
│   ├── group-ontology.ttl            ← 【組別自建】Group 04 ontology
│   ├── inferred-results.ttl          ← 【自動生成】推理後的 graph
│   └── imports/
│       ├── course-affordance.ttl     ← 【官方提供】課程共用 ontology
│       └── course-alignment.ttl      ← 【官方提供】SKOS 對齊
├── queries/
│   ├── graspable_objects.rq          ← 【必要】GraspableObject 查詢
│   ├── task_objects.rq               ← 【推薦】任務物件查詢
│   └── concealing_cup.rq             ← 【advanced】藏球目標杯查詢
├── results/
│   ├── graspable_objects_output.txt  ← 【自動生成】查詢結果
│   ├── task_objects_output.txt       ← 【自動生成】查詢結果
│   └── concealing_cup_output.txt     ← 【自動生成】查詢結果
├── src/
│   └── reasoning.py                  ← Python 自訂推理腳本
└── shacl/                            ← 【選用】SHACL 結構驗證
    ├── shapes.ttl                    ← SHACL shapes
    ├── validate.py                   ← pyshacl 驗證腳本
    └── shacl_validation_report.txt   ← 【自動生成】驗證報告
```
