"""
Mock Data Loader for Governance Hackathon Standalone Project
Loads data from JSON files instead of database
"""
import json
from pathlib import Path

MOCK_DATA_DIR = Path(__file__).parent.parent / 'mock_data'


def load_mock_data(filename):
    """Load JSON mock data"""
    filepath = MOCK_DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def get_mock_agents():
    """Get mock AI agents"""
    return load_mock_data('agents.json')


def get_mock_use_cases():
    """Get mock AI use cases"""
    return load_mock_data('use_cases.json')


def get_mock_models():
    """Get mock AI models"""
    return load_mock_data('models.json')


def get_mock_datasets():
    """Get mock AI datasets"""
    return load_mock_data('datasets.json')


def get_mock_evidences():
    """Get mock evidences"""
    return load_mock_data('evidences.json')


def get_mock_evaluation_reports():
    """Get mock evaluation reports"""
    return load_mock_data('evaluation_reports.json')


def get_mock_review_comments():
    """Get mock review comments"""
    return load_mock_data('review_comments.json')


def get_compliance_projects(archived=False):
    """Get mock compliance projects (Active or Archived)."""
    projects = load_mock_data('compliance_projects.json')
    details = load_mock_data('compliance_details.json')
    
    if not projects or not isinstance(projects, list):
        return []

    filtered_projects = []

    # Merge dynamic stats from compliance_details into the list view
    if details:
        for p in projects:
            is_archived = p.get('archived', False)
            if archived and not is_archived:
                continue
            if not archived and is_archived:
                continue
                
            pid = str(p.get('id'))
            if pid in details:
                detail = details[pid]
                
                # Dynamic Progress
                progress = detail.get('overall_progress', 0)
                p['progress'] = progress
                p['progress_label'] = f"{progress}% Complete"
                
                # Dynamic Blockers
                stats = detail.get('stats', {})
                blocked = stats.get('blocked', 0)
                
                if blocked > 0:
                    p['blockers_label'] = f"{blocked} item{'s' if blocked != 1 else ''} blocked"
                    p['blockers_class'] = "text-[#B42318]"
                else:
                    p['blockers_label'] = "No blockers"
                    p['blockers_class'] = "text-[#6B7280]"
            else:
                 # Default if no details found
                p['progress'] = 0
                p['progress_label'] = "0% Complete"
                p['blockers_label'] = "No blockers"
                p['blockers_class'] = "text-[#6B7280]"
                
            filtered_projects.append(p)
    
    return filtered_projects

# ... existing code ...

def restore_compliance_projects(project_ids):
    """
    Restore a list of compliance projects (un-archive).
    Sets 'archived' = False in compliance_projects.json
    """
    filepath = MOCK_DATA_DIR / 'compliance_projects.json'
    if not filepath.exists():
        return False
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            projects = json.load(f)
            
        updated = False
        ids_str = set(map(str, project_ids))
        
        for p in projects:
            if str(p.get('id')) in ids_str:
                p['archived'] = False
                updated = True
                
        if updated:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(projects, f, indent=4)
            return True
        return False
        
    except Exception as e:
        print(f"Error restoring projects: {e}")
        return False


def get_compliance_detail(project_id):
    """Get mock compliance project detail for a specific ID."""
    data = load_mock_data('compliance_details.json')
    if not data or not isinstance(data, dict):
        return None
    return data.get(str(project_id))


