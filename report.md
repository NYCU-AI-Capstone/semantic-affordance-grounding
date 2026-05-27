# HW5: Ontology-based Semantic Grounding — 設計報告

> AI Capstone 2026 — Group 04

---

## 1. Repository Contents

本 repository 包含 Group 04 針對 Homework 5 的完整交付物：

| 目錄/檔案 | 角色 |
|-----------|------|
| `ontology/group-ontology.ttl` | 組別自建的 OWL ontology，定義 `cap:GraspableObject` 推理模式、7 個物件 instances、affordance individuals、task individuals |
| `ontology/imports/course-affordance.ttl` | 官方提供的課程共用 ontology（匯入用） |
| `ontology/imports/course-alignment.ttl` | 官方提供的 SKOS 概念對齊（參考用） |
| `ontology/inferred-results.ttl` | 推理腳本自動生成的推理後 graph |
| `queries/graspable_objects.rq` | 查詢推理後 GraspableObject 的 SPARQL |
| `queries/task_objects.rq` | 查詢所有任務物件的 SPARQL |
| `src/reasoning.py` | Python RDFLib 推理腳本 |
| `results/graspable_objects_output.txt` | SPARQL 查詢結果文字檔 |

---

## 2. Design Rationale

### 2.1 五層語義建模

本 ontology 嚴格區分五個語義層級（PDF §6）：

1. **Object Type**：`cap:Cup`, `cap:Knife` 等 — 描述物件的「是什麼」
2. **Task Role**：`cap:TargetObject`, `cap:ReferenceObject` 等 — 描述物件在任務中「扮演什麼角色」
3. **Affordance**：`cap:GraspingAffordance`, `cap:SupportAffordance` 等 — 描述物件「能被如何操作」
4. **Instance**：`g04:blueCup01` 等 — 具體環境中「哪一個」物件
5. **Inferred Class**：`cap:GraspableObject` — 推理器根據定義「推導出」的類別

這種分層設計的目的是避免 PDF §18 指出的常見陷阱：把所有與任務相關的物件都直接標記為 graspable。例如，basket 雖然與 toy block collection 任務相關，但它的角色是容器（ContainerTarget），不是被抓取的目標。

### 2.2 Affordance 個體化

每個物件的 affordance 使用獨立的 individual（如 `g04:graspAffordBlueCup01`），而不是所有物件共享同一個 affordance 個體。這樣的設計有兩個好處：
- 更精確地對應 OWL existential restriction 的語義：每個物件「有一個」屬於 GraspingAffordance 類型的 affordance
- 未來可以為不同物件的 affordance 附加不同的屬性（如 grasp width、force 等）

### 2.3 Plate 和 Basket 的建模選擇

- **Plate**：被建模為 `cap:ReferenceObject`，附帶 `cap:SupportAffordance`。在 cutlery arrangement 任務中，plate 是刀叉擺放的參考物，機器人不需要抓取它。
- **Basket**：被建模為 `cap:ContainerTarget`，附帶 `cap:ContainmentAffordance`。在 toy block collection 任務中，basket 是積木的目標容器，不是抓取對象。

---

## 3. Namespace Policy

| Prefix | URI | 用途範圍 |
|--------|-----|----------|
| `cap:` | `https://hcis.io/ontology/aicapstone/2026/` | 課程共用詞彙：classes（`PhysicalObject`, `Cup`, `GraspableObject` 等）、properties（`hasAffordance`, `hasTaskRole` 等）、affordance/role classes |
| `g04:` | `https://hcis.io/ontology/aicapstone/2026/group04/` | Group 04 專屬詞彙：物件 instances（`blueCup01` 等）、affordance instances（`graspAffordBlueCup01` 等）、task instances（`cupStackingTask` 等）、robot/gripper instances |

**原則**：
- 重用 `cap:` namespace 的現有 class 和 property，不重複定義
- `cap:GraspableObject` 雖使用 `cap:` namespace，但其 `owl:equivalentClass` 定義由本組在 `group-ontology.ttl` 中提供（因官方 course-affordance.ttl 未包含此定義）
- 所有 group-specific individuals 均使用 `g04:` namespace

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
| `cap:GraspableObject` | owl:Class (equivalentClass) | group-ontology.ttl | 推理目標 class，使用 owl:equivalentClass 定義 |
| `g04:blueCup01` 等 7 個 | owl:NamedIndividual | group-ontology.ttl | 環境物件 instances |
| `g04:graspAffordBlueCup01` 等 10 個 | owl:NamedIndividual | group-ontology.ttl | Affordance instances |
| `g04:cupStackingTask` 等 3 個 | owl:NamedIndividual | group-ontology.ttl | Task instances |
| `g04:robotAgent01`, `g04:gripper01` | owl:NamedIndividual | group-ontology.ttl | Robot agent 與 end effector |

