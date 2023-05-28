import re
import sys

def get_solc_version_list():
    with open('solc_list.txt', 'r') as f:
        version_list = f.read().splitlines()
    return version_list

def extract_solidity_version(file_path):
    try:
        with open(file_path, 'r') as file:
            source_code = file.read()
        
        pattern = r"pragma solidity\s+(.*?);"
        match = re.search(pattern, source_code)
        if match:
            version_with_condition = match.group(1)
            version_pattern = r"(\^|=|~|>=|<=|>|<)?\s*([0-9]+\.[0-9]+(\.[0-9]+)?)"
            version_match = re.search(version_pattern, version_with_condition)
            if version_match:
                condition = version_match.group(1)
                version = version_match.group(2)
                return condition, version.strip()
        
        return None, None
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)


def find_matching_index(versions, version_list):
    for i, v in enumerate(version_list):
        if versions == v:
            return i
    return None


def select_version(solidity_file_path):
    condition, versions = extract_solidity_version(solidity_file_path)
    version_list = get_solc_version_list()
    index = find_matching_index(versions, version_list)
    if condition == None or condition == "=" or condition == "<=" or condition == ">=":
       version = versions
    elif condition == "<":
        version = version_list[index+1]
    elif condition == ">":
        version = version_list[index-1]
    else:
        print("Error: Condition Error")
        sys.exit(1)
    
    return version, condition


if len(sys.argv) < 2:
    print("Error: Solidity file path not provided.")
    sys.exit(1)

solidity_file_path = sys.argv[1]
v, c = select_version(solidity_file_path)
print("version :", v)
print("condition :", c)

