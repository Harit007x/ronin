import os
import subprocess


def read_file(path):
    with open(path, "r") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)
    return "file written"


def list_files(path="."):
    return os.listdir(path)


def run_command(cmd):

    blocked = ["rm -rf", "shutdown", "reboot"]

    if any(b in cmd for b in blocked):
        return "blocked command"

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True
    )

    return result.stdout.decode()


TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "run_command": run_command
}