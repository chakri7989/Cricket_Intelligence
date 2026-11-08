import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.data_ingestion.historical_ingestion import (
    historical_ingestion_service,
    IngestionReport
)

def run_ingestion(
    raw_dir: Optional[str] = None, 
    max_files: Optional[int] = None
) -> IngestionReport:
    """
    Executes historical data ingestion from raw datasets into SQLite.
    """
    print(f"Starting Historical Cricket Ingestion (Target dir: {raw_dir or 'data/raw'})...")
    report = historical_ingestion_service.ingest_raw_directory(
        base_dir=raw_dir,
        max_files=max_files
    )
    print(report.summary_table())
    return report

if __name__ == "__main__":
    max_limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_ingestion(max_files=max_limit)
