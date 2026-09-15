from fastapi import APIRouter
from app.services.compliance_engine import load_qco_data
from app.core.exceptions import APIException

router = APIRouter(prefix="/standards", tags=["standards"])

@router.get("/{standard_id}/history")
def get_standard_history(standard_id: str):
    qco_list = load_qco_data()
    # Normalize comparison (e.g. IS 17043:2018 or QCO-FOOTWEAR-2024)
    target_norm = standard_id.lower().strip()

    matched_entry = None
    for entry in qco_list:
        if (
            entry.get("standard_id", "").lower().strip() == target_norm
            or entry.get("qco_id", "").lower().strip() == target_norm
        ):
            matched_entry = entry
            break

    if not matched_entry:
        raise APIException(
            status_code=404,
            error_code="NO_MATCHING_QCO",
            message=f"Standard ID or QCO ID '{standard_id}' not found in QCO database."
        )

    history = matched_entry.get("amendment_history", [])
    return {
        "standard_id": matched_entry["standard_id"],
        "qco_id": matched_entry["qco_id"],
        "title": matched_entry["title"],
        "history": history
    }
