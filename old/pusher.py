import os
import keyring
import subprocess

# Function to store credentials securely
def store_git_credentials():
    service_name = "git"
    username = input("Enter your Git username: ").strip()
    token = input("Enter your Git personal access token: ").strip()
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

# Main function
def main():
    while True:
        print("\nOptions:")
        print("1. Store Git credentials")
        print("2. Push files to a Git repository")
        print("3. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            store_git_credentials()

        elif choice == "2":
            username, token = get_git_credentials()
            if not username or not token:
                continue

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
            if run_git_command(
                f"git -c http.extraheader='Authorization: Basic {username}:{token}' push {repo_url} main"
            ):
                print("Files pushed successfully!")

        elif choice == "3":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please try again.")

# Run the script
if __name__ == "__main__":
    main()
