# HW5: Ontology-based Semantic Grounding

> AI Capstone 2026 — Group 04

## 1. Project Title and Group Members

**Homework 5: Ontology-based Semantic Grounding**

| Member | Student ID |
|--------|------------|
| (待補充) | (待補充) |

## 2. Selected Tasks

本組涵蓋作業要求的三個基本任務：

1. **Cup Stacking** — 機器人抓取並堆疊藍色杯與粉紅色杯
2. **Cutlery Arrangement** — 機器人抓取刀叉並相對盤子擺放
3. **Toy Block Collection** — 機器人抓取積木並放入籃子

## 3. Ontology Design

本體論採用五層語義建模結構（PDF §6）：

| Layer | Description | Example |
|-------|-------------|---------|
| **Object Type** | 共用的物件類別 | `cap:Cup`, `cap:Knife`, `cap:Fork`, `cap:Plate`, `cap:ToyBlock`, `cap:Basket` |
| **Task Role** | 物件在任務中的角色 | `cap:TargetObject`, `cap:ReferenceObject`, `cap:ContainerTarget`, `cap:CollectableObject` |
| **Affordance** | 物件的操作可能性 | `cap:GraspingAffordance`, `cap:SupportAffordance`, `cap:ContainmentAffordance`, `cap:StackabilityAffordance` |
| **Instance** | 組別專屬的具體物件個體 | `g04:blueCup01`, `g04:knife01`, `g04:block01` |
| **Inferred Class** | 推理器推導出的類別成員 | `g04:blueCup01 rdf:type cap:GraspableObject` |

### 核心推理模式

`cap:GraspableObject` 使用 OWL `owl:equivalentClass` 定義（PDF §11）：

```
cap:GraspableObject ≡ cap:PhysicalObject ⊓ ∃cap:hasAffordance.cap:GraspingAffordance
```

意即：一個物件若是 `cap:PhysicalObject` 且具有至少一個 `cap:GraspingAffordance` 類型的 affordance，即被推理為 `cap:GraspableObject`。

## 4. Modeled Objects and Affordances

| Object | Type | Color | Task Role | Affordances | Graspable? |
|--------|------|-------|-----------|-------------|------------|
| `g04:blueCup01` | `cap:Cup` | blue | `cap:TargetObject` | GraspingAffordance, StackabilityAffordance | ✅ Yes (inferred) |
| `g04:pinkCup01` | `cap:Cup` | pink | `cap:TargetObject` | GraspingAffordance, StackabilityAffordance | ✅ Yes (inferred) |
| `g04:knife01` | `cap:Knife` | silver | `cap:TargetObject` | GraspingAffordance | ✅ Yes (inferred) |
| `g04:fork01` | `cap:Fork` | silver | `cap:TargetObject` | GraspingAffordance | ✅ Yes (inferred) |
| `g04:plate01` | `cap:Plate` | white | `cap:ReferenceObject` | SupportAffordance | ❌ No |
| `g04:block01` | `cap:ToyBlock` | red | `cap:CollectableObject` | GraspingAffordance | ✅ Yes (inferred) |
| `g04:basket01` | `cap:Basket` | brown | `cap:ContainerTarget` | ContainmentAffordance | ❌ No |

**設計決策**：`plate01` 和 `basket01` 不被推理為 GraspableObject，因為它們在任務中分別擔任參考物和容器角色，不具備 `GraspingAffordance`。

## 5. Namespace Policy

| Prefix | Namespace URI | 用途 |
|--------|--------------|------|
| `cap:` | `https://hcis.io/ontology/aicapstone/2026/` | 課程共用詞彙（classes, properties, affordances） |
| `g04:` | `https://hcis.io/ontology/aicapstone/2026/group04/` | Group 04 專屬詞彙（instances, affordance individuals） |

- **`cap:`** namespace 下的 term 來自官方 `course-affordance.ttl`，加上 `cap:GraspableObject`（各組需自行定義）
- **`g04:`** namespace 下的 term 由本組自行定義，包括所有物件 instances、affordance instances、task instances

## 6. Instructions for Running the Query

### 環境建置

```bash
# 建立 conda 虛擬環境
conda create -n hw5-ontology python=3.11 -y
conda activate hw5-ontology

# 安裝依賴
pip install -r requirements.txt
```

### 執行推理與查詢

```bash
# 從專案根目錄執行
python src/reasoning.py
```

這會：
1. 載入 `ontology/imports/course-affordance.ttl` 和 `ontology/group-ontology.ttl`
2. 執行三階段推理（subClassOf 閉包 → type 繼承 → GraspableObject 分類）
3. 執行 SPARQL 查詢（`queries/graspable_objects.rq`）
4. 匯出推理結果至 `ontology/inferred-results.ttl`
5. 儲存查詢結果至 `results/graspable_objects_output.txt`

