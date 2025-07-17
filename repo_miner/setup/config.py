import os
from decouple import Config, RepositoryEnv

# Function to clear problematic variables
def clear_env_conflicts():
    """Remove environment variables that might conflict with .env"""
    problematic_vars = [
        'MIN_STARS', 'MAX_ISSUE_CLOSE_DAYS', 'SEARCH_LANGUAGE', 
        'BATCH_SIZE', 'TOTAL_TARGET_REPOS', 'MAX_PRS_PER_REPO',
        'MAX_REPOS'  # Include MAX_REPOS in the cleanup
    ]
    cleared = []
    
    for var in problematic_vars:
        if var in os.environ:
            cleared.append(f"{var}={os.environ[var]}")
            del os.environ[var]
    
    if cleared:
        print(f"🧹 Clearing conflicting variables: {', '.join(cleared)}")

# Clear conflicts automatically
clear_env_conflicts()

# Force reading only from .env
env_config = Config(RepositoryEnv('.env'))

# GitHub API Settings
GITHUB_TOKEN = env_config('GITHUB_TOKEN', default='')
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

# Search and Filtering Settings (MAX_REPOS REMOVED)
MIN_STARS = env_config('MIN_STARS', default=50, cast=int)
MAX_PRS_PER_REPO = env_config('MAX_PRS_PER_REPO', default=5, cast=int)
MAX_ISSUE_CLOSE_DAYS = env_config('MAX_ISSUE_CLOSE_DAYS', default=3.0, cast=float)
SEARCH_LANGUAGE = env_config('SEARCH_LANGUAGE', default='java')

# Rate Limit and Pagination Settings
SLEEP_ON_RATE_LIMIT = env_config('SLEEP_ON_RATE_LIMIT', default=30, cast=int)
ISSUES_PER_PAGE = env_config('ISSUES_PER_PAGE', default=100, cast=int)
MAX_ISSUE_PAGES = env_config('MAX_ISSUE_PAGES', default=3, cast=int)
REPOS_PER_PAGE = env_config('REPOS_PER_PAGE', default=100, cast=int)

# Output Settings
OUTPUT_FILE = env_config('OUTPUT_FILE', default='github_repos_filtered.json')
OUTPUT_ENCODING = env_config('OUTPUT_ENCODING', default='utf-8')
EXPORT_FORMAT = env_config('EXPORT_FORMAT', default='json')  # json, csv, both
CSV_OUTPUT_FILE = env_config('CSV_OUTPUT_FILE', default='github_repos_filtered.csv')

# Batch Execution Settings
BATCH_SIZE = env_config('BATCH_SIZE', default=200, cast=int)
TOTAL_TARGET_REPOS = env_config('TOTAL_TARGET_REPOS', default=1000, cast=int)

# Debug: show loaded settings
print(f"🔧 Settings loaded:")
print(f"   MIN_STARS: {MIN_STARS}")
print(f"   MAX_ISSUE_CLOSE_DAYS: {MAX_ISSUE_CLOSE_DAYS}")
print(f"   SEARCH_LANGUAGE: {SEARCH_LANGUAGE}")
print(f"   BATCH_SIZE: {BATCH_SIZE}")
print(f"   TOTAL_TARGET_REPOS: {TOTAL_TARGET_REPOS}")