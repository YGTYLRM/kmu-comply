import pytest
from fastapi.testclient import TestClient
import sys
import os

# Allow imports from backend root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app
from models.company_profile import CompanyProfile


@pytest.fixture
def client():
    return TestClient(app)


# ── Canonical test profiles ────────────────────────────────────────────────────

@pytest.fixture
def profile_it_agency():
    """Profile 1: Small IT agency — 5 employees, processes personal data."""
    return CompanyProfile(
        company_name="TechBit GmbH",
        industry="it_software",
        employee_count=5,
        annual_revenue_eur=400_000,
        processes_personal_data=True,
        processes_special_category_data=False,
        processing_is_occasional=False,
        has_supply_chain_abroad=False,
    )


@pytest.fixture
def profile_manufacturer():
    """Profile 2: Large manufacturer — 1200 employees, supply chain in Asia, high energy.
    Employee count >= 1000 so LkSG applies directly (§1(1) LkSG)."""
    return CompanyProfile(
        company_name="MaschBau AG",
        industry="manufacturing",
        employee_count=1200,
        annual_revenue_eur=75_000_000,
        balance_sheet_total_eur=40_000_000,
        processes_personal_data=True,
        processes_special_category_data=False,
        processing_is_occasional=False,
        has_supply_chain_abroad=True,
        supply_chain_countries=["CN", "VN", "IN"],
        annual_energy_consumption_mwh=10_000,
    )


@pytest.fixture
def profile_large_listed():
    """Profile 3: Large listed company — 1500 employees, all regulations apply."""
    return CompanyProfile(
        company_name="Konzern SE",
        industry="manufacturing",
        employee_count=1500,
        annual_revenue_eur=200_000_000,
        balance_sheet_total_eur=80_000_000,
        processes_personal_data=True,
        processes_special_category_data=False,
        processing_is_occasional=False,
        is_listed_company=True,
        has_supply_chain_abroad=True,
        supply_chain_countries=["CN"],
        annual_energy_consumption_mwh=12_000,
    )


@pytest.fixture
def profile_freelancer():
    """Profile 4: Solo freelancer — 1 employee, minimal obligations."""
    return CompanyProfile(
        company_name="Max Mustermann Consulting",
        industry="consulting",
        employee_count=1,
        annual_revenue_eur=80_000,
        processes_personal_data=True,
        processing_is_occasional=True,
    )


@pytest.fixture
def profile_healthcare():
    """Profile 5: Healthcare company — 50 employees, special category data."""
    return CompanyProfile(
        company_name="MediCare Praxis GmbH",
        industry="healthcare",
        employee_count=50,
        annual_revenue_eur=3_000_000,
        processes_personal_data=True,
        processes_special_category_data=True,
        processing_is_occasional=False,
    )
