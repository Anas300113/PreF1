"""P0.2 regression tests: driver_quali_vs_teammate_3 must measure the
driver-vs-teammate qualifying delta, NOT the gap to pole.

The original defect averaged `gap_to_pole_s`, so the feature silently
measured "how far from pole" instead of "how fast vs teammate".
"""
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.features.driver_features import DriverFeatureExtractor
from app.models import (
    Circuit,
    Driver,
    QualifyingResult,
    Race,
    Season,
    Team,
)


async def _make_session(tmp_path):
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path}/teammate_test.db", future=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, factory


async def _seed(factory):
    """Two teammates at Team A; driver X consistently faster than Y.

    A third driver (Z, Team B) takes pole at every event, so gap_to_pole for
    X is POSITIVE (~0.5s) while the true teammate delta is NEGATIVE (−1.0s) —
    the two must never be confused.
    """
    async with factory() as db:
        db.add(Season(year=2024))
        db.add(Circuit(id="c1", name="Circuit 1", country="X", locality="Y"))
        db.add(Team(id="team_a", name="Team A"))
        db.add(Team(id="team_b", name="Team B"))
        db.add(Driver(id="drv_x", first_name="X", last_name="Driver", code="DRX"))
        db.add(Driver(id="drv_y", first_name="Y", last_name="Driver", code="DRY"))
        db.add(Driver(id="drv_z", first_name="Z", last_name="Driver", code="DRZ"))

        # 5 events before the cutoff race; pole by Z with 90.000.
        for i in range(1, 6):
            rid = f"2024_{i}"
            db.add(Race(
                id=rid, season_year=2024, round_number=i, circuit_id="c1",
                name=f"Race {i}", race_date=date(2024, i + 2, 10),
                status="completed",
            ))
            db.add(QualifyingResult(
                race_id=rid, driver_id="drv_x", team_id="team_a",
                position=2, best_time_s=90.5, gap_to_pole_s=0.5,
            ))
            db.add(QualifyingResult(
                race_id=rid, driver_id="drv_y", team_id="team_a",
                position=4, best_time_s=91.5, gap_to_pole_s=1.5,
            ))
            db.add(QualifyingResult(
                race_id=rid, driver_id="drv_z", team_id="team_b",
                position=1, best_time_s=90.0, gap_to_pole_s=0.0,
            ))

        # Cutoff race: strictly AFTER the seeded events (leakage boundary).
        db.add(Race(
            id="2024_6", season_year=2024, round_number=6, circuit_id="c1",
            name="Race 6", race_date=date(2024, 8, 10), status="scheduled",
        ))
        await db.commit()



