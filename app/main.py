import sys
import os
import zlib
import hashlib
import time
import shutil

def initialize_git_repo():
    # Create necessary directories
    os.makedirs('.git/refs/heads', exist_ok=True)
    os.makedirs('.git/objects', exist_ok=True)

    # Initialize the main branch (empty commit initially)
    with open('.git/refs/heads/main', 'w') as f:
        f.write('0000000000000000000000000000000000000000\n')  # Initial commit SHA
    
    # Set HEAD to point to the main branch
    with open('.git/HEAD', 'w') as f:
        f.write('ref: refs/heads/main\n')

def get_blob_content(blob_sha):
    # Construct the file path for the blob object
    blob_dir = f".git/objects/{blob_sha[:2]}"
    blob_file = f"{blob_dir}/{blob_sha[2:]}"

    if not os.path.exists(blob_file):
        raise RuntimeError(f"Blob {blob_sha} not found")

    # Read the compressed data from the blob file
    with open(blob_file, "rb") as f:
        compressed_data = f.read()

    # Decompress the data
    decompressed_data = zlib.decompress(compressed_data)

    # Split the decompressed data into the header and content
    header, content = decompressed_data.split(b'\0', 1)
    blob_type, size = header.split(b' ', 1)

    if blob_type != b"blob":
        raise RuntimeError(f"Unexpected object type: {blob_type.decode()}")

    # Return the file content as a string
    return content.decode()

def hash_object(file_path):
    # Read the file's content
    with open(file_path, 'rb') as f:
        content = f.read()

    # Compute the SHA-1 hash over the uncompressed content
    file_size = len(content)
    header = f'blob {file_size}\0'.encode()  # Format: blob <size>\0
    data_to_hash = header + content
    sha1_hash = hashlib.sha1(data_to_hash).hexdigest()

    # Create the file path based on the first two characters of the hash
    object_dir = '.git/objects'
    dir_name = sha1_hash[:2]
    file_name = sha1_hash[2:]

    object_path = os.path.join(object_dir, dir_name, file_name)

    # Ensure the directory exists
    os.makedirs(os.path.dirname(object_path), exist_ok=True)

    # Compress the data using zlib and write it to the object file
    with open(object_path, 'wb') as out_file:
        compressed_data = zlib.compress(data_to_hash)
        out_file.write(compressed_data)

    # Output the hash to stdout
    print(sha1_hash)

def hash_object_tree(data, obj_type="blob"):
    """
    Hash the given data (file content or tree data) and store it as a Git object.
    """
    # Prepare object header
    header = f"{obj_type} {len(data)}\0".encode()
    content = header + data

    # Compute SHA-1 hash
    sha1_hash = hashlib.sha1(content).hexdigest()

    # Create the object file path
    object_dir = f".git/objects/{sha1_hash[:2]}"
    object_file = f"{object_dir}/{sha1_hash[2:]}"

    # Ensure the directory exists
    os.makedirs(object_dir, exist_ok=True)

    # Write compressed data to the object file
    if not os.path.exists(object_file):  # Avoid overwriting if object exists
        with open(object_file, "wb") as f:
            f.write(zlib.compress(content))

    return sha1_hash

def get_object_content(object_sha):
    # Construct the file path for the object
    obj_dir = f".git/objects/{object_sha[:2]}"
    obj_file = f"{obj_dir}/{object_sha[2:]}"

    if not os.path.exists(obj_file):
        raise RuntimeError(f"Object {object_sha} not found")

    # Read and decompress the object file
    with open(obj_file, "rb") as f:
        compressed_data = f.read()

    decompressed_data = zlib.decompress(compressed_data)
    return decompressed_data

