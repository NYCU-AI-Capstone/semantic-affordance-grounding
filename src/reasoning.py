"""
reasoning.py — HW5 Ontology-based Semantic Grounding 推理腳本
Group 04 | Option C: Python RDFLib + 自訂推理層

本腳本使用 RDFLib 載入 course ontology 和 group ontology，
執行自訂推理，最終匯出推理結果與 SPARQL 查詢結果。

推理機制（PDF §13.3 要求明確記錄）：
  - RDFLib 不支援完整 OWL 推理，因此本腳本實作自訂推理層。
  - 階段 1: rdfs:subClassOf 傳遞性閉包
  - 階段 2: rdf:type 繼承推理
  - 階段 2b: class-level existential restrictions materialization
  - 階段 3: owl:equivalentClass 模式匹配（GraspableObject 分類）
"""

import os
import sys
import logging
import hashlib
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, BNode
from rdflib.collection import Collection

# =============================================================================
# 強制 stdout 使用 UTF-8
# =============================================================================
# 日誌訊息含中文字元；在非中文語系（如英文 cp1252）的 Windows 上直接印到
# console 會觸發 UnicodeEncodeError。此處強制 UTF-8，讓助教不需設定任何環境
# 變數即可直接執行重現。所有狀態標示一律使用純 ASCII（[OK]/[INFERRED] 等）。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# =============================================================================
# Debug Logging 設定
# =============================================================================
# 同時輸出到 console 與 log/reasoning.log（log 檔以 UTF-8 寫入）。
_LOG_FILE_PATH = Path(__file__).resolve().parent.parent / "log" / "reasoning.log"
_LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_LOG_FILE_PATH, mode="w", encoding="utf-8"),
    ]
)
logger = logging.getLogger("reasoning")

# =============================================================================
# Namespace 定義
# =============================================================================
CAP = Namespace("https://hcis.io/ontology/aicapstone/2026/")
G04 = Namespace("https://hcis.io/ontology/aicapstone/2026/group04/")

# =============================================================================
# 路徑設定
# =============================================================================
# 支援從專案根目錄或 src/ 目錄執行
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

COURSE_ONTOLOGY_PATH = PROJECT_ROOT / "ontology" / "imports" / "course-affordance.ttl"
GROUP_ONTOLOGY_PATH = PROJECT_ROOT / "ontology" / "group-ontology.ttl"
INFERRED_OUTPUT_PATH = PROJECT_ROOT / "ontology" / "inferred-results.ttl"
QUERY_PATH = PROJECT_ROOT / "queries" / "graspable_objects.rq"
TASK_QUERY_PATH = PROJECT_ROOT / "queries" / "task_objects.rq"
CONCEAL_QUERY_PATH = PROJECT_ROOT / "queries" / "concealing_cup.rq"
RESULT_OUTPUT_PATH = PROJECT_ROOT / "results" / "graspable_objects_output.txt"


def loadOntologies() -> Graph:
    """載入 course ontology 和 group ontology 到同一個 Graph。"""
    graph = Graph()

    logger.info("=== 載入 Ontology 檔案 ===")

    # 載入 course ontology
    logger.info(f"載入 course ontology: {COURSE_ONTOLOGY_PATH}")
    graph.parse(str(COURSE_ONTOLOGY_PATH), format="turtle")
    courseTripleCount = len(graph)
    logger.info(f"  -> course ontology 載入完成，共 {courseTripleCount} 個 triples")

    # 載入 group ontology
    logger.info(f"載入 group ontology: {GROUP_ONTOLOGY_PATH}")
    graph.parse(str(GROUP_ONTOLOGY_PATH), format="turtle")
    groupTripleCount = len(graph) - courseTripleCount
    logger.info(f"  -> group ontology 載入完成，新增 {groupTripleCount} 個 triples")

    logger.info(f"  -> 總計 {len(graph)} 個 triples")
    return graph


