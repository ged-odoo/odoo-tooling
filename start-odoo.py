#!/usr/bin/env python3

import subprocess
import sys
import argparse

DB_NAME = "testdb"
DB_USER = "odoo"
DB_PASSWORD = "odoo"
ODOO_BIN_CMD = "source env15/bin/activate;cd community;./odoo-bin"

# https://www.geeksforgeeks.org/print-colors-python-terminal/
COLOR_MAP = {"red": 91, "cyan": 96, "yellow": 93}


def color(string: str, col: str) -> str:
    """
    return the input string wrapped in ansi color code corresponding to 'col'
    """
    return f"\033[{COLOR_MAP[col]}m{string}\033[00m"


def _run_command(command, cwd="./"):
    return (
        subprocess.run(command, cwd=cwd, capture_output=True, check=True)
        .stdout.decode()
        .rstrip("\n")
    )


def get_db_version():
    run_query = lambda q: _run_command((["psql", DB_NAME, "-c", q]))
    version_query = "SELECT latest_version FROM ir_module_module WHERE name='base'"
    enterprise_query = "SELECT license from ir_module_module where name='web_enterprise' and state='installed'"
    try:
        result_line = run_query(version_query).split()[2]
        db_version = ".".join(result_line.split(".")[:2])
        is_enterprise = "1 row" in run_query(enterprise_query)
        if is_enterprise:
            db_version = db_version + " (enterprise)"
        return db_version
    except:
        return "?"


def read_git_branch(cwd: str, with_status=False) -> str:
    """
    Return current git branch in working directory
    """
    branch_name = _run_command(["git", "branch", "--show-current"], cwd)
    if with_status:
        is_dirty = _run_command(["git", "status", "--porcelain"], cwd) != ""
        if is_dirty:
            branch_name = branch_name + " (*)"

    return branch_name


def start_odoo(args: str):
    """
    start a odoo server with the corresponding addons path and args
    """
    subprocess.call(f"{ODOO_BIN_CMD} {args}", shell=True, executable="/bin/bash")


def show_status():
    sys.path.append("community/odoo")
    import release

    community_branch = read_git_branch("community", with_status=True)
    enterprise_branch = read_git_branch("enterprise", with_status=True)
    print("{:<18} {}".format("Odoo server:", release.version))
    print("{:<18} {}".format(f"{DB_NAME} version:", get_db_version()))
    print("{:<18} {}".format("Community branch:", community_branch))
    print("{:<18} {}".format("Enterprise branch:", enterprise_branch))


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------


def main():
    # Step 1: processing args
    args = sys.argv[1:]
    odoo_args = []

    for i, val in enumerate(args):
        if val == "--":
            odoo_args = args[i + 1 :]
            args = args[:i]

    parser = argparse.ArgumentParser(description="GED odoo commander script")
    parser.add_argument(
        "-e", "--enterprise", help="activate enterprise addons", action="store_true"
    )
    parser.add_argument("-t", "--test", help="run tests", action="store_true")
    parser.add_argument("-d", "--drop-db", help="drop test db", action="store_true")
    parser.add_argument(
        "-w", "--web", help="run web test suite (implies --test)", action="store_true"
    )
    parser.add_argument(
        "-s",
        "--status",
        help="show Odoo version and current branches",
        action="store_true",
    )
    config = parser.parse_args(args)
    if config.web:
        config.test = True

    if config.status:
        show_status()
        quit()

    if config.drop_db:
        _run_command(["dropdb", DB_NAME])

    # Step 2: sanity check: do enterprise and community branch match?
    if config.enterprise:
        community_branch = read_git_branch("community")
        enterprise_branch = read_git_branch("enterprise")

        if community_branch != enterprise_branch:
            print(
                color("Warning:", "yellow"),
                "community and enterprise branches do not match:",
                color(community_branch, "cyan"),
                "!=",
                color(enterprise_branch, "cyan"),
            )
            should_continue = input("do you want to continue? (y/N) ") == "y"
            if not should_continue:
                quit()

    # Step 3: another check: error if db does not match enterprise config
    is_db_enterprise = "enterprise" in get_db_version()
    if not config.drop_db and is_db_enterprise != config.enterprise:
        msg = (
            "Error: no enterprise addons requested, but current db is enterprise"
            if is_db_enterprise
            else "Error: enterprise addons requested, but current db is not enterprise"
        )
        print(color(msg, "red"))
        quit()

    # Step 4: start odoo server
    addons_path = "addons,../enterprise" if config.enterprise else "addons"
    base_args = f"-r {DB_USER} -w {DB_PASSWORD} -d {DB_NAME} --db-filter={DB_NAME} --dev=all --addons-path {addons_path} "

    if config.test:
        test_args = " --test-enable --stop-after-init "
        if config.web:
            test_args = test_args + "--test-tags /web:WebSuite "
        start_odoo(base_args + test_args + " ".join(odoo_args))
    else:
        start_odoo(base_args + " " + " ".join(odoo_args))


if __name__ == "__main__":
    main()
