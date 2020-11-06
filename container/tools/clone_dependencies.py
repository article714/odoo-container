#!/usr/bin/env python
"""
 This file is an updated version of the following one:
      https://github.com/OCA/maintainer-quality-tools/blob/master/travis/clone_oca_dependencies

 Credits: OCA <https://odoo-community.org/>

Usage: clone_dependencies <default_branch> <dir>
Arguments:

dir: the directory in which the dependency repositories will be cloned
default_branch: the default branch to clone

The program will process the file module_dependencies.txt at the root of the
tested repository, and clone the dependency repositories in checkout_dir,
before recursively processing the oca_dependencies.txt files of the
dependencies.
The expected format for module_dependencies.txt:
* comment lines start with # and are ignored
* a dependency line contains:
  - the name of the project
  - the URL to the git repository (defaulting to the OCA repository)
  - (optional) the name of the branch to use (defaulting to ${VERSION})
"""
import sys
import os
import os.path as osp
import subprocess
import logging


_logger = logging.getLogger()
FORMAT = "%(asctime)-15s [%(levelname)s] %(message)s"
logging.basicConfig(format=FORMAT)


def parse_depfile(depfile, owner="OCA", default_branch="12.0"):
    deps = []
    for line in depfile:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        repo = parts[0]
        if len(parts) > 2:
            branch = parts[2]
        else:
            branch = default_branch
        if len(parts) > 1:
            url = parts[1]
        else:
            url = "https://github.com/%s/%s.git" % (owner, repo)
        deps.append((repo, url, branch))
    return deps


def git_checkout(deps_checkout_dir, reponame, url, branch):
    checkout_dir = osp.join(deps_checkout_dir, reponame)
    if not osp.isdir(checkout_dir):
        command = [
            "git",
            "clone",
            "-q",
            url,
            "-b",
            branch,
            "--single-branch",
            "--depth=1",
            checkout_dir,
        ]
        _logger.info("Calling %s", " ".join(command))
        subprocess.check_call(command)
        command = [
            "git",
            "--git-dir=" + os.path.join(checkout_dir, ".git"),
            "--work-tree=" + checkout_dir,
            "config",
            "--replace-all",
            "remote.origin.fetch",
            "+refs/heads/*:refs/remotes/origin/*",
        ]
        subprocess.check_call(command)

    else:

        command = [
            "git",
            "--git-dir=" + os.path.join(checkout_dir, ".git"),
            "--work-tree=" + checkout_dir,
            "fetch",
            "origin",
            branch,
        ]
        _logger.info("Calling %s", " ".join(command))
        subprocess.check_call(command)
        command = [
            "git",
            "--git-dir=" + os.path.join(checkout_dir, ".git"),
            "--work-tree=" + checkout_dir,
            "reset",
            "--hard",
            branch,
        ]
        _logger.info("Calling %s", " ".join(command))
        subprocess.check_call(command)
        command = [
            "git",
            "--git-dir=" + os.path.join(checkout_dir, ".git"),
            "--work-tree=" + checkout_dir,
            "clean",
            "-d",
            "-f",
            branch,
        ]
        _logger.info("Calling %s", " ".join(command))
        subprocess.check_call(command)
        command = [
            "git",
            "--git-dir=" + os.path.join(checkout_dir, ".git"),
            "--work-tree=" + checkout_dir,
            "checkout",
            branch,
        ]
        _logger.info("Calling %s", " ".join(command))
        subprocess.check_call(command)
        command = [
            "git",
            "--git-dir=" + os.path.join(checkout_dir, ".git"),
            "--work-tree=" + checkout_dir,
            "merge",
            "origin/%s" % branch,
        ]
        subprocess.check_call(command)
    return checkout_dir


def run(deps_checkout_dir, deps_default_branch):
    dependencies = [
        "modules_dependencies.txt",
        "oca_dependencies.txt",
        "a714_dependencies.txt",
    ]
    processed = set()
    reqfilenames = []
    if osp.isfile("requirements.txt"):
        reqfilenames.append("requirements.txt")
    for repo in os.listdir(deps_checkout_dir):
        _logger.info("examining %s", repo)
        depfilename = osp.join(deps_checkout_dir, repo, "oca_dependencies.txt")
        dependencies.append(depfilename)
        reqfilename = osp.join(deps_checkout_dir, repo, "requirements.txt")
        if osp.isfile(reqfilename):
            reqfilenames.append(reqfilename)
    for depfilename in dependencies:
        try:
            with open(depfilename) as depfile:
                deps = parse_depfile(depfile, default_branch=deps_default_branch)
        except IOError:
            deps = []
        for depname, url, branch in deps:
            if depname in processed:
                continue
            _logger.info("* processing %s", depname)
            processed.add(depname)
            checkout_dir = git_checkout(deps_checkout_dir, depname, url, branch)
            new_dep_filename = osp.join(checkout_dir, "oca_dependencies.txt")
            reqfilename = osp.join(checkout_dir, "requirements.txt")
            if osp.isfile(reqfilename):
                reqfilenames.append(reqfilename)
            if new_dep_filename not in dependencies:
                dependencies.append(new_dep_filename)
    for reqfilename in reqfilenames:
        command = ["pip3", "install", "--no-binary", "pycparser", "-Ur", reqfilename]
        _logger.info("Calling %s", " ".join(command))
        subprocess.check_call(command)


if __name__ == "__main__":
    _logger.setLevel(logging.WARNING)
    if len(sys.argv) < 3:
        deps_checkout_dir = osp.join(os.environ["HOME"], "dependencies")
        deps_default_branch = "12.0"
        if not osp.exists(deps_checkout_dir):
            os.makedirs(deps_checkout_dir)
    elif len(sys.argv) > 3:
        print(__doc__)
        sys.exit(1)
    else:
        deps_checkout_dir = sys.argv[1]
        deps_default_branch = sys.argv[2]
    run(deps_checkout_dir, deps_default_branch)
