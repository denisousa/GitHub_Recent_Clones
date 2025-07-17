from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

@dataclass
class CommitData:
    sha: str
    message: str
    author_name: str
    author_email: Optional[str]
    author_date: str

@dataclass
class PullRequestData:
    pr_number: int
    pr_title: str
    base_branch: str
    base_commit_sha: str
    base_commit_date: str
    pr_commit_sha: str
    pr_commit_date: str
    comparison_url: str
    author_name: str
    author_email: Optional[str]
    author_login: str
    commits: List[CommitData]

@dataclass
class RepositoryData:
    name: str
    url: str
    stars: int
    watchers: int
    forks: int
    created_at: str
    updated_at: str
    avg_issue_close_days: float
    prs: List[PullRequestData]
    default_branch: str
    languages: Optional[Dict[str, int]] = None
    dominant_language: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Converts the dataclass to a dictionary for serialization"""
        try:
            return asdict(self)
        except Exception as e:
            print(f"⚠️ Error converting to dict: {e}")
            # Fallback to manual conversion if asdict fails
            return {
                'name': self.name,
                'url': self.url,
                'stars': self.stars,
                'watchers': self.watchers,
                'forks': self.forks,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'avg_issue_close_days': self.avg_issue_close_days,
                'prs': [pr.to_dict() if hasattr(pr, 'to_dict') else pr for pr in self.prs],
                'default_branch': self.default_branch,
                'languages': self.languages,
                'dominant_language': self.dominant_language
            }