@pytest.mark.asyncio
async def test_teammate_feature_is_teammate_delta_not_gap_to_pole(tmp_path):
    engine, factory = await _make_session(tmp_path)
    await _seed(factory)
    try:
        async with factory() as db:
            feats = await DriverFeatureExtractor(db).compute_teammate_relative_features(
                "drv_x", "2024_6"
            )
            gap = feats["driver_quali_vs_teammate_3"]
            # True delta: 90.5 − 91.5 = −1.0.  Gap-to-pole would be +0.5.
            assert gap == pytest.approx(-1.0), (
                f"expected teammate delta −1.0s, got {gap} — feature may still "
                "be measuring gap_to_pole"
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_teammate_feature_symmetric_for_slower_teammate(tmp_path):
    engine, factory = await _make_session(tmp_path)
    await _seed(factory)
    try:
        async with factory() as db:
            feats = await DriverFeatureExtractor(db).compute_teammate_relative_features(
                "drv_y", "2024_6"
            )
            # Y is 1.0s slower than X: 91.5 − 90.5 = +1.0.
            assert feats["driver_quali_vs_teammate_3"] == pytest.approx(1.0)
            # Head-to-head: Y lost every comparison.
            assert feats["driver_teammate_q_h2h_win_rate"] == pytest.approx(0.0)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_teammate_rolling_stats_and_h2h(tmp_path):
    engine, factory = await _make_session(tmp_path)
    await _seed(factory)
    try:
        async with factory() as db:
            feats = await DriverFeatureExtractor(db).compute_teammate_relative_features(
                "drv_x", "2024_6"
            )
            assert feats["driver_quali_vs_teammate_5_mean"] == pytest.approx(-1.0)
            assert feats["driver_quali_vs_teammate_5_median"] == pytest.approx(-1.0)
            assert feats["driver_quali_vs_teammate_5_std"] == pytest.approx(0.0)
            # X beat Y at every one of the 5 events.
            assert feats["driver_teammate_q_h2h_win_rate"] == pytest.approx(1.0)
            assert feats["driver_teammate_q_comparisons"] == pytest.approx(5.0)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_teammate_feature_respects_cutoff_leakage(tmp_path):
    """Events ON/AFTER the cutoff race date must not contribute."""
    engine, factory = await _make_session(tmp_path)
    await _seed(factory)
    try:
        async with factory() as db:
            # Cutoff = first seeded event → nothing strictly before it.
            feats = await DriverFeatureExtractor(db).compute_teammate_relative_features(
                "drv_x", "2024_1"
            )
            import math
            assert math.isnan(feats["driver_quali_vs_teammate_3"])
            assert feats["driver_teammate_q_comparisons"] == 0.0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_no_cross_team_comparison(tmp_path):
    """drv_z (Team B) has no same-team qualifying partner → NaN, never a
    comparison against Team A drivers."""
    engine, factory = await _make_session(tmp_path)
    await _seed(factory)
    try:
        async with factory() as db:
            feats = await DriverFeatureExtractor(db).compute_teammate_relative_features(
                "drv_z", "2024_6"
            )
            import math
            assert math.isnan(feats["driver_quali_vs_teammate_3"])
            assert feats["driver_teammate_q_comparisons"] == 0.0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_missing_teammate_time_skipped(tmp_path):
    """If the teammate has no valid qualifying time the event is skipped."""
    engine, factory = await _make_session(tmp_path)
    await _seed(factory)
    async with factory() as db:
        row = (
            await db.execute(
                select(QualifyingResult).where(
                    QualifyingResult.race_id == "2024_5",
                    QualifyingResult.driver_id == "drv_y",
                )
            )
        ).scalar_one()
        row.best_time_s = None
        await db.commit()
    try:
        async with factory() as db:
            feats = await DriverFeatureExtractor(db).compute_teammate_relative_features(
                "drv_x", "2024_6"
            )
            # Only 4 valid comparisons remain.
            assert feats["driver_teammate_q_comparisons"] == pytest.approx(4.0)
            assert feats["driver_quali_vs_teammate_3"] == pytest.approx(-1.0)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_teammate_change_uses_per_event_team(tmp_path):
    """After a mid-season transfer the driver compares against the NEW
    teammate — never against the old team's driver."""
    engine, factory = await _make_session(tmp_path)
    await _seed(factory)
    async with factory() as db:
        # Events 4 & 5: X now drives for team_b alongside Z.
        for rid in ("2024_4", "2024_5"):
            x = (
                await db.execute(
                    select(QualifyingResult).where(
                        QualifyingResult.race_id == rid,
                        QualifyingResult.driver_id == "drv_x",
                    )
                )
            ).scalar_one()
            x.team_id = "team_b"
            # X now 90.2, Z (teammate) 90.0 → delta +0.2 for X.
            x.best_time_s = 90.2
            x.gap_to_pole_s = 0.2
        # Give team_a a stand-in so Y keeps a teammate after X leaves.
        db.add(Driver(id="drv_w", first_name="W", last_name="Driver", code="DRW"))
        for rid in ("2024_4", "2024_5"):
            db.add(QualifyingResult(
                race_id=rid, driver_id="drv_w", team_id="team_a",
                position=5, best_time_s=92.0, gap_to_pole_s=2.0,
            ))
        await db.commit()
    try:
        async with factory() as db:
            feats = await DriverFeatureExtractor(db).compute_teammate_relative_features(
                "drv_x", "2024_6"
            )
            # Newest two comparisons (team_b vs Z): 90.2 − 90.0 = +0.2.
            # Older three (team_a vs Y): 90.5 − 91.5 = −1.0.
            assert feats["driver_teammate_q_comparisons"] == pytest.approx(5.0)
            # Mean of last 3: +0.2, +0.2, −1.0 → −0.2
            assert feats["driver_quali_vs_teammate_3"] == pytest.approx(
                (0.2 + 0.2 - 1.0) / 3
            )
    finally:
        await engine.dispose()

