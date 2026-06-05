"""
validate.py — HW5 Ontology-based Semantic Grounding SHACL 驗證腳本 (OPTIONAL)
Group 04 | PDF §15

本腳本使用 pyshacl 對 Group 04 的本體做「結構驗證」，與 reasoning.py 的「OWL 推理」
分工不同：
  - reasoning.py：用 OWL 等價類公理「推理」class 成員（如 GraspableObject）。
  - validate.py ：用 SHACL shapes「驗證」圖是否滿足必要結構約束（PDF §15）。

資料圖 = course-affordance.ttl + group-ontology.ttl，再套用 reasoning.py 中與 affordance
相關的輕量 materialization，使 class-level existential restrictions 產生的匿名
cap:hasAffordance blank nodes 也能被 SHACL 驗證看見。
"""

import sys
import logging
from pathlib import Path

from rdflib import Graph
from pyshacl import validate

# =============================================================================
# 強制 stdout 使用 UTF-8（日誌含中文；非中文語系 Windows 會 UnicodeEncodeError）
# =============================================================================
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# =============================================================================
# Logging 設定（同時輸出 console 與 shacl/validate.log）
# =============================================================================
_LOG_FILE_PATH = Path(__file__).resolve().parent / "validate.log"
_LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_LOG_FILE_PATH, mode="w", encoding="utf-8"),
    ]
)
logger = logging.getLogger("validate")

# =============================================================================
# 路徑設定
# =============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent           # shacl/
PROJECT_ROOT = SCRIPT_DIR.parent                       # repository root
sys.path.insert(0, str(PROJECT_ROOT))

from src.reasoning import (  # noqa: E402
    computeSubClassOfClosure,
    inferTypeInheritance,
    materializeClassLevelAffordances,
)

COURSE_ONTOLOGY_PATH = PROJECT_ROOT / "ontology" / "imports" / "course-affordance.ttl"
GROUP_ONTOLOGY_PATH = PROJECT_ROOT / "ontology" / "group-ontology.ttl"
SHAPES_PATH = SCRIPT_DIR / "shapes.ttl"
REPORT_OUTPUT_PATH = SCRIPT_DIR / "shacl_validation_report.txt"


def loadDataGraph() -> Graph:
    """載入 course ontology 與 group ontology，並 materialize class-level affordances。"""
    graph = Graph()
    logger.info("=== 載入資料圖 ===")
    logger.info(f"載入 course ontology: {COURSE_ONTOLOGY_PATH}")
    graph.parse(str(COURSE_ONTOLOGY_PATH), format="turtle")
    logger.info(f"載入 group ontology: {GROUP_ONTOLOGY_PATH}")
    graph.parse(str(GROUP_ONTOLOGY_PATH), format="turtle")
    logger.info(f"  -> asserted 資料圖共 {len(graph)} 個 triples")

    logger.info("套用 reasoning.py 的 class-level affordance materialization")
    closureMap = computeSubClassOfClosure(graph)
    inferTypeInheritance(graph, closureMap)
    materializeClassLevelAffordances(graph, closureMap)
    logger.info(f"  -> materialized 資料圖共 {len(graph)} 個 triples")
    return graph


def buildValidationScopeSummary() -> str:
    """Return a human-readable summary of validated SHACL fields and constraints."""
    lines = [
        "Validated Fields and Constraints",
        "-" * 80,
        "1. Target group: all cap:PhysicalObject instances",
        "   - Shape: g04:PhysicalObjectShape",
        "   - Field: cap:hasObjectLabel",
        "   - Requirement: at least 1 value",
        "   - Datatype: xsd:string",
        "   - Meaning: every physical object must have a perception/object label.",
        "",
        "2. Target group: all objects used as cap:hasTargetObject",
        "   - Shape: g04:TaskTargetShape",
        "   - Field: cap:hasTaskRole",
        "   - Requirement: at least 1 value",
        "   - Meaning: every task target must state its task role.",
        "",
        "3. Target group: all objects used as cap:hasTargetObject",
        "   - Shape: g04:TaskTargetShape",
        "   - Field: cap:hasAffordance",
        "   - Requirement: at least 1 value",
        "   - Meaning: every task target must have at least one affordance.",
        "   - Note: class-level affordance restrictions are materialized before validation,",
        "     so inferred anonymous affordance blank nodes are visible to SHACL.",
        "-" * 80,
        "",
    ]
    return "\n".join(lines)


def main():
    logger.info("=" * 80)
    logger.info("HW5 SHACL 結構驗證 — Group 04 (PDF §15, optional)")
    logger.info("=" * 80)

    for filePath in [COURSE_ONTOLOGY_PATH, GROUP_ONTOLOGY_PATH, SHAPES_PATH]:
        if not filePath.exists():
            logger.error(f"找不到必要檔案: {filePath}")
            sys.exit(1)

    dataGraph = loadDataGraph()

    logger.info("")
    logger.info(f"=== 執行 SHACL 驗證 (shapes: {SHAPES_PATH.name}) ===")
    logger.info("  rdfs inference: 開啟（使 targetClass 能匹配子類個體）")
    logger.info("  affordance materialization: 開啟（沿用 reasoning.py class-level restrictions）")

    conforms, resultsGraph, resultsText = validate(
        dataGraph,
        shacl_graph=str(SHAPES_PATH),
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        debug=False,
    )

    logger.info("")
    logger.info(f"=== 驗證結果：Conforms = {conforms} ===")
    logger.info("")
    for line in resultsText.rstrip().split("\n"):
        logger.info(f"  {line}")

    # 寫出報告
    REPORT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"SHACL Validation Report — Group 04 (PDF §15)\n"
        f"Shapes: shacl/shapes.ttl\n"
        f"Data:   ontology/imports/course-affordance.ttl + ontology/group-ontology.ttl + affordance materialization\n"
        f"Inference: rdfs + reasoning.py class-level affordance materialization\n"
        f"Conforms: {conforms}\n"
        + "-" * 80 + "\n"
    )
    validationScopeSummary = buildValidationScopeSummary()
    REPORT_OUTPUT_PATH.write_text(
        header + validationScopeSummary + resultsText,
        encoding="utf-8",
    )
    logger.info("")
    logger.info(f"  -> 報告已儲存至: {REPORT_OUTPUT_PATH}")

    logger.info("")
    logger.info("=" * 80)
    if conforms:
        logger.info("驗證通過：圖滿足所有 SHACL 結構約束。")
    else:
        logger.info("驗證未通過：請見上方違規清單。")
    logger.info("=" * 80)

    # conforms 為 True 時 exit 0，否則 exit 1（方便 CI / 重現判定）
    sys.exit(0 if conforms else 1)


if __name__ == "__main__":
    main()
