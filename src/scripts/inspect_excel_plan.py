
import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_excel(filepath):
    logger.info(f"Inspecting file: {filepath}")
    
    try:
        xl = pd.ExcelFile(filepath)
        logger.info(f"Sheet names: {xl.sheet_names}")
        
        for sheet_name in xl.sheet_names:
            logger.info(f"--- Sheet: {sheet_name} ---")
            df = xl.parse(sheet_name, header=None, nrows=10) # Read first 10 rows without header assumption
            logger.info("First 10 rows (raw):")
            logger.info(f"\n{df.to_string(index=False, header=False)}")
            
    except Exception as e:
        logger.error(f"Error reading Excel: {e}")

if __name__ == "__main__":
    target_file = "data_samples/NEW Ежедненвый Даниловский.xlsx"
    if os.path.exists(target_file):
        inspect_excel(target_file)
    else:
        logger.error(f"File not found: {target_file}")
