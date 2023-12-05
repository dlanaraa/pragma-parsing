import re
import sys
import os
import requests
import json
from pyparsing import Word, Optional, Regex, Path
from pathlib import Path

class PragmaParser:
    def __init__(self):
        self.SOLCX_BINARY_PATH_VARIABLE = "SOLCX_BINARY_PATH"
        self.BINARY_DOWNLOAD_BASE = "https://solc-bin.ethereum.org/{}-amd64/{}"
        self.SOURCE_DOWNLOAD_BASE = "https://github.com/ethereum/solidity/releases/download/v{}/{}"

    def get_solc_version_list(self):
        url = f"https://binaries.soliditylang.org/macosx-amd64/list.json"
        list_json = requests.get(url).content
        solc_version_list = json.loads(list_json)["releases"]
        return solc_version_list

    def extract_pragma(self, solidity_code):
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

    def extract_version(self, file_path):
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

    def select_version(self, solidity_file_path):
        pragma = self.extract_version(solidity_file_path)
        pragma_result = self.extract_pragma(pragma)

        condition1 = pragma_result["condition1"]
        version1 = pragma_result["version1"]
        condition2 = pragma_result["condition2"]
        version2 = pragma_result["version2"]

        version_list = self.get_solc_version_list()
        index = self.find_matching_index(version1, version_list)

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
        
    def find_matching_index(self, versions, version_list):
        for i, v in enumerate(version_list):
            if versions == v:
                return i
        return None

    def get_installed_solcx_folder(self):
        if os.getenv(self.SOLCX_BINARY_PATH_VARIABLE):
            return Path(os.environ[self.SOLCX_BINARY_PATH_VARIABLE])
        else:
            path = Path.home().joinpath(".solc-select")
            path.mkdir(exist_ok=True)
            return path

    def get_installed_solc_versions(self):
        solc_select_path = self.get_installed_solcx_folder().joinpath("artifacts")
        versions = [path.name for path in solc_select_path.glob("solc-*")]
        return sorted(versions, key=lambda s: tuple(map(int, s.split("-")[1].split("."))), reverse=True)

    def install_solc(self, version):
        installed_versions = self.get_installed_solc_versions()

        if "solc-"+version not in installed_versions:
            print(version)
            sys.exit(0)
            cmd = f"solc-select install {version}"
            os.system(cmd)

        cmd = f"solc-select use {version}"
        os.system(cmd)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Solidity file path not provided.")
        sys.exit(1)

    solidity_file_path = sys.argv[1]

    pragma_parser = PragmaParser()
    version = pragma_parser.select_version(solidity_file_path)
    pragma_parser.install_solc(version)
