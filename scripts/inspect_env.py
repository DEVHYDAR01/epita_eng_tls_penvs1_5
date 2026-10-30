# scripts/inspect_env.py
import sys
import os

def print_section(title, data):
    print(f"\n=== {title} ===")
    if isinstance(data, list):
        for item in data:
            print(f"  - {item}")
    else:
        print(f"  {data}")

if __name__ == "__main__":
    print_section("OS Executable Path ($PATH)", os.environ.get("PATH", "").split(os.pathsep)[:4])
    print_section("Active Python Binary (sys.executable)", sys.executable)
    print_section("Python Version", sys.version.split()[0])
    print_section("Virtual Env Prefix (sys.prefix)", sys.prefix)
    print_section("Base Prefix (sys.base_prefix)", sys.base_prefix)
    print_section("Is in Virtual Environment?", sys.prefix != sys.base_prefix)
    print_section("Search Paths for Imports (sys.path)", sys.path[:5])