def update_compliance_task_status(project_id, task_id, new_status):
    """Update task status in compliance_details.json"""
    filepath = MOCK_DATA_DIR / 'compliance_details.json'
    if not filepath.exists():
        return False
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        project = data.get(str(project_id))
        if not project:
            return False
            
        tasks = project.get('tasks', [])
        updated = False
        
        # Mapping status to CSS classes for consistency with frontend
        status_classes = {
            'Done': 'bg-[#ECFDF3] text-[#027A48]',
            'In Progress': 'bg-[#EFF8FF] text-[#175CD3]',
            'Blocked': 'bg-[#FEE4E2] text-[#B42318]',
            'To-Do': 'bg-[#F2F4F7] text-[#344054]'
        }
        
        for task in tasks:
            if str(task.get('id', '')) == str(task_id):
                task['status'] = new_status
                task['status_class'] = status_classes.get(new_status, '')
                updated = True
                break
        
        if updated:
            # Recalculate stats
            stats = project.get('stats', {})
            # Reset counts
            stats = {
                "todo": 0,
                "in_progress": 0,
                "blocked": 0,
                "done": 0
            }
            
            for task in tasks:
                s = task.get('status')
                if s == 'Done': stats['done'] += 1
                elif s == 'In Progress': stats['in_progress'] += 1
                elif s == 'Blocked': stats['blocked'] += 1
                else: stats['todo'] += 1
            
            project['stats'] = stats
            
            # Recalculate progress
            total = len(tasks)
            if total > 0:
                # Weighted progress? Or just simple % of tasks done?
                # Using simple Done count for now or maintain existing logic if specific
                # existing logic seems to come from file, let's just do (done / total) * 100
                project['overall_progress'] = int((stats['done'] / total) * 100)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
            return True
            
    except Exception as e:
        print(f"Error updating mock data: {e}")
        return False
    
    return False


def get_compliance_task_notes(project_id, task_id):
    """Get notes for a specific task"""
    data = get_compliance_detail(project_id)
    if not data:
        return []
    
    tasks = data.get('tasks', [])
    for task in tasks:
        if str(task.get('id')) == str(task_id):
            notes = task.get('notes', [])
            # If no notes exist, add some dummy ones for demo if it match the image
            if not notes and str(task_id) == '1': 
                 notes = [
                    {
                        "id": 1,
                        "content": "Completed initial review of data governance requirements",
                        "author": "Sarah Chen",
                        "timestamp": "2 days ago"
                    },
                    {
                        "id": 2,
                        "content": "All checklist items verified and approved",
                        "author": "Michael Torres",
                        "timestamp": "1 day ago"
                    }
                ]
                 # Save these initial dummy notes back to file so they persist? 
                 # Or just return them dynamically. Let's return dynamically for simplicity unless saved.
            return notes
    return []


def add_compliance_task_note(project_id, task_id, content, author="Current User"):
    """Add a note to a specific task"""
    filepath = MOCK_DATA_DIR / 'compliance_details.json'
    if not filepath.exists():
        return None
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        project = data.get(str(project_id))
        if not project:
            return None
            
        tasks = project.get('tasks', [])
        # Find task
        target_task = None
        for task in tasks:
            if str(task.get('id')) == str(task_id):
                target_task = task
                break
        
        if not target_task:
            return None
            
        if 'notes' not in target_task:
            target_task['notes'] = []
            
            # If it's task 1, prepopulate with the dummy ones if they weren't saved yet
            if str(task_id) == '1':
                 target_task['notes'] = [
                    {
                        "id": 1,
                        "content": "Completed initial review of data governance requirements",
                        "author": "Sarah Chen",
                        "timestamp": "2 days ago"
                    },
                    {
                        "id": 2,
                        "content": "All checklist items verified and approved",
                        "author": "Michael Torres",
                        "timestamp": "1 day ago"
                    }
                ]
        
        from datetime import datetime
        new_note = {
            "id": len(target_task['notes']) + 1,
            "content": content,
            "author": author,
            "timestamp": "Just now" # in real app use datetime.now().isoformat()
        }
        
        target_task['notes'].append(new_note)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return new_note
            
    except Exception as e:
        print(f"Error adding note: {e}")
        return None
    except Exception as e:
        print(f"Error adding note: {e}")
        return None

