
"""
Download data file from a remote server. The data file can be complete or can be split
into multiple pieces using the 'split' Unix command, and this state is taken into
account when processing the downloaded file.
"""

import argparse
import urllib.request
import urllib.error
import os
import hashlib
import sys


BLOCK_SIZE = 8192


def parse_args() -> argparse.Namespace:
    """
    Parse the command line arguments and return a data structure with argument data.

    Returns
    -------
        argparse.Namespace object holding attributes corresponding to arguments
    """

    parser = argparse.ArgumentParser(description="Download data file for EFI KBase app")
    parser.add_argument("--remote-dir", required=True, type=str, help="URL of the directory in which the file resides")
    parser.add_argument("--remote-file", required=True, type=str, help="Name of the file on the remote to download")
    parser.add_argument("--local-dir", required=True, type=str, help="Path to local directory where file will be unpacked")
    parser.add_argument("--local-file", required=True, type=str, help="Path to file on local system where download file is placed")
    args = parser.parse_args()
    return args


def get_remote_file_contents(remote_file: str) -> str:
    """
    Download the file as a string and return file contents to user.

    Parameters
    ----------
        remote_file
            complete URL for a file

    Returns
    -------
        UTF-8 string containing file contents if successful retrieval; False otherwise
    """

    try:
        response = urllib.request.urlopen(remote_file)
    except urllib.error.HTTPError as e:
        print(f"Unable to urlopen {remote_file}: {e}")
        return False
    file_contents = response.read()
    file_contents = str(file_contents.decode('utf-8'))
    return file_contents


def get_file_list(remote_dir: str, remote_file: str) -> tuple[list, dict]:
    """
    Retrieve a list of files created by 'split' on the remote that need to be fetched.
    If a file 'remote_dir/remote_file.file_list' is present on the server, that means
    that the file has been split and a list of the split files is returned.  If there
    is no file ending in '.file_list' then an empty list is returned.  '.file_list'
    is assumed to be the output of the 'md5sum' program used to generate hashes for
    verification of file integrity.

    Parameters
    ----------
        remote_dir
            URL of directory on remote that contains files
        remote_file
            name of the file on the remote to download

    Returns
    -------
        files
            list of file names (not URL) on remote that are split
        checksums
            checksum (MD5) for each file on the remote
    """

    remote_file = remote_dir + "/" + remote_file + ".file_list"

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


def get_remote_checksum(remote_dir: str, remote_file: str) -> str:
    """
    Return the MD5 hash from the MD5 file corresponding to the remote file (not split).

    Parameters:
        remote_dir
            URL of directory on remote that contains files
        remote_file
            name of the file on the remote to download

    Returns
    -------
        MD5 hash of the remote file
    """
    remote_file = remote_dir + "/" + remote_file + ".md5"

    file_contents = get_remote_file_contents(remote_file)
    if not file_contents:
        return ""

    parts = file_contents.split(" ")
    if parts[0]:
        return parts[0]
    else:
        return ""


def download_file(url: str, dest_file: str) -> bool:
    """ 
    Download a file from the remote and save it to the specified local file.

    Parameters:
        url
            URL of the remote file
        dest_file
            local path to store downloaded file to
    """

    try:
        u = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print(f"Unable to urlopen {url}: {e}")
        return False

    with open(dest_file, "wb") as f:
        while True:
            buffer = u.read(BLOCK_SIZE)
            if not buffer:
                break
            f.write(buffer)

    return True


def calculate_md5(file_path: str) -> str:
    """
    Calculate the MD5 hash for the file specified by the path.

    Parameters
    ----------
        file_path
            path to a file on the local file system

    Returns
    -------
        MD5 hash of the file
    """

    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as fh:
        while chunk := fh.read(BLOCK_SIZE):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def compare_md5(remote_md5: str, local_md5: str) -> str:
    """
    Compare two checksums.

    Parameters
    ----------
        remote_md5
            hash computed remotely of the remote file by md5sum 
        local_md5
            hash computed locally of local file by md5sum 
    """
    if remote_md5 != local_md5:
        print(f"Remote MD5 {remote_md5} doesn't match local MD5 {local_md5}")
        return False
    else:
        return True




if __name__ == '__main__':

    args = parse_args()

    if not os.path.isdir(args.local_dir):
        os.mkdir(args.local_dir)

    # Check if the remote file is actually a collection of files that were split up
    file_list, checksums = get_file_list(args.remote_dir, args.remote_file)

    # If the remote was split, then download all of the split files
    if len(file_list) > 0:
        temp_files = []
        for fname in file_list:
            temp_local_file = os.path.join(args.local_dir, fname)
            temp_files.append(temp_local_file)
            remote_url = args.remote_dir + "/" + fname

            print(f"Downloading {remote_url}")
            if not download_file(remote_url, temp_local_file):
                print(f"Unable to download {remote_url} to {temp_local_file}")
                sys.exit(1)

            local_md5 = calculate_md5(temp_local_file)
            if not compare_md5(checksums[fname], local_md5):
                print(f"File {fname} was not downloaded correctly from {remote_url}; checksums do not match")
                sys.exit(1)

        # Concatenate all of the files that were downloaded into one file
        with open(args.local_file, "wb") as merged:
            for fname in temp_files:
                with open(fname, "rb") as fh:
                    while chunk := fh.read(BLOCK_SIZE):
                        merged.write(chunk)

    else:
        remote_url = args.remote_dir + "/" + args.remote_file

        print(f"Downloading {remote_url}")
        if not download_file(remote_url, args.local_file):
            print(f"Unable to download {remote_url} to {args.local_file}")
            sys.exit(1)

        remote_md5 = get_remote_checksum(args)
        local_md5 = calculate_md5(args.local_file)
        if not compare_md5(remote_md5, local_md5):
            print(f"File {args.local_file} was not downloaded correctly from {remote_url}; checksums do not match")
            sys.exit(1)

