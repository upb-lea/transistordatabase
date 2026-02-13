"""Tests for catalog CSV importer."""
from __future__ import annotations

from pathlib import Path

import pytest

from transistordatabase.catalog_importer import (
    CatalogEntry,
    catalog_to_transistors,
    parse_catalog_csv,
    rank_by_fom,
)

TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture
def sample_csv() -> Path:
    """Return path to sample catalog CSV."""
    return TEST_DATA_DIR / "sample_catalog.csv"


@pytest.fixture
def catalog_entries(sample_csv: Path) -> list[CatalogEntry]:
    """Parse the sample catalog CSV."""
    return parse_catalog_csv(sample_csv)


class TestCatalogParsing:
    """Tests for CSV catalog parsing."""

    def test_parse_returns_entries(self, catalog_entries: list[CatalogEntry]) -> None:
        """Verify parsing returns correct number of entries."""
        assert len(catalog_entries) == 5

    def test_part_number_parsed(self, catalog_entries: list[CatalogEntry]) -> None:
        """Verify part numbers are correctly extracted."""
        names = [e.part_number for e in catalog_entries]
        assert "C3M0060065J" in names
        assert "GS66516T" in names

    def test_voltage_parsed(self, catalog_entries: list[CatalogEntry]) -> None:
        """Verify voltage values are correctly parsed."""
        for entry in catalog_entries:
            assert entry.v_ds_max == 650.0

    def test_resistance_parsed(self, catalog_entries: list[CatalogEntry]) -> None:
        """Verify Rds(on) is parsed with mOhm conversion."""
        entry = next(e for e in catalog_entries if e.part_number == "C3M0060065J")
        assert entry.r_ds_on == pytest.approx(0.060)

    def test_charge_parsed(self, catalog_entries: list[CatalogEntry]) -> None:
        """Verify gate charge is parsed with nC conversion."""
        entry = next(e for e in catalog_entries if e.part_number == "C3M0060065J")
        assert entry.q_g == pytest.approx(30e-9)

    def test_file_not_found(self) -> None:
        """Verify FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            parse_catalog_csv("/nonexistent/path.csv")


class TestFomCalculation:
    """Tests for Figure of Merit calculations."""

    def test_fom_rds_qg(self) -> None:
        """Verify Rds*Qg FOM calculation."""
        entry = CatalogEntry(
            part_number="TEST", manufacturer="Test",
            r_ds_on=0.060, q_g=30e-9,
        )
        fom = entry.calc_fom_rds_qg()
        assert fom == pytest.approx(0.060 * 30e-9)

    def test_fom_missing_data(self) -> None:
        """Verify FOM returns None when data is missing."""
        entry = CatalogEntry(
            part_number="TEST", manufacturer="Test",
        )
        assert entry.calc_fom_rds_qg() is None

    def test_ranking(self, catalog_entries: list[CatalogEntry]) -> None:
        """Verify FOM ranking sorts correctly (lower is better)."""
        ranked = rank_by_fom(catalog_entries)
        assert len(ranked) > 0
        # GaN should rank well (low Rds*Qg)
        fom_values = [fom for _, fom in ranked]
        assert fom_values == sorted(fom_values)


class TestCatalogToTransistors:
    """Tests for converting catalog entries to Transistor objects."""

    def test_conversion(self, catalog_entries: list[CatalogEntry]) -> None:
        """Verify catalog entries convert to Transistor objects."""
        transistors = catalog_to_transistors(catalog_entries)
        assert len(transistors) == 5
        for t in transistors:
            assert t.metadata.name != ""
            assert t.electrical_ratings.v_abs_max > 0
            assert t.electrical_ratings.i_abs_max > 0

    def test_type_mapping(self, catalog_entries: list[CatalogEntry]) -> None:
        """Verify device types are preserved."""
        transistors = catalog_to_transistors(catalog_entries)
        types = {t.metadata.type for t in transistors}
        assert "SiC MOSFET" in types or "SiC-MOSFET" in types or "MOSFET" in types
