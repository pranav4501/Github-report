import requests
import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()

# GitHub API configuration
GITHUB_API_URL = "https://api.github.com"
GITHUB_USERNAME = "pranav4501"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# OpenAI configuration
oAIClient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Headers for authentication
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_user_events():
    """Fetch recent events for the authenticated user."""
    url = f"{GITHUB_API_URL}/users/{GITHUB_USERNAME}/events"
    events = []
    page = 1
    
    while len(events) < 10:
        response = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
        if response.status_code == 200:
            page_events = response.json()
            if not page_events:
                break
            push_events = [event for event in page_events if event['type'] == 'PushEvent']
            events.extend(push_events)
            page += 1
        else:
            print(f"Error fetching events: {response.status_code}")
            break
    
    return events[:10]  # Return only the last 10 push events

def get_commit_changes(repo_name, commit_sha):
    """Fetch the changes for a specific commit."""
    url = f"{GITHUB_API_URL}/repos/{repo_name}/commits/{commit_sha}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        commit_data = response.json()
        return commit_data['files']
    else:
        print(f"Error fetching commit changes: {response.status_code}")
        return []

def generate_report(commits_data):
    """Generate a report using GPT-4 based on the commits data."""
    prompt = f"""
    As an AI assistant, analyze the following GitHub commit data and generate a concise report. 
    Focus on key changes, patterns, and potential impacts of these commits.

    Commit Data:
    {json.dumps(commits_data, indent=2)}

    Please provide a summary that includes:
    1. An overview of the repositories affected
    2. The main types of changes made (e.g., bug fixes, new features, refactoring)
    3. Any notable patterns or trends in the commits
    4. Potential impacts or implications of these changes

    Keep the report concise and informative.
    """

    response = oAIClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes GitHub commit data."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def main():
    events = get_user_events()
    
    commits_data = []
    
    for event in events:
        repo_name = event['repo']['name']
        commits = event['payload']['commits']
        for commit in commits:
            author = commit['author']['name']
            message = commit['message']
            sha = commit['sha']
            date = datetime.datetime.strptime(event['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            
            changes = get_commit_changes(repo_name, sha)
            
            commit_info = {
                "repository": repo_name,
                "author": author,
                "date": date.isoformat(),
                "sha": sha,
                "message": message,
                "changes": [
                    {
                        "filename": file['filename'],
                        "additions": file['additions'],
                        "deletions": file['deletions'],
                        "patch": file.get('patch', '')[:500]  # Limit patch size
                    } for file in changes
                ]
            }
            
            commits_data.append(commit_info)
    
    report = generate_report(commits_data)
    print("\nGPT-4 Generated Report:")
    print(report)

if __name__ == "__main__":
    main()
