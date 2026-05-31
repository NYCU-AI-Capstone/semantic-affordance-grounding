# CLAUDE.md — 專案統整與工作指引

> 本文件是本專案的 **Source of Truth**：統整作業目標、架構、設計決策與現況。
> 小組成員可藉此快速理解專案；AI 助手（Claude / Antigravity）亦以此為 context。

---

## 1. 專案概述

| 項目 | 內容 |
|------|------|
| **專案名稱** | HW5: Ontology-based Semantic Grounding |
| **課程** | AI Capstone 2026 Spring (NYCU) |
| **組別** | Group 04 |
| **作業規格** | `ori_github/Homework 5 Ontology-based Semantic Grounding.pdf` |
| **技術路線** | Option C — Python RDFLib + 自訂推理層 |

## 2. 作業目標（要解決的問題）

為一個**具備夾爪的機器人代理**建立語意明確的 Ontology，將環境中被感知的物件做語意接地，
最終要能回答：**「環境中哪些物件可被抓取（graspable），以及為什麼？」**

核心是區分「辨識」與「接地」，並把物件建模成有類型、可查詢、**可推理**的實體：
一個藍杯子 → 物理物件 → 疊杯任務的目標物 → 具抓取 affordance → **被推理出**是 GraspableObject。

### 必須涵蓋的三個 entry-level 任務物件
1. **疊杯（Cup stacking）**：blue cup、pink cup
2. **餐具擺放（Cutlery arrangement）**：knife、fork、plate
3. **積木收集（Toy block collection）**：toy block、basket

### Advanced Task：Shell Game（藏球猜杯）
桌上有數個視覺相同的不透明杯子，一顆小球藏在其中一個杯子下，洗牌後機器手臂須
**抓起「藏有球的那個杯子」**。Ontology 建模洗牌後的最終狀態；「哪個杯子是抓取目標」
由 reasoner **推理**得出（`g04:BallConcealingCup`），而非手寫斷言。這示範了 spec §18 的
核心區分：**「可抓取（graspable）」≠「任務目標（target）」**——三個杯子都可抓，但只有藏球的是該抓的。

## 3. 核心架構

```
Ontology Layer:
  course-affordance.ttl (cap:) → 課程共用詞彙（classes, properties, restrictions）
       ↓ owl:imports
  group-ontology.ttl (g04:) → Group 04 instances + GraspableObject 等價類定義
       ↓ src/reasoning.py
  inferred-results.ttl → 推理後的完整 graph

Reasoning Pipeline（src/reasoning.py 四階段自訂推理層）:
  1. rdfs:subClassOf 傳遞性閉包
  2. rdf:type 繼承推理
  3. owl:equivalentClass 模式匹配 → GraspableObject 分類
  4. owl:equivalentClass 模式匹配 → BallConcealingCup 分類（Advanced Task）

Query Layer:
  graspable_objects.rq → 查詢推理後的 GraspableObject（必交，PDF §12）
  task_objects.rq      → 查詢所有任務物件與 affordance（選交）
  concealing_cup.rq    → 查詢藏球且可抓取的目標杯（Advanced Task）
```

## 4. Namespace 邊界（PDF §8）

- `cap:` = `https://hcis.io/ontology/aicapstone/2026/` — **共用詞彙**，不在此 namespace 下新增 group-specific terms
- `g04:` = `https://hcis.io/ontology/aicapstone/2026/group04/` — **Group 04 專屬**，所有 instances 放這裡
- 例外：`cap:GraspableObject` 使用 `cap:` namespace 但定義在 `group-ontology.ttl`（官方 TTL 未提供其定義，由各組自行定義其等價類公理）

## 5. 重要設計決策

1. **GraspableObject 推理公理**：`cap:GraspableObject ≡ cap:PhysicalObject ⊓ ∃cap:hasAffordance.cap:GraspingAffordance`（PDF §11 Listing 5），定義於 `group-ontology.ttl`。
2. **官方 TTL 語法修復**：`ontology/imports/course-affordance.ttl` 中 `cap:hasApproxWidth` 原缺 label/comment、檔尾有孤立 triples，已修復以利解析。（屬匯入依賴，README/report 須說明此修改）
3. **Affordance 個體化**：每個物件使用獨立 affordance 個體（如 `g04:graspAffordBlueCup01`），不共享。
4. **OWL Punning**：`cap:hasTaskRole cap:TargetObject` 將 class 當 individual 使用，遵循 PDF Listing 4 範例。
5. **graspable 與否的建模**：plate（ReferenceObject）、basket（ContainerTarget）**刻意不給** GraspingAffordance，因此不會被推理為 GraspableObject，避免 PDF §18「task relevance ≠ graspability」的 pitfall。

### Advanced Task（Shell Game，kitchen scene）設計決策
6. **杯子設定**：新增 3 個**完全相同**的不透明杯 `g04:shellCup01/02/03`（與 baseline 藍/粉杯分開）。三杯**同類別、同外觀**（皆 `cap:Cup`、`hasColor "pink"`、`g04:isOpaque true`、`hasObjectLabel "shell_cup"`），機器人**看不出差別**——只靠 identity / pose frame 區分。命名用純編號（非 A/B/C）以強調是「同款杯的不同實例」。場景可擴充到 3~5 杯。
   - **顏色與透明度拆成兩個正交屬性**：`cap:hasColor "pink"` 只記顏色，不透明則用獨立的 boolean 屬性 `g04:isOpaque true`，**不**塞成 `"粉色不透明"` 這種混合字串（否則兩者皆不可查詢、且違反 `cap:hasColor` 的語意）。不透明是 concealment affordance 成立的**感知前提**——正因杯子不透明、看不穿，目標杯才必須靠推理而非觀察得出。`g04:isOpaque` 目前為純描述性事實，未接入推理鏈。
7. **桌子不建模**：桌子/檯面屬 kitchen scene 背景，**不**作為任務物件建模（無 `g04:Table`）。
8. **球不可抓**：`g04:ball01`（`g04:Ball`）**不給** GraspingAffordance；機器只抓杯子、間接取球。故球不會被推理為 GraspableObject。
9. **第二個推理目標**：`g04:BallConcealingCup ≡ cap:Cup ⊓ ∃g04:conceals.g04:Ball`。斷言 `shellCup02 g04:conceals ball01`（感知事實），reasoner 推理出 `shellCup02` 是目標杯——答案是**推理**得來，非斷言。
10. **不洩漏答案**：3 個杯子都先掛 `g04:CandidateContainer` 角色（候選），沒有任何一杯被預先標成答案；最終目標由推理決定。
11. **新增詞彙**（皆 `g04:`）：class `g04:Ball`、`g04:BallConcealingCup`、affordance `g04:ConcealmentAffordance`、role `g04:CandidateContainer`/`g04:HiddenItem`、object property `g04:conceals`/`g04:concealedBy`、datatype property `g04:isOpaque`。遠超 spec §15「至少 1 新 class + 1 新 affordance/role」的門檻。

## 6. 推理結果（已驗證可重現）

- **8 個 GraspableObject**（推理得出，非手動斷言）：blueCup01、pinkCup01、knife01、fork01、block01（baseline 5 個）+ shellCup01、shellCup02、shellCup03（shell-game 3 個）
- **非 GraspableObject**：plate01、basket01、ball01（球不可抓）
- **1 個 BallConcealingCup**（Advanced Task 推理得出）：**shellCup02**（藏球的目標杯）；shellCup01、shellCup03 為空杯，未被推理為目標
- baseline 推理結果與 PDF §12 預期完全吻合。
- `concealing_cup.rq` 回傳唯一目標：shellCup02（pose `world/object_cup02`）藏 ball01。

## 7. 檔案責任

| 檔案 | 作者 | 角色 |
|------|------|------|
| `ontology/group-ontology.ttl` | Group 04 | 核心交付物（實例 + GraspableObject 定義） |
| `ontology/imports/course-affordance.ttl` | 官方（已修復語法） | 匯入依賴 |
| `ontology/imports/course-alignment.ttl` | 官方 | SKOS 對齊參考 |
| `ontology/inferred-results.ttl` | reasoning.py 生成 | 推理後 graph（必交） |
| `src/reasoning.py` | Group 04 | 推理腳本 |
| `queries/*.rq` | Group 04 | SPARQL 查詢 |
| `results/*` | reasoning.py 生成 | 查詢結果輸出 |
| `README.md` / `report.md` | Group 04 | 文件與報告 |

## 8. 如何重現（執行方式）

```bash
# 環境：conda env hw5-ontology（已安裝 rdflib，見 requirements.txt）
conda run -n hw5-ontology python src/reasoning.py
```

執行後會重新產生 `ontology/inferred-results.ttl`、`results/graspable_objects_output.txt`、
`results/task_objects_output.txt`。重跑結果與已提交版本一致（reproducible）。

完整執行日誌（含三階段推理逐步過程）會同時寫入 `results/reasoning.log`（UTF-8）。
此 log 內含本機絕對路徑且每次重跑會覆寫，故列入 `.gitignore` 不提交。
腳本啟動時會強制 stdout 為 UTF-8，狀態標示一律使用純 ASCII（`[INFERRED]`/`[YES]`/`[NO]`），
助教不需設定任何環境變數即可直接執行。

## 9. 待完成事項

- [x] Advanced Task（Shell Game 藏球猜杯）— 本體、推理、查詢、輸出皆完成並驗證可重現
- [ ] 補充組員名單（README + report）
- [ ] README.md / report.md 逐項稽核（PDF §16.2 的 10 項要求；含 advanced task 的設計說明、物件-affordance 表更新、concealing_cup.rq 執行說明與預期輸出）
- [ ] 可選：SHACL 驗證（PDF §15）
