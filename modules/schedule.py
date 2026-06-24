"""
Agentic OS — Schedule Module
PDF generation endpoint for the call schedule system.
"""
import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from fastapi import APIRouter, HTTPException, UploadFile, File, Form
except ImportError:
    APIRouter = None
    HTTPException = None
    UploadFile = None
    File = None
    Form = None

# Re-use the standalone generator
from generate_schedule_pdfs import (
    DEFAULT_MASTER,
    load_master_data,
    load_resident_data,
    merge_data,
    generate_pdfs,
)

# Only define router if fastapi is available
router = None

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
REPORTS_DIR = SCRIPT_DIR / "reports" / "schedules"


def _get_output_dir() -> str:
    """Create a timestamped output directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = REPORTS_DIR / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)
    return str(out_dir)


# Only register endpoints when FastAPI is available
if APIRouter is not None:

    router = APIRouter(prefix="/api/schedule", tags=["schedule"])

    @router.post("/generate")
    async def generate_schedule(
        residents: Optional[UploadFile] = File(None),
    ):
        """Generate 3 PDFs from the master xlsx, optionally merged with resident data.

        Accepts an optional xlsx upload with resident-completed columns
        (Chief Resident, 1st Call Resident, 2nd Call Resident).

        Returns the paths to the 3 generated PDFs.
        """
        master_path = DEFAULT_MASTER
        if not os.path.exists(master_path):
            raise HTTPException(
                status_code=500,
                detail=f"Master xlsx not found at {master_path}",
            )

        # Load master data
        try:
            master_data = load_master_data(master_path)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load master xlsx: {e}",
            )

        # Load resident data if uploaded
        resident_data = None
        if residents:
            # Save uploaded file to temp location
            try:
                suffix = ".xlsx"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    content = await residents.read()
                    tmp.write(content)
                    tmp_path = tmp.name

                resident_data = load_resident_data(tmp_path)
                os.unlink(tmp_path)  # Clean up temp file
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to read resident xlsx: {e}",
                )

        # Merge and generate
        try:
            merged = merge_data(master_data, resident_data)
            output_dir = _get_output_dir()
            pdf_paths = generate_pdfs(merged, output_dir)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate PDFs: {e}",
            )

        # Build response
        pdfs_info = []
        for p in pdf_paths:
            pdfs_info.append({
                "sheet": Path(p).stem.replace("_call_schedule", "").title(),
                "path": p,
                "filename": Path(p).name,
                "size_bytes": os.path.getsize(p),
            })

        return {
            "success": True,
            "output_dir": output_dir,
            "pdfs": pdfs_info,
            "message": f"Generated {len(pdfs_info)} PDFs",
        }

    @router.get("/status")
    def schedule_status():
        """Check if the schedule generation system is configured."""
        master_exists = os.path.exists(DEFAULT_MASTER)
        return {
            "master_xlsx_exists": master_exists,
            "master_xlsx_path": DEFAULT_MASTER,
            "reports_dir": str(REPORTS_DIR),
            "reports_dir_exists": REPORTS_DIR.exists(),
        }
