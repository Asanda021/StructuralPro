"""Offline-first project persistence with SQLite, revisions and backups."""
from __future__ import annotations
import json, sqlite3, time
from pathlib import Path
from typing import Any

class ProjectStore:
    def __init__(self, path: str | Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path); self.db.row_factory=sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS projects(
            id TEXT PRIMARY KEY, name TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
            updated_at REAL NOT NULL, payload TEXT NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS revisions(
            project_id TEXT NOT NULL, version INTEGER NOT NULL, created_at REAL NOT NULL,
            payload TEXT NOT NULL, PRIMARY KEY(project_id,version))""")
        self.db.commit()

    def save(self, project_id: str, project: dict[str,Any]) -> dict[str,Any]:
        pid=str(project_id); now=time.time()
        row=self.db.execute("SELECT version FROM projects WHERE id=?",(pid,)).fetchone()
        version=int(row["version"])+1 if row else 1
        payload=json.dumps(project,ensure_ascii=False,sort_keys=True)
        self.db.execute("INSERT OR REPLACE INTO projects(id,name,version,updated_at,payload) VALUES(?,?,?,?,?)",
                        (pid,str(project.get("name","")),version,now,payload))
        self.db.execute("INSERT OR REPLACE INTO revisions(project_id,version,created_at,payload) VALUES(?,?,?,?)",
                        (pid,version,now,payload))
        self.db.commit()
        return {"id":pid,"version":version,"updated_at":now}

    def get(self, project_id: str) -> dict[str,Any] | None:
        row=self.db.execute("SELECT * FROM projects WHERE id=?",(str(project_id),)).fetchone()
        if not row: return None
        data=json.loads(row["payload"]); data["_meta"]={"id":row["id"],"version":row["version"],"updated_at":row["updated_at"]}
        return data

    def list(self) -> list[dict[str,Any]]:
        return [dict(r) for r in self.db.execute("SELECT id,name,version,updated_at FROM projects ORDER BY updated_at DESC")]

    def revisions(self, project_id: str) -> list[dict[str,Any]]:
        return [{"version":r["version"],"created_at":r["created_at"],"payload":json.loads(r["payload"])}
                for r in self.db.execute("SELECT version,created_at,payload FROM revisions WHERE project_id=? ORDER BY version",(str(project_id),))]

    def close(self): self.db.close()
