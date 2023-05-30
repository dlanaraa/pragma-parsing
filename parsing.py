import re
import sys
import os
import subprocess
import solcx
import platform
from pyparsing import Word, Optional, Regex, Combine, Literal

def get_solc_version_list():
    with open('solc_list.txt', 'r') as f:
        version_list = f.read().splitlines()
    return version_list

def extract_pragma(solidity_code):
    lt = Word("<")
    gtr = Word(">")
    eq = Word("=")
    tilde = Word("~")
    carrot = Word("^")
    inequality = Optional(
        eq | (Combine(gtr + Optional(eq)) | Combine(lt + Optional(eq)))
    )

    ver1 = Regex(r"\s*[0-9]+\s*\.\s*[0-9]+\s*\.\s*[0-9]+")
    ver2 = Regex(r"\s*0\.[0-9]+(\.[0-9]+)?")

    version1 = Optional(carrot | tilde | inequality) + (ver1 | ver2)
    version2 = Optional(carrot | tilde | inequality) + Optional(ver1 | ver2)
    pragma = Word("pragma") + Word("solidity") + version1 + Optional(version2)

    result = pragma.parseString(solidity_code)

    return {
        "con1" : result[2] if len(result) > 3 else None,
        "ver1" : result[3] if len(result) > 3 else result[2],
        "con2" : result[4] if len(result) > 4 else None,
        "ver2" : result[5] if len(result) > 4 else None,
    }


def extract_version(file_path):
    try:
        with open(file_path, 'r') as file:
            source_code = file.read()
        
        if source_code is None:
            return None
        version_line = None

        for line in source_code.split("\n"):
            if "pragma solidity" not in line:
                continue
            version_line = line.rstrip()
            break
        if version_line is None:
            return None

        assert "pragma solidity" in version_line
        if version_line[-1] == ";":
            version_line = version_line[:-1]
        version_line = version_line[version_line.find("pragma") :]
        return(version_line)


    except FileNotFoundError:
        print(f"Error: File '{file}' not found.")
        sys.exit(1)


def select_version(solidity_file_path):
    pragma = extract_version(solidity_file_path)
    print("[INPUT]", pragma)
    pragma_dict = extract_pragma(pragma)

    con1 = pragma_dict.get("con1", None)
    ver1 = pragma_dict.get("ver1", None)
    con2 = pragma_dict.get("con2", None)
    ver2 = pragma_dict.get("ver2", None)
    
    if con2 is not None:
        if ver1 < ver2:
            condition = con1
            version = ver1
        else: 
            condition = con2
            version = ver2
    else: 
        condition = con1
        version = ver1

    version_list = get_solc_version_list()
    index = find_matching_index(version, version_list)

    if condition == None or condition == "=" or condition == "<=" or condition == ">=":
        ver = version
    elif condition == "<":
        ver = version_list[index+1]
    elif condition == ">":
        ver = version_list[index-1]
    elif condition == "^" or condition == "~":
        matching_versions = []
        target_major_minor = '.'.join(version.split('.')[:2])
        for v in version_list:
            if v.startswith(target_major_minor):
                matching_versions.append(v)
        ver = matching_versions[0]

    else:
        print("error")

    print("[OUTPUT]", ver)

    return ver
    

def find_matching_index(versions, version_list):
    for i, v in enumerate(version_list):
        if versions == v:
            return i
    return None


def install_solc(version):
    solc_installed_versions = solcx.get_installed_solc_versions()

    if version in solc_installed_versions:
        print(f"Solc v{version} is already installed.")
        solcx.set_solc_version(version)
    
    solcx.install_solc(version)
    solcx.set_solc_version(version)
    
    get_solc_ver = solcx.get_solc_version()

    return get_solc_ver
    
    
if len(sys.argv) < 2:
    print("Error: Solidity file path not provided.")
    sys.exit(1)

solidity_file_path = sys.argv[1]

version = select_version(solidity_file_path)
ret = install_solc(version)