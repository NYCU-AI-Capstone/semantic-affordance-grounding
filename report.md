# HW5: Ontology-based Semantic Grounding — 設計報告

> AI Capstone 2026 — Group 04

### Group Members

| Member | Student ID |
|--------|------------|
| 謝侑哲 | 112550069 |
| 李佑軒 | 112550011 |
| 江秉璋 | 112550129 |
| 蔡承志 | 112550183 |
| 廖漢軒 | 112550087 |
| 張程翔 | 112550205 |

### Contribution Statements

| Member | Contribution Statement |
|--------|------------------------|
| 謝侑哲 | Contributed to the baseline ontology modeling by defining task objects, task roles, and affordance-related class usage for the three entry-level tasks. Concrete repository parts: `ontology/group-ontology.ttl`, `report.md`. |
| 李佑軒 | Contributed to the custom RDFLib reasoning workflow, including subclass/type inference and class-level affordance materialization for graspability inference. Concrete repository parts: `src/reasoning.py`, `ontology/inferred-results.ttl`. |
| 江秉璋 | Contributed to repository documentation and consistency checks, and reviewed/adjusted the logic connecting ontology modeling with the reasoning workflow. Concrete repository parts: `README.md`, `report.md`, `src/reasoning.py`, `ontology/group-ontology.ttl`. |
| 蔡承志 | Contributed to the SPARQL query layer for retrieving inferred graspable objects, task objects, and the advanced shell-game target. Concrete repository parts: `queries/graspable_objects.rq`, `queries/task_objects.rq`, `queries/concealing_cup.rq`. |
| 廖漢軒 | Contributed to the advanced shell-game ontology design, including the ball, concealment relation, candidate container roles, and target-cup inference pattern. Concrete repository parts: `ontology/group-ontology.ttl`, `queries/concealing_cup.rq`. |
| 張程翔 | Contributed to SHACL validation and generated output verification, including structural validation for object labels, task roles, and affordance materialization. Concrete repository parts: `shacl/shapes.ttl`, `shacl/validate.py`, `shacl/shacl_validation_report.txt`. |

---

## 1. Repository Contents

本 repository 包含 Group 04 針對 Homework 5 的所有檔案：

| 目錄/檔案 | 角色 |
|-----------|------|
| `ontology/group-ontology.ttl` | 組別自建 OWL ontology：`cap:GraspableObject` 與 `g04:BallConcealingCup` 推理模式、11 個物件 instances、class-level/anonymous affordance modeling、4 個 task individuals、advanced task 新詞彙 |
| `ontology/imports/course-affordance.ttl` | 官方課程共用 ontology |
| `ontology/imports/course-alignment.ttl` | 官方 SKOS 概念對齊 |
| `ontology/inferred-results.ttl` | 推理腳本自動生成的推理後 graph |
| `shacl/shapes.ttl` | SHACL 結構驗證 shapes |
| `queries/graspable_objects.rq` | 查詢推理後 GraspableObject 的 SPARQL |
| `queries/task_objects.rq` | 查詢所有任務物件的 SPARQL |
| `queries/concealing_cup.rq` | 查詢 advanced task 藏球目標杯的 SPARQL |
| `src/reasoning.py` | Python RDFLib 自訂推理 + 查詢腳本 |
| `shacl/validate.py` | pyshacl SHACL 驗證腳本 |
| `results/*_output.txt` | 三個 SPARQL 查詢結果文字檔 |
| `shacl/shacl_validation_report.txt` | SHACL 驗證報告（Conforms: True） |

物件規模：11 個 PhysicalObject 實例（7 baseline + 3 shell-game 杯 + 1 球）、
4 個 task instances（cupStacking、cutleryArrangement、blockCollection、shellGame）。
<!-- baseline affordance 不再逐物件命名為 `g04:graspAfford...` 等 individuals；推理腳本會從 course ontology 的
class-level restrictions materialize 匿名 affordance blank nodes。shell-game 杯的 concealment affordance
以匿名 blank node 描述，不建立具名 `g04:concealAfford...` individuals。 -->

