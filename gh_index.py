import os
import requests
from dotenv import load_dotenv
import base64
from tqdm import tqdm

# Load environment variables
load_dotenv()

# GitHub API configuration
GITHUB_API_URL = "https://api.github.com"
GITHUB_USERNAME = "pranav4501"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Headers for authentication
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_user_repos():
    """Fetch all repositories for the authenticated user."""
    url = f"{GITHUB_API_URL}/user/repos"
    repos = []
    page = 1
    
    while True:
        response = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
        if response.status_code == 200:
            page_repos = response.json()
            if not page_repos:
                break
            repos.extend(page_repos)
            page += 1
        else:
            print(f"Error fetching repositories: {response.status_code}")
            break
    
    return repos

def get_repo_contents(repo_name, path=""):
    """Recursively fetch contents of a repository."""
    url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/contents/{path}"
    print(url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        files = []
        for item in contents:
            if item['type'] == 'file':
                file_content = get_file_content(repo_name, item['path'])
                files.append({
                    'path': item['path'],
                    'content': file_content
                })
            elif item['type'] == 'dir':
                files.extend(get_repo_contents(repo_name, item['path']))
        return files
    else:
        print(f"Error fetching contents for {repo_name}/{path}: {response.status_code}")
        return []

def get_file_content(repo_name, file_path):
    """Fetch content of a specific file."""
    url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/contents/{file_path}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()['content']
        return base64.b64decode(content).decode('utf-8')
    else:
        print(f"Error fetching file content for {repo_name}/{file_path}: {response.status_code}")
        return ""

def get_commit_history(repo_name):
    """Fetch commit history for a repository."""
    url = f"{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/{repo_name}/commits"
    commits = []
    page = 1
    
    while True:
        response = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
        if response.status_code == 200:
            page_commits = response.json()
            if not page_commits:
                break
            commits.extend(page_commits)
            page += 1
        else:
            print(f"Error fetching commit history for {repo_name}: {response.status_code}")
            break
    
    return commits

def prepare_data_for_embedding(repos):
    """Prepare repository data for embedding."""
    data_for_embedding = []
    
    for repo in tqdm(repos, desc="Processing repositories"):
        repo_name = repo['name']
        print(repo_name)
        # Get repository contents
        contents = get_repo_contents(repo_name)
        for file in contents:
            print(type(file))
            data_for_embedding.append({
                'type': 'file',
                'repo': repo_name,
                'path': file['path'],
                'content': file['content']
            })
        print(len(data_for_embedding))
        # Get commit history
        commits = get_commit_history(repo_name)
        for commit in commits:
            print(commit)
            data_for_embedding.append({
                'type': 'commit',
                'repo': repo_name,
                'sha': commit['sha'],
                'message': commit['commit']['message'],
                'author': commit['commit']['author']['name'],
                'date': commit['commit']['author']['date']
            })
    
    return data_for_embedding

def main():
    repos = get_user_repos()
    data = prepare_data_for_embedding(repos)
    
    print(f"Prepared {len(data)} items for embedding.")
    
    # Here you would typically send 'data' to your embedding function
    # and then store the embeddings in your vector database
    # For example:
    # embeddings = create_embeddings(data)
    # store_in_vector_db(embeddings)

if __name__ == "__main__":
    main()
