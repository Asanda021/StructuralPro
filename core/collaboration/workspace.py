"""Deterministic collaboration/CDE primitives with optimistic concurrency control."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import hashlib,json

def req(v,n):
 s=str(v or "").strip()
 if not s: raise ValueError(f"{n} is required")
 return s
@dataclass(frozen=True)
class Permission: name:str
@dataclass(frozen=True)
class Role:
 name:str; permissions:frozenset[str]=frozenset()
 def allows(self,p): return p in self.permissions
@dataclass(frozen=True)
class User:
 user_id:str; display_name:str; role:str
 def __post_init__(self): req(self.user_id,"user_id"); req(self.display_name,"display_name"); req(self.role,"role")
@dataclass(frozen=True)
class Assignment:
 assignment_id:str; user_id:str; object_id:str; status:str="assigned"
@dataclass(frozen=True)
class Comment:
 comment_id:str; user_id:str; object_id:str; text:str; parent_id:str=""
@dataclass(frozen=True)
class Review:
 review_id:str; object_id:str; reviewer_id:str; status:str="pending"; comment:str=""
@dataclass(frozen=True)
class Notification:
 notification_id:str; user_id:str; event:str; object_id:str; read:bool=False
@dataclass(frozen=True)
class Activity:
 activity_id:str; actor_id:str; action:str; object_id:str; version:int; details:dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class CollaborationObject:
 object_id:str; payload:dict[str,Any]; version:int=1
 def fingerprint(self): return hashlib.sha256(json.dumps(self.payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
class CollaborationWorkspace:
 def __init__(self): self.users={}; self.roles={}; self.objects={}; self.assignments=[]; self.comments=[]; self.reviews=[]; self.notifications=[]; self.activities=[]
 def add_role(self,role): self.roles[req(role.name,"role.name")]=role
 def add_user(self,user):
  if user.role not in self.roles: raise ValueError("unknown role")
  self.users[req(user.user_id,"user_id")]=user
 def create_object(self,object_id,payload):
  oid=req(object_id,"object_id")
  if oid in self.objects: raise ValueError("duplicate object_id")
  self.objects[oid]=CollaborationObject(oid,dict(payload),1); return self.objects[oid]
 def update_object(self,user_id,object_id,payload,expected_version):
  user=self.users.get(user_id); obj=self.objects.get(object_id)
  if not user or not obj: raise ValueError("unknown user or object")
  if not self.roles[user.role].allows("edit"): raise PermissionError("edit permission required")
  if obj.version!=expected_version: raise RuntimeError(f"version_conflict:{obj.version}")
  new=CollaborationObject(obj.object_id,dict(payload),obj.version+1); self.objects[object_id]=new
  self.activities.append(Activity(f"ACT-{len(self.activities)+1}",user_id,"update",object_id,new.version)); return new
 def assign(self,assignment):
  if assignment.user_id not in self.users: raise ValueError("unknown user")
  if assignment.object_id not in self.objects: raise ValueError("unknown object")
  self.assignments.append(assignment); return assignment
 def comment(self,comment):
  if comment.user_id not in self.users: raise ValueError("unknown user")
  if comment.object_id not in self.objects: raise ValueError("unknown object")
  self.comments.append(comment); return comment
 def review(self,review):
  if review.reviewer_id not in self.users: raise ValueError("unknown reviewer")
  if review.object_id not in self.objects: raise ValueError("unknown object")
  self.reviews.append(review); return review
 def notify(self,n): self.notifications.append(n); return n
 def snapshot(self): return {"users":len(self.users),"objects":len(self.objects),"assignments":len(self.assignments),"comments":len(self.comments),"reviews":len(self.reviews),"notifications":len(self.notifications),"activities":len(self.activities)}
