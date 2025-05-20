from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import requests
import os

load_dotenv()

# Configurações do repositório
owner = "Stirling-Tools"       # Ex: "microsoft"
repo = "Stirling-PDF"    # Ex: "vscode"
token = os.getenv("GH_TOKEN")

def get_date_ranges():
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    yesterday_end = today_start
    return yesterday_start, yesterday_end, today_start, now

def fetch_pull_requests(owner, repo, token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Accept": "application/vnd.github+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "state": "all",
        "per_page": 100
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Erro ao buscar PRs: {response.status_code} - {response.text}")
        return []

    return response.json()

def filter_prs_by_date(prs, start_date, end_date):
    result = []
    for pr in prs:
        created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if start_date <= created_at < end_date:
            result.append(pr)
    return result

def display_prs(prs, label):
    print(f"\n{label} ({len(prs)} PRs):")
    if prs:
        for pr in prs:
            print(f"- #{pr['number']}: {pr['title']} (opened at {pr['created_at']})")
    else:
        print("None.")

def check_prs_opened_yesterday_and_today(owner, repo, token=None):
    y_start, y_end, t_start, t_now = get_date_ranges()
    prs = fetch_pull_requests(owner, repo, token)

    prs_yesterday = filter_prs_by_date(prs, y_start, y_end)
    prs_today = filter_prs_by_date(prs, t_start, t_now)

    display_prs(prs_yesterday, "PRs opened yesterday")
    display_prs(prs_today, "PRs opened today")

if __name__ == "__main__":
    check_prs_opened_yesterday_and_today(owner, repo, token)
