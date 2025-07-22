from github import Auth, Github
import os
import subprocess
import requests
from datetime import datetime, timedelta, timezone
import hashlib


def clone_and_checkout_pr_base_commit(repo_name, pr_number, base_dir="repo"):
    repo_url = f"https://github.com/{repo_name}.git"
    api_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    # Caminho completo: repo/org/repo
    org, repo = repo_name.split("/")
    target_path = os.path.join(base_dir, org, repo)

    # Criar diretório base se não existir
    os.makedirs(os.path.join(base_dir, org), exist_ok=True)

    # Clonar o repositório se ainda não existir
    if not os.path.isdir(target_path):
        print(f"Cloning repository {repo_name} into {target_path}...")
        subprocess.run(["git", "clone", repo_url, target_path], check=True)
    else:
        print(f"Repository already cloned at '{target_path}'.")

    # Buscar dados da PR via API
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch PR data: {response.status_code}")
        return

    pr_data = response.json()
    base_commit_sha = pr_data["base"]["sha"]

    # Mudar para o commit base
    print(f"Checking out base commit {base_commit_sha} from PR #{pr_number}...")
    subprocess.run(["git", "checkout", base_commit_sha], cwd=target_path, check=True)
    print("Done.")


def fetch_recent_merged_prs(repo_name, days=7):
    base_api_url = f"https://api.github.com/repos/{repo_name}/pulls"
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": os.getenv('GH_TOKEN')}

    # Data limite (ex: últimos 30 dias)
    since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"

    params = {
        "state": "closed",
        "sort": "updated",
        "direction": "desc",
        "per_page": 100
    }

    print(f"Searching for merged PRs in the last {days} days for {repo_name}...\n")
    response = requests.get(base_api_url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Failed to fetch PRs: {response.status_code}")
        return

    pulls = response.json()
    merged_prs = []

    # Filtrar apenas as PRs mergeadas recentemente
    for pr in pulls:
        if pr.get("merged_at") and pr["merged_at"] > since:
            merged_prs.append({
                "number": pr["number"],
                "title": pr["title"],
                "diff_url": pr["diff_url"]
            })

    if not merged_prs:
        print("No merged PRs found.")
        return

    print(f"Found {len(merged_prs)} merged PRs.\nDownloading and parsing diffs...")

    return merged_prs


def extract_java_diffs_from_pr(pr, output_dir):
    os.system(f'rm -rf {output_dir}')
    os.makedirs(output_dir, exist_ok=True)

    diff_response = requests.get(pr["diff_url"], headers={"Accept": "application/vnd.github.v3.diff"})
    if diff_response.status_code != 200:
        print(f"Failed to fetch diff for PR #{pr['number']}")
        return

    diff_text = diff_response.text
    chunks = diff_text.split("diff --git ")

    for chunk in chunks[1:]:  # pula a primeira parte vazia
        if ".java" not in chunk:
            continue

        lines = chunk.strip().splitlines()
        file_line = lines[0] if lines else ""
        if ".java" not in file_line:
            continue

        hash_name = hashlib.sha256(chunk.encode()).hexdigest()[:6]
        output_path = os.path.join(output_dir, f"{hash_name}.diff")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("diff --git " + chunk)

        print(f"Saved .java diff as {output_path}")

print("\nAll .java diffs extracted.")


def download_java_files_from_github(repo_name: str, commit_index: int):
    token = os.getenv('GH_TOKEN')
    auth = Auth.Token(token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    # Get SHA of the selected commit
    commits = repo.get_commits()
    if commit_index >= commits.totalCount:
        raise ValueError(f"The repository has only {commits.totalCount} commits. Index {commit_index} is out of range.")
    sha = commits[commit_index].sha

    # Get the full tree recursively
    print(f"Fetching repository tree at commit {sha}...")
    tree = repo.get_git_tree(sha=sha, recursive=True).tree

    java_files = [item for item in tree if item.path.endswith(".java") and item.type == "blob"]
    print(f"Found {len(java_files)} Java files.")

    headers = {"Authorization": f"token {token}"}

    output_dir = repo_name.split('/')[-1]

    for file in java_files:
        raw_url = f"https://raw.githubusercontent.com/{repo_name}/{sha}/{file.path}"
        dest_path = os.path.join(output_dir, file.path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        response = requests.get(raw_url, headers=headers)
        if response.status_code == 200:
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(response.text)
        else:
            print(f"Failed to download {file.path} (HTTP {response.status_code})")

    print(f"All Java files downloaded to: {os.path.abspath(output_dir)}")


def checkout_repo_commit_by_index(repo_name: str, commit_index: int, local_dir: str = None):
    auth = Auth.Token(os.getenv("GH_TOKEN"))
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    commits = repo.get_commits()
    if commit_index >= commits.totalCount:
        raise ValueError(f"The repository has only {commits.totalCount} commits. Index {commit_index} is out of range.")
    sha = commits[commit_index].sha

    if local_dir is None:
        project_name = repo_name.split("/")[-1]
        local_dir = f"{project_name}"

    if not os.path.exists(local_dir):
        print(f"Cloning {repo_name} into {local_dir}...")
        subprocess.run(["git", "clone", f"https://github.com/{repo_name}.git", local_dir], check=True)
    else:
        print(f"Repository already exists at {local_dir}, reusing it...")

    print(f"Checking out commit {sha}...")
    subprocess.run(["git", "checkout", sha], cwd=local_dir, check=True)

    print(f"Repository '{repo_name}' is now at commit #{commit_index} ({sha}).")
    print(f"Local path: {os.path.abspath(local_dir)}")
    return os.path.abspath(local_dir)


from github import Github, Auth
from datetime import datetime, timedelta, timezone

def get_closed_prs_before_days(repo_name: str, token: str, days: int):
    # TODO: Get merged commit
    auth = Auth.Token(token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    target_date = datetime.now(timezone.utc) - timedelta(days=days)
    closed_prs = repo.get_pulls(state='closed', sort='updated', direction='desc')
    result = []

    for pr in closed_prs:
        if pr.closed_at > target_date:  # Filtro pela data de fechamento
            head_commit = repo.get_commit(pr.head.sha)
            opened_at = head_commit.commit.author.date

            last_commit_sha = pr.head.sha  # o último commit é o commit de HEAD (última atualização da PR)
            last_commit = repo.get_commit(last_commit_sha)
            last_commit_at = last_commit.commit.author.date

            pr_info = {
                'id': pr.number,
                'opened_commit': pr.head.sha,
                'opened_at': opened_at,
                'last_commit': last_commit_sha,
                'last_commit_at': last_commit_at
            }
            result.append(pr_info)
        else:
            break  # PRs já estão ordenadas da mais nova para a mais antiga

    return result
