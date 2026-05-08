"""ROT-avdrag eligibility — pure function, no I/O."""

from __future__ import annotations

from svarsa.tools.schemas import CheckRotEligibilityResult

ROT_OK_WORK_TYPES: frozenset[str] = frozenset(
    {
        "vvs", "el", "snickeri", "kakel", "tak", "badrumsrenovering",
        "köksrenovering", "värmepump", "fönsterbyte", "isolering",
    }
)


def assess(
    *,
    is_private_person: bool,
    owns_property: bool,
    property_age_years: int,
    work_type: str,
) -> CheckRotEligibilityResult:
    work_norm = work_type.lower().strip()
    eligible = (
        is_private_person
        and owns_property
        and property_age_years >= 5
        and any(k in work_norm for k in ROT_OK_WORK_TYPES)
    )
    if eligible:
        return CheckRotEligibilityResult(
            eligible=True,
            max_deduction_sek_estimate=75_000,
            caveats_sv=(
                "Maxbelopp 75 000 kr/person/år. ROT gäller arbetskostnad, ej material. "
                "Kontrollera bostadsöversikt på Skatteverket innan slutligt avtal."
            ),
        )
    why: list[str] = []
    if not is_private_person:
        why.append("kräver privatperson")
    if not owns_property:
        why.append("kräver att kunden äger bostaden")
    if property_age_years < 5:
        why.append("bostaden måste vara minst 5 år")
    if not any(k in work_norm for k in ROT_OK_WORK_TYPES):
        why.append("arbetstypen är inte ROT-grundande")
    return CheckRotEligibilityResult(
        eligible=False,
        max_deduction_sek_estimate=0,
        caveats_sv="Inte berättigad: " + ", ".join(why) + ".",
    )