def get_compliance_assignees(project_id):
    """Get unique list of assignees for a project, plus some defaults"""
    data = get_compliance_detail(project_id)
    if not data:
        return []
        
    tasks = data.get('tasks', [])
    
    # Start with default consistent list or extract from tasks
    # The requirement says "All available/existing Assignees"
    # We can extract unique ones and maybe some hardcoded defaults
    
    assignees_map = {}
    
    # 1. Add some defaults if not present
    defaults = [
        {"name": "Sarah Chen", "initials": "SC", "class": "bg-[#F79009] text-white"},
        {"name": "Michael Torres", "initials": "MT", "class": "bg-[#F04438] text-white"},
        {"name": "Emma Wilson", "initials": "EW", "class": "bg-[#F04438] text-white"},
        {"name": "James Park", "initials": "JP", "class": "bg-[#667085] text-white"}
    ]
    
    for d in defaults:
        assignees_map[d['name']] = d
        
    # 2. Add from tasks
    for task in tasks:
        name = task.get('assignee')
        if name and name != "Not assigned yet" and name not in assignees_map:
            assignees_map[name] = {
                 "name": name,
                 "initials": task.get('assignee_initials', name[:2].upper()),
                 "class": task.get('assignee_class', "bg-gray-500 text-white")
            }

    # 3. Add any newly created assignees saved in the project metadata (if we were persisting new ones globally)
    # For now, let's look for a 'custom_assignees' key in the project root
    custom_assignees = data.get('custom_assignees', [])
    for c in custom_assignees:
        if c['name'] not in assignees_map:
             assignees_map[c['name']] = c
             
    return list(assignees_map.values())

def update_compliance_task_assignee(project_id, task_id, assignee_name):
    """Update assignee for a task"""
    filepath = MOCK_DATA_DIR / 'compliance_details.json'
    if not filepath.exists():
        return False
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        project = data.get(str(project_id))
        if not project:
            return False
            
        tasks = project.get('tasks', [])
        
        # Get assignee details from our "database" (the get_compliance_assignees logic simulated)
        # Or look it up from defaults/customs list in the file
        
        # Helper to find assignee props
        assignee_props = None
        
        # Check defaults first
        defaults = [
            {"name": "Sarah Chen", "initials": "SC", "class": "bg-[#F79009] text-white"},
            {"name": "Michael Torres", "initials": "MT", "class": "bg-[#F04438] text-white"},
            {"name": "Emma Wilson", "initials": "EW", "class": "bg-[#F04438] text-white"},
            {"name": "James Park", "initials": "JP", "class": "bg-[#667085] text-white"}
        ]
        for d in defaults:
            if d['name'] == assignee_name:
                assignee_props = d
                break
        
        # Check custom assignees
        if not assignee_props:
             custom_assignees = project.get('custom_assignees', [])
             for c in custom_assignees:
                 if c['name'] == assignee_name:
                     assignee_props = c
                     break
        
        # If still not found (maybe existing task assignee), try to find in other tasks
        if not assignee_props:
             for t in tasks:
                 if t.get('assignee') == assignee_name:
                     assignee_props = {
                         "name": assignee_name,
                         "initials": t.get('assignee_initials'),
                         "class": t.get('assignee_class')
                     }
                     break
        
        # Default fallback if somehow updated to unknown
        if not assignee_props:
             assignee_props = {
                 "name": assignee_name,
                 "initials": assignee_name[:2].upper(),
                 "class": "bg-gray-500 text-white"
             }

        updated = False
        for task in tasks:
            if str(task.get('id')) == str(task_id):
                task['assignee'] = assignee_props['name']
                task['assignee_initials'] = assignee_props['initials']
                task['assignee_class'] = assignee_props['class']
                updated = True
                break
        
        if updated:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
            
    except Exception as e:
        print(f"Error updating assignee: {e}")
        return False
    
    return False

def add_new_assignee_to_project(project_id, name, email):
    """Add a new custom assignee to the project list"""
    filepath = MOCK_DATA_DIR / 'compliance_details.json'
    if not filepath.exists():
        return None
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        project = data.get(str(project_id))
        if not project:
            return None
            
        if 'custom_assignees' not in project:
            project['custom_assignees'] = []
            
        # Create new assignee object
        initials = "".join([n[0] for n in name.split()[:2]]).upper()
        # Randomize color or strict default? let's pick a nice one
        new_assignee = {
            "name": name,
            "email": email,
            "initials": initials,
            "class": "bg-[#7F56D9] text-white" # Purple for new ones
        }
        
        project['custom_assignees'].append(new_assignee)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return new_assignee
            
    except Exception as e:
        print(f"Error adding assignee: {e}")
        return None



