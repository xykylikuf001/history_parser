import time
import pandas as pd
import requests
from datetime import datetime

# ===================== CONFIG =====================

CSV_PATH = "data-200.csv"
BACKEND_URL = "https://sport.ashgabat.gov.tm/api/seats/stores"

REQUIRED_COLUMNS = [
    "sector_name",
    "row_name",
    "start_number",
    "end_number",
]


# ===================== VALIDATION =====================

def build_invalid_mask(df: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=df.index)

    # Schema validation
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            return pd.Series(True, index=df.index)

    # Null values
    mask |= df[REQUIRED_COLUMNS].isnull().any(axis=1)

    # Empty strings
    mask |= (
        df[REQUIRED_COLUMNS]
        .astype(str)
        .apply(lambda c: c.str.strip() == "")
        .any(axis=1)
    )

    # Numeric validation
    for col in ["row_name", "start_number", "end_number"]:
        mask |= pd.to_numeric(df[col], errors="coerce").isnull()

    # Logical validation
    mask |= df["start_number"] > df["end_number"]
    mask |= (df[["start_number", "end_number"]] <= 0).any(axis=1)

    return mask


def export_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    invalid_mask = build_invalid_mask(df)
    invalid_df = df[invalid_mask]

    if not invalid_df.empty:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"invalid_rows_{ts}.csv"
        invalid_df.to_csv(filename, index=False)

    return invalid_df


# ===================== EXPANSION =====================

def expand_seats(df: pd.DataFrame) -> pd.DataFrame:
    seats = []

    for _, r in df.iterrows():
        start = int(r["start_number"])
        end = int(r["end_number"])
        seats.append({
            "sector_name": str(r["sector_name"]),
            "row_name": str(r["row_name"]),
            "start_number": start,
            "end_number": end,
            # "type": r["type"],
        })
    return pd.DataFrame(seats)


# ===================== SENDER =====================

def send_seats_individually(df: pd.DataFrame):
    failed_rows = []

    for _, row in df.iterrows():
        payload = row.to_dict()
        print(payload)
        try:
            response = requests.post(
                BACKEND_URL,
                json=payload,
                timeout=30,
            )
            # Consider any non-200 as failure
            if response.status_code != 200:
                print(f"Failed request (status {response.status_code}): {payload}")
                failed_rows.append(payload)

        except requests.RequestException as e:
            print(f"Request exception for row {payload}: {e}")
            failed_rows.append(payload)

        # rate-limit delay (5 seconds)
        time.sleep(5)
    # Save failed requests if any
    if failed_rows:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        failed_df = pd.DataFrame(failed_rows)
        filename = f"failed_requests_{ts}.csv"
        failed_df.to_csv(filename, index=False)
        print(f"Failed requests saved to: {filename}")


# ===================== MAIN =====================

if __name__ == "__main__":
    df = pd.read_csv(CSV_PATH, sep=";")

    invalid_df = export_invalid_rows(df)
    valid_df = df.drop(invalid_df.index)

    seats_df = expand_seats(valid_df)

    send_seats_individually(seats_df)
