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
    """
    Retrieve the content of a Git object, whether it's a commit, tree, or blob.
    """
    obj_dir = f".git/objects/{object_sha[:2]}"
    obj_file = f"{obj_dir}/{object_sha[2:]}"

    if not os.path.exists(obj_file):
        raise RuntimeError(f"Object {object_sha} not found")

    # Read and decompress the object file
    with open(obj_file, "rb") as f:
        compressed_data = f.read()

    decompressed_data = zlib.decompress(compressed_data)

    # Get the object type and content
    header, content = decompressed_data.split(b'\x00', 1)
    obj_type, _ = header.split(b' ', 1)

    if obj_type == b'commit':
        return content  # Return raw commit data
    elif obj_type == b'tree':
        return content  # Return tree entries (blobs or subtrees)
    elif obj_type == b'blob':
        return content  # Return file contents
    else:
        raise RuntimeError(f"Unsupported object type: {obj_type.decode()}")

def parse_tree_object(tree_sha):
    """
    Parse a tree object and return its entries.
    """
    tree_data = get_object_content(tree_sha)  # Get the raw binary content of the tree
    entries = []
    
    i = 0
    while i < len(tree_data):
        # Extract the file mode (e.g., '100644') from the first part of the entry
        mode_len = 6  # Assuming the file mode is a 6-character string (adjust if necessary)
        file_mode = tree_data[i:i + mode_len].decode('ascii')  # Decode the mode as ASCII (not UTF-8)
        
        # Skip past the mode
        i += mode_len
        
        # Extract the file name (null-terminated string)
        file_name = b""
        while tree_data[i:i+1] != b"\0":  # Null-terminated filename
            file_name += tree_data[i:i+1]
            i += 1
        file_name = file_name.decode('utf-8')  # Decode filename as UTF-8 (safe here because filenames are UTF-8)
        
        # Skip the null byte
        i += 1
        
        # Extract the object SHA (20 bytes)
        file_sha = tree_data[i:i+20]
        i += 20
        
        # Append the entry as a tuple (mode, filename, sha)
        entries.append((file_mode, file_name, file_sha))
    
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

def compare_trees(tree_sha1, tree_sha2):
    """
    Compare two tree objects and return a diff or conflict report.
    """
    # Parse the tree objects and get their entries
    entries1 = parse_tree_object(tree_sha1)
    entries2 = parse_tree_object(tree_sha2)

    diff = []
    # Create dictionaries using filenames as keys for easy comparison
    set1 = {entry[1]: entry for entry in entries1}  # Using file names as keys
    set2 = {entry[1]: entry for entry in entries2}

    # Check for conflicts between two trees
    for file_name, entry in set1.items():
        if file_name not in set2:
            diff.append(f"File {file_name} exists only in tree1")
        elif entry[2] != set2[file_name][2]:  # Different SHA means conflict
            diff.append(f"Conflict: {file_name} differs in both trees")

    for file_name, entry in set2.items():
        if file_name not in set1:
            diff.append(f"File {file_name} exists only in tree2")

    return diff

def get_commit_sha(branch_name):
    """
    Retrieve the latest commit SHA from a branch.
    """
    branch_path = f".git/refs/heads/{branch_name}"
    if not os.path.exists(branch_path):
        raise RuntimeError(f"Branch '{branch_name}' does not exist.")
    
    with open(branch_path, "r") as f:
        return f.read().strip()
    
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
    
    # Attempt to decode only if the content is text (i.e., it's not binary)
    try:
        commit_data = commit_data.decode()
    except UnicodeDecodeError:
        raise RuntimeError(f"Commit data for SHA {commit_sha} is not valid UTF-8.")
    
    lines = commit_data.split("\n")
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

def merge_trees(target_tree, source_tree):
    """
    Merge two tree objects (representing directories).
    Returns the SHA of the new merged tree.
    """
    # Extract the list of entries from both trees (blobs or subtrees)
    target_entries = get_tree_entries(target_tree)
    source_entries = get_tree_entries(source_tree)

    merged_entries = {}
    
    # Merge the entries, handling conflicts
    for entry in target_entries + source_entries:
        file_name = entry['name']
        if file_name in merged_entries:
            # Resolve conflict (if the file is changed in both trees)
            if merged_entries[file_name] != entry['sha']:
                # Handle conflict (e.g., take the source file)
                merged_entries[file_name] = entry['sha']
        else:
            merged_entries[file_name] = entry['sha']
    
    # Create a new tree object with the merged entries
    return create_tree_object(merged_entries)

