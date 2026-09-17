"""Central academic, attendance, and fee calculation rules."""

GRADE_SCALE = ((90, "A+", 10), (80, "A", 9), (70, "B+", 8), (60, "B", 7),
               (50, "C", 6), (40, "D", 5), (0, "F", 0))


def grade_for(total: float) -> tuple[str, int]:
    """Return the grade label and grade point for a score out of 100."""
    for minimum, grade, point in GRADE_SCALE:
        if total >= minimum:
            return grade, point
    return "F", 0


def calculate_gpa(records: list) -> float:
    """Calculate credit-weighted GPA from rows containing grade and credits."""
    credits = sum(float(row["credits"]) for row in records)
    if not credits:
        return 0.0
    points = {grade: point for _, grade, point in GRADE_SCALE}
    return round(sum(points.get(row["grade"], 0) * float(row["credits"])
                     for row in records) / credits, 2)


def attendance_percentage(attended: int, total: int) -> float:
    """Return attendance percentage, handling a newly created zero-class record."""
    return round((attended / total) * 100, 2) if total else 0.0


def fee_details(total: float, paid: float) -> tuple[float, str]:
    """Return pending balance and payment status."""
    pending = round(total - paid, 2)
    status = "PAID" if pending == 0 else "PARTIALLY PAID" if paid else "PENDING"
    return pending, status
