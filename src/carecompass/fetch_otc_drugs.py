
"""
Fields:
    - id
    - name
    - indications_and_usage
    - warnings

Results are stored in a JSON file.

To extract files use:
    from fetch_otc_drugs import fetch_otc_drugs

    drugs = fetch_otc_drugs(max_records=100)
    ## Display name and indications_and_usage
    for drug in drugs:
        print(drug["name"])
        print(drug["indications_and_usage"])
"""

import os
import json
import argparse
import logging
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


API_URL = "https://api.fda.gov/drug/label.json"
API_KEY = os.getenv("OPENFDA_API_KEY")

SEARCH_QUERY = 'openfda.product_type.exact:"HUMAN OTC DRUG"'
BATCH_SIZE = 1000

# Determine the repository root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "data" / "otc_drugs.json"

logger = logging.getLogger(__name__)


def create_session():
    """
    Creates an HTTP session with automatic retries.
    """
    session = requests.Session()

    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    return session


def extract_drug_data(record):
    """
    Extracts the required fields from an FDA drug record.

    Missing names fall back to the generic name.
    Missing indications and warnings are stored as None.
    """
    openfda = record.get("openfda", {})

    names = (
        openfda.get("brand_name")
        or openfda.get("generic_name")
        or []
    )

    name = names[0] if names else None

    indications = record.get("indications_and_usage", [])
    warnings = record.get("warnings", [])

    return {
        "id": record.get("id"),
        "name": name,
        "indications_and_usage": (
            "\n".join(indications) if indications else None
        ),
        "warnings": (
            "\n".join(warnings) if warnings else None
        )
    }


def fetch_otc_drugs(max_records=None):
    """
    Retrieves human OTC drug records from openFDA.

    Parameters:
        max_records (int | None):
            Maximum number of records to retrieve.
            None retrieves all matching records.

    Returns:
        list[dict]: Extracted drug records.
    """
    if max_records is not None and max_records <= 0:
        raise ValueError("max_records must be positive.")

    drugs = []
    seen_ids = set()

    url = API_URL

    params = {
        "search": SEARCH_QUERY,
        "limit": min(BATCH_SIZE, max_records)
        if max_records is not None else BATCH_SIZE,
        "sort": "effective_time:asc"
    }

    if API_KEY:
        params["api_key"] = API_KEY

    with create_session() as session:

        while url:

            response = session.get(
                url,
                params=params,
                timeout=60
            )

            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if not results:
                break

            for record in results:

                drug = extract_drug_data(record)
                drug_id = drug["id"]

                # Prevent duplicate or unidentified records
                if not drug_id or drug_id in seen_ids:
                    continue

                seen_ids.add(drug_id)
                drugs.append(drug)

                if (
                    max_records is not None
                    and len(drugs) >= max_records
                ):
                    return drugs

            logger.info(
                "Retrieved %s drug records",
                len(drugs)
            )

            # Retrieve the next page using the Link header
            next_page = response.links.get("next", {})
            url = next_page.get("url")

            # The next-page URL already contains query parameters
            params = None

    return drugs


def save_drugs(drugs, output_file=OUTPUT_FILE):
    """
    Saves extracted drug records to a JSON file.
    """
    output_file = Path(output_file)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_file = output_file.with_suffix(".json.tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(
            drugs,
            file,
            indent=4,
            ensure_ascii=False
        )

    # Replace the existing dataset only after a successful write
    temporary_file.replace(output_file)

    logger.info(
        "Saved %s records to %s",
        len(drugs),
        output_file
    )


def main():
    """
    Runs the drug retrieval script from the command line.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Retrieve OTC drug data from openFDA."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of drug records to retrieve."
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help="Path to the output JSON file."
    )

    args = parser.parse_args()

    try:
        drugs = fetch_otc_drugs(
            max_records=args.limit
        )

        save_drugs(drugs, args.output)

    except (requests.RequestException, ValueError, OSError) as error:
        logger.error("Drug retrieval failed: %s", error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