---

## 2. Design Rationale

### 2.1 五層語義建模

本 ontology 嚴格區分五個語義層級：

1. **Object Type**：`cap:Cup`, `cap:Knife`, `g04:Ball` 等 — 描述物件的「是什麼」
2. **Task Role**：`cap:TargetObject`, `cap:ReferenceObject`, `g04:CandidateContainer` 等 — 描述物件在任務中「扮演什麼角色」
3. **Affordance**：`cap:GraspingAffordance`, `g04:ConcealmentAffordance` 等 — 描述物件「能被如何操作」
4. **Instance**：`g04:blueCup01`, `g04:shellCup02` 等 — 具體環境中「哪一個」物件
5. **Inferred Class**：`cap:GraspableObject`, `g04:BallConcealingCup` — 推理器根據定義「推導出」的類別

這種分層設計的目的是避免常見陷阱：把所有與任務相關的物件都直接標記為 graspable。
例如 basket 雖與 toy block collection 相關，但角色是容器（ContainerTarget），不是被抓取目標。

### 2.2 Affordance 建模：class-level restriction + anonymous blank node

本組不為每個 baseline 物件建立具名 affordance individual（例如不寫 `g04:graspAffordBlueCup01`）。
可抓取、可堆疊、支撐、容納等 affordance 由 course ontology 的 class-level existential restrictions 表示，
例如 `cap:Cup ⊑ ∃cap:hasAffordance.cap:GraspingAffordance`。因 RDFLib 不是完整 OWL reasoner，
`reasoning.py` 會將這些 restrictions materialize 成匿名 affordance blank nodes，再用於
`cap:GraspableObject` 分類。

此設計保留「存在某種 affordance」的 OWL 語意，同時避免為每個物件人工命名大量 affordance individuals。

### 2.3 Baseline 的 Plate / Basket 建模選擇

- **Plate**：`cap:ReferenceObject` + `cap:SupportAffordance`。cutlery arrangement 中是刀叉擺放的參考物，不需抓取。
- **Basket**：`cap:ContainerTarget` + `cap:ContainmentAffordance`。toy block collection 中是積木的目標容器，不是抓取對象。

### 2.4 Advanced Task：Shell Game（藏球猜杯，kitchen scene）

自定義進階任務：數個**外觀完全相同**的不透明杯子中，一顆球藏在其中一個杯子下並洗牌，
機器人必須抓起藏球的杯子。建模重點：

1. **同款多實例**：3 個杯子皆 `cap:Cup`、`hasColor "pink"`、`hasObjectLabel "shell_cup"`、`g04:isOpaque true`，
   外觀無從區分；它們是 3 個**獨立 individual**（不同物理杯、不同 pose frame），命名用純編號 `shellCup01/02/03`
   以強調是「同款杯的不同實例」。
2. **目標靠推理而非觀察**：機器人由感知/追蹤得到事實 `shellCup02 g04:conceals ball01`；
   「哪一杯是抓取目標」則由 `g04:BallConcealingCup` 等價類**推理**得出，而非斷言。
   這正是「graspable ≠ task target」—— 三杯都可抓，只有藏球的該抓。
3. **不洩漏答案**：3 杯都先掛 `g04:CandidateContainer`（候選）角色，無任何一杯被預先標記為答案。
4. **球不可抓**：`g04:ball01` 的 class 不導出 GraspingAffordance；機器只抓杯子、間接取球。
5. **顏色與透明度正交**：`cap:hasColor "pink"` 只記顏色，不透明用獨立 boolean `g04:isOpaque true`，
   **不**合併成 `"粉色不透明"` 這種混合字串（否則兩者皆不可查詢、且違反 `cap:hasColor` 語意）。
   不透明是 concealment affordance 成立的**感知前提**——正因杯子不透明、看不穿，目標杯才必須靠推理。
   `g04:isOpaque` 目前為純描述性事實，未接入推理鏈。
