from collections.abc import Iterator
from datetime import datetime

import pytest

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import DB_TZ, convert_tz
from vnpy.trader.object import BarData, TickData
from vnpy_mysql.mysql_database import MysqlDatabase
import vnpy_mysql.mysql_database as mysql_db


sql_log: list[tuple[str, tuple[object, ...]]] = []


class _Cursor:
    def __init__(self) -> None:
        self.rowcount = 2
        self.lastrowid = 1
        self.description = None

    def execute(self, sql: str, params: object = None) -> None:
        stored: tuple[object, ...] = tuple(params) if params is not None else ()
        sql_log.append((sql, stored))

    def __iter__(self) -> Iterator[tuple[object, ...]]:
        return iter(())

    def fetchone(self) -> None:
        return None

    def fetchall(self) -> list[tuple[object, ...]]:
        return []

    def close(self) -> None:
        return None


class _Connection:
    def cursor(self, *_args: object, **_kwargs: object) -> _Cursor:
        return _Cursor()

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


def _connect(*_args: object, **_kwargs: object) -> bool:
    mysql_db.db._state.set_connection(_Connection())
    return True


def _driver_sql() -> list[tuple[str, tuple[object, ...]]]:
    skipped: set[str] = {"BEGIN", "COMMIT", "ROLLBACK"}
    return [item for item in sql_log if item[0] not in skipped]


def _make_bars(symbol: str) -> list[BarData]:
    start: datetime = datetime(2024, 1, 15, 10, 0, tzinfo=DB_TZ)
    end: datetime = datetime(2024, 1, 15, 10, 1, tzinfo=DB_TZ)
    return [
        BarData(
            gateway_name="TEST",
            symbol=symbol,
            exchange=Exchange.SHFE,
            datetime=start,
            interval=Interval.MINUTE,
            volume=12.0,
            turnover=1.5,
            open_interest=3.0,
            open_price=100.0,
            high_price=110.0,
            low_price=90.0,
            close_price=105.0,
        ),
        BarData(
            gateway_name="TEST",
            symbol=symbol,
            exchange=Exchange.SHFE,
            datetime=end,
            interval=Interval.MINUTE,
            volume=8.0,
            turnover=0.0,
            open_interest=0.0,
            open_price=105.0,
            high_price=112.0,
            low_price=101.0,
            close_price=108.0,
        ),
    ]


def _make_ticks(symbol: str) -> list[TickData]:
    start: datetime = datetime(2024, 1, 16, 10, 0, tzinfo=DB_TZ)
    end: datetime = datetime(2024, 1, 16, 10, 0, 1, tzinfo=DB_TZ)
    return [
        TickData(
            gateway_name="TEST",
            symbol=symbol,
            exchange=Exchange.SHFE,
            datetime=start,
            name="au",
            last_price=400.5,
            volume=20.0,
            localtime=start,
        ),
        TickData(
            gateway_name="TEST",
            symbol=symbol,
            exchange=Exchange.SHFE,
            datetime=end,
            name="au",
            last_price=401.0,
            volume=21.0,
            localtime=end,
        ),
    ]


def _bar_params(bar: BarData) -> tuple[object, ...]:
    interval: Interval | None = bar.interval
    assert interval is not None
    return (
        bar.symbol,
        bar.exchange.value,
        convert_tz(bar.datetime),
        interval.value,
        bar.volume,
        bar.turnover,
        bar.open_interest,
        bar.open_price,
        bar.high_price,
        bar.low_price,
        bar.close_price,
    )


@pytest.fixture
def database(monkeypatch: pytest.MonkeyPatch) -> MysqlDatabase:
    sql_log.clear()
    monkeypatch.setattr(mysql_db.db, "connect", _connect)
    db: MysqlDatabase = MysqlDatabase()
    sql_log.clear()
    return db


