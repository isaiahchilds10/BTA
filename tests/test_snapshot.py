from cryptography.fernet import Fernet, InvalidToken
import pytest
from scripts.secure_snapshot import seal_snapshot,inspect_snapshot


def test_encrypted_snapshot_checksum_and_key():
    key=Fernet.generate_key()
    snap={"tables":{"tickets":[{"id":"x"}]}}
    encrypted=seal_snapshot(snap,key)
    assert b'"tickets"' not in encrypted
    assert inspect_snapshot(encrypted,key)==snap
    with pytest.raises(InvalidToken): inspect_snapshot(encrypted,Fernet.generate_key())
