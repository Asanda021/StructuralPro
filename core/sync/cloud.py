"""Optional HTTP sync adapter; never used by offline core."""
from __future__ import annotations
import json,urllib.request
class HTTPJSONSyncProvider:
    def __init__(self,base_url,token=None):
        self.base_url=base_url.rstrip("/"); self.token=token
    def _request(self,method,path,payload=None):
        data=None if payload is None else json.dumps(payload,ensure_ascii=False).encode()
        req=urllib.request.Request(self.base_url+path,data=data,method=method,headers={"Content-Type":"application/json",**({"Authorization":"Bearer "+self.token} if self.token else {})})
        with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read().decode())
    def push(self,records): return self._request("POST","/sync/push",records)
    def pull(self,project_id): return self._request("GET","/sync/pull/"+str(project_id))