def test_save_bar_data_replaces_symbol_exchange_interval_ohlcv(database: MysqlDatabase) -> None:
    symbol: str = "rb2405"
    bars: list[BarData] = _make_bars(symbol)
    expected: tuple[object, ...] = _bar_params(bars[0]) + _bar_params(bars[1])

    assert database.save_bar_data(bars) is True

    inserts: list[tuple[str, tuple[object, ...]]] = [
        item for item in _driver_sql() if item[0].startswith("REPLACE INTO `dbbardata`")
    ]
    assert len(inserts) == 1
    sql, params = inserts[0]
    assert "(`symbol`, `exchange`, `datetime`, `interval`, `volume`, `turnover`, `open_interest`, `open_price`, `high_price`, `low_price`, `close_price`)" in sql
    assert "gateway_name" not in sql
    assert "vt_symbol" not in sql
    assert params == expected

    overviews: list[tuple[str, tuple[object, ...]]] = [
        item for item in _driver_sql() if item[0].startswith("INSERT INTO `dbbaroverview`")
    ]
    assert len(overviews) == 1
    assert overviews[0][1] == (
        symbol,
        Exchange.SHFE.value,
        Interval.MINUTE.value,
        2,
        expected[2],
        expected[13],
    )


def test_load_bar_data_filters_symbol_and_datetime_bounds(database: MysqlDatabase) -> None:
    start: datetime = datetime(2024, 1, 1, tzinfo=DB_TZ)
    end: datetime = datetime(2024, 2, 1, tzinfo=DB_TZ)
    loaded: list[BarData] = database.load_bar_data(
        "rb2405",
        Exchange.SHFE,
        Interval.MINUTE,
        start,
        end,
    )
    assert loaded == []
    assert len(sql_log) == 1
    sql, params = sql_log[0]
    assert "FROM `dbbardata`" in sql
    assert "ORDER BY `t1`.`datetime`" in sql
    assert params == ("rb2405", Exchange.SHFE.value, Interval.MINUTE.value, start, end)


def test_delete_bar_data_uses_symbol_exchange_interval(database: MysqlDatabase) -> None:
    count: int = database.delete_bar_data("rb2405", Exchange.SHFE, Interval.MINUTE)
    assert count == 2
    deletes: list[tuple[str, tuple[object, ...]]] = [
        item for item in sql_log if item[0].startswith("DELETE")
    ]
    assert len(deletes) == 2
    assert "DELETE FROM `dbbardata`" in deletes[0][0]
    assert deletes[0][1] == ("rb2405", Exchange.SHFE.value, Interval.MINUTE.value)
    assert "DELETE FROM `dbbaroverview`" in deletes[1][0]
    assert deletes[1][1] == ("rb2405", Exchange.SHFE.value, Interval.MINUTE.value)


def test_save_tick_data_replaces_symbol_exchange_and_last_price(database: MysqlDatabase) -> None:
    symbol: str = "au2406"
    ticks: list[TickData] = _make_ticks(symbol)
    first_dt: datetime = convert_tz(ticks[0].datetime)
    second_dt: datetime = convert_tz(ticks[1].datetime)

    assert database.save_tick_data(ticks) is True

    inserts: list[tuple[str, tuple[object, ...]]] = [
        item for item in _driver_sql() if item[0].startswith("REPLACE INTO `dbtickdata`")
    ]
    assert len(inserts) == 1
    sql, params = inserts[0]
    assert "`symbol`, `exchange`, `datetime`" in sql
    assert "`last_price`" in sql
    assert "gateway_name" not in sql
    assert params[0] == symbol
    assert params[1] == Exchange.SHFE.value
    assert first_dt in params
    assert second_dt in params
    assert 400.5 in params
    assert 401.0 in params
    assert ticks[0].localtime in params


def test_load_tick_data_filters_symbol_and_datetime_bounds(database: MysqlDatabase) -> None:
    start: datetime = datetime(2024, 1, 1, tzinfo=DB_TZ)
    end: datetime = datetime(2024, 2, 1, tzinfo=DB_TZ)
    loaded: list[TickData] = database.load_tick_data("au2406", Exchange.SHFE, start, end)
    assert loaded == []
    assert len(sql_log) == 1
    sql, params = sql_log[0]
    assert "FROM `dbtickdata`" in sql
    assert params == ("au2406", Exchange.SHFE.value, start, end)


def test_delete_tick_data_uses_symbol_and_exchange(database: MysqlDatabase) -> None:
    count: int = database.delete_tick_data("au2406", Exchange.SHFE)
    assert count == 2
    deletes: list[tuple[str, tuple[object, ...]]] = [
        item for item in sql_log if item[0].startswith("DELETE")
    ]
    assert len(deletes) == 2
    assert "DELETE FROM `dbtickdata`" in deletes[0][0]
    assert deletes[0][1] == ("au2406", Exchange.SHFE.value)
    assert "DELETE FROM `dbtickoverview`" in deletes[1][0]
    assert deletes[1][1] == ("au2406", Exchange.SHFE.value)
