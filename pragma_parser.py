import re
import sys
import os
import requests
import json
from pyparsing import Word, Optional, Regex, Path

from pathlib import Path

SOLCX_BINARY_PATH_VARIABLE = "SOLCX_BINARY_PATH"
BINARY_DOWNLOAD_BASE = "https://solc-bin.ethereum.org/{}-amd64/{}"
SOURCE_DOWNLOAD_BASE = "https://github.com/ethereum/solidity/releases/download/v{}/{}"

def get_solc_version_list():
    url = f"https://binaries.soliditylang.org/macosx-amd64/list.json"
    list_json = requests.get(url).content
    solc_version_list = json.loads(list_json)["releases"]
    return solc_version_list

def extract_pragma(solidity_code):
    version_pattern = (
        Word("pragma")
        + Word("solidity")
        + (
            Optional(Word("^~<=>")) + (Regex(r"\d+\.\d+\.\d+") | Regex(r"0\.\d+(\.\d+)?"))
        )
        + Optional(
            Optional(Word("^~<=>")) + (Regex(r"\d+\.\d+\.\d+") | Regex(r"0\.\d+(\.\d+)?"))
        )
    )

    result = version_pattern.parseString(solidity_code)

    return {
        "condition1": result[2] if len(result) > 3 else None,
        "version1": result[3] if len(result) > 3 else result[2],
        "condition2": result[4] if len(result) > 4 else None,
        "version2": result[5] if len(result) > 4 else None,
    }


def extract_version(file_path):
    try:
        with open(file_path, 'r') as file:
            source_code = file.read()
        
        if source_code is None:
            return None

        pattern = r"pragma solidity\s*(.*?);"
        version_match = re.search(pattern, source_code)
        
        if version_match:
            version_line = version_match.group(0)
            return version_line

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None


def select_version(solidity_file_path):
    pragma = extract_version(solidity_file_path)
    pragma_result = extract_pragma(pragma)

    condition1 = pragma_result["condition1"]
    version1 = pragma_result["version1"]
    condition2 = pragma_result["condition2"]
    version2 = pragma_result["version2"]

    version_list = get_solc_version_list()
    index = find_matching_index(version1, version_list)

    if condition2 is not None:
        condition, version = (condition1, version1) if version1 < version2 else (condition2, version2)
    else:
        condition, version = condition1, version1

    if condition in (None, "=", "<=", ">="):
        return version
    elif condition == "<":
        return version_list[index + 1]
    elif condition == ">":
        return version_list[index - 1]
    elif condition in ("^", "~"):
        target_major_minor = '.'.join(version.split('.')[:2])
        matching_versions = [v for v in version_list if v.startswith(target_major_minor)]
        return matching_versions[0]
    else:
        print("Error: Invalid condition")
        return None
    

def find_matching_index(versions, version_list):
    for i, v in enumerate(version_list):
        if versions == v:
            return i
    return None


def get_installed_solcx_folder():
    if os.getenv(SOLCX_BINARY_PATH_VARIABLE):
        return Path(os.environ[SOLCX_BINARY_PATH_VARIABLE])
    else:
        path = Path.home().joinpath(".solcx")
        path.mkdir(exist_ok=True)
        return path

def get_installed_solc_versions(solcx_binary_path):
    versions = sorted(solcx_binary_path.glob("solc-v*"), reverse=True)
    versions = [i.name.split("v")[1] for i in versions]
    versions.sort(key=lambda s: tuple(map(int, s.split('.'))), reverse=True)
    return versions

def install_solc(version, solcx_binary_path=None):
    solcx_binary_path = solcx_binary_path or get_installed_solcx_folder()
    solc_installed_versions = get_installed_solc_versions(solcx_binary_path)

    if version not in solc_installed_versions:       
        print(f"Installing solc v{version}.")
        cmd = f"solc-select install {version}"
        os.system(cmd)

        print(f"Solc v{version} installed successfully.")

    print(f"Set solc v{version}.")
    cmd = f"solc-select use {version}"
    os.system(cmd)
    

# main
if len(sys.argv) < 2:
    print("Error: Solidity file path not provided.")
    sys.exit(1)

solidity_file_path = sys.argv[1]

version = select_version(solidity_file_path)
install_solc(version)