def create_compliance_project(name, ai_systems):
    """
    Create a new compliance project.
    ai_systems: list of dicts {id, name, risk_classification, ...}
    """
    projects_filepath = MOCK_DATA_DIR / 'compliance_projects.json'
    details_filepath = MOCK_DATA_DIR / 'compliance_details.json'
    
    if not projects_filepath.exists() or not details_filepath.exists():
        return None
        
    try:
        # Load existing
        with open(projects_filepath, 'r', encoding='utf-8') as f:
            projects = json.load(f)
        with open(details_filepath, 'r', encoding='utf-8') as f:
            details = json.load(f)
            
        # Generate ID
        new_id = 1
        if projects:
            new_id = max(p.get('id', 0) for p in projects) + 1
            
        # Determine properties
        system_names = [s.get('name') for s in ai_systems]
        source_system_str = ", ".join(system_names)
        
        main_risk = "Minimal" # Default
        if ai_systems:
            # Pick the highest risk? Or just the first?
            main_risk = ai_systems[0].get('risk_classification', 'Minimal')
            # Normalize
            main_risk = main_risk.replace('_', ' ').title()
            
        if not name:
             name = f"{system_names[0]} Project" if system_names else "Compliance Project"

        # Risk Class map
        risk_class_map = {
            "Prohibited": "bg-[#FEF6EE] text-[#B93815]", 
            "High-Risk": "bg-[#FEE4E2] text-[#B42318]",
            "High Risk": "bg-[#FEE4E2] text-[#B42318]",
            "Limited Transparency": "bg-[#FEF0C7] text-[#B54708]",
            "Minimal": "bg-[#ECFDF3] text-[#027A48]"
        }
        
        risk_label = main_risk
        if risk_label.lower() == "high risk": risk_label = "High-Risk"
        if risk_label.lower() == "limited transparency": risk_label = "Limited transparency"
        
        r_class = risk_class_map.get(risk_label, "bg-[#F3F4F6] text-[#374151]")
        if "high" in risk_label.lower(): r_class = risk_class_map["High-Risk"]
        elif "limited" in risk_label.lower(): r_class = risk_class_map["Limited Transparency"]
        elif "minimal" in risk_label.lower(): r_class = risk_class_map["Minimal"]

        from datetime import datetime
        date_str = datetime.now().strftime("Updated %b %d")

        # 1. Add to projects list (compliance_projects.json)
        new_project_summary = {
            "id": new_id,
            "name": name,
            "updated": date_str,
            "source_system": source_system_str,
            "risk_label": risk_label,
            "risk_class": r_class
        }
        projects.append(new_project_summary)
        
        # 2. Add to details (compliance_details.json)
        default_tasks = [
             {
                "id": 1,
                "name": "Initial Risk Assessment",
                "category": "Risk",
                "category_class": "bg-[#FEF6EE] text-[#B93815]",
                "status": "To-Do",
                "status_class": "bg-[#F2F4F7] text-[#344054]",
                "linked_articles": ["Art. 9"],
                "evidence": "Missing",
                "evidence_status": "Missing",
                "evidence_class": "text-[#D92D20]",
                "assignee": "Not assigned yet",
                "assignee_initials": None,
                "assignee_class": "bg-[#F2F4F7] text-[#475467]"
            },
            {
                "id": 2,
                "name": "Data Governance Setup",
                "category": "Data",
                "category_class": "bg-[#EFF8FF] text-[#175CD3]",
                "status": "To-Do",
                "status_class": "bg-[#F2F4F7] text-[#344054]",
                "linked_articles": ["Art. 10"],
                "evidence": "Missing",
                "evidence_status": "Missing",
                "evidence_class": "text-[#D92D20]",
                "assignee": "Not assigned yet",
                "assignee_initials": None,
                "assignee_class": "bg-[#F2F4F7] text-[#475467]"
            }
        ]
        
        new_detail = {
            "id": new_id,
            "name": name,
            "ai_system": source_system_str,
            "role": "Deployer", 
            "regulatory_profile": [risk_label],
            "overall_progress": 0,
            "stats": {
                "todo": 2,
                "in_progress": 0,
                "blocked": 0,
                "done": 0
            },
            "tasks": default_tasks,
            "custom_assignees": []
        }
        details[str(new_id)] = new_detail
        
        # Save both
        with open(projects_filepath, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=4)
        with open(details_filepath, 'w', encoding='utf-8') as f:
            json.dump(details, f, indent=4)
            
        return new_project_summary
        
    except Exception as e:
        print(f"Error creating project: {e}")
        return None


        return new_project_summary
        
    except Exception as e:
        print(f"Error creating project: {e}")
        return None


