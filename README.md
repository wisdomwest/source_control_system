# Table of Contents

1. [Git-like Repository Management CLI Overview](#git-like-repository-management-cli)
2. [Questions Asked](#questions)


# Git-like Repository Management CLI

## Overview

This project implements a command-line interface (CLI) for managing a Git-like repository system. The CLI provides several commands for interacting with a repository, such as initializing a repository, managing commits, branches, and objects, and performing various Git operations like diff, checkout, and merge.

The primary goal of this project is to simulate a basic version control system with Git-like commands. It's intended for educational purposes to understand how version control systems work under the hood and to explore how Git operations are implemented at a low level.

### Process Overview

1. **Reading the File Content**: The `hash-object` command reads the content of a specified file.
2. **Computing the SHA-1 Hash**: It computes the SHA-1 hash of the file content to create a unique identifier for the file.
3. **Storing the File**: The file content is stored in the `.git/objects` directory in a specific format.
4. **Zlib Compression**: Before storing the content, it is compressed using zlib to reduce the size of the objects.
From this main functions we can create branches by updating .git contents doing merges and diffs between commits, tres and branches as well as cloning files

## Command List

1. **`init`**: Initializes a new Git repository in the current directory.
2. **`cat-file -p <blob_sha>`**: Retrieves and prints the content of a Git object (blob) identified by its SHA hash.
3. **`hash-object -w <file_path>`**: Calculates the hash of a file, compresses it, and stores it as an object in the `.git/objects` directory.
4. **`ls-tree [--name-only] <tree_sha>`**: Lists the entries of a tree object by its SHA hash, with an optional flag to show only filenames.
5. **`write-tree`**: Creates a tree object from the current working directory, which represents the file structure.
6. **`commit-tree <tree_sha> -p <parent_sha> -m <message>`**: Creates a commit object with a specified tree object, a parent commit SHA, and a commit message.
7. **`show-history <branch_name>`**: Displays the commit history of a given branch.
8. **`create-branch <branch_name> <commit_sha>`**: Creates a new branch that starts from a given commit.
9. **`merge <target_branch> <source_branch>`**: Merges two branches together.
10. **`diff <commit_sha1> <commit_sha2>`**: Compares two commits and shows the difference between them.
11. **`clone <source_dir> <destination_dir>`**: Clones the repository (.git) from a source directory to a destination directory.
12. **`stage <file1> [<file2> ...]`**: Stages files to be committed.
13. **`checkout <branch_name>`**: Switches to the specified branch.
14. **`parent`**: Prints the SHA hash of the parent commit of the current HEAD.

In Git, there are three main types of objects used for storing data:

1. **Blobs**: Store the content of files.
2. **Trees**: Represent directory structures, including file names and permissions.
3. **Commits**: Represent changes made to the repository, including metadata like commit messages, authorship, and timestamps.

Each of these objects is identified by a **40-character SHA-1 hash**. Git objects are stored in the `.git/objects` directory, and the file path is derived from the hash.

### Example of a Git object hash:

e88f7a929cd70b0274c4ea33b209c97fa845fdbc


## Git Object Storage

Git objects are stored in the `.git/objects` directory. The path to each object is based on its SHA-1 hash:
- The first two characters of the hash form the directory.
- The remaining characters form the file name.

For example, an object with the hash `e88f7a929cd70b0274c4ea33b209c97fa845fdbc` would be stored at:
```
.git/objects/e8/8f7a929cd70b0274c4ea33b209c97fa845fdbc
```

## Blob Object Storage

A **Blob** is a Git object used to store the contents of a file. It contains a header with the size of the content and the content itself, which is compressed using Zlib. The format of a blob object looks like:

```
blob <size>\0<content>


Where:
- `<size>` is the size of the content in bytes.
- `\0` is a null byte.
- `<content>` is the actual content of the file.

For example, a file with the contents "hello world" will be stored as:

blob 11\0hello world
```

## cat-file Command

The `cat-file` command is used to read and display the contents of a blob object. When given a SHA-1 hash of a blob, it reads the corresponding file in the `.git/objects` directory, decompresses it using Zlib, and outputs the content.

To use the `cat-file` command:
1. Initialize a Git-like repository with the `init` command.
2. Insert a blob object into the `.git/objects` directory.
3. Run the `cat-file -p <blob_sha>` command to view the content.

Example:
```
$ ./your_program.sh init 
$ ./your_program.sh cat-file -p 256150983730c7b296403e4ee466cd885c6c56a9
```
## hash-object Command

The process includes:

Reading the file content.
Computing the SHA-1 hash of the file.
Storing the file in .git/objects using a specific format.
Zlib compression of the content before storage.
The hash-object command can be used as follows:

```
$ ./your_program.sh hash-object -w <file_path>
```

The program should read the content of the file, compute the SHA-1 hash, and store the file in the .git/objects directory. The output should be the SHA-1 hash of the file.

Here's the detailed explanation in Markdown format:

## Tree Object Structure

A **tree object** in Git-like systems is used to store a directory structure. Each entry in a tree object corresponds to either a file or a directory. These entries have the following components:

- **SHA Hash**: This points to either a blob (file object) or another tree (directory object).
    - If the entry is a file, it points to a **blob object**.
    - If the entry is a directory, it points to another **tree object**.
- **File/Directory Name**: The name of the file or directory.
- **Mode**: The mode represents the permissions of the file or directory in a simplified way, similar to Unix file permissions:
    - `100644` for a regular file.
    - `100755` for an executable file.
    - `120000` for a symbolic link.
    - `40000` for a directory.

### Example Directory Structure

For the following directory structure:

your_repo/ ├── file1 ├── dir1/ │ ├── file_in_dir_1 │ └── file_in_dir_2 └── dir2/ └── file_in_dir_3

The tree object would look like:

40000 dir1 <tree_sha_1> 40000 dir2 <tree_sha_2> 100644 file1 <blob_sha_1>

- Line 1 (`40000 dir1 <tree_sha_1>`) indicates that `dir1` is a directory, and `<tree_sha_1>` is the SHA hash of the tree object representing `dir1`.
- Line 2 (`40000 dir2 <tree_sha_2>`) indicates that `dir2` is a directory, and `<tree_sha_2>` is the SHA hash of the tree object representing `dir2`.
- Line 3 (`100644 file1 <blob_sha_1>`) indicates that `file1` is a regular file, and `<blob_sha_1>` is the SHA hash of the file content.

The `ls-tree` command is used to inspect a tree object and list the entries.

## The `ls-tree` Command

The `ls-tree` command in Git is used to list the contents of a tree object (directory). For a directory structure like this:

your_repo/ ├── file1 ├── dir1/ │ ├── file_in_dir_1 │ └── file_in_dir_2 └── dir2/ └── file_in_dir_3

Running `git ls-tree <tree_sha>` would output:

040000 tree <tree_sha_1> dir1 040000 tree <tree_sha_2> dir2 100644 blob <blob_sha_1> file1

Here:
- `040000 tree <tree_sha_1>    dir1`: Indicates that `dir1` is a directory.
- `100644 blob <blob_sha_1>    file1`: Indicates that `file1` is a regular file.

# `--name-only` Flag

When using the `--name-only` flag, Git outputs only the names of the files and directories in the tree, sorted alphabetically. For the above structure, the output would be:

dir1 dir2 file1

This simplified format is useful for testing, as it allows checking the structure without needing to examine the full details of each entry.

To implement the functionality of the `write-tree` and `ls-tree` commands, we need to store the directory structure as tree objects. Here is how the process works:

1. **Reading the Directory Structure**:
   - The files and directories in the working directory are read.
   - For each file, a corresponding **blob object** is created, and its SHA hash is computed.
   - For each directory, a **tree object** is created recursively for its contents.

2. **Storing the Tree Object**:
   - The tree object is written to the `.git/objects` directory in a compressed format (using zlib compression).
   - Each tree object is assigned a SHA-1 hash based on its contents.

3. **Creating the Tree Object**:
   - The `write-tree` command creates a tree object that represents the state of the working directory (staged files).
   - This tree object is stored in the `.git/objects` directory.

### `write-tree` Command

The `write-tree` command creates a tree object representing the current working directory. It outputs the SHA hash of the tree object. Here’s an example of the process:

1. **Create Files and Directories**:
   - `echo "hello world" > test.txt`
   - `mkdir test_dir_1`
   - `echo "hello world" > test_dir_1/test_file_2.txt`
   - `mkdir test_dir_2`
   - `echo "hello world" > test_dir_2/test_file_3.txt`

2. **Run the `write-tree` Command**:
   ```bash
   $ ./your_program.sh write-tree
   4b825dc642cb6eb9a060e54bf8d69288fbee4904
The SHA hash (4b825dc642cb6eb9a060e54bf8d69288fbee4904) is the unique identifier for the tree object created for this directory structure.
Implementing ls-tree --name-only
To implement the ls-tree --name-only command, follow these steps:
1.	Iterate Over the Entries in the Tree Object:
    o	For each entry, check if it's a file or a directory.
    o	If it's a file, the entry points to a blob object.
    o	If it's a directory, the entry points to another tree object.
2.	Output the Names:
    o	Output only the names of the directories and files.
    o	Sort the names alphabetically.
Example:
$ ./your_program.sh ls-tree --name-only <tree_sha>
    dir1
    dir2
    file1
    Tests
The following tests will verify that the implementation works as expected:

1.	Initialize a Git-like Repository:
2.	$ mkdir test_dir && cd test_dir
3.	$ /path/to/your_program.sh init
4.	Write a Tree Object: After creating files and directories, run the write-tree command to create a tree object:
5.	$ /path/to/your_program.sh write-tree
6.	4b825dc642cb6eb9a060e54bf8d69288fbee4904
7.	Run ls-tree --name-only:
8.	$ /path/to/your_program.sh ls-tree --name-only <tree_sha>
9.	dir1
10.	dir2
11.	file1
Make sure the output matches the expected SHA hash and file/directory names..

## Commit Object Structure

A **commit object** contains the following components:

- **Committer/Author Name**: The name of the person who made the commit.
- **Committer/Author Email**: The email address of the person who made the commit.
- **Timestamp**: The time when the commit was made.
- **Tree SHA**: The SHA-1 hash of the tree object representing the snapshot of the repository at the time of the commit.
- **Parent Commit SHA(s)**: The SHA-1 hash of the parent commit(s). If the commit is the first one, it has no parent.

### Example of a Commit Object

A commit object for a simple repository might look like this:

```
tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904 parent 3b18e512dba79e4c8300dd08aeb37f8e728b8dad author Harmony harmony@example.com 1616161616 +0000 committer Harmony harmony@example.com 1616161616 +0000 Initial commit
```

- **`tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904`**: Points to the SHA of the tree object that represents the directory structure at the time of the commit.
- **`parent 3b18e512dba79e4c8300dd08aeb37f8e728b8dad`**: Points to the SHA of the parent commit (if applicable). For the first commit, there will be no parent.
- **`author Harmony <harmony@example.com>`**: Indicates the author of the commit.
- **`committer Harmony <harmony@example.com>`**: Indicates who made the commit (could be the same as the author).
- **Timestamp**: The time when the commit was made (represented as a Unix timestamp).
- **Commit Message**: A message that describes the changes in this commit, such as `"Initial commit"`.

## The `commit-tree` Command

The `commit-tree` command creates a commit object and stores it in the `.git/objects` directory. It takes the following arguments:

- **`<tree_sha>`**: The SHA hash of the tree object that represents the directory structure for this commit.
- **`-p <commit_sha>`**: The parent commit's SHA hash. This is optional for the first commit, which does not have a parent.
- **`-m <message>`**: The commit message that describes the changes in this commit.

### Example Usage

```
1. **Initialize a Git-like Repository**:
   $ mkdir test_dir && cd test_dir
   $ git init
   Initialized empty Git repository in /path/to/test_dir/.git/
2.	Create a Tree Object: Create a file and add it to the staging area:
3.	$ echo "hello world" > test.txt
4.	$ git add test.txt
Then, create the tree object:
$ git write-tree
4b825dc642cb6eb9a060e54bf8d69288fbee4904
5.	Create the Initial Commit: Now, create the first commit:
6.	$ git commit-tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904 -m "Initial commit"
7.	3b18e512dba79e4c8300dd08aeb37f8e728b8dad
8.	Make Changes and Create a New Commit: Modify the file, stage the change, and create a new tree object:
9.	$ echo "hello world 2" > test.txt
10.	$ git add test.txt
11.	$ git write-tree
12.	5b825dc642cb6eb9a060e54bf8d69288fbee4904
Then, create the second commit:
$ git commit-tree 5b825dc642cb6eb9a060e54bf8d69288fbee4904 -p 3b18e512dba79e4c8300dd08aeb37f8e728b8dad -m "Second commit"
The output will be the SHA hash of the second commit object:
9b01f9e9c1d29c535ba7c9e3fe8a35a8504d2e4a
Example of commit-tree Command
$ ./your_program.sh commit-tree <tree_sha> -p <commit_sha> -m <message>
•	<tree_sha>: SHA hash of the tree object.
•	-p <commit_sha>: SHA hash of the parent commit (optional for the first commit).
•	-m <message>: The commit message describing the changes.
Output
    The program will output the 40-character SHA hash of the commit object that was created.
    Commit Object Creation Process
```

The process of creating a commit object includes the following steps:
1.	Get the Tree SHA: Obtain the SHA hash of the tree object that represents the state of the repository.
2.	Get Parent Commit SHA: If this is not the first commit, get the SHA hash of the parent commit.
3.	Create Commit Object: Construct the commit object in the following format: 
4.	tree <tree_sha>
5.	parent <parent_commit_sha>  # Optional for the first commit
6.	author <author_name> <author_email> <timestamp> +0000
7.	committer <committer_name> <committer_email> <timestamp> +0000
8.	<commit_message>
9.	Store the Commit Object: Write the commit object to the .git/objects directory, and compute its SHA hash.
10.	Output the SHA: Print the SHA hash of the commit object.
Tests
The program will be tested as follows:
```
1.	Initialize a New Git-like Repository:
    2.	$ mkdir test_dir && cd test_dir
    3.	$ ./your_program.sh init
4.	Create a Tree Object and Commit:
    o	Create a file, add it, and create a tree object.
    o	Run the commit-tree command to create the initial commit.
5.	$ echo "hello world" > test.txt
6.	$ git add test.txt
7.	$ git write-tree
8.	4b825dc642cb6eb9a060e54bf8d69288fbee4904
9.	$ ./your_program.sh commit-tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904  -p 0000000000000000000000000000000000000000 -m "Initial commit" #since -p is null or use parent command to get parentsha
10.	3b18e512dba79e4c8300dd08aeb37f8e728b8dad
11.	Create a Second Commit:
o	Modify the file, create a new tree object, and commit the changes:
12.	$ echo "hello world 2" > test.txt
13.	$ git add test.txt
14.	$ git write-tree
15.	5b825dc642cb6eb9a060e54bf8d69288fbee4904
16.	$ ./your_program.sh commit-tree 5b825dc642cb6eb9a060e54bf8d69288fbee4904 -p 3b18e512dba79e4c8300dd08aeb37f8e728b8dad -m "Second commit"
17.	9b01f9e9c1d29c535ba7c9e3fe8a35a8504d2e4a
```

## How to Use

1. Clone the repository and navigate to the project directory:
    ```
    git clone <repository_url>
    cd <repository_name>
    ```

2. Initialize the repository:
    ```
    python3 main.py init  # Initializes the Git-like repository structure
    ```

3. Read the content of a Blob:
    ```
    python3 main.py cat-file -p <blob_sha>  # Reads and displays the content of the specified blob
    ```

## Issues

1. The checkout function switches branches but deletes the current branch files

# Questions
**What do you love most about computing?**
Computing gives you access to the world and so much information. Information that if used and researched on can be of benefit to many in the world. Computing offers a platform for a everyone to see and expereince your product in a short amount of time, thus you can change the world in an instant

**If you could meet any scientist or engineer who died before A.D. 2000, whom would you choose, and why?**

Isaac Newton
Newtons works opened up the world to science and led to the developemnt of calculus. His work changed the world. Everything today from computing to going to the moon to AI it was becuase of the foundations he laid in mathematics and physics