def parse_tree_object(tree_sha):
    # Get the raw content of the tree object
    content = get_object_content(tree_sha)
    
    # Split header and data
    header, tree_data = content.split(b'\0', 1)
    object_type, size = header.split(b' ', 1)

    if object_type != b"tree":
        raise RuntimeError(f"Unexpected object type: {object_type.decode()}")

    # Parse tree entries
    entries = []
    i = 0
    while i < len(tree_data):
        # Read mode (e.g., "100644" or "040000") and name
        mode_end = tree_data.find(b' ', i)
        mode = tree_data[i:mode_end].decode()
        name_end = tree_data.find(b'\0', mode_end + 1)
        name = tree_data[mode_end + 1:name_end].decode()
        
        # Read the raw SHA (20 bytes)
        sha = tree_data[name_end + 1:name_end + 21]
        sha_hex = sha.hex()
        
        entries.append((mode, name, sha_hex))
        i = name_end + 21  # Move to the next entry

    return entries

def ls_tree(tree_sha, name_only=False):
    # Parse the tree object
    entries = parse_tree_object(tree_sha)
    if name_only:
        # Print only names
        for _, name, _ in sorted(entries, key=lambda x: x[1]):
            print(name)
    else:
        # Print full details
        for mode, name, sha in sorted(entries, key=lambda x: x[1]):
            object_type = "tree" if mode == "40000" else "blob"
            print(f"{mode} {object_type} {sha}    {name}")


def read_gitignore():
    ignored_files = []
    try:
        with open(".gitignore", "r") as f:
            ignored_files = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        pass
    return ignored_files

def write_tree(directory="."):
    entries = []
    ignored_files = read_gitignore()
    
    for entry in sorted(os.listdir(directory)):
        # Skip files in .gitignore
        if entry in ignored_files or entry == ".git":
            continue

        entry_path = os.path.join(directory, entry)
        if os.path.isfile(entry_path):
            # Create a blob object for the file
            with open(entry_path, "rb") as f:
                blob_data = f.read()
            blob_sha = hash_object_tree(blob_data, obj_type="blob")
            mode = "100644"  # Regular file mode
            entries.append((mode, entry, blob_sha))
        elif os.path.isdir(entry_path):
            # Recursively create a tree object for the directory
            tree_sha = write_tree(entry_path)
            mode = "40000"  # Directory mode
            entries.append((mode, entry, tree_sha))

    # Construct the tree data
    tree_data = b""
    for mode, name, sha in entries:
        tree_data += f"{mode} {name}\0".encode() + bytes.fromhex(sha)

    # Create and return the SHA of the tree object
    return hash_object_tree(tree_data, obj_type="tree")

    """
    Recursively create tree objects for the current directory.
    """
    entries = []
    for entry in sorted(os.listdir(directory)):
        # Ignore the .git directory
        if entry == ".git":
            continue

        entry_path = os.path.join(directory, entry)
        if os.path.isfile(entry_path):
            # Create a blob object for the file
            with open(entry_path, "rb") as f:
                blob_data = f.read()
            blob_sha = hash_object_tree(blob_data, obj_type="blob")
            mode = "100644"  # Regular file mode
            entries.append((mode, entry, blob_sha))
        elif os.path.isdir(entry_path):
            # Recursively create a tree object for the directory
            tree_sha = write_tree(entry_path)
            mode = "40000"  # Directory mode
            entries.append((mode, entry, tree_sha))

    # Construct the tree data
    tree_data = b""
    for mode, name, sha in entries:
        tree_data += f"{mode} {name}\0".encode() + bytes.fromhex(sha)

    # Create and return the SHA of the tree object
    return hash_object_tree(tree_data, obj_type="tree")

def create_commit_object(tree_sha, parent_sha, message, branch_name="main"):
    """
    Create a commit object and update the branch reference.
    """
    author = "John Doe <johndoe@example.com>"
    timestamp = int(time.time())
    timezone_offset = time.strftime('%z')

    # Format the commit content
    content = f"tree {tree_sha}\n"
    if parent_sha and parent_sha != "0" * 40:  # Validate parent SHA
        content += f"parent {parent_sha}\n"
    content += f"""author {author} {timestamp} {timezone_offset}
committer {author} {timestamp} {timezone_offset}

{message}\n"""


    # Encode the complete content as bytes
    content = content.encode()

    # Compute the SHA-1 hash of the commit object
    header = f"commit {len(content)}\0".encode()
    commit_data = header + content
    sha1_hash = hashlib.sha1(commit_data).hexdigest()

    # Save the commit object
    object_dir = f".git/objects/{sha1_hash[:2]}"
    object_file = f"{object_dir}/{sha1_hash[2:]}"
    os.makedirs(object_dir, exist_ok=True)
    if not os.path.exists(object_file):
        with open(object_file, "wb") as f:
            f.write(zlib.compress(commit_data))
    
    # Update the branch reference
    with open(f".git/refs/heads/{branch_name}", "w") as f:
        f.write(sha1_hash)
    
    return sha1_hash


