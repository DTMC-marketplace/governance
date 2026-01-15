"""
Context processors for Governance project
"""
def csrf_token(request):
    """Provide csrf_token for templates (returns empty string since no CSRF in demo)"""
    return {'csrf_token': ''}
