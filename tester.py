import requests
import json
import pdb

base_url = 'https://planner-backend-fz01.onrender.com'
headers = {'Content-Type': 'application/json'}

def create_period():
    url = f'{base_url}/period'
    data = {
        "start_date": "2025-02-03",
        "end_date": "2025-04-28", 
        "name": "Q1 2025"
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()

def create_project():
    url = f'{base_url}/project'
    data = {
        "name":"Attendance Analytics",
        "description":"Tracking Attendance",
        "period_id":"a94c0d7d-9ede-4171-a082-fe3032b0e934"
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()

def create_skill(skill_name):
    url = f'{base_url}/skill'
    data = {
        "name":skill_name
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def populate_skills():
    skills = ["Frontend","Backend","Firmware","Android","iOS"]
    for skill in skills:
        result = create_skill(skill)
        print(result)

def create_component(component_name,description,project_id,skill_id):
    url = f'{base_url}/component'
    data = {
        "name":component_name,
        "description":description,
        "project_id":project_id,
        "skill_id":skill_id
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def populate_components():
    components = [
        {
            "name":"Attendance Analytics Backend",
            "description":"Backend for the Attendance Analytics project",
            "project_id":"bd347508-c8a4-435c-afa8-64bb9e200e07",
            "skill_id":"1ef55107-4afc-413f-9f21-8e5b1a7d8bd7"
        }
    ]
    for component in components:
        result = create_component(component["name"],component["description"],component["project_id"],component["skill_id"])
        print(result)


def create_contributor(contributor_name,skill_ids):
    url = f'{base_url}/contributor'
    data = {
        "name":contributor_name,
        "skill_ids":skill_ids
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def populate_contributors():
    contributors = [
        {
            "name":"Austin Wahle",
            "skill_ids":["1ef55107-4afc-413f-9f21-8e5b1a7d8bd7"]
        }
    ]
    for contributor in contributors:
        result = create_contributor(contributor["name"],contributor["skill_ids"])
        print(result)

def create_assignment(component_id,contributor_id,week):
    url = f'{base_url}/assignment'
    data = {
        "component_id":component_id,
        "contributor_id":contributor_id,
        "week":week
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()

def populate_assignments():
    assignments = [
        {
            "component_id":"a9f475b2-8297-4fcf-82f2-d9cf07aedc67",
            "contributor_id":"3d0ed038-1cb0-4506-81e6-82efadc04ac5",
            "week":"2025-02-03"
        }
    ]
    for assignment in assignments:
        result = create_assignment(assignment["component_id"],assignment["contributor_id"],assignment["week"])
        print(result)

def get_assignments(contributor_id):
    url = f'{base_url}/assignments/contributor/{contributor_id}'
    response = requests.get(url)
    return response.json()


def get_skills():
    url = f'{base_url}/skills'
    response = requests.get(url)
    return response.json()

def get_projects(period_id):
    url = f'{base_url}/period/{period_id}/projects'
    response = requests.get(url)
    return response.json()

def get_contributors_by_skill(skill_id):
    url = f'{base_url}/contributors/get_contributors_by_skill/{skill_id}'
    response = requests.get(url)
    return response.json()

def delete_project(project_id):
    url = f'{base_url}/project/{project_id}'
    response = requests.delete(url)
    return response.json()

def get_contributor_chart(period_id):
    url = f'{base_url}/period/{period_id}/contributor_chart'
    response = requests.get(url)
    return response.json()

if __name__ == '__main__':
    try:
        result = create_period()
        print(json.dumps(result, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")