def get_commit_sha(branch_name):
    """
    Retrieve the latest commit SHA from a branch.
    """
    try:
        with open(f".git/refs/heads/{branch_name}", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(f"Branch '{branch_name}' does not exist.")
    
def get_parent_commit_sha(commit_data):
    """
    Extract the parent commit SHA from commit data.
    Return None if no parent exists.
    """
    lines = commit_data.decode().split("\n")
    for line in lines:
        if line.startswith("parent "):
            return line.split()[1]
    return None  # No parent found

def get_commit_tree(commit_sha):
    """
    Retrieve the tree SHA from a commit object.
    """
    commit_data = get_object_content(commit_sha)
    lines = commit_data.decode().split("\n")
    if lines and lines[0].startswith("tree "):
        return lines[0].split()[1]
    raise RuntimeError(f"Invalid commit format for SHA {commit_sha}")

def show_commit_history(branch_name="main"):
    """
    Display the commit history of a branch.
    """
    try:
        commit_sha = get_commit_sha(branch_name)
        while commit_sha:
            commit_data = get_object_content(commit_sha)
            print_commit(commit_data)
            commit_sha = get_parent_commit_sha(commit_data)
    except FileNotFoundError:
        print(f"Branch '{branch_name}' does not exist.")
    except RuntimeError as e:
        print(f"Error: {e}")

def print_commit(commit_data):
    try:
        lines = commit_data.decode().split("\n")
        commit_info = {
            "Commit": "(unknown)",
            "Tree": "(unknown)",
            "Parent": "(none)",
            "Author": "(unknown)",
            "Committer": "(unknown)",
            "Message": "(No commit message provided)",
        }
        
        # Parse known prefixes
        for line in lines:
            if line.startswith("tree"):
                commit_info["Tree"] = line.split()[1]
            elif line.startswith("parent"):
                commit_info["Parent"] = line.split()[1]
            elif line.startswith("author"):
                commit_info["Author"] = " ".join(line.split()[1:])
            elif line.startswith("committer"):
                commit_info["Committer"] = " ".join(line.split()[1:])
            elif not line.strip():  # Empty line indicates message follows
                message_index = lines.index(line) + 1
                commit_info["Message"] = "\n".join(lines[message_index:]).strip()
                break
        
        # Display parsed data
        print(f"Commit: {commit_info['Commit']}")
        print(f"Tree: {commit_info['Tree']}")
        print(f"Parent: {commit_info['Parent']}")
        print(f"Author: {commit_info['Author']}")
        print(f"Committer: {commit_info['Committer']}")
        print(f"Message: {commit_info['Message']}")
    except Exception as e:
        print(f"Error parsing commit: {e}")
        raise RuntimeError("Malformed commit data.")

def create_branch(branch_name, start_commit_sha):
    branch_path = f".git/refs/heads/{branch_name}"
    if os.path.exists(branch_path):
        raise RuntimeError(f"Branch {branch_name} already exists.")
    
    with open(branch_path, "w") as f:
        f.write(start_commit_sha)

def merge_branches(target_branch, source_branch):
    target_commit = get_commit_sha(target_branch)
    source_commit = get_commit_sha(source_branch)
    
    # Assuming that we have a function `compare_trees` that checks differences
    target_tree = get_commit_tree(target_commit)
    source_tree = get_commit_tree(source_commit)
    
    if compare_trees(target_tree, source_tree):
        print("Conflicts detected during merge.")
    else:
        # Perform the merge (we won't resolve conflicts, just stage a merge commit)
        merged_tree = merge_trees(target_tree, source_tree)
        new_commit_sha = create_commit_object(merged_tree, target_commit, "Merged changes.")
        print(f"Merged commit: {new_commit_sha}")

def diff_commits(commit_sha1, commit_sha2):
    tree1 = get_commit_tree(commit_sha1)
    tree2 = get_commit_tree(commit_sha2)
    
    diff = compare_trees(tree1, tree2)
    print(diff)

def clone_repository(source_dir, destination_dir):
    shutil.copytree(source_dir + "/.git", destination_dir + "/.git")
    print(f"Cloned repository from {source_dir} to {destination_dir}")
    
def main():
    print("Logs from your program will appear here!", file=sys.stderr)

    if len(sys.argv) < 2:
        raise RuntimeError("No command provided")

    command = sys.argv[1]

    if command == "init":
        # Initialize the git repository
        initialize_git_repo()
        print("Initialized git repository")
    elif command == "cat-file":
        if len(sys.argv) != 4 or sys.argv[2] != "-p":
            raise RuntimeError("Usage: cat-file -p <blob_sha>")

        # Retrieve the content of the blob by its SHA hash
        blob_sha = sys.argv[3]
        content = get_blob_content(blob_sha)
        print(content, end="")  # Print without a newline
    elif command == "hash-object" and len(sys.argv) == 4 and sys.argv[2] == "-w":
        file_path = sys.argv[3]  # Get the file path from the arguments
        hash_object(file_path)
    elif command == "ls-tree":
        if len(sys.argv) < 3:
            raise RuntimeError("Usage: ls-tree [--name-only] <tree_sha>")
        
        name_only = "--name-only" in sys.argv
        tree_sha = sys.argv[-1]
        ls_tree(tree_sha, name_only)
    elif command == "write-tree":
        # Write the working directory as a tree object
        tree_sha = write_tree()
        print(tree_sha)
    elif command == "commit-tree":
        if len(sys.argv) < 7 or sys.argv[3] != "-p" or sys.argv[5][:2] != "-m":
            raise RuntimeError("Usage: commit-tree <tree_sha> -p <parent_sha> -m <message>")
        
        tree_sha = sys.argv[2]
        parent_sha = sys.argv[4]
        message = sys.argv[5][3:]
        
        # Default branch name
        branch_name = "main"

        # Update parent SHA from the current branch if it's the first commit
        if parent_sha == "0" * 40:
            try:
                parent_sha = get_commit_sha(branch_name)
            except RuntimeError:
                parent_sha = None  # First commit has no parent

        commit_sha = create_commit_object(tree_sha, parent_sha, message, branch_name)
        print(f"Commit created with SHA: {commit_sha}")

    elif command == "show-history":
        if len(sys.argv) != 3:
            raise RuntimeError("Usage: show-history <branch_name>")
        branch_name = sys.argv[2]
        show_commit_history(branch_name)
    elif command == "create-branch":
        if len(sys.argv) != 4:
            raise RuntimeError("Usage: create-branch <branch_name> <commit_sha>")
        branch_name = sys.argv[2]
        commit_sha = sys.argv[3]
        create_branch(branch_name, commit_sha)
    elif command == "merge":
        if len(sys.argv) != 4:
            raise RuntimeError("Usage: merge <target_branch> <source_branch>")
        target_branch = sys.argv[2]
        source_branch = sys.argv[3]
        merge_branches(target_branch, source_branch)
    elif command == "diff":
        if len(sys.argv) != 4:
            raise RuntimeError("Usage: diff <commit_sha1> <commit_sha2>")
        commit_sha1 = sys.argv[2]
        commit_sha2 = sys.argv[3]
        diff_commits(commit_sha1, commit_sha2)
    elif command == "clone":
        if len(sys.argv) != 4:
            raise RuntimeError("Usage: clone <source_dir> <destination_dir>")
        source_dir = sys.argv[2]
        destination_dir = sys.argv[3]
        clone_repository(source_dir, destination_dir)
    else:
        raise RuntimeError(f"Unknown command #{command}")

if __name__ == "__main__":
    main()
