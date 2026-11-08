from cryptography.fernet import Fernet
from scripts.secure_backup import encode_payload,decode_payload,isolated_integrity_test

def test_encrypt_decrypt_and_isolated_integrity():
    key=Fernet.generate_key().decode()
    data={'created_at':'2026-01-01','schema':'test','tables':{'members':[{'id':'a'}],'tickets':[{'id':'1'}]}}
    blob=encode_payload(data,key)
    assert b'"id":"a"' not in blob
    recovered=decode_payload(blob,key)
    assert recovered==data
    assert isolated_integrity_test(recovered)=={'members':1,'tickets':1}
