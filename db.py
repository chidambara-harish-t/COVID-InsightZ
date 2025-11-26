import pandas as pd
from typing import Iterable, Optional
from pathlib import Path

import duckdb 
from .transform import format_region

def _connect_duckdb(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(path)

def wide_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """Convert your MultiIndex wide df → long table (date, country, province, cases)."""

    melted = (
        df
        .drop(columns=[("GlobalCases","")], errors="ignore")
        .melt(
            id_vars=[("Date","")],
            var_name="region",
            value_name="cases"
        )
        .rename(columns={("Date",""): "date"})
    )

    # region country, province split out
    melted["country"] = melted["region"].apply(lambda x: x[0])
    melted["province"] = melted["region"].apply(lambda x: x[1])

    melted["cases"] = pd.to_numeric(melted["cases"], errors="coerce").fillna(0)

    melted["province"] = melted["province"].astype(object)
    melted.loc[melted["province"].isna(), "province"] = None

    return melted[["date","country","province","cases"]]


def init_db(config):
    if config.DB_BACKEND == "duckdb":
        con = _connect_duckdb(config.DUCKDB_PATH)
        con.execute("""
            CREATE TABLE IF NOT EXISTS fact_cases (
              date DATE,
              country TEXT,
              province TEXT,
              cases DOUBLE
            );
        """)
        con.close()
    else:
        pass  

def load_to_db(df: pd.DataFrame, config, replace: bool=False):
    data = wide_to_long(df)
    if config.DB_BACKEND == "duckdb":
        con = _connect_duckdb(config.DUCKDB_PATH)
        if replace:
            con.execute("DELETE FROM fact_cases;")
        con.register("tmp_df", data)
        con.execute("""
            INSERT INTO fact_cases
            SELECT * FROM tmp_df;
        """)
        con.close()
    else:
        pass

def query_range(config, start_date, end_date, regions: Optional[Iterable[tuple[str, str]]] = None) -> pd.DataFrame:
    """Return long data filtered by date range and optional region list."""
    if config.DB_BACKEND == "duckdb":
        con = _connect_duckdb(config.DUCKDB_PATH)

        if regions:
            # VALUES country, province
            vals = []
            for c, p in regions:
                country = c.replace("'", "''")
                if p is None or str(p).lower() == "nan" or str(p).strip() == "":
                    province = "NULL"
                else:
                    province = "'" + str(p).replace("'", "''") + "'"
                vals.append(f"('{country}', {province})")

            values = ",".join(vals)

            sql = f"""
                WITH sel(country, province) AS (VALUES {values})
                SELECT f.*
                FROM fact_cases f
                JOIN sel s ON f.country = s.country
                           AND ((f.province IS NULL AND s.province IS NULL) OR f.province = s.province)
                WHERE f.date BETWEEN ? AND ?
                ORDER BY f.date;
            """
            out = con.execute(sql, [start_date, end_date]).df()

        else:
            out = con.execute("""
                SELECT * 
                FROM fact_cases
                WHERE date BETWEEN ? AND ?
                ORDER BY date;
            """, [start_date, end_date]).df()

        con.close()
        return out
    else:
        return pd.DataFrame()