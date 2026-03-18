from __future__ import annotations
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd


def read_in_data(filepath, name):

    # date = ''
    filename = f"{name}.csv"
    full_path = os.path.join(filepath, filename)

    
    df = pd.read_csv(full_path)
    
    return df

def save_data(df, filepath, name):

    date = ''
    filename = f"{date}-{name}.csv"
    full_path = os.path.join(filepath, filename)

    df.to_csv(full_path, ignore_index=True)

    print('Data saved!')

def combine_data(output_file, cip, cp, bs, a, eq, t):
    # Specify the filename

    # Save the DataFrames to the Excel file with sheet names
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        cip.to_excel(writer, sheet_name='Companies in Portfolio', index=False)
        cp.to_excel(writer, sheet_name='Company Page Data', index=False)
        bs.to_excel(writer, sheet_name='Buy Sell Alerts', index=False)
        a.to_excel(writer, sheet_name='Analytics', header=False)
        eq.to_excel(writer, sheet_name='Equity Curve', index=False)
        t.to_excel(writer, sheet_name='Trades', index=False)

    print(f"Data saved to {output_file} successfully!")


#new
def read_excel_sheet(directory_path: str | Path, sheet: str | int = 0, file_extension: str = '.xlsx', **pd_kwargs) -> pd.DataFrame:
    """
    Read a single sheet from the most recently updated Excel file in a directory.
    Args:
        directory_path: Path to directory containing Excel files.
        sheet: Sheet name or 0-based index.
        file_extension: File extension to filter by (default: '.xlsx').
        **pd_kwargs: Forwarded to pandas.read_excel (dtype=, usecols=, etc.)
    """
    dir_path = Path(directory_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    # Get all Excel files in directory
    valid_extensions = ['.xlsx', '.xlsm']
    files = [f for f in dir_path.iterdir() 
             if f.is_file() and f.suffix.lower() in valid_extensions]
    
    # Filter by specific extension if provided
    if file_extension:
        files = [f for f in files if f.suffix.lower() == file_extension.lower()]
    
    if not files:
        raise FileNotFoundError(f"No Excel files found in directory: {dir_path}")
    
    # Find the most recent file by modification time
    most_recent_file = max(files, key=lambda f: f.stat().st_mtime)
    
    print(f"Reading from most recent file: {most_recent_file.name}")
    return pd.read_excel(most_recent_file, sheet_name=sheet, engine="openpyxl", **pd_kwargs)

#new
def overwrite_excel_sheet(path: str | Path,
                            df: pd.DataFrame,
                            sheet: str = "Sheet1",
                            *,
                            index: bool = False,
                            backup: bool = True,
                            keep_vba: bool = False) -> Path:
    """
    Overwrite (replace) a single sheet in an Excel workbook with the provided DataFrame.
    - Preserves other sheets.
    - If file doesn't exist, creates it.

    Args:
        path: Target .xlsx/.xlsm file.
        df: DataFrame to write.
        sheet: Sheet name to replace/create.
        index: Write DataFrame index to Excel.
        backup: If True, create a timestamped .bak copy before writing.
        keep_vba: Use True when editing .xlsm macro workbooks.

    Returns:
        Path to the saved workbook.
    """
    p = Path(path)
    if p.suffix.lower() not in (".xlsx", ".xlsm"):
        raise ValueError("Only .xlsx/.xlsm supported.")

    # Optional backup of existing file
    if backup and p.exists():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = p.with_name(f"{p.stem}.bak-{ts}{p.suffix}")
        shutil.copy2(p, bak)

    # Create or update: replace just the target sheet
    engine_kwargs = {"keep_vba": keep_vba} if p.suffix.lower() == ".xlsm" else {}
    mode = "a" if p.exists() else "w"

    with pd.ExcelWriter(
        p, engine="openpyxl", mode=mode,
        if_sheet_exists="replace" if mode == "a" else None,
        engine_kwargs=engine_kwargs or None,
    ) as writer:
        df.to_excel(writer, sheet_name=sheet, index=index)

    return p

def copy_most_recent_file(directory: str | Path, new_filename: str, file_extension: str = '.xlsx') -> Path:
    """
    Find the most recent file in a directory and copy it with a new filename.
    Args:
        directory: Directory path to search for files.
        new_filename: New name for the copied file (without extension).
        file_extension: Optional file extension filter (e.g., '.csv', '.xlsx'). If None, searches all files.
    Returns:
        Path to the newly created file.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    # Get all files in directory
    if file_extension:
        # Filter by extension
        files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() == file_extension.lower()]
    else:
        # Get all files
        files = [f for f in dir_path.iterdir() if f.is_file()]
    
    if not files:
        raise FileNotFoundError(f"No files found in directory: {dir_path}")
    
    # Find the most recent file by modification time
    most_recent_file = max(files, key=lambda f: f.stat().st_mtime)
    
    # Create new filename with same extension as the most recent file
    new_file_path = dir_path / f"{new_filename}{most_recent_file.suffix}"
    
    # Copy the most recent file to the new filename
    shutil.copy2(most_recent_file, new_file_path)
    
    print(f"Copied '{most_recent_file.name}' to '{new_file_path.name}'")
    
    return new_file_path