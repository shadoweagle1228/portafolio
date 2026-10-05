from waste_finder import Volume, estimated_monthly_waste_usd, orphan_volumes, untagged

ALL = frozenset({"Environment", "Owner", "DataClassification"})
VOLS = [
    Volume("vol-1", "in-use", 100, ALL),
    Volume("vol-2", "available", 500, frozenset({"Owner"})),
]


def test_orphans():
    assert [v.volume_id for v in orphan_volumes(VOLS)] == ["vol-2"]


def test_waste():
    assert estimated_monthly_waste_usd(VOLS) == 40.0


def test_untagged():
    assert untagged(VOLS) == [("vol-2", {"Environment", "DataClassification"})]
