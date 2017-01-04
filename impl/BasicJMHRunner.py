import os
from subprocess import call
import xml.etree.ElementTree as ET

import api.result as result

class BasicJMHRunner:
    ''' This runner is for projects that use Git/JMH/Gradle, such as RxJava. It reuses almost everything from the
     Git/JMH/Gradle backend, just with a slightly different way of compiling and figuring out versions.
    '''

    JAVA_COMMAND = [os.environ['JAVA_HOME']+"/bin/java", "-jar",  "target/benchmarks.jar"]
    JMH_ARGS = "%s -rf json -rff %s"
    TMP_FILE = "tmp.json"

    MVN_COMMAND = "mvn"
    MVN_ARGS = ["clean", "install", "-DskipTests"]

    def __init__(self, config):
        self.config = config

    def run_benchmark(self, version, sha, parser, benchmarks=None):
        self.run_jmh_test(benchmarks)
        res = parser.parse_result(BasicJMHRunner.TMP_FILE)
        if res:
            version_result = result.Version(version, sha)
            version_result.benchmarks = res
        else:
            version_result = None
        if os.path.isfile(BasicJMHRunner.TMP_FILE):
            os.remove(BasicJMHRunner.TMP_FILE)
        return version_result

    def run_jmh_test(self, benchmarks):
        jhm_arg = BasicJMHRunner.JMH_ARGS % (self.config.arguments, BasicJMHRunner.TMP_FILE)
        cmd = BasicJMHRunner.JAVA_COMMAND + jhm_arg.split()
        if benchmarks:
            cmd = cmd + [benchmarks]
        call(cmd)

    def prepare_version(self, project, version):
        os.chdir(project.jmh_root)
        self.update_pom(version)
        call([BasicJMHRunner.MVN_COMMAND] + BasicJMHRunner.MVN_ARGS)

    def update_pom(self, version):
        ET.register_namespace('', "http://maven.apache.org/POM/4.0.0")
        tree = ET.parse('pom.xml')
        version_tag = tree.find(".//{http://maven.apache.org/POM/4.0.0}target.version")
        version_tag.text = version
        tree.write('pom.xml')
