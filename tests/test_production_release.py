from core.platform.production_release_v1 import evaluate_production_release,require_production_release
VALID={"version":"0.1.0","commit":"a"*40,"release_preparation_fingerprint":"b"*64,"artifact_manifest":{"package.zip":"c"*64},"rollback_commit":"d"*40}
def test_valid_release_is_deterministic():
 a=evaluate_production_release(VALID); b=evaluate_production_release(dict(reversed(list(VALID.items()))))
 assert a.released and not a.blockers and a.fingerprint==b.fingerprint
def test_missing_field_blocks():
 r=evaluate_production_release({**VALID,"rollback_commit":""}); assert not r.released
def test_unknown_field_blocks():
 r=evaluate_production_release({**VALID,"extra":True}); assert not r.released
def test_bad_artifact_digest_blocks():
 r=evaluate_production_release({**VALID,"artifact_manifest":{"package.zip":"bad"}}); assert not r.released
def test_fingerprint_changes():
 assert evaluate_production_release(VALID).fingerprint != evaluate_production_release({**VALID,"version":"0.1.1"}).fingerprint
def test_require_raises():
 try: require_production_release({**VALID,"commit":""})
 except ValueError: pass
 else: raise AssertionError("expected ValueError")