def archive_compliance_projects(project_ids):
    """
    Archive a list of compliance projects.
    Sets 'archived' = True in compliance_projects.json
    """
    filepath = MOCK_DATA_DIR / 'compliance_projects.json'
    if not filepath.exists():
        return False
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            projects = json.load(f)
            
        updated = False
        ids_str = set(map(str, project_ids))
        
        for p in projects:
            if str(p.get('id')) in ids_str:
                p['archived'] = True
                updated = True
                
        if updated:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(projects, f, indent=4)
            return True
        return False
        
    except Exception as e:
        print(f"Error archiving projects: {e}")
        return False


def delete_compliance_projects(project_ids):
    """
    Delete a list of compliance projects.
    Removes from compliance_projects.json and compliance_details.json
    """
    projects_filepath = MOCK_DATA_DIR / 'compliance_projects.json'
    details_filepath = MOCK_DATA_DIR / 'compliance_details.json'
    
    if not projects_filepath.exists():
        return False
        
    try:
        # 1. Update Projects List
        with open(projects_filepath, 'r', encoding='utf-8') as f:
            projects = json.load(f)
            
        initial_len = len(projects)
        ids_set = set(map(str, project_ids))
        
        # Filter out deleted projects
        projects = [p for p in projects if str(p.get('id')) not in ids_set]
        
        if len(projects) == initial_len:
             # No changes
             return False
             
        with open(projects_filepath, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=4)
            
        # 2. Update Details (Remove keys)
        if details_filepath.exists():
            with open(details_filepath, 'r', encoding='utf-8') as f:
                details = json.load(f)
            
            # Remove keys
            keys_to_remove = [k for k in details.keys() if k in ids_set]
            if keys_to_remove:
                for k in keys_to_remove:
                    del details[k]
                
                with open(details_filepath, 'w', encoding='utf-8') as f:
                    json.dump(details, f, indent=4)
                    
        return True
        
    except Exception as e:
        print(f"Error deleting projects: {e}")
        return False


