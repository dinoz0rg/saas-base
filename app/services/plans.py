"""Static subscription plan catalog.

Kept in code (not DB) so forks of this SaaS base can tweak pricing/features
in one place. The `slug` is what gets stored on `User.subscription_tier`
and `Subscription.plan`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    slug: str
    name: str
    tagline: str
    price_monthly: int   # USD whole dollars
    price_yearly: int    # USD whole dollars (per year)
    features: tuple[str, ...]
    is_free: bool = False
    is_popular: bool = False


PLANS: tuple[Plan, ...] = (
    Plan(
        slug="free",
        name="Free",
        tagline="Kick the tires.",
        price_monthly=0,
        price_yearly=0,
        is_free=True,
        features=(
            "1 account",
            "Basic analytics",
            "Community support",
        ),
    ),
    Plan(
        slug="pro",
        name="Pro",
        tagline="For growing teams.",
        price_monthly=19,
        price_yearly=190,
        is_popular=True,
        features=(
            "Unlimited projects",
            "Advanced analytics",
            "Priority email support",
            "API access",
        ),
    ),
    Plan(
        slug="business",
        name="Business",
        tagline="Scale with confidence.",
        price_monthly=99,
        price_yearly=990,
        features=(
            "Everything in Pro",
            "SSO + SCIM",
            "Dedicated support",
            "Custom contracts",
        ),
    ),
)

PLAN_SLUGS = {p.slug for p in PLANS}


def get_plan(slug: str) -> Plan | None:
    return next((p for p in PLANS if p.slug == slug), None)


def plan_price(slug: str, interval: str) -> int:
    """Return price in whole USD for a plan/interval, or 0 if unknown."""
    p = get_plan(slug)
    if not p:
        return 0
    return p.price_yearly if interval == "yearly" else p.price_monthly