def computeSubClassOfClosure(graph: Graph) -> dict[URIRef, set[URIRef]]:
    """
    階段 1: 計算 rdfs:subClassOf 的傳遞性閉包。
    回傳一個 dict，key 為 class URI，value 為該 class 的所有 superclass（含自身）。
    """
    logger.info("")
    logger.info("=== 階段 1: rdfs:subClassOf 傳遞性閉包 ===")

    # 收集所有直接的 subClassOf 關係（排除 blank nodes，即 owl:Restriction）
    directSuperMap: dict[URIRef, set[URIRef]] = {}
    for subClass, _, superClass in graph.triples((None, RDFS.subClassOf, None)):
        if isinstance(subClass, URIRef) and isinstance(superClass, URIRef):
            if subClass not in directSuperMap:
                directSuperMap[subClass] = set()
            directSuperMap[subClass].add(superClass)
            logger.debug(f"  直接 subClassOf: {_shortName(subClass)} -> {_shortName(superClass)}")

    # 計算傳遞性閉包
    closureMap: dict[URIRef, set[URIRef]] = {}

    def _getAncestors(classUri: URIRef) -> set[URIRef]:
        """遞迴取得所有祖先 class。"""
        if classUri in closureMap:
            return closureMap[classUri]

        ancestors = {classUri}  # 包含自身
        if classUri in directSuperMap:
            for superClass in directSuperMap[classUri]:
                ancestors.add(superClass)
                ancestors.update(_getAncestors(superClass))

        closureMap[classUri] = ancestors
        return ancestors

    # 對所有出現過的 class 計算閉包
    allClasses = set(directSuperMap.keys())
    for superSet in directSuperMap.values():
        allClasses.update(superSet)

    for classUri in allClasses:
        _getAncestors(classUri)

    logger.info(f"  -> 共處理 {len(closureMap)} 個 classes 的 subClassOf 閉包")
    for classUri, ancestors in sorted(closureMap.items(), key=lambda x: str(x[0])):
        ancestorNames = sorted([_shortName(a) for a in ancestors if a != classUri])
        if ancestorNames:
            logger.debug(f"  {_shortName(classUri)} 的祖先: {', '.join(ancestorNames)}")

    return closureMap


def inferTypeInheritance(graph: Graph, closureMap: dict[URIRef, set[URIRef]]) -> int:
    """
    階段 2: rdf:type 繼承推理。
    若 X rdf:type C 且 C rdfs:subClassOf D，則推入 X rdf:type D。
    回傳新增的 triple 數量。
    """
    logger.info("")
    logger.info("=== 階段 2: rdf:type 繼承推理 ===")

    newTripleCount = 0
    triplesToAdd = []

    # 找出所有具有 rdf:type 的 individual（排除 class 本身、property 等）
    for individual, _, directType in graph.triples((None, RDF.type, None)):
        if not isinstance(directType, URIRef):
            continue
        if directType in closureMap:
            for superClass in closureMap[directType]:
                if superClass != directType:
                    # 檢查是否已經存在
                    if (individual, RDF.type, superClass) not in graph:
                        triplesToAdd.append((individual, RDF.type, superClass))

    for triple in triplesToAdd:
        graph.add(triple)
        newTripleCount += 1
        logger.debug(f"  TYPE-INHERIT: {_shortName(triple[0])} a {_shortName(triple[2])}")

    logger.info(f"  -> 新增 {newTripleCount} 個 type-inheritance triples")
    return newTripleCount


def materializeClassLevelAffordances(graph: Graph, closureMap: dict[URIRef, set[URIRef]]) -> int:
    """
    階段 2b: materialize class-level existential affordance restrictions。

    若 class C 有：
      C rdfs:subClassOf [
          owl:onProperty cap:hasAffordance ;
          owl:someValuesFrom A
      ]
    且 individual X rdf:type C，則為 X 建立一個匿名 affordance blank node：
      X cap:hasAffordance _:affordance .
      _:affordance rdf:type A .

    這讓 group ontology 不需要為每個物件建立具名 affordance individual，
    同時仍能保留 GraspableObject 所需的 hasAffordance 語義。
    """
    logger.info("")
    logger.info("=== 階段 2b: class-level affordance restrictions materialization ===")

    classRestrictionMap = _collectAffordanceRestrictions(graph, closureMap)
    newTripleCount = 0
    triplesToAdd = []

    for individual, _, classUri in graph.triples((None, RDF.type, None)):
        if not isinstance(individual, URIRef) or not isinstance(classUri, URIRef):
            continue
        if classUri not in classRestrictionMap:
            continue

        for affordanceClass in sorted(classRestrictionMap[classUri], key=str):
            affordanceNode = _stableAffordanceBlankNode(individual, affordanceClass)
            candidateTriples = [
                (individual, CAP.hasAffordance, affordanceNode),
                (affordanceNode, RDF.type, affordanceClass),
            ]

            # Also add superclass types for the anonymous affordance, because
            # type inheritance already ran before these blank nodes are created.
            for superClass in closureMap.get(affordanceClass, {affordanceClass}):
                if superClass != affordanceClass:
                    candidateTriples.append((affordanceNode, RDF.type, superClass))

            for triple in candidateTriples:
                if triple not in graph and triple not in triplesToAdd:
                    triplesToAdd.append(triple)

            logger.debug(
                f"  MATERIALIZE: {_shortName(individual)} has anonymous {_shortName(affordanceClass)}"
            )

    for triple in triplesToAdd:
        graph.add(triple)
        newTripleCount += 1

    logger.info(f"  -> 新增 {newTripleCount} 個 class-level affordance triples")
    return newTripleCount


