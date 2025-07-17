from datetime import datetime
from typing import Optional
from services.github_api import GitHubAPIService
from setup.config import ISSUES_PER_PAGE, MAX_ISSUE_PAGES

class IssueService(GitHubAPIService):
    """Service responsible for analyzing issues"""
    
    def get_avg_issue_close_time(self, repo_full_name: str) -> Optional[float]:
        """Calculates the average issue closing time in days"""
        url = f"{self.base_url}/repos/{repo_full_name}/issues"
        params = {
            'state': 'closed',
            'per_page': ISSUES_PER_PAGE
        }
        
        total_seconds = 0
        count = 0
        
        # Analyze up to MAX_ISSUE_PAGES pages
        for _ in range(MAX_ISSUE_PAGES):
            data = self.get_json_response(url, params)
            if not data:
                break
            
            # Process each issue
            for issue in data:
                # Ignore Pull Requests, as they are also listed as issues
                if 'pull_request' in issue:
                    continue
                
                # Calculate duration if it has a closing date
                if issue.get('created_at') and issue.get('closed_at'):
                    try:
                        created = datetime.fromisoformat(issue['created_at'].rstrip('Z'))
                        closed = datetime.fromisoformat(issue['closed_at'].rstrip('Z'))
                        duration = (closed - created).total_seconds()
                        total_seconds += duration
                        count += 1
                    except Exception as e:
                        print(f"Error processing dates: {str(e)}")
                        continue
            
            # Check for the next page
            response = self.make_request(url, params)
            if response and 'next' in response.links:
                url = response.links['next']['url']
                params = None  # URL already contains the parameters
            else:
                break
        
        if count == 0:
            return None
        
        # Calculate average in days
        avg_seconds = total_seconds / count
        return avg_seconds / (24 * 3600)