## 7. Expected Query Output

執行 `graspable_objects.rq` 後預期回傳 5 個 inferred GraspableObject：

| obj | label | role |
|-----|-------|------|
| `g04:block01` | toy_block | `cap:CollectableObject` |
| `g04:blueCup01` | blue_cup | `cap:TargetObject` |
| `g04:fork01` | fork | `cap:TargetObject` |
| `g04:knife01` | knife | `cap:TargetObject` |
| `g04:pinkCup01` | pink_cup | `cap:TargetObject` |

`g04:plate01` 和 `g04:basket01` **不會**出現在結果中。

## 8. What is Inferred vs Asserted

### Asserted（直接斷言）
- 物件類型：`g04:blueCup01 a cap:Cup`
- Affordance 連結：`g04:blueCup01 cap:hasAffordance g04:graspAffordBlueCup01`
- Task Role：`g04:blueCup01 cap:hasTaskRole cap:TargetObject`
- Class 階層：`cap:Cup rdfs:subClassOf cap:PhysicalObject`

### Inferred（推理得出）
- **Type 繼承**：`g04:blueCup01 a cap:PhysicalObject`（透過 `cap:Cup rdfs:subClassOf cap:PhysicalObject`）
- **GraspableObject 分類**：`g04:blueCup01 a cap:GraspableObject`（透過 `owl:equivalentClass` 定義推理）

GraspableObject 的推理完全由 OWL 定義驅動，**不是**手動在 ontology 中寫入 `a cap:GraspableObject`。

## 9. How `inferred-results.ttl` Was Generated

`ontology/inferred-results.ttl` 由 `src/reasoning.py` 自動生成，流程如下：

1. **載入**: RDFLib 解析 course-affordance.ttl 和 group-ontology.ttl 到同一個 RDF graph
2. **階段 1 推理**: 計算 `rdfs:subClassOf` 的傳遞性閉包
3. **階段 2 推理**: 根據 subClassOf 繼承推入缺失的 `rdf:type` triples
4. **階段 3 推理**: 解析 `cap:GraspableObject` 的 `owl:equivalentClass` 定義，對滿足條件的 individual 推入 `rdf:type cap:GraspableObject`
5. **序列化**: 將完整的推理後 graph（含原始 + 推理新增的 triples）序列化為 Turtle 格式

由於 RDFLib 不內建完整 OWL 推理器，本腳本實作自訂的推理規則層來完成所需的 class classification（PDF §13.3）。

## 10. File Links

### Ontology Files
| File | Description | Authored By |
|------|-------------|-------------|
| [group-ontology.ttl](ontology/group-ontology.ttl) | Group 04 ontology（含 GraspableObject 定義） | Group 04 |
| [inferred-results.ttl](ontology/inferred-results.ttl) | 推理後的完整 graph（自動生成） | reasoning.py |
| [course-affordance.ttl](ontology/imports/course-affordance.ttl) | 課程共用 ontology（官方提供） | Course |
| [course-alignment.ttl](ontology/imports/course-alignment.ttl) | SKOS 對齊（官方提供） | Course |

### Query Files
| File | Description |
|------|-------------|
| [graspable_objects.rq](queries/graspable_objects.rq) | 查詢推理後的 GraspableObject（必要） |
| [task_objects.rq](queries/task_objects.rq) | 查詢所有任務物件（推薦） |

### Source Code
| File | Description |
|------|-------------|
| [reasoning.py](src/reasoning.py) | Python RDFLib 推理腳本 |

### Result Files
| File | Description |
|------|-------------|
| [graspable_objects_output.txt](results/graspable_objects_output.txt) | SPARQL 查詢結果（自動生成） |

## Repository Structure

```
semantic-affordance-grounding/
├── README.md                         ← 本文件
├── report.md                         ← 設計報告
├── requirements.txt                  ← Python 依賴
├── ontology/
│   ├── group-ontology.ttl            ← 【組別自建】Group 04 ontology
│   ├── inferred-results.ttl          ← 【自動生成】推理後的 graph
│   └── imports/
│       ├── course-affordance.ttl     ← 【官方提供】課程共用 ontology
│       └── course-alignment.ttl      ← 【官方提供】SKOS 對齊
├── queries/
│   ├── graspable_objects.rq          ← 【必要】GraspableObject 查詢
│   └── task_objects.rq               ← 【推薦】任務物件查詢
├── results/
│   ├── graspable_objects_output.txt  ← 【自動生成】查詢結果
│   └── screenshots/                  ← 選用截圖
└── src/
    └── reasoning.py                  ← Python 推理腳本
```