def _collectAffordanceRestrictions(
    graph: Graph,
    closureMap: dict[URIRef, set[URIRef]],
) -> dict[URIRef, set[URIRef]]:
    """收集每個 class 繼承到的 cap:hasAffordance some AffordanceClass restrictions。"""
    directRestrictionMap: dict[URIRef, set[URIRef]] = {}

    for classUri, _, restriction in graph.triples((None, RDFS.subClassOf, None)):
        if not isinstance(classUri, URIRef):
            continue
        if isinstance(restriction, URIRef):
            continue
        if (restriction, RDF.type, OWL.Restriction) not in graph:
            continue
        if (restriction, OWL.onProperty, CAP.hasAffordance) not in graph:
            continue

        for affordanceClass in graph.objects(restriction, OWL.someValuesFrom):
            if isinstance(affordanceClass, URIRef):
                directRestrictionMap.setdefault(classUri, set()).add(affordanceClass)

    inheritedRestrictionMap: dict[URIRef, set[URIRef]] = {}
    allClasses = set(closureMap.keys())
    for ancestors in closureMap.values():
        allClasses.update(ancestors)
    allClasses.update(directRestrictionMap.keys())

    for classUri in allClasses:
        restrictions = set()
        for ancestor in closureMap.get(classUri, {classUri}):
            restrictions.update(directRestrictionMap.get(ancestor, set()))
        if restrictions:
            inheritedRestrictionMap[classUri] = restrictions
            logger.debug(
                f"  AFFORDANCE-RESTRICTIONS: {_shortName(classUri)} -> "
                + ", ".join(sorted(_shortName(item) for item in restrictions))
            )

    return inheritedRestrictionMap


def _stableAffordanceBlankNode(individual: URIRef, affordanceClass: URIRef) -> BNode:
    """用 deterministic blank-node id 讓重跑時 inferred graph 較穩定。"""
    digest = hashlib.sha1(f"{individual}|{affordanceClass}".encode("utf-8")).hexdigest()[:16]
    return BNode(f"affordance_{digest}")


def inferGraspableObjects(graph: Graph) -> int:
    """
    階段 3: owl:equivalentClass 模式匹配 — GraspableObject 推理。

    解析 cap:GraspableObject 的 owl:equivalentClass 定義，
    檢查每個 individual 是否滿足：
      1. 是 cap:PhysicalObject（經 type 繼承後）
      2. 有 cap:hasAffordance 連結到 cap:GraspingAffordance 實例
         （可由 class-level restriction materialize 成匿名 blank node）

    滿足則推入 rdf:type cap:GraspableObject。
    回傳新增的 triple 數量。
    """
    logger.info("")
    logger.info("=== 階段 3: GraspableObject 推理 ===")
    logger.info("  推理規則: cap:GraspableObject ≡ cap:PhysicalObject ⊓ ∃cap:hasAffordance.cap:GraspingAffordance")

    newTripleCount = 0

    # 找出所有是 cap:PhysicalObject 的 named individuals
    physicalObjects = set()
    for individual in graph.subjects(RDF.type, CAP.PhysicalObject):
        if isinstance(individual, URIRef):
            physicalObjects.add(individual)

    logger.info(f"  找到 {len(physicalObjects)} 個 cap:PhysicalObject individuals")

    for individual in sorted(physicalObjects, key=str):
        individualName = _shortName(individual)

        # 檢查是否有 cap:hasAffordance 指向 cap:GraspingAffordance
        hasGraspingAffordance = False
        for affordance in graph.objects(individual, CAP.hasAffordance):
            affordanceTypes = set(graph.objects(affordance, RDF.type))
            if CAP.GraspingAffordance in affordanceTypes:
                hasGraspingAffordance = True
                logger.debug(f"  [YES] {individualName} 有 GraspingAffordance: {_shortName(affordance)}")
                break

        if hasGraspingAffordance:
            if (individual, RDF.type, CAP.GraspableObject) not in graph:
                graph.add((individual, RDF.type, CAP.GraspableObject))
                newTripleCount += 1
                logger.info(f"  [INFERRED] {individualName} -> cap:GraspableObject")
            else:
                logger.debug(f"  (已存在) {individualName} 已是 GraspableObject")
        else:
            logger.debug(f"  [NO] {individualName} 沒有 GraspingAffordance -> 不是 GraspableObject")

    logger.info(f"  -> 新增 {newTripleCount} 個 GraspableObject 推理 triples")
    return newTripleCount


