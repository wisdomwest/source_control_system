import sys
import os
import zlib
import hashlib  # Import hashlib for SHA-1 hashing

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

def main():
    print("Logs from your program will appear here!", file=sys.stderr)

    if len(sys.argv) < 2:
        raise RuntimeError("No command provided")

    command = sys.argv[1]

    if command == "init":
        # Initialize the git directory structure
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
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
    else:
        raise RuntimeError(f"Unknown command #{command}")

if __name__ == "__main__":
    main()
