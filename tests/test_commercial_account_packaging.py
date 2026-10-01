from core.commercial.contract import Contract,ContractItem
from core.account import make_account,device_identity,LocalAccountStore
from core.sync.local_snapshot import export_snapshot,import_snapshot

def test_commercial_rates_and_validation():
    c=Contract("C","T",[ContractItem("1","x","m3",2,10)],overhead_rate=.1,regional_rate=.05,tax_rate=.09,insurance_rate=.03)
    assert c.validate()==[] and c.commercial_total()==23

def test_account_store_and_snapshot(tmp_path):
    a=make_account("M",account_id="a1"); d=device_identity("desktop",seed="x")
    s=LocalAccountStore(tmp_path/"account.json"); s.save(a,d); aa,dd=s.load(); assert aa==a and dd==d
    p=tmp_path/"snapshot.json"; export_snapshot([{"id":"p1"}],p); assert import_snapshot(p)["projects"][0]["id"]=="p1"