6. **桌子不建模**：桌子/檯面屬 kitchen scene 背景，不作為任務物件。

---

## 3. Namespace Policy

| Prefix | URI | 用途範圍 |
|--------|-----|----------|
| `cap:` | `https://hcis.io/ontology/aicapstone/2026/` | 課程共用詞彙：classes（`PhysicalObject`, `Cup`, `GraspableObject` 等）、properties、affordance/role classes |
| `g04:` | `https://hcis.io/ontology/aicapstone/2026/group04/` | Group 04 專屬詞彙：物件 instances、task instances、robot/gripper，以及 advanced task 新增的 class/property/role |

**原則**：
- 重用 `cap:` namespace 的現有 class 和 property，不重複定義。
- `cap:GraspableObject` 雖用 `cap:` namespace，但其 `owl:equivalentClass` 定義由本組在 `group-ontology.ttl` 提供。
- advanced task 的新詞彙（`g04:Ball`、`g04:BallConcealingCup`、`g04:ConcealmentAffordance`、`g04:CandidateContainer`、`g04:HiddenItem`、`g04:conceals`、`g04:concealedBy`、`g04:isOpaque`）一律置於 `g04:` namespace。
- 所有 group-specific individuals 均使用 `g04:` namespace。

---

## 4. Reused and Newly Introduced Terms

### 4.1 重用的 cap: 術語

| 術語 | 類型 | 來源 |
|------|------|------|
| `cap:PhysicalObject`, `cap:Cup`, `cap:Knife`, `cap:Fork`, `cap:Plate`, `cap:ToyBlock`, `cap:Basket` | owl:Class | course-affordance.ttl |
| `cap:Affordance`, `cap:GraspingAffordance`, `cap:SupportAffordance`, `cap:ContainmentAffordance`, `cap:StackabilityAffordance` | owl:Class | course-affordance.ttl |
| `cap:TaskRole`, `cap:TargetObject`, `cap:ReferenceObject`, `cap:ContainerTarget`, `cap:CollectableObject` | owl:Class | course-affordance.ttl |
| `cap:RobotAgent`, `cap:EndEffector`, `cap:Task`, `cap:ManipulationTask` | owl:Class | course-affordance.ttl |
| `cap:hasAffordance`, `cap:hasTaskRole`, `cap:hasTargetObject`, `cap:hasReferenceObject`, `cap:canBeManipulatedBy` | owl:ObjectProperty | course-affordance.ttl |
| `cap:hasObjectLabel`, `cap:hasColor`, `cap:hasPoseFrame` | owl:DatatypeProperty | course-affordance.ttl |

### 4.2 組別新增/定義的術語

| 術語 | 類型 | 定義位置 | 說明 |
|------|------|----------|------|
| `cap:GraspableObject` | owl:Class (equivalentClass) | group-ontology.ttl | baseline 推理目標 class |
| `g04:Ball` | owl:Class | group-ontology.ttl | advanced：被藏的小球（不可抓） |
| `g04:BallConcealingCup` | owl:Class (equivalentClass) | group-ontology.ttl | advanced：藏球的抓取目標 class |
| `g04:ConcealmentAffordance` | owl:Class (⊑ ContainmentAffordance) | group-ontology.ttl | advanced：杯子遮蔽小物的 affordance |
| `g04:CandidateContainer`, `g04:HiddenItem` | owl:Class (⊑ TaskRole) | group-ontology.ttl | advanced：候選杯/被藏物的 task role |
| `g04:conceals`, `g04:concealedBy` | owl:ObjectProperty | group-ontology.ttl | advanced：杯子藏球的關係 |
| `g04:isOpaque` | owl:DatatypeProperty (xsd:boolean) | group-ontology.ttl | advanced：杯子是否不透明（描述性，未入推理鏈） |
| `g04:blueCup01` 等 11 個 | owl:NamedIndividual | group-ontology.ttl | 環境物件 instances（7 baseline + 3 shell cup + 1 ball） |
| `g04:cupStackingTask` 等 4 個 | owl:NamedIndividual | group-ontology.ttl | Task instances（含 shellGameTask） |
| `g04:robotAgent01`, `g04:gripper01` | owl:NamedIndividual | group-ontology.ttl | Robot agent 與 end effector |

