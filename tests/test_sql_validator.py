from main import _validate_sql_query


def test_cross_join_with_on_is_invalid():
    sql = """
    SELECT *
    FROM GLTransactions t
    CROSS JOIN GLAccount a ON t.GLAccountID = a.GLAccountDimPKID
    """
    errors = _validate_sql_query(sql, "total revenue")
    assert any("CROSS JOIN cannot have an ON clause" in e for e in errors)


def test_invalid_community_column_is_detected():
    sql = """
    SELECT cm.Community
    FROM Community cm
    """
    errors = _validate_sql_query(sql, "revenue for EWIG")
    assert any("Invalid community label column" in e for e in errors)


def test_ytd_explicit_year_should_not_use_getdate():
    sql = """
    SELECT SUM(GLNetChangeACY)
    FROM GLTransactions
    WHERE DateID BETWEEN YEAR(GETDATE()) * 10000 + 101
    AND CAST(CONVERT(char(8), GETDATE(), 112) AS INT)
    """
    errors = _validate_sql_query(sql, "total revenue YTD for 2025")
    assert any("must not use GETDATE" in e for e in errors)