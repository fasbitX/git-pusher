import os
import keyring
import requests
import subprocess

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com"

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

# Updated main function to initialize the repo if necessary
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

# Check if there are any commits in the repository
def verify_and_create_commit():

    result = subprocess.run("git log", shell=True, text=True, capture_output=True)

    if result.returncode != 0:  # No commits in the repository
        print("No commits found in the repository. Creating an initial commit.")

        # Stage all files
        if run_git_command("git add ."):
            # Create an initial commit
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

# Function to list files in the current directory
def list_files():
    print("\nAvailable files:")
    files = os.listdir(".")
    for i, file in enumerate(files, start=1):
        print(f"{i}. {file}")
    return files

# Function to select files to push
def select_files(files):
    selected_files = input(
        "\nEnter the numbers of the files to add (comma-separated, e.g., 1,3): "
    ).strip()
    try:
        indices = [int(i.strip()) - 1 for i in selected_files.split(",")]
        chosen_files = [files[i] for i in indices]
        return chosen_files
    except (ValueError, IndexError):
        print("Invalid input. Please try again.")
        return []

# Function to execute a Git command
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

# Function to create a GitHub repository
def create_repo(repo_name, private=True):
    username, token = get_git_credentials()
    if not username or not token:
        return None

    url = f"{GITHUB_API_URL}/user/repos"
    headers = {"Authorization": f"token {token}"}
    data = {
        "name": repo_name,
        "private": private,
    }
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 201:
        print(f"Repository '{repo_name}' created successfully!")
        return response.json()["html_url"]
    else:
        print("Failed to create repository:", response.json().get("message", "Unknown error"))
        return None

# Function to check Git identity
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

# Main function
def main():
    while True:
        print("\nOptions:")
        print("1. Store Git credentials")
        print("2. Push files to a Git repository")
        print("3. Create a new repository")
        print("4. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            store_git_credentials()

        elif choice == "2":
            if not is_git_repo():
                if not initialize_repo():
                    continue

            # Ensure username and email are set
            check_git_identity()

            # Proceed with commit verification
            if not verify_and_create_commit():
                continue


            # Proceed with file selection, staging, and commit
            username, token = get_git_credentials()
            if not username or not token:
                continue

            # Ask the user for the repository name
            repo_name = input("Enter the name of the repository to push to: ").strip()
            repo_url = f"https://github.com/{username}/{repo_name}.git"

            # List files and get user's selection
            files = list_files()
            if not files:
                print("No files in the current directory.")
                continue

            selected_files = select_files(files)
            if not selected_files:
                print("No files selected. Operation cancelled.")
                continue

            # Add selected files to Git staging
            for file in selected_files:
                if not run_git_command(f"git add {file}"):
                    print(f"Failed to add {file}.")
                    continue

            # Commit changes
            commit_message = input("Enter a commit message: ").strip()
            if not run_git_command(f'git commit -m "{commit_message}"'):
                print("Commit failed. Please try again.")
                continue

            # Ask for the repository URL
            repo_url = input("Enter the Git repository URL: ").strip()

            # Push changes
            if run_git_command("git branch -M main"):  # Ensure the branch is named 'main'
                if run_git_command(
                    f"git -c http.extraheader='Authorization: Basic {username}:{token}' push -u {repo_url} main"
                ):
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
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please try again.")

# Run the script
if __name__ == "__main__":
    main()