<!-- > 已滿足 advanced task 的建模要求（至少 1 個新 object class + 1 個新 affordance 或 task role）：
> 新增 2 個 class、1 個 affordance、2 個 task role、2 個 object property、1 個 datatype property。 -->

---

## 5. Key Axioms and Restrictions

### 5.1 GraspableObject equivalentClass 定義（baseline）

```turtle
cap:GraspableObject
    a owl:Class ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf (
            cap:PhysicalObject
            [ a owl:Restriction ;
              owl:onProperty cap:hasAffordance ;
              owl:someValuesFrom cap:GraspingAffordance ]
        )
    ] .
```

DL：`GraspableObject ≡ PhysicalObject ⊓ ∃hasAffordance.GraspingAffordance`

### 5.2 BallConcealingCup equivalentClass 定義（advanced task）

```turtle
g04:BallConcealingCup
    a owl:Class ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf (
            cap:Cup
            [ a owl:Restriction ;
              owl:onProperty g04:conceals ;
              owl:someValuesFrom g04:Ball ]
        )
    ] .
```

DL：`BallConcealingCup ≡ Cup ⊓ ∃conceals.Ball`。配合事實 `shellCup02 g04:conceals ball01`，
推理出 `shellCup02 a g04:BallConcealingCup`（抓取目標）。

### 5.3 Course Ontology 中的 subClassOf Restrictions

course-affordance.ttl 中的 restrictions：

| Class | Restriction | 效果 |
|-------|-------------|------|
| `cap:Cup` | `owl:someValuesFrom cap:GraspingAffordance`（與 StackabilityAffordance） | 所有 Cup 都應有 GraspingAffordance |
| `cap:Knife`, `cap:Fork`, `cap:ToyBlock` | `owl:someValuesFrom cap:GraspingAffordance` | 都應有 GraspingAffordance |
| `cap:Plate` | `owl:someValuesFrom cap:SupportAffordance` | 有 SupportAffordance，**沒有** GraspingAffordance |
| `cap:Basket` | `owl:someValuesFrom cap:ContainmentAffordance` | 有 ContainmentAffordance，**沒有** GraspingAffordance |

---

## 6. Reasoning Pattern

### 6.1 技術選擇

使用 **Python RDFLib**，搭配自訂推理邏輯。RDFLib 本身不支援完整 OWL 2 DL 推理，
因此本組實作了所需的推理步驟，並明確記錄推理機制。

### 6.2 推理流程

**階段 1：rdfs:subClassOf 傳遞性閉包** — 計算所有 class 的完整 subClassOf 繼承鏈（如 `cap:Cup → cap:PhysicalObject`）。

**階段 2：rdf:type 繼承推理** — 若 `X a C` 且 `C rdfs:subClassOf D`，推入 `X a D`（如 `g04:blueCup01 a cap:PhysicalObject`）。

**階段 2b：class-level affordance materialization** — 讀取 `C rdfs:subClassOf [ owl:onProperty cap:hasAffordance ; owl:someValuesFrom A ]`，
若 `X a C`，則為 `X` materialize 一個匿名 affordance blank node，並標記其 type 為 `A`。

**階段 3：GraspableObject 等價類推理** — 對每個 individual 檢查：(1) 是否為 `cap:PhysicalObject`，
(2) 是否透過 `cap:hasAffordance` 連到 `cap:GraspingAffordance`（可為階段 2b 產生的匿名 blank node）；兩者皆滿足 → 推入 `a cap:GraspableObject`。

**階段 4：BallConcealingCup 等價類推理（advanced）** — 對每個 `cap:Cup` 檢查是否透過 `g04:conceals`
連到 `g04:Ball` 實例；滿足 → 推入 `a g04:BallConcealingCup`（shell-game 抓取目標）。

### 6.3 推理與手動斷言的區別

- **手動斷言**（❌ 不正確）：直接寫 `g04:blueCup01 a cap:GraspableObject` 或 `shellCup02 a g04:BallConcealingCup`
- **推理得出**（✅ 正確）：ontology 只定義等價類語義，由推理腳本根據每個 individual 的屬性/關係自動判斷推入

特別地，shell game 的答案（哪一杯藏球）不是被斷言的，而是從感知事實 `conceals` 推理得到。

---

## 7. Query Results

### 7.1 `graspable_objects.rq` — 8 個 inferred GraspableObject

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

未出現：`g04:plate01`（class restriction 只導出 SupportAffordance）、`g04:basket01`（只導出 ContainmentAffordance）、`g04:ball01`（無 affordance restriction）。

### 7.2 `concealing_cup.rq` — 1 個 inferred 抓取目標（advanced task）

| cup | cupLabel | ball | ballLabel | poseFrame |
|-----|----------|------|-----------|-----------|
| `g04:shellCup02` | shell_cup | `g04:ball01` | ball | world/object_cup02 |

只回傳 `shellCup02`（同時是 GraspableObject 且為 BallConcealingCup）；空杯 `shellCup01`、`shellCup03` 不在結果中。

### 7.3 SHACL 驗證結果

`shacl/validate.py` 對 `shacl/shapes.ttl` 執行驗證，結果 **Conforms: True**（報告見 `shacl/shacl_validation_report.txt`）。驗證前會沿用 `reasoning.py` 的 class-level affordance materialization，使 SHACL 能看見由 restriction 導出的匿名 `cap:hasAffordance` blank nodes。SHACL 相關檔案集中於選用的 `shacl/` 資料夾。
驗證的結構約束：每個 `cap:PhysicalObject` 須有 `cap:hasObjectLabel`；每個任務目標須有 `cap:hasTaskRole` 與 `cap:hasAffordance`。

---

## 8. Design Choices and Limitations

### 8.1 設計選擇

1. **不使用逐物件具名 affordance 個體**：baseline affordance 由 class-level restrictions 表示，並在推理時 materialize 成匿名 blank nodes。
2. **GraspableObject 放在 cap: namespace**：雖定義在 group-ontology.ttl，但保持 `cap:GraspableObject` 命名；
   advanced task 的新詞彙則一律置於 `g04:`。
3. **兩個平行推理目標**：baseline 的 `GraspableObject` 與 advanced 的 `BallConcealingCup` 採同一 equivalentClass +
   existential restriction 模式，凸顯「可抓取」與「任務目標」的區分。
4. **顏色/透明度正交建模**：顏色與不透明度分別建模，避免混合成不可查詢的單一字串。

### 8.2 限制

1. **推理範圍有限**：自訂推理層僅實作 `rdfs:subClassOf` 傳遞性、type 繼承、以及
   `owl:equivalentClass` + `owl:intersectionOf` + `owl:someValuesFrom` 的特定模式，不支援完整 OWL 2 DL
   推理（disjointness、cardinality 等）。
2. **靜態狀態建模**：shell game 僅建模「洗牌後的最終狀態」，未建模洗牌動作或時序（fluents）；
   `g04:isOpaque` 等描述性屬性未接入推理鏈。
3. **靜態 Affordance**：affordance 靜態定義，未考慮動態環境變化或 gripper capability constraints（如夾爪寬度 vs 物件尺寸）。
4. **SHACL 為選用補充**：已實作結構驗證（`shapes.ttl` + `validate.py`，Conforms: True）。
   「advanced task 須定義新 class + affordance/role」屬 TBox meta-constraint，不適合用 instance SHACL 表達，
   改以設計保證。
