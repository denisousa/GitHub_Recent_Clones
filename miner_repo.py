import requests
import time
import os

GITHUB_TOKEN = os.getenv("GH_TOKEN")

# Set headers for authentication
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# Minimum thresholds
MIN_CLOSED_ISSUES = 100
MIN_COMMITS = 100

# Step 1: Search Java repositories with >200 stars and not forked
def search_java_repositories():
    query = 'language:Java stars:>200 fork:false'
    url = 'https://api.github.com/search/repositories'
    params = {
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'per_page': 10,
        'page': 1
    }
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()['items']

# Step 2: Check if repo has more than 100 commits
def has_enough_commits(repo):
    commits_url = repo['commits_url'].split('{')[0]
    response = requests.get(commits_url, headers=HEADERS, params={'per_page': 1})
    if 'Link' in response.headers and 'last' in response.headers['Link']:
        last_page = int(response.headers['Link'].split('page=')[-1].split('>')[0])
        print(f'nº commits: {last_page}')
        return last_page > MIN_COMMITS
    return False

# Step 3: Check if repo has more than 100 closed issues
def has_enough_closed_issues(repo):
    owner = repo['owner']['login']
    name = repo['name']
    url = f'https://api.github.com/repos/{owner}/{name}'
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    search_url = 'https://api.github.com/search/issues'
    params = {
        'q': f'repo:{owner}/{name} is:issue is:closed',
        'per_page': 1
    }
    response = requests.get(search_url, headers=HEADERS, params=params)
    response.raise_for_status()
    
    total_closed = response.json().get('total_count', 0)
    print(f'Closed issues: {total_closed}')

    return total_closed > MIN_CLOSED_ISSUES

def get_repositories():
    repositories = search_java_repositories()
    print(f"Checking {len(repositories)} repositories...\n")
    
    valid_repositories = []
    for repo in repositories:
        print(f"→ {repo['full_name']}")
        try:
            if has_enough_commits(repo) and has_enough_closed_issues(repo):
                print(f"✅ {repo['html_url']} meets all criteria\n")
                valid_repositories.append(repo)
            else:
                print("⛔ Does not meet commit/issue criteria\n")
        except Exception as e:
            print(f"⚠️ Error processing {repo['full_name']}: {e}")
        time.sleep(1)  # Prevent API rate limit issues

# if __name__ == '__main__':
#     main()