def inferBallConcealingCups(graph: Graph) -> int:
    """
    階段 4 (Advanced Task): owl:equivalentClass 模式匹配 — BallConcealingCup 推理。

    解析 g04:BallConcealingCup 的 owl:equivalentClass 定義，
    檢查每個 cup 是否滿足：
      1. 是 cap:Cup
      2. 有 g04:conceals 連結到 g04:Ball 實例

    滿足則推入 rdf:type g04:BallConcealingCup（即 shell-game 的抓取目標）。
    回傳新增的 triple 數量。
    """
    logger.info("")
    logger.info("=== 階段 4: BallConcealingCup 推理 (Advanced Task) ===")
    logger.info("  推理規則: g04:BallConcealingCup ≡ cap:Cup ⊓ ∃g04:conceals.g04:Ball")

    newTripleCount = 0

    # 找出所有是 cap:Cup 的 named individuals（經 type 繼承後 cap:Cup 已存在）
    cups = set()
    for individual in graph.subjects(RDF.type, CAP.Cup):
        if isinstance(individual, URIRef):
            cups.add(individual)

    logger.info(f"  找到 {len(cups)} 個 cap:Cup individuals")

    for cup in sorted(cups, key=str):
        cupName = _shortName(cup)

        # 檢查是否有 g04:conceals 指向 g04:Ball 實例
        concealsBall = False
        for concealed in graph.objects(cup, G04.conceals):
            concealedTypes = set(graph.objects(concealed, RDF.type))
            if G04.Ball in concealedTypes:
                concealsBall = True
                logger.debug(f"  [YES] {cupName} conceals Ball: {_shortName(concealed)}")
                break

        if concealsBall:
            if (cup, RDF.type, G04.BallConcealingCup) not in graph:
                graph.add((cup, RDF.type, G04.BallConcealingCup))
                newTripleCount += 1
                logger.info(f"  [INFERRED] {cupName} -> g04:BallConcealingCup (retrieval target)")
        else:
            logger.debug(f"  [NO] {cupName} 未藏球 -> 不是 BallConcealingCup")

    logger.info(f"  -> 新增 {newTripleCount} 個 BallConcealingCup 推理 triples")
    return newTripleCount


def runSparqlQuery(graph: Graph, queryPath: Path, outputPath: Path = None) -> str:
    """執行 SPARQL 查詢並回傳格式化的結果。"""
    logger.info("")
    logger.info(f"=== 執行 SPARQL 查詢: {queryPath.name} ===")

    queryString = queryPath.read_text(encoding="utf-8")
    # 移除 comment 行以避免解析問題
    cleanedQueryLines = [
        line for line in queryString.split("\n")
        if not line.strip().startswith("#")
    ]
    cleanedQuery = "\n".join(cleanedQueryLines)

    results = graph.query(cleanedQuery)

    # 格式化結果
    outputLines = []
    outputLines.append(f"SPARQL Query: {queryPath.name}")
    outputLines.append(f"Results: {len(results)} rows")
    outputLines.append("-" * 80)

    # 欄位標頭
    varNames = [str(varItem) for varItem in results.vars]
    headerLine = " | ".join(f"{varName:<40}" for varName in varNames)
    outputLines.append(headerLine)
    outputLines.append("-" * 80)

    for row in results:
        rowValues = []
        for value in row:
            if value is not None:
                rowValues.append(f"{str(value):<40}")
            else:
                rowValues.append(f"{'(none)':<40}")
        outputLines.append(" | ".join(rowValues))

    outputLines.append("-" * 80)
    outputText = "\n".join(outputLines)

    logger.info(f"\n{outputText}")

    if outputPath:
        outputPath.parent.mkdir(parents=True, exist_ok=True)
        outputPath.write_text(outputText, encoding="utf-8")
        logger.info(f"  -> 結果已儲存至: {outputPath}")

    return outputText


