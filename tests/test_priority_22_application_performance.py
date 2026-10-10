"""Persistence and application integration tests for Priority 22."""
from core.projects.store import ProjectStore
from core.platform.application import StructuralProApp

def test_store_cache_returns_safe_copy_and_pagination(tmp_path):
    store=ProjectStore(tmp_path/"p.db")
    store.save("P22",{"id":"P22","name":"Demo","takeoffs":[{"id":1}]})
    a=store.get("P22"); a["takeoffs"].append({"id":2})
    assert len(store.get("P22")["takeoffs"])==1
    assert len(store.list(limit=1))==1
    assert store.get_many(["P22","missing"])[0]["id"]=="P22"
    store.close()

def test_application_performance_snapshot_and_bounded_page(tmp_path):
    app=StructuralProApp(tmp_path)
    app.create_project("Demo","P22")
    p=app.open_project("P22")
    p["takeoffs"]=[{"id":str(i)} for i in range(250)]
    app.store.save("P22",p)
    snap=app.project_performance_snapshot("P22")
    assert snap["collection_counts"]["takeoffs"]==250
    page=app.project_collection_page("P22","takeoffs",page=2,page_size=100)
    assert len(page["items"])==100 and page["items"][0]["id"]=="100"


def test_second_sqlite_connection_invalidates_stale_cached_project(tmp_path):
    database = tmp_path / "projects.db"
    first = ProjectStore(database)
    second = ProjectStore(database)
    first.save("P22", {"id": "P22", "name": "old", "boq": []})
    assert first.get("P22")["name"] == "old"  # fills the first cache
    latest = second.get("P22")
    latest["name"] = "updated elsewhere"
    second.save("P22", latest)
    assert first.get("P22")["name"] == "updated elsewhere"
    first.close()
    second.close()
