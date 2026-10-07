"""Adaptador de salida: boto3 -> dominio."""
from __future__ import annotations

import json

import boto3
from typing import Any

from botocore.exceptions import ClientError

from auditor.domain.model import BucketConfiguration


class Boto3BucketInspector:
    def __init__(self, s3_client: Any = None, kms_client: Any = None) -> None:
        self._s3 = s3_client or boto3.client("s3")
        self._kms = kms_client or boto3.client("kms")

    def list_buckets(self) -> list[str]:
        return [b["Name"] for b in self._s3.list_buckets().get("Buckets", [])]

    def inspect(self, bucket_name: str) -> BucketConfiguration:
        algorithm, key_id = self._encryption(bucket_name)
        return BucketConfiguration(
            name=bucket_name,
            public_access_blocked=self._public_access_blocked(bucket_name),
            encryption_algorithm=algorithm,
            kms_rotation_enabled=self._rotation(key_id) if key_id else None,
            versioning_enabled=self._s3.get_bucket_versioning(Bucket=bucket_name).get("Status") == "Enabled",
            access_logging_enabled="LoggingEnabled" in self._s3.get_bucket_logging(Bucket=bucket_name),
            tls_enforced=self._tls_enforced(bucket_name),
        )

    def _public_access_blocked(self, name: str) -> bool:
        try:
            cfg = self._s3.get_public_access_block(Bucket=name)["PublicAccessBlockConfiguration"]
            return all(cfg.values())
        except ClientError:
            return False

    def _encryption(self, name: str) -> tuple[str | None, str | None]:
        try:
            rules = self._s3.get_bucket_encryption(Bucket=name)["ServerSideEncryptionConfiguration"]["Rules"]
            default = rules[0]["ApplyServerSideEncryptionByDefault"]
            return default["SSEAlgorithm"], default.get("KMSMasterKeyID")
        except ClientError:
            return None, None

    def _rotation(self, key_id: str) -> bool | None:
        try:
            val = self._kms.get_key_rotation_status(KeyId=key_id)["KeyRotationEnabled"]
            return bool(val)
        except ClientError:
            return None

    def _tls_enforced(self, name: str) -> bool:
        try:
            policy = json.loads(self._s3.get_bucket_policy(Bucket=name)["Policy"])
        except ClientError:
            return False
        for st in policy.get("Statement", []):
            cond = st.get("Condition", {}).get("Bool", {})
            if st.get("Effect") == "Deny" and str(cond.get("aws:SecureTransport")).lower() == "false":
                return True
        return False
