
import sys
import os
import re
import logging
from typing import List, Dict

sys.path.append(os.getcwd())
from src.services.data_loader.sheets_client import SheetsClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_orgs_list(file_path: str) -> List[Dict[str, str]]:
    """Parses orgs_list.txt to extract ID and Name."""
    orgs = []
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return orgs
        
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Look for pattern: ID: <uid>, Name: <name>
            match = re.search(r"ID:\s+([a-f0-9\-]+),\s+Name:\s+(.+)", line)
            if match:
                org_slug = match.group(2).strip()
                org_id = match.group(1).strip()
                orgs.append({"name": org_slug, "id": org_id})
    return orgs

def main():
    logger.info("Initializing Settings Tab...")
    client = SheetsClient(settings.GOOGLE_SHEETS_SPREADSHEET_ID)
    
    # 1. Parse Orgs
    orgs = parse_orgs_list("orgs_list.txt")
    if not orgs:
        logger.error("No organizations found in orgs_list.txt")
        return
        
    logger.info(f"Found {len(orgs)} organizations.")
    
    # 2. Prepare Data for Sheet
    # Header
    header = ["Настройка", "Значение", "", "Список Ресторанов (Справочник)", "ID Ресторана"]
    
    # Config Section (Top Left)
    # We want B2 to be the specific cell for Active Restaurant ID
    # But usually user wants to select by Name. 
    # Let's make A2="Active Restaurant", B2="NAME" (Dropdown), C2="ID" (VLOOKUP)
    
    # Actually, simpler: 
    # A2: "Активный Ресторан (ID)"
    # B2: <The UUID>
    
    # Even better user experience:
    # A2: "Активный Ресторан"
    # B2: <Drop down of Names>
    # C2: <Formula to get ID> or just script finds ID from the list below.
    
    # For MVP: Let's just list them and let user copy-paste or just have B2 be the ID.
    # Updated Plan:
    # Col A: Config Name, Col B: Config Value
    # Col D: Rest Name, Col E: Rest ID
    
    rows = []
    rows.append(header)
    
    # Current Active (Default to first or env var)
    active_id = orgs[0]["id"]
    active_name = orgs[0]["name"]
    
    # Row 2: Active Config
    rows.append(["Активный Ресторан ID:", active_id, "", "-->", "<-- Скопируйте ID отсюда"])
    
    # Spacer
    rows.append(["", "", "", "", ""])
    
    # List of Orgs
    for org in orgs:
        # Col D (index 3) and E (index 4)
        row = ["", "", "", org["name"], org["id"]]
        rows.append(row)
        
    # 3. Update Sheet
    # Ensure it exists
    client.get_or_create_worksheet("НАСТРОЙКИ ⚙️")
    
    client.clear_worksheet("НАСТРОЙКИ ⚙️")
    client.update_worksheet("НАСТРОЙКИ ⚙️", rows)
    logger.info("Settings Tab Updated! Go to 'НАСТРОЙКИ ⚙️' to select your restaurant.")

if __name__ == "__main__":
    main()