def get_tree_entries(tree_sha):
    """
    Retrieve the entries from a tree object.
    """
    tree_data = get_object_content(tree_sha)
    entries = []

    # A tree object is a list of <mode> <sha> <file_name>
    lines = tree_data.split(b'\n')
    for line in lines:
        parts = line.split(b' ')
        if len(parts) == 3:
            entry = {'mode': parts[0], 'sha': parts[1], 'name': parts[2].decode()}
            entries.append(entry)
    
    return entries

def create_object(object_type, data):
    """
    Create an object of the given type and return its SHA.
    This function will:
    - Compress the object data using zlib.
    - Store the compressed data in the .git/objects directory.
    - Return the SHA-1 hash of the object.
    """
    # Create the object data (including the type and length prefix)
    object_data = f"{object_type} {len(data)}\0".encode() + data

    # Compress the object data using zlib
    compressed_data = zlib.compress(object_data)

    # Calculate the SHA-1 hash of the compressed data
    object_sha = hashlib.sha1(compressed_data).hexdigest()

    # Get the directory and file path where the object will be stored
    obj_dir = f".git/objects/{object_sha[:2]}"
    obj_file = f"{obj_dir}/{object_sha[2:]}"

    # Create the directory if it doesn't exist
    os.makedirs(obj_dir, exist_ok=True)

    # Write the compressed data to the object file
    with open(obj_file, "wb") as f:
        f.write(compressed_data)

    # Return the SHA of the created object
    return object_sha

def create_tree_object(entries):
    """
    Create a new tree object and return its SHA.
    """
    tree_data = b''
    for entry in entries:
        tree_data += f"{entry['mode']} {entry['sha']} {entry['name']}".encode() + b'\n'

    # Create the tree object and return its SHA
    return create_object("tree", tree_data)

def get_parent_sha(commit_sha):
    try:
        commit_data = get_object_content(commit_sha)  # Retrieve the commit object content
        parent_sha = None
        if b"parent" in commit_data:
            # Extract parent SHA if available
            parent_sha = commit_data.split(b"parent")[1].split(b'\n')[0].strip()
        return parent_sha
    except RuntimeError:
        return None

def create_commit_object(tree_sha, parent_sha, message):
    """
    Create a new commit object pointing to the merged tree.
    Update parent_sha from the current latest commit (or None if the first commit).
    """
    commit_data = f"tree {tree_sha}\n".encode()

    if parent_sha:
        commit_data += f"parent {parent_sha}\n".encode()  # Add parent commit reference
    
    commit_data += f"author John Doe <johndoe@example.com> 1733220978 +0300\n".encode()
    commit_data += f"committer John Doe <johndoe@example.com> 1733220978 +0300\n".encode()
    commit_data += f"\n{message}\n".encode()

    commit_sha = create_object("commit", commit_data)

    # Update the current branch (main) reference with the new commit SHA
    with open('.git/refs/heads/main', 'w') as f:
        f.write(commit_sha)  # Write the new commit SHA to the branch reference

    return commit_sha

def merge_branches(target_branch, source_branch):
    target_commit = get_commit_sha(target_branch)
    source_commit = get_commit_sha(source_branch)
    
    # Retrieve the trees from the commits
    target_tree = get_commit_tree(target_commit)
    source_tree = get_commit_tree(source_commit)
    
    # Compare trees for conflicts
    if compare_trees(target_tree, source_tree):
        print("Conflicts detected during merge.")
    else:
        # Merge the trees if no conflicts
        merged_tree = merge_trees(target_tree, source_tree)
        new_commit_sha = create_commit_object(merged_tree, target_commit, "Merged changes.")
        print(f"Merged commit: {new_commit_sha}")

def diff_commits(commit_sha1, commit_sha2):
    """
    Compare the trees of two commits.
    """
    try:
        tree1 = get_commit_tree(commit_sha1)
        tree2 = get_commit_tree(commit_sha2)
    except RuntimeError as e:
        print(f"Error retrieving trees: {e}")
        return
    
    diff = compare_trees(tree1, tree2)
    
    if diff:
        print("Differences found between commits:")
        for line in diff:
            print(line)
    else:
        print("No differences found between commits.")

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
        message = sys.argv[5][3:]  # Extract message after the "-m " part

        # Default branch name
        branch_name = "main"

        # Update parent SHA from the current branch if it's the first commit
        try:
            if parent_sha == "0" * 40:  # Placeholder for no parent
                parent_sha = get_commit_sha(branch_name) or None  # None for first commit
        except RuntimeError:
            if parent_sha == "0" * 40:  # Only ignore parent if placeholder
                parent_sha = None

        # Create the commit object using the provided tree SHA, parent SHA, and message
        commit_sha = create_commit_object(tree_sha, parent_sha, message)

        # Print the SHA of the newly created commit
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
