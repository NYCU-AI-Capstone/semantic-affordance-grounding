# AIREADME.md — Antigravity 專用專案設計記憶

> 本文件僅供 Google Antigravity AI 自身閱讀，作為專案全貌與內部設計的 Source of Truth。

---

## 專案概述

| 項目 | 內容 |
|------|------|
| **專案名稱** | HW5: Ontology-based Semantic Grounding |
| **課程** | AI Capstone 2026 Spring (NYCU) |
| **組別** | Group 04 |
| **作業規格** | `Homework 5 Ontology-based Semantic Grounding.pdf` |
| **技術路線** | Option C — Python RDFLib + 自訂推理層 |

## 核心架構

```
Ontology Layer:
  course-affordance.ttl (cap:) → 課程共用詞彙（classes, properties）
       ↓ imports
  group-ontology.ttl (g04:) → Group 04 instances + GraspableObject 定義
       ↓ reasoning.py
  inferred-results.ttl → 推理後完整 graph

Reasoning Pipeline:
  1. rdfs:subClassOf 傳遞性閉包
  2. rdf:type 繼承推理
  3. owl:equivalentClass 模式匹配 → GraspableObject 分類

Query Layer:
  graspable_objects.rq → 查詢推理後的 GraspableObject
  task_objects.rq → 查詢所有任務物件
```

## Namespace 邊界

- `cap:` = `https://hcis.io/ontology/aicapstone/2026/` — **共用詞彙**，不在此 namespace 下新增 group-specific terms
- `g04:` = `https://hcis.io/ontology/aicapstone/2026/group04/` — **Group 04 專屬**，所有 instances 放這裡
- 例外：`cap:GraspableObject` 雖用 `cap:` namespace 但定義在 group-ontology.ttl 中（官方 TTL 未提供定義）

## 重要設計決策

1. **官方 TTL 有語法問題**：`cap:hasApproxWidth`（198-201 行）缺少 label/comment，且 281-283 行有孤立 triples。已修復在 `ontology/imports/course-affordance.ttl` 中。
2. **Affordance 個體化**：每個物件使用獨立的 affordance 個體（`g04:graspAffordBlueCup01` 等），不共享。
3. **OWL Punning**：`cap:hasTaskRole cap:TargetObject` — 將 class 作為 individual 使用，遵循 PDF Listing 4 範例。
4. **推理結果**：5 個 GraspableObject（blueCup01, pinkCup01, knife01, fork01, block01），2 個非 GraspableObject（plate01, basket01）。

## 檔案責任

| 檔案 | 作者 | 角色 |
|------|------|------|
| `ontology/group-ontology.ttl` | Group 04 | 核心交付物 |
| `ontology/imports/course-affordance.ttl` | 官方（已修復語法） | 匯入依賴 |
| `ontology/imports/course-alignment.ttl` | 官方 | SKOS 對齊參考 |
| `ontology/inferred-results.ttl` | reasoning.py 生成 | 推理後 graph |
| `src/reasoning.py` | Group 04 | 推理腳本 |
| `queries/*.rq` | Group 04 | SPARQL 查詢 |
| `results/*` | reasoning.py 生成 | 查詢結果 |

## 待完成事項

- [ ] 補充組員名單（README + report）
- [ ] Advanced Task（待使用者提供）
- [ ] 可選：SHACL 驗證
