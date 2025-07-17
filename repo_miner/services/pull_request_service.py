from typing import List, Optional, Dict, Any
from services.github_api import GitHubAPIService
from models.repository import PullRequestData, CommitData
from setup.config import MAX_PRS_PER_REPO

class PullRequestService(GitHubAPIService):
    """Service responsible for analyzing Pull Requests"""
    
    def get_pr_comparison_data(self, repo_full_name: str) -> List[PullRequestData]:
        """Gets comparison data for open PRs"""
        url = f"{self.base_url}/repos/{repo_full_name}/pulls"
        params = {'state': 'open', 'per_page': MAX_PRS_PER_REPO}
        
        try:
            prs = self.get_json_response(url, params)
            if not prs:
                return []
            
            prs_data = []
            
            # Process each PR
            for pr in prs:
                # 1. Get base branch and creation date
                base_branch = pr['base']['ref']
                pr_created_at = pr['created_at']
                
                # 2. Get PR author information
                author_info = pr.get('user', {})
                author_login = author_info.get('login', 'unknown')
                author_name = author_info.get('name') or author_login
                
                # 3. Get all commits from the PR
                pr_commits_data = self.get_json_response(pr['commits_url'])
                if not pr_commits_data:
                    continue
                
                # 4. Process PR commits
                commits = []
                author_email = None
                
                for commit_data in pr_commits_data:
                    commit_info = commit_data.get('commit', {})
                    commit_author = commit_info.get('author', {})
                    
                    commit = CommitData(
                        sha=commit_data.get('sha', ''),
                        message=commit_info.get('message', '').split('\n')[0],  # First line of the message
                        author_name=commit_author.get('name', ''),
                        author_email=commit_author.get('email'),
                        author_date=commit_author.get('date', '')
                    )
                    commits.append(commit)
                    
                    # Use email from the last commit if we don't have one from the profile
                    if not author_email and commit.author_email:
                        author_email = commit.author_email
                
                # 5. Last commit of the PR
                last_pr_commit = pr_commits_data[-1] if pr_commits_data else None
                if not last_pr_commit:
                    continue
                
                # 6. If we don't have a name from the profile, try to get it from the last commit
                if author_name == author_login and commits:
                    last_commit_name = commits[-1].author_name
                    if last_commit_name:
                        author_name = last_commit_name
                
                # 7. Find the last commit before the PR was created
                base_commit = self._get_commit_before_date(
                    repo_full_name, 
                    base_branch, 
                    pr_created_at
                )
                
                # 8. Add data if the base commit exists
                if base_commit:
                    pr_data = PullRequestData(
                        pr_number=pr['number'],
                        pr_title=pr['title'],
                        base_branch=base_branch,
                        base_commit_sha=base_commit['sha'],
                        base_commit_date=base_commit['commit']['author']['date'],
                        pr_commit_sha=last_pr_commit['sha'],
                        pr_commit_date=last_pr_commit['commit']['author']['date'],
                        comparison_url=(
                            f"https://github.com/{repo_full_name}/"
                            f"compare/{base_commit['sha']}...{last_pr_commit['sha']}"
                        ),
                        author_name=author_name,
                        author_email=author_email,
                        author_login=author_login,
                        commits=commits
                    )
                    prs_data.append(pr_data)
            
            return prs_data
        except Exception as e:
            print(f"Error processing PRs: {str(e)}")
            return []
    
    def _get_commit_before_date(self, repo_full_name: str, branch: str, target_date: str) -> Optional[Dict[str, Any]]:
        """Finds the last commit on a branch before a specific date"""
        url = f"{self.base_url}/repos/{repo_full_name}/commits"
        params = {
            'sha': branch,
            'until': target_date,
            'per_page': 1  # Only the most recent commit before the date
        }
        
        try:
            commits = self.get_json_response(url, params)
            if commits:
                return commits[0]
        except Exception as e:
            print(f"Error fetching commit: {str(e)}")
        
        return None
    