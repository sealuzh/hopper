import os
import subprocess
import shutil

import untangle

import api.result as result
import api.runner as runner
import fs
from impl.BasicJMHRunner import BasicJMHRunner
from impl.GitRepoHandler import GitRepoHandler


###############
### private ###
###############
def _checkout_version(project_dir, version, mode):
    repo = GitRepoHandler(project_dir)
    if mode == 'commit-mode':
        sha = repo.checkout_commit(version)
    elif mode == 'time-mode':
        sha = repo.checkout_time(version)
    else:
        raise RuntimeError("Mode not yet implemented.")
    return sha


def _run(statement, *args):
    try:
        subprocess.call(statement)
        return True
    except Exception as e:
        print "### " + ("Compilation failed"  if args[0] == None else args[0]) + ": %s ###" % e.message
        return False


_MVN_CMD = "mvn"
_MVN_CLEAN = "clean"
_MVN_INSTALL = ["install", "-DskipTests"]


def _is_clean(**kwargs):
    if 'build' in kwargs and kwargs['build'] == 'clean':
        return True
    return False


def _build_cmd(**kwargs):
    build_cmd = [_MVN_CMD]
    if _is_clean(**kwargs):
        build_cmd += [_MVN_CLEAN]
    build_cmd += _MVN_INSTALL
    return build_cmd


def _add_results(old_results, new_results):
    """
    _add_results adds new results to existing results of the same test
    :return a new dictionary of BenchmarkResults:
    """
    if not old_results:
        return new_results
    else:
        ret = {}
        for k, v in old_results.iteritems():
            ne = result.Benchmark(v.benchmark, v.parameter)
            ne.individual_results = v.individual_results + new_results[k].individual_results
            ret[ne.benchmark] = ne
        return ret


##############
### public ###
##############
class JMHRunner(runner.Test):
    JAVA_COMMAND = [os.environ['JAVA_HOME']+"/bin/java", "-jar",  "target/benchmarks.jar"]
    JMH_ARGS = "%s -rf json -rff %s"
    TMP_FILE = "tmp.json"

    def __init__(self, config):
        self.config = config

    def run(self, version, parser, run=None, **kwargs):
        try:
            sha = _checkout_version(self.config.project.dir, version, kwargs['mode'])
            _run(_build_cmd(**kwargs))
            pom_version = self.find_pom_version()
            jmh = BasicJMHRunner(self.config)
            jmh.prepare_version(self.config.project, pom_version)
            version_result = jmh.run_benchmark(version, sha, parser, run)
            return version_result
        except Exception as e:
            print "Failed to run benchmark for version %s: %s" % (str(version), e.message)
            return None

    def find_pom_version(self):
        return str(untangle.parse('pom.xml').project.version.cdata).strip()


class JUnitRunner(runner.Test):
    MVN_TEST = ["mvn", "test"]
    MVN_TEST_NAME = "-Dtest="

    RESULTS_DIR = "target/surefire-reports/"
    RESULTS_FILEPATTERN = "TEST-*.xml"

    TMP_FOLDER = '{0}/tmp/hopper-files/java-test-handler/'.format(os.path.expanduser('~'))

    def __init__(self, config):
        self.config = config
        self.proj_dir = config.project.dir
        self.test_dir = config.project.junit['dir']
        self.test_execs = config.project.junit['execs']
        self.regression = config.project.junit['reg']
        self.add_regression = False

    def run(self, version, parser, tests=None, **kwargs):
        # checkout current version
        sha = _checkout_version(self.config.project.dir, version, kwargs['mode'])
        # add regression
        if self.regression:
            self._add_regression(sha)
        self._chdir()
        # compile version
        success = _run(_build_cmd(**kwargs))
        #todo: check if build for project was successful
        if not success:
            print '### building process execution failed for version: {}'.format(sha)
            return result.Version(version, sha)
        # prepare version result
        version_result = result.Version(version, sha)
        version_result.benchmarks = {}
        # run tests and retrieve results
        os.chdir(self.test_dir)
        for n in range(0, self.test_execs):
            _run(self.exec_statement(tests), "Test execution failed")
            if not success:
                print '### test execution failed for version: {}'.format(sha)
                continue
            # generate test result file paths and pass those to the parser
            files = fs.matching_files(self.test_dir, JUnitRunner.RESULTS_FILEPATTERN, JUnitRunner.RESULTS_DIR)
            results = parser.parse_result(files)
            # add new test results
            version_result.benchmarks = _add_results(version_result.benchmarks, results)
            # check if incremental build -> if True delete sure fire reports
            self._del_surefire_results(**kwargs)

        version_result.benchmarks = version_result.benchmarks.values()

        # remove regression
        if self.regression:
            self._remove_regression()
        return version_result

    def exec_statement(self, tests):
        # prepare test execution statement
        if tests:
            ret = JUnitRunner.MVN_TEST[:]
            ret.append(JUnitRunner.MVN_TEST_NAME + tests.replace(' ', ''))
            return ret
        else:
            return JUnitRunner.MVN_TEST

    def _del_surefire_results(self, **kwargs):
        if _is_clean(**kwargs):
            return
        sf_dir = self.test_dir if self.test_dir.endswith('/') else self.test_dir + '/'
        sf_dir += 'target/surefire-reports'
        shutil.rmtree(sf_dir, ignore_errors=True)

    def _chdir(self):
        """
        _chdir changes the directory to either project dir or junit dir depending on whether a sub-project build is sufficient
        :return: None
        """
        dir = self.proj_dir
        #TODO: parse parent pom -> retrieve all sub-projects (poms) -> parse sub-poms
        #TODO: -> generate matrix/graph with interdependencies between sub-projects -> decide whether sub-projects needs installation of other sub-projects
        #TODO: have a look at mvn dependency
        os.chdir(dir)

    def _add_regression(self, sha):
        if (self.regression['commit'] and self.regression['commit'].startswith(sha)) or self.add_regression:
            self.add_regression = True
            print '### {0}: introduce regression'.format(sha)
            method = self.regression['method'].split('::')
            path = self.test_dir + '/src/main/java/' + method[0].replace('.', '/') + '.java'
            f = open(path, 'r')
            contents = f.readlines()

            pos = -1
            counter = -1
            in_comment = False
            for l in contents:
                stripped = l.strip()
                counter += 1
                if pos != -1:
                    if stripped.startswith('//'):
                        continue
                    if stripped.startswith('/*'):
                        in_comment = True
                        continue
                    if in_comment and stripped.endswith('*/'):
                        in_comment = False
                        continue
                    if in_comment:
                        continue
                    # not in comment -> first line
                    print '### insert point for regression: line {0}'.format(counter + 1)
                    break
                if method[1] + '(' in stripped:
                    pos = counter
            f.close()

            contents.insert(counter, 'try { Thread.sleep(' + str(self.regression['code']) + '); } catch (InterruptedException e) {}\n')

            f = open(path, 'w');
            contents = ''.join(contents)
            f.write(contents)
            f.close()

        else:
            print '### {0}: don\'t introduce regression'.format(sha)

    def _remove_regression(self):
        os.chdir(self.config.project.dir)
        subprocess.call(['git', 'reset', '--hard'])
