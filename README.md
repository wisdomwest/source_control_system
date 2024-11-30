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