---

## 5. Key Axioms and Restrictions

### 5.1 GraspableObject equivalentClass 定義

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

Description Logic 表示：`GraspableObject ≡ PhysicalObject ⊓ ∃hasAffordance.GraspingAffordance`

### 5.2 Course Ontology 中的 subClassOf Restrictions

官方 course-affordance.ttl 中的 restrictions 是推理能成功的關鍵前提：

| Class | Restriction | 效果 |
|-------|-------------|------|
| `cap:Cup` | `rdfs:subClassOf [owl:onProperty cap:hasAffordance ; owl:someValuesFrom cap:GraspingAffordance]` | 所有 Cup 都應有 GraspingAffordance |
| `cap:Knife` | 同上 | 所有 Knife 都應有 GraspingAffordance |
| `cap:Fork` | 同上 | 所有 Fork 都應有 GraspingAffordance |
| `cap:ToyBlock` | 同上 | 所有 ToyBlock 都應有 GraspingAffordance |
| `cap:Plate` | `owl:someValuesFrom cap:SupportAffordance` | Plate 有 SupportAffordance，**沒有** GraspingAffordance |
| `cap:Basket` | `owl:someValuesFrom cap:ContainmentAffordance` | Basket 有 ContainmentAffordance，**沒有** GraspingAffordance |

---

## 6. Reasoning Pattern

### 6.1 技術選擇

使用 **Python RDFLib**（Option C），搭配自訂推理規則層。RDFLib 本身不支援完整 OWL 2 DL 推理，因此本腳本實作了所需的三個推理步驟。

### 6.2 三階段推理流程

**階段 1：rdfs:subClassOf 傳遞性閉包**
- 計算所有 class 的完整 subClassOf 繼承鏈
- 例：`cap:Cup → cap:PhysicalObject`

**階段 2：rdf:type 繼承推理**
- 若 `X rdf:type C` 且 `C rdfs:subClassOf D`，則推入 `X rdf:type D`
- 例：`g04:blueCup01 a cap:Cup` → 推入 `g04:blueCup01 a cap:PhysicalObject`

**階段 3：GraspableObject 等價類推理**
- 對每個 named individual 檢查：
  1. 是否為 `cap:PhysicalObject`（經過階段 2 的 type 繼承）
  2. 是否透過 `cap:hasAffordance` 連結到 `cap:GraspingAffordance` 實例
- 兩條件皆滿足 → 推入 `rdf:type cap:GraspableObject`

### 6.3 推理與手動斷言的區別

- **手動斷言**方式（❌ 不正確）：在 ontology 中直接寫 `g04:blueCup01 a cap:GraspableObject`
- **推理得出**方式（✅ 正確）：ontology 中只定義 `cap:GraspableObject` 的 equivalentClass 語義，透過推理腳本根據每個 individual 的屬性自動判斷並推入

---

## 7. Query Results

推理完成後，`graspable_objects.rq` 查詢回傳 5 個 inferred GraspableObject：

| obj | label | role |
|-----|-------|------|
| `g04:block01` | toy_block | `cap:CollectableObject` |
| `g04:blueCup01` | blue_cup | `cap:TargetObject` |
| `g04:fork01` | fork | `cap:TargetObject` |
| `g04:knife01` | knife | `cap:TargetObject` |
| `g04:pinkCup01` | pink_cup | `cap:TargetObject` |

未出現在結果中的物件：
- `g04:plate01`：只有 SupportAffordance，不滿足 GraspableObject 條件
- `g04:basket01`：只有 ContainmentAffordance，不滿足 GraspableObject 條件

---

## 8. Design Choices and Limitations

### 8.1 設計選擇

1. **OWL Punning for Task Roles**：`cap:hasTaskRole cap:TargetObject` 將 class 作為 individual 使用（OWL punning），遵循 PDF Listing 4 的範例模式。
2. **每物件獨立 affordance 個體**：避免語義歧義，支持未來擴展。
3. **GraspableObject 放在 cap: namespace**：雖然定義在 group-ontology.ttl 中，但遵循 PDF §8 的描述保持 `cap:GraspableObject` 命名。

### 8.2 限制

1. **推理範圍有限**：自訂推理層僅實作 `rdfs:subClassOf` 傳遞性、type 繼承、和 `owl:equivalentClass` + `owl:intersectionOf` + `owl:someValuesFrom` 的特定模式。不支援完整 OWL 2 DL 推理（如 disjointness、cardinality restrictions 等）。
2. **未實作 SHACL 驗證**：PDF §15 建議的 SHACL 驗證為可選項目，本組未實作。
3. **靜態 Affordance 建模**：Affordance 在 ontology 中靜態定義，未考慮動態環境變化或 gripper capability constraints。
