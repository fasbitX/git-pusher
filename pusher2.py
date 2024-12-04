import os
import keyring
import requests
import subprocess

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com"

# Execute a Git command
def run_git_command(command):
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            print("Command executed successfully!")
        else:
            print("Error:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print("An error occurred:", str(e))
        return False


# Function to store credentials securely
def store_git_credentials():
    service_name = "git"
    username = input("Enter your GitHub username: ").strip()
    token = input("Enter your GitHub personal access token: ").strip()
    keyring.set_password(service_name, "username", username)
    keyring.set_password(service_name, "token", token)
    print("Credentials stored securely!")

# Function to retrieve credentials
def get_git_credentials():
    service_name = "git"
    username = keyring.get_password(service_name, "username")
    token = keyring.get_password(service_name, "token")
    if not username or not token:
        print("Credentials not found. Please store them first.")
        return None, None
    return username, token

# Function to check if the current directory is a Git repository
def is_git_repo():
    result = subprocess.run("git rev-parse --is-inside-work-tree", shell=True, text=True, capture_output=True)
    return result.returncode == 0

# Initialize the repo if necessary
def initialize_repo():
    print("The current directory is not a Git repository.")
    choice = input("Would you like to initialize a new Git repository here? (yes/no): ").strip().lower()
    if choice == "yes":
        if run_git_command("git init"):
            print("Initialized an empty Git repository.")
            return True
        else:
            print("Failed to initialize Git repository.")
            return False
    return False

# Verify and create a commit if none exists
def verify_and_create_commit():
    result = subprocess.run("git log", shell=True, text=True, capture_output=True)
    if result.returncode != 0:  # No commits in the repository
        print("No commits found in the repository. Creating an initial commit.")
        if run_git_command("git add ."):
            if run_git_command('git commit -m "Initial commit"'):
                print("Initial commit created successfully!")
                return True
            else:
                print("Failed to create the initial commit.")
        else:
            print("Failed to stage files for the initial commit.")
        return False
    else:
        print("Existing commits found in the repository.")
        return True

# Ensure remote exists
def ensure_remote_exists(repo_url):
    result = subprocess.run("git remote -v", shell=True, text=True, capture_output=True)
    if repo_url not in result.stdout:
        print(f"Adding remote repository: {repo_url}")
        if run_git_command(f"git remote add origin {repo_url}"):
            print("Remote repository added successfully!")
        else:
            print("Failed to add remote repository. Check your URL or access rights.")
    else:
        print("Remote repository already exists.")

# List files in the current directory
def list_files():
    print("\nAvailable files:")
    files = os.listdir(".")
    for i, file in enumerate(files, start=1):
        print(f"{i}. {file}")
    return files

# Select files to push
def select_files(files):
    selected_files = input("\nEnter the numbers of the files to add (comma-separated, e.g., 1,3): ").strip()
    try:
        indices = [int(i.strip()) - 1 for i in selected_files.split(",")]
        return [files[i] for i in indices]
    except (ValueError, IndexError):
        print("Invalid input. Please try again.")
        return []

# Create a GitHub repository
def create_repo(repo_name, private=True):
    username, token = get_git_credentials()
    if not username or not token:
        return None
    url = f"{GITHUB_API_URL}/user/repos"
    headers = {"Authorization": f"token {token}"}
    data = {"name": repo_name, "private": private}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print(f"Repository '{repo_name}' created successfully!")
        return response.json()["html_url"]
    else:
        print("Failed to create repository:", response.json().get("message", "Unknown error"))
        return None

# Check Git identity
def check_git_identity():
    result_name = subprocess.run("git config user.name", shell=True, text=True, capture_output=True)
    result_email = subprocess.run("git config user.email", shell=True, text=True, capture_output=True)
    if not result_name.stdout.strip() or not result_email.stdout.strip():
        print("Git identity is not set. Let's configure it now.")
        name = input("Enter your Git user name: ").strip()
        email = input("Enter your Git user email: ").strip()
        subprocess.run(f'git config --global user.name "{name}"', shell=True)
        subprocess.run(f'git config --global user.email "{email}"', shell=True)
        print("Git identity configured successfully!")
    else:
        print(f"Git identity found: {result_name.stdout.strip()} <{result_email.stdout.strip()}>")

# Create a README.md file
def create_readme():
    if os.path.exists("README.md"):
        print("README.md already exists. Overwrite? (yes/no): ", end="")
        choice = input().strip().lower()
        if choice != "yes":
            print("Operation cancelled. README.md was not modified.")
            return

    # Ask the user for README content
    content = input("Enter the content for the README.md file:\n")
    
    # Write content to README.md
    with open("README.md", "w") as readme_file:
        readme_file.write(content)
    print("README.md file created successfully!")

    # Stage and commit the README.md file
    if run_git_command("git add README.md"):
        if run_git_command('git commit -m "Add README.md"'):
            print("README.md committed successfully!")
        else:
            print("Failed to commit README.md.")
    else:
        print("Failed to stage README.md.")

# Update the repository with changes
def update_repository():
    if not is_git_repo():
        print("This is not a Git repository. Please initialize it first.")
        return

    # Stage all changes
    if run_git_command("git add ."):
        print("All changes staged successfully.")
    else:
        print("Failed to stage changes.")
        return

    # Commit the changes
    commit_message = input("Enter a commit message for the changes: ").strip()
    if not run_git_command(f'git commit -m "{commit_message}"'):
        print("Failed to commit changes. Ensure there are changes to commit.")
        return

    # Push changes
    username, token = get_git_credentials()
    if not username or not token:
        print("GitHub credentials not found. Please store them first.")
        return

    # Ensure the remote repository exists
    repo_url = subprocess.run("git config --get remote.origin.url", shell=True, text=True, capture_output=True).stdout.strip()
    if not repo_url:
        print("No remote repository found. Please set up the remote repository first.")
        return

    # Push changes
    pat_repo_url = repo_url.replace("https://", f"https://{username}:{token}@")
    if run_git_command(f"git push {pat_repo_url}"):
        print("Changes pushed successfully!")
    else:
        print("Failed to push changes to the repository.")



## MAIN  ## 
def main():
    while True:
        print("\nOptions:")
        print("1. Store Git credentials")
        print("2. Push files to a Git repository")
        print("3. Create a new repository")
        print("4. Create a README.md file")
        print("5. Update repository with changes")
        print("6. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            store_git_credentials()
        elif choice == "2":
            if not is_git_repo():
                if not initialize_repo():
                    continue

            # Check and set Git identity
            check_git_identity()

            # Ensure a commit exists
            if not verify_and_create_commit():
                continue

            # Retrieve GitHub credentials
            username, token = get_git_credentials()
            if not username or not token:
                continue

            # Ask the user for the repository name
            repo_name = input("Enter the name of the repository to push to: ").strip()
            repo_url = f"https://github.com/{username}/{repo_name}.git"

            # Ensure the remote repository is set
            ensure_remote_exists(repo_url)

            # Push the branch with embedded token
            if run_git_command("git branch -M main"):  # Ensure branch is named 'main'
                pat_repo_url = repo_url.replace("https://", f"https://{username}:{token}@")
                if run_git_command(f"git push -u {pat_repo_url} main"):
                    print("Files pushed successfully!")
                else:
                    print("Failed to push changes. Check your repository and branch setup.")
            else:
                print("Failed to set the branch to 'main'.")

        elif choice == "3":
            repo_name = input("Enter the name of the new repository: ").strip()
            is_private = input("Should the repository be private? (yes/no): ").strip().lower() == "yes"
            repo_url = create_repo(repo_name, private=is_private)
            if repo_url:
                print(f"Repository URL: {repo_url}")

        elif choice == "4":
            create_readme()

        elif choice == "5":
            update_repository()

        elif choice == "6":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()


#####################################################################################################
#################################  Python by fasbit.com  ############################################
