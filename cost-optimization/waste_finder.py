"""Detecta recursos que generan gasto innecesario o incumplen el tagging.

La logica de decision es pura (testeable sin AWS); boto3 solo alimenta los datos.
"""
from __future__ import annotations

from dataclasses import dataclass

REQUIRED_TAGS = {"Environment", "Owner", "DataClassification"}


@dataclass(frozen=True)
class Volume:
    volume_id: str
    state: str
    size_gb: int
    tags: frozenset[str]


def orphan_volumes(volumes: list[Volume]) -> list[Volume]:
    return [v for v in volumes if v.state == "available"]


def untagged(volumes: list[Volume]) -> list[tuple[str, set[str]]]:
    return [(v.volume_id, REQUIRED_TAGS - set(v.tags)) for v in volumes if REQUIRED_TAGS - set(v.tags)]


def estimated_monthly_waste_usd(volumes: list[Volume], price_gb: float = 0.08) -> float:
    return round(sum(v.size_gb for v in orphan_volumes(volumes)) * price_gb, 2)


def load_volumes(region: str = "us-east-1") -> list[Volume]:
    import boto3

    ec2 = boto3.client("ec2", region_name=region)
    result: list[Volume] = []
    for page in ec2.get_paginator("describe_volumes").paginate():
        for v in page["Volumes"]:
            result.append(Volume(v["VolumeId"], v["State"], v["Size"],
                                 frozenset(t["Key"] for t in v.get("Tags", []))))
    return result


if __name__ == "__main__":
    vols = load_volumes()
    print(f"Volumenes huerfanos: {[v.volume_id for v in orphan_volumes(vols)]}")
    print(f"Desperdicio estimado: USD {estimated_monthly_waste_usd(vols)}/mes")
    print(f"Sin tags obligatorios: {untagged(vols)}")
