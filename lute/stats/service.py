"""
Calculating stats.
"""

from datetime import datetime, timedelta
from sqlalchemy import text
from collections import defaultdict

def _get_data_per_lang(session):
    "Return dict of lang name to dict[date_yyyymmdd}: count"
    ret = {}
    sql = """
    select lang, dt, sum(WrWordCount) as count
    from (
      select LgName as lang, strftime('%Y-%m-%d', WrReadDate) as dt, WrWordCount
      from wordsread
      inner join languages on LgID = WrLgID
    ) raw
    group by lang, dt
    """
    result = session.execute(text(sql)).all()
    for row in result:
        langname = row[0]
        if langname not in ret:
            ret[langname] = {}
        ret[langname][row[1]] = int(row[2])
    return ret


def get_chart_data(session):
    sql = """
    SELECT
        LgName AS lang,
        strftime('%Y-%m-%d', WoStatusChanged) AS dt,
        COUNT(*) AS updates
    FROM words
    JOIN languages ON LgID = WoLgID
    WHERE WoStatusChanged IS NOT NULL
    GROUP BY LgName, dt
    ORDER BY dt
    """
    rows = session.execute(text(sql))
    result = defaultdict(lambda: defaultdict(int))
    for row in rows:
        result[row[0]][row[1]] = row[2]
    return result


def get_table_data(session):
    now = datetime.now()
    day = now.date().isoformat()
    week = (now - timedelta(days=7)).date().isoformat()
    month = (now - timedelta(days=30)).date().isoformat()
    year = (now - timedelta(days=365)).date().isoformat()

    sql = """
    SELECT
        LgName AS lang,
        WoStatusChanged AS changed
    FROM words
    JOIN languages ON LgID = WoLgID
    WHERE WoStatusChanged IS NOT NULL
    """
    rows = session.execute(text(sql))
    stats = defaultdict(list)
    for row in rows:
        stats[row[0]].append(row[1])  # group dates by language

    result = []
    for lang, dates in stats.items():
        counts = {
            "day": 0,
            "week": 0,
            "month": 0,
            "year": 0,
            "total": len(dates),
        }
        for d in dates:
            if d >= day:
                counts["day"] += 1
            if d >= week:
                counts["week"] += 1
            if d >= month:
                counts["month"] += 1
            if d >= year:
                counts["year"] += 1
        result.append({"name": lang, "counts": counts})

    return result


def _readcount_by_date(readbydate):
    """
    Return data as array: [ today, week, month, year, all time ]

    This may be inefficient, but will do for now.
    """
    today = datetime.now().date()

    def _in_range(i):
        start_date = today - timedelta(days=i)
        dates = [
            start_date + timedelta(days=x) for x in range((today - start_date).days + 1)
        ]
        ret = 0
        for d in dates:
            df = d.strftime("%Y-%m-%d")
            ret += readbydate.get(df, 0)
        return ret

    return {
        "day": _in_range(0),
        "week": _in_range(6),
        "month": _in_range(29),
        "year": _in_range(364),
        "total": _in_range(3650),  # 10 year drop off :-P
    }