def exportInferredGraph(graph: Graph, outputPath: Path):
    """將推理後的完整 graph 序列化為 Turtle 並輸出。"""
    logger.info("")
    logger.info(f"=== 匯出推理後的 graph ===")

    # 綁定常用 prefix 以提高可讀性
    graph.bind("cap", CAP)
    graph.bind("g04", G04)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("rdf", RDF)

    outputPath.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(outputPath), format="turtle")

    logger.info(f"  -> 推理後的 graph（{len(graph)} triples）已匯出至: {outputPath}")


def _shortName(uri: URIRef) -> str:
    """將完整 URI 縮短為易讀的 prefix:localName 格式。"""
    uriStr = str(uri)
    if uriStr.startswith(str(G04)):
        return f"g04:{uriStr[len(str(G04)):]}"
    elif uriStr.startswith(str(CAP)):
        return f"cap:{uriStr[len(str(CAP)):]}"
    elif uriStr.startswith("http://www.w3.org/2002/07/owl#"):
        return f"owl:{uriStr.split('#')[-1]}"
    elif uriStr.startswith("http://www.w3.org/2000/01/rdf-schema#"):
        return f"rdfs:{uriStr.split('#')[-1]}"
    elif uriStr.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
        return f"rdf:{uriStr.split('#')[-1]}"
    return uriStr


def main():
    """主程式入口。"""
    logger.info("=" * 80)
    logger.info("HW5 Ontology-based Semantic Grounding — 推理腳本")
    logger.info("Group 04 | Option C: Python RDFLib + 自訂推理層")
    logger.info("=" * 80)

    # 檢查檔案存在
    for filePath in [COURSE_ONTOLOGY_PATH, GROUP_ONTOLOGY_PATH, QUERY_PATH]:
        if not filePath.exists():
            logger.error(f"找不到必要檔案: {filePath}")
            sys.exit(1)

    # Step 1: 載入 Ontology
    graph = loadOntologies()

    # Step 2: 自訂推理
    closureMap = computeSubClassOfClosure(graph)
    typeInheritCount = inferTypeInheritance(graph, closureMap)
    affordanceMaterializationCount = materializeClassLevelAffordances(graph, closureMap)
    graspableCount = inferGraspableObjects(graph)
    concealingCupCount = inferBallConcealingCups(graph)

    # 推理摘要
    logger.info("")
    logger.info("=== 推理摘要 ===")
    logger.info(f"  rdfs:subClassOf 閉包中的 class 數量: {len(closureMap)}")
    logger.info(f"  type 繼承新增的 triples: {typeInheritCount}")
    logger.info(f"  class-level affordance materialization 新增的 triples: {affordanceMaterializationCount}")
    logger.info(f"  GraspableObject 推理新增的 triples: {graspableCount}")
    logger.info(f"  BallConcealingCup 推理新增的 triples: {concealingCupCount}")
    logger.info(f"  推理後總 triple 數量: {len(graph)}")

    # Step 3: 執行 SPARQL 查詢
    runSparqlQuery(graph, QUERY_PATH, RESULT_OUTPUT_PATH)

    # 如果有 task_objects.rq，也執行
    if TASK_QUERY_PATH.exists():
        taskResultPath = PROJECT_ROOT / "results" / "task_objects_output.txt"
        runSparqlQuery(graph, TASK_QUERY_PATH, taskResultPath)

    # Advanced Task: 執行 concealing_cup.rq（找出藏球的抓取目標杯）
    if CONCEAL_QUERY_PATH.exists():
        concealResultPath = PROJECT_ROOT / "results" / "concealing_cup_output.txt"
        runSparqlQuery(graph, CONCEAL_QUERY_PATH, concealResultPath)

    # Step 4: 匯出推理後的 graph
    exportInferredGraph(graph, INFERRED_OUTPUT_PATH)

    logger.info("")
    logger.info("=" * 80)
    logger.info("推理完成！所有結果已匯出。")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