# Helper class to simulate Django model objects
class MockObject:
    """Simple mock object that behaves like a Django model"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __getattr__(self, name):
        # Return None for any missing attributes
        return None


def create_mock_agent(data):
    """Create a mock agent object from dict"""
    return MockObject(
        id=data.get('id'),
        name=data.get('name', ''),
        business_unit=data.get('business_unit', ''),
        compliance_status=data.get('compliance_status', 'assessing'),
        ai_act_role=data.get('ai_act_role', 'deployer'),
        vendor=data.get('vendor', ''),
        risk_classification=data.get('risk_classification', 'limited_risks'),
        investment_type=data.get('investment_type', ''),
        use_cases=[],  # Will be populated separately
    )


def create_mock_use_case(data):
    """Create a mock use case object from dict"""
    return MockObject(
        id=data.get('id'),
        name=data.get('name', ''),
        display_name=data.get('display_name', ''),
        overview=data.get('overview', ''),
        risk_type=data.get('risk_type', ''),
        review_status=data.get('review_status', 'missing'),
        compliance_assessed=data.get('compliance_assessed', False),
        agent_id=data.get('agent_id'),
        models=data.get('models', []),
        datasets=data.get('datasets', []),
    )


def calculate_compliance_mock(use_case):
    """Calculate compliance for a mock use case"""
    # Simple mock compliance calculation
    # For demo, assume partial compliance if assessed
    if use_case.compliance_assessed:
        # Randomize compliance status for demo
        status = 'partial'  # Most use cases are partially compliant in demo
        gdpr = True
        eu_ai_act = True
        data_act = True
    else:
        status = 'not_started'
        gdpr = False
        eu_ai_act = False
        data_act = False
    
    return {
        'status': status,
        'gdpr': gdpr,
        'eu_ai_act': eu_ai_act,
        'data_act': data_act,
        'models_count': len(use_case.models) if hasattr(use_case, 'models') else 0,
        'datasets_count': len(use_case.datasets) if hasattr(use_case, 'datasets') else 0,
    }


def calculate_risks_mock(use_case):
    """Calculate risks for a mock use case"""
    # Simple mock risk calculation
    if use_case.risk_type:
        return [use_case.risk_type]
    return ['limited_risks']


def convert_evidences_to_objects(evidences_data, use_cases_list):
    """Convert evidence dicts to objects with use_case attribute"""
    evidences = []
    for e_data in evidences_data:
        evidence = MockObject(**e_data)
        # Find use_case for this evidence
        use_case_id = e_data.get('use_case_id')
        if use_case_id:
            use_case = next((uc['use_case'] for uc in use_cases_list if uc['use_case'].id == use_case_id), None)
            if not use_case:
                use_case = MockObject(id=use_case_id, name="Unknown Use Case")
            evidence.use_case = use_case
        else:
            evidence.use_case = MockObject(id=None, name="No Use Case")
        evidences.append(evidence)
    return evidences


def convert_reports_to_objects(reports_data, use_cases_list):
    """Convert evaluation report dicts to objects with use_case attribute"""
    reports = []
    for r_data in reports_data:
        report = MockObject(**r_data)
        # Find use_case for this report
        use_case_id = r_data.get('use_case_id')
        if use_case_id:
            use_case = next((uc['use_case'] for uc in use_cases_list if uc['use_case'].id == use_case_id), None)
            if not use_case:
                use_case = MockObject(id=use_case_id, name="Unknown Use Case")
            report.use_case = use_case
        else:
            report.use_case = MockObject(id=None, name="No Use Case")
        reports.append(report)
    return reports


def convert_comments_to_objects(comments_data, use_cases_list=None):
    """Convert review comment dicts to objects with author and use_case attributes"""
    from datetime import datetime, timedelta
    
    if use_cases_list is None:
        use_cases_list = []
    
    comments = []
    for c_data in comments_data:
        comment = MockObject(**c_data)
        # Create author object
        author_username = c_data.get('author', 'demo_user')
        comment.author = MockObject(username=author_username, id=c_data.get('author_id', 1))
        
        # Find use_case for this comment
        use_case_id = c_data.get('use_case_id')
        if use_case_id:
            use_case = next((uc['use_case'] for uc in use_cases_list if uc['use_case'].id == use_case_id), None)
            if not use_case:
                use_case = MockObject(id=use_case_id, name="Unknown Use Case")
            comment.use_case = use_case
        else:
            comment.use_case = MockObject(id=None, name="No Use Case")
        
        # Handle created_at - convert string to datetime if needed
        created_at = c_data.get('created_at')
        if isinstance(created_at, str):
            try:
                # Try ISO format first
                comment.created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                try:
                    # Try common format
                    comment.created_at = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S%z')
                except:
                    # Fallback to datetime.now() if parsing fails
                    comment.created_at = datetime.now() - timedelta(days=1)
        elif not hasattr(comment, 'created_at') or comment.created_at is None:
            comment.created_at = datetime.now() - timedelta(days=1)
        
        # Add replies if any
        replies_data = c_data.get('replies', [])
        if replies_data:
            class RepliesList:
                def __init__(self, replies_data):
                    self._replies = []
                    for r in replies_data:
                        reply = MockObject(**r)
                        reply.author = MockObject(username=r.get('author', 'demo_user'), id=r.get('author_id', 1))
                        # Handle created_at for replies
                        reply_created_at = r.get('created_at')
                        if isinstance(reply_created_at, str):
                            try:
                                reply.created_at = datetime.fromisoformat(reply_created_at.replace('Z', '+00:00'))
                            except:
                                try:
                                    reply.created_at = datetime.strptime(reply_created_at, '%Y-%m-%dT%H:%M:%S%z')
                                except:
                                    reply.created_at = datetime.now() - timedelta(hours=12)
                        elif not hasattr(reply, 'created_at') or reply.created_at is None:
                            reply.created_at = datetime.now() - timedelta(hours=12)
                        self._replies.append(reply)
                def all(self):
                    return self._replies
            comment.replies = RepliesList(replies_data)
        else:
            class EmptyReplies:
                def all(self):
                    return []
            comment.replies = EmptyReplies()
        comments.append(comment)
    return comments
