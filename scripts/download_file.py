
import argparse
import urllib.request
import urllib.error
import os
import hashlib
import sys


parser = argparse.ArgumentParser(description="Download data file for EFI KBase app")
parser.add_argument("--remote-dir", required=True, type=str, help="URL of the directory in which the file resides")
parser.add_argument("--remote-file", required=True, type=str, help="Name of the file on the remote to download")
parser.add_argument("--local-dir", required=True, type=str, help="Path to local directory where file will be unpacked")
parser.add_argument("--local-file", required=True, type=str, help="Path to file on local system where download file is placed")
args = parser.parse_args()


if not os.path.isdir(args.local_dir):
    os.mkdir(args.local_dir)






def get_remote_file_contents(remote_file):
    """
    Downloads the file as a string and return to user; if HTTP error then returns False
    """
    try:
        response = urllib.request.urlopen(remote_file)
    except urllib.error.HTTPError as e:
        return False
    file_contents = response.read()
    file_contents = str(file_contents.decode('utf-8'))
    return file_contents


def get_file_list(args):
    """
    Retrieves a list of files on the remote that need to be fetched
    """
    remote_file = args.remote_dir + "/" + args.remote_file + ".file_list"

    file_contents = get_remote_file_contents(remote_file)
    if not file_contents:
        return [], {} 

    lines = file_contents.splitlines()
    checksums = {}
    files = []
    for line in lines:
        parts = line.split(" *")
        files.append(parts[1])
        checksums[parts[1]] = parts[0]

    return files, checksums


def get_remote_checksum(args):
    """
    Return the MD5 hash from the MD5 file corresponding to the remote file
    """
    remote_file = args.remote_dir + "/" + args.remote_file + ".md5"

    file_contents = get_remote_file_contents(remote_file)
    if not file_contents:
        return False

    parts = file_contents.split(" ")
    if parts[0]:
        return parts[0]
    else:
        return False


def download_file(url, dest_file):
    """ 
    Download and save a file specified by url to the destination file
    """
    u = urllib.request.urlopen(url)

    with open(dest_file, "wb") as f:
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            f.write(buffer)


def calculate_md5(file_path):
    """
    Calculate the MD5 hash for the given file_path
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def compare_md5(remote_md5, local_md5):
    """
    String comparison of local and remote MD5 checksums
    """
    if remote_md5 != local_md5:
        print(f"Remote MD5 {remote_md5} doesn't match local MD5 {local_md5}\n")
        return False
    else:
        return True





file_list, checksums = get_file_list(args)

if len(file_list) > 0:
    temp_files = []
    for fname in file_list:
        temp_local_file = os.path.join(args.local_dir, fname)
        temp_files.append(temp_local_file)
        remote_url = args.remote_dir + "/" + fname

        #TODO: error check
        download_file(remote_url, temp_local_file)
        local_md5 = calculate_md5(temp_local_file)
        if not compare_md5(checksums[fname], local_md5):
            print(f"File {fname} was not downloaded correctly; checksums do not match\n")
            sys.exit(1)

    with open(args.local_file, "wb") as afh:
        for fname in temp_files:
            with open(fname, "rb") as fh:
                for chunk in iter(lambda: fh.read(4096), b""):
                    afh.write(chunk)

    remote_md5 = get_remote_checksum(args)
    local_md5 = calculate_md5(args.local_file)

else:
    remote_url = args.remote_dir + "/" + args.remote_file
    download_file(remote_url, args.local_file)
    remote_md5 = get_remote_checksum(args)
    local_md5 = calculate_md5(args.local_file)
    if not compare_md5(remote_md5, local_md5):
        print(f"File {remote_url} -> {args.local_file} was not downloaded correctly; checksums do not match\n")
        sys.exit(1)

