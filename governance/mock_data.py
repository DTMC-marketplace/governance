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


def get_compliance_projects():
    """Get mock compliance projects (Active Projects list)."""
    data = load_mock_data('compliance_projects.json')
    if not data or not isinstance(data, list):
        return []
    return data


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
