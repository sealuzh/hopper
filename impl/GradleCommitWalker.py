import re
from subprocess import check_output

from impl import MvnGit
from impl.BasicJMHRunner import BasicJMHRunner
from impl.GitRepoHandler import GitRepoHandler

class GradleJMHGitRunner(MvnGit.JMHRunner):

    GRADLE_COMMAND = "./gradlew"
    GRADLE_ARGS = ["publishToMavenLocal", "-x", "test"]
    GRADLE_VERSION_PATTERN = '(Inferred version:? ([^\s]*)\s)|(No committed changes since ([^\s]*), using that version)'


    def __init__(self, config):
        self.config = config

    def run(self, version, parser, run=None, **kwargs):
        try:
            sha = MvnGit.checkout_version(self.config.project.dir, version, kwargs['mode'])
            self.fix_gradle_config()    # we use this to fix an issue in older RxJava configurations
            mvn_version = self.compile_version()
            print "Found Mvn version %s" % mvn_version
            jmh = BasicJMHRunner(self.config)
            jmh.prepare_version(self.config.project, mvn_version)
            version_result = jmh.run_benchmark(version, sha, parser, run)
            self.reset_git()
            return version_result
        except Exception as e:
            print "Failed to run benchmark for version %s: %s" % (str(version), e.message)
            return None

    def compile_version(self):
        output_string = check_output([GradleJMHGitRunner.GRADLE_COMMAND] + GradleJMHGitRunner.GRADLE_ARGS)
        match = re.search(GradleJMHGitRunner.GRADLE_VERSION_PATTERN, output_string)
        if not match:
            print "Failed inferring version from Gradle output"
            print output_string
            return ""
        if match.group(2):
            return match.group(2)
        if match.group(4):
            return match.group(4)
        return ""

    def reset_git(self):
        repo = GitRepoHandler(self.config.project.dir)
        repo.reset()

    def fix_gradle_config(self):
        with open("build.gradle", "r") as file:
            file_content = file.read()
        file_content = file_content.replace('\ndependencies {', '\ndependencies {\n  apply plugin: "java"')
        with open("build.gradle", "w") as file:
            file.write(file_content)
            file.flush()
