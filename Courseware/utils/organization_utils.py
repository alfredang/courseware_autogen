import json
import os
from typing import Optional
from pydantic import BaseModel

ORG_FILE = "Courseware/utils/organizations.json"

class Organization(BaseModel):
    name: str
    uen: str
    logo: Optional[str] = None

def load_organizations():
    if os.path.exists(ORG_FILE):
        with open(ORG_FILE, "r") as f:
            return json.load(f)
    return []

def save_organizations(org_list):
    with open(ORG_FILE, "w") as f:
        json.dump(org_list, f, indent=4)

def add_organization(org):
    org_list = load_organizations()
    org_list.append(org.dict())
    save_organizations(org_list)

def update_organization(index, org):
    org_list = load_organizations()
    org_list[index] = org.dict()
    save_organizations(org_list)

def delete_organization(index):
    org_list = load_organizations()
    org_list.pop(index)
    save_organizations(org_list)
