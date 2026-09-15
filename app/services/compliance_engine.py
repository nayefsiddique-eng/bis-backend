import json
from pathlib import Path
from datetime import date, datetime
from app.schemas.product import ProductInput
from app.schemas.compliance import QCOResult, SourceCitation, ComplianceRequirement

DATA_FILE = Path(__file__).parent.parent / "data" / "mock_qco.json"

def load_qco_data() -> list[dict]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def match_qco_entry(product: ProductInput, qco_list: list[dict]) -> dict | None:
    prod_cat = product.category.lower().strip()
    prod_subcat = (product.sub_category or "").lower().strip()
    prod_desc = product.description.lower().strip()

    for qco in qco_list:
        qco_cat = qco.get("category", "").lower()
        qco_subcat = qco.get("sub_category", "").lower()

        if qco_cat in prod_cat or prod_cat in qco_cat:
            return qco
        if qco_subcat and (qco_subcat in prod_subcat or qco_subcat in prod_desc):
            return qco
    return None

def check_qco_applicability(product: ProductInput, today_date: date | None = None) -> QCOResult:
    if today_date is None:
        today_date = date.today()

    qco_list = load_qco_data()
    qco_entry = match_qco_entry(product, qco_list)

    if not qco_entry:
        default_citation = SourceCitation(
            document_id="N/A",
            clause=None,
            title="BIS QCO Database",
            url=None
        )
        return QCOResult(
            qco_id="N/A",
            standard_id="N/A",
            applies=False,
            reasoning=f"No Quality Control Order (QCO) currently applies to product category '{product.category}'.",
            effective_date=today_date,
            exemption_status="none",
            source=default_citation
        )

    citation_data = qco_entry.get("citation", {})
    citation = SourceCitation(
        document_id=citation_data.get("document_id", qco_entry["qco_id"]),
        clause=citation_data.get("clause"),
        title=citation_data.get("title", qco_entry["title"]),
        url=citation_data.get("url")
    )

    eff_date_str = qco_entry.get("effective_date", "2000-01-01")
    effective_date = datetime.strptime(eff_date_str, "%Y-%m-%d").date()

    applies = True
    reason_parts = []

    if today_date < effective_date:
        reason_parts.append(
            f"QCO '{qco_entry['title']}' applies to '{product.category}' but is not yet mandatory. Effective date is {eff_date_str}."
        )
    else:
        reason_parts.append(
            f"QCO '{qco_entry['title']}' applies and is mandatory for '{product.category}' as of {eff_date_str}."
        )

    exemption_status = "none"
    if product.manufacturer_scale == "msme" and qco_entry.get("msme_exemption"):
        exemption_status = "msme"
        reason_parts.append(f"Exemption Status: MSME exemption applies. {qco_entry.get('exemption_notes', '')}")
    elif product.is_imported and qco_entry.get("import_exemption"):
        exemption_status = "import"
        reason_parts.append(f"Exemption Status: Import exemption applies. {qco_entry.get('exemption_notes', '')}")
    else:
        reason_parts.append(f"Exemption Status: No exemption applies ({qco_entry.get('exemption_notes', '')}).")

    return QCOResult(
        qco_id=qco_entry["qco_id"],
        standard_id=qco_entry["standard_id"],
        applies=applies,
        reasoning=" ".join(reason_parts),
        effective_date=effective_date,
        exemption_status=exemption_status,
        source=citation
    )

def resolve_requirements(qco_result: QCOResult) -> tuple[list[ComplianceRequirement], list[str]]:
    if not qco_result.applies or qco_result.qco_id == "N/A":
        return [], []

    qco_list = load_qco_data()
    qco_entry = next((q for q in qco_list if q["qco_id"] == qco_result.qco_id), None)
    if not qco_entry:
        return [], []

    citation = qco_result.source
    requirements: list[ComplianceRequirement] = []

    # Required Tests
    for test in qco_entry.get("required_tests", []):
        req_title = test["name"] if isinstance(test, dict) else str(test)
        clause = test.get("standard_clause") if isinstance(test, dict) else citation.clause
        req_citation = SourceCitation(
            document_id=citation.document_id,
            clause=clause,
            title=citation.title,
            url=citation.url
        )
        requirements.append(
            ComplianceRequirement(
                requirement=req_title,
                test_or_document="test",
                mandatory=True,
                source=req_citation
            )
        )

    # Required Documents
    for doc in qco_entry.get("required_documents", []):
        requirements.append(
            ComplianceRequirement(
                requirement=doc,
                test_or_document="document",
                mandatory=True,
                source=citation
            )
        )

    labs = qco_entry.get("recommended_labs", [])
    return requirements, labs
