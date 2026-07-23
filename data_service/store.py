"""SQLite 持久化快取：只存「歷史」K 線（日/週/月），即時資料（五檔/分時/分鐘 K）
不落地——它們 30 秒就過期，落地只是存垃圾。設計定稿見 plan.md Phase 1a。

一列＝一根 K 棒，主鍵 (ticker, interval, ts)：同一天重寫即覆蓋，所以「當日 K 棒
盤中一直變」不用特殊處理，收盤後自然定型。存 yfinance 原始精度，四捨五入在
輸出層（sources/stock.py）做，跟改動前行為一致。
"""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

# repo 根目錄下的 data/cache.db（gitignored；WAL 會另產生 -wal/-shm）
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "cache.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS candles (
    ticker     TEXT NOT NULL,
    interval   TEXT NOT NULL,
    ts         TEXT NOT NULL,
    open       REAL NOT NULL,
    high       REAL NOT NULL,
    low        REAL NOT NULL,
    close      REAL NOT NULL,
    volume     INTEGER NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (ticker, interval, ts)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS source_meta (
    ticker       TEXT NOT NULL,
    interval     TEXT NOT NULL,
    source_start TEXT NOT NULL,  -- 資料源最早只有到這天（新上市股票避免反覆全抓）
    PRIMARY KEY (ticker, interval)
) WITHOUT ROWID;
"""


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


def coverage(ticker: str, interval: str) -> tuple[str, str] | None:
    """已存區間 (最早 ts, 最晚 ts)；沒存過回 None。"""
    with closing(_conn()) as conn:
        row = conn.execute(
            "SELECT MIN(ts), MAX(ts) FROM candles WHERE ticker=? AND interval=?",
            (ticker, interval),
        ).fetchone()
    return (row[0], row[1]) if row and row[0] else None


def source_start(ticker: str, interval: str) -> str | None:
    with closing(_conn()) as conn:
        row = conn.execute(
            "SELECT source_start FROM source_meta WHERE ticker=? AND interval=?",
            (ticker, interval),
        ).fetchone()
    return row[0] if row else None


def record_source_start(ticker: str, interval: str, ts: str) -> None:
    """記下「資料源最早只有到 ts」；已有更早記錄就保留更早的。"""
    with closing(_conn()) as conn, conn:
        conn.execute(
            """INSERT INTO source_meta (ticker, interval, source_start) VALUES (?, ?, ?)
               ON CONFLICT(ticker, interval)
               DO UPDATE SET source_start = MIN(source_start, excluded.source_start)""",
            (ticker, interval, ts),
        )


def tail_ts(ticker: str, interval: str, n: int) -> str | None:
    """倒數第 n 根 K 棒的 ts（增量抓取的重疊起點）；不足 n 根就回最早那根。"""
    with closing(_conn()) as conn:
        rows = conn.execute(
            "SELECT ts FROM candles WHERE ticker=? AND interval=? ORDER BY ts DESC LIMIT ?",
            (ticker, interval, n),
        ).fetchall()
    return rows[-1][0] if rows else None


def closes_since(ticker: str, interval: str, start_ts: str) -> dict[str, float]:
    """start_ts（含）以後的 {ts: close}，給除權息偵測比對用。"""
    with closing(_conn()) as conn:
        rows = conn.execute(
            "SELECT ts, close FROM candles WHERE ticker=? AND interval=? AND ts>=?",
            (ticker, interval, start_ts),
        ).fetchall()
    return dict(rows)


def rows_since(ticker: str, interval: str, start_ts: str | None) -> list[dict]:
    """start_ts（含）以後的 K 棒，時間升冪；start_ts=None 回全部。"""
    sql = "SELECT ts, open, high, low, close, volume FROM candles WHERE ticker=? AND interval=?"
    params: list = [ticker, interval]
    if start_ts is not None:
        sql += " AND ts>=?"
        params.append(start_ts)
    sql += " ORDER BY ts ASC"
    with closing(_conn()) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        {"time": r[0], "open": r[1], "high": r[2], "low": r[3], "close": r[4], "volume": r[5]}
        for r in rows
    ]


def upsert(ticker: str, interval: str, rows: list[dict]) -> None:
    """寫入 K 棒，同 (ticker, interval, ts) 直接覆寫（除權息重抓、當日棒更新都靠這個）。"""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(_conn()) as conn, conn:
        conn.executemany(
            """INSERT OR REPLACE INTO candles
               (ticker, interval, ts, open, high, low, close, volume, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (ticker, interval, r["time"], r["open"], r["high"], r["low"],
                 r["close"], r["volume"], now)
                for r in rows
            ],
        )
