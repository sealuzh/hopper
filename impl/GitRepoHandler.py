import os
from subprocess import call, check_output
import pygit2
import re

class GitRepoHandler:
    """ This represents a Git repo, and can be used to check out specific versions, or ask
    questions such as 'which commits are between those two dates?' or 'Is this a code change
    (following our heuristics)?'.
    This internally uses a combination of pygit2 and direct calls of the git cmd interface,
    mostly for convenience.
    """

    GIT = "git"
    GIT_REVLIST_CMD = "rev-list"
    GIT_CHECKOUT_CMD = "checkout"
    GIT_RESET_CMD = ["reset", "--hard"]

    PRODUCTION_CODE_DIRS = ['src/main/java', 'pom.xml']
    JAVADOC = '(^\s*\*)|(^\s*/\*\*)|(^\s*$)'

    def __init__(self, repo_path):
        self.repo_path = repo_path
        os.chdir(repo_path)
        self.pygit_repo = pygit2.Repository('.git')

    @staticmethod
    def is_code_change(diff):
        return GitRepoHandler.is_code_file(diff) and not GitRepoHandler.is_javadoc_change(diff)

    @staticmethod
    def is_code_file(diff):
        for patch in diff:
            for codedir in GitRepoHandler.PRODUCTION_CODE_DIRS:
                if re.search(codedir, patch.delta.new_file.path):
                    return True
        return False

    @staticmethod
    def is_javadoc_change(diff):
        # we'll call it a Javadoc change if all added or removed lines start with either /** or *, or are purely whitespace
        for patch in diff:
            for hunk in patch.hunks:
                for line in hunk.lines:
                    origin = line.origin
                    if origin == '+' or origin == '-':
                        if not re.search(GitRepoHandler.JAVADOC, line.content):
                            return False
        return True


    def find_commits_between(self, start, end, codeonly):
        if start == end:
            return [start]

        os.chdir(self.repo_path)

        # for diff-ing, we need a full list of all commits in this time frame first
        # I am sure there has got to be a better way to do this, but here we go
        all_commits = [commit for commit in self.pygit_repo.walk(end, pygit2.GIT_SORT_TOPOLOGICAL)]

        the_commits = []
        i = 0
        for commit in self.pygit_repo.walk(end, pygit2.GIT_SORT_TOPOLOGICAL):
            use = True
            next = all_commits[i+1]
            if codeonly:
                diff = commit.tree.diff_to_tree(next.tree)
                use = GitRepoHandler.is_code_change(diff)
            if use:
                the_commits.append(str(commit.id)[:7])
            i += 1
            if str(commit.id).startswith(start):
                the_commits.reverse()
                return the_commits

    def reset(self):
        os.chdir(self.repo_path)
        call([GitRepoHandler.GIT] + GitRepoHandler.GIT_RESET_CMD)

    def checkout_commit(self, version):
        os.chdir(self.repo_path)
        call([GitRepoHandler.GIT] + [GitRepoHandler.GIT_CHECKOUT_CMD] + [version])
        return version

    def checkout_time(self, version):
        os.chdir(self.repo_path)
        # find out the Git version hash for the revision at this date
        # (note that this only considers master, not other branches)
        checkout_params = ["-n1", "--before=%s" % version, "origin/master"]
        revision_id = check_output(
            [GitRepoHandler.GIT, GitRepoHandler.GIT_REVLIST_CMD] + checkout_params
        ).strip()

        # now check out the revision with this hash
        call([GitRepoHandler.GIT, GitRepoHandler.GIT_CHECKOUT_CMD, revision_id])
        return revision_id[:7]