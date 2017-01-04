# hopper - Performance History Mining
hopper is a command line tool that executes tests (unit tests or performance tests) over multiple versions of a software project and retrieves performance metrics (e.g. throughput, execution time) for each test.
Currently hopper supports Java projects that use [Maven](https://maven.apache.org) or [Gradle](https://gradle.org) as build tool, [JUnit](http://junit.org/junit4/) or [JMH](http://openjdk.java.net/projects/code-tools/jmh/) as testing frameworks, and [git](https://git-scm.com) or Maven for versioning.

## Installation Steps
The following steps are required to install the required dependencies for executing hopper. hopper is developed on OSX , hence the installation steps are only provided for OSX.
In the future we will focus on providing IaC scripts (e.g. Docker, Chef and/or Puppet) to ease the insallation process.

### OSX / macOS

* General
	* OSX command line tools
	* Java JDK (set JAVA_HOME correctly)
	* git
* Homebrew (install Homebrew first)
	* python (Python 2.x version incl. pip)
	* libgit2
	* maven/gradle
* Python (via pip)
	* untangle
	* pygit2

**CAVEAT**: make sure libgit2 and pygit2 are compatible!


## Usage
Execution of performance/unit tests of Java projects.
Supported:

* performance tests: JHM 
* unit tests: JUnit
* build systems: Maven, Gradle
* version control systems: git, Maven

### Configuration File
A configuration file is required to provide hopper with information about the project to mine. The following configuration file example shows the settings needed for executing either JUnit tests or JMH benchmarks.

Essential/required configurations:
* historian[type] - defines the backend used to do the mining. Must be one of "MvnCommitWalker", for walking the code history by git commits (also for Gradle projects), or "MvnVersionWalker", for walking the code history by maven versions.
* historian.project[name] - the name of the project.
* historian.project[dir] - the path to the project to mine.
* historian.project.jmh_root[dir] - the path to the JMH benchmarks. Only needed if performance tests are mined.
* historian.project.junit.execs - number of consecutive executions of a single JUnit test. Only needed if unit tests are mined and test executions is greater than 1. Defaults to 1 if left out.
* historian.project.versions.start - the version where mining starts.
* historian.project.versions.end - the version where mining ends.
* historian.jmh_arguments - command line arguments passed to JMH. Follow instructions on the [official JMH website](http://openjdk.java.net/projects/code-tools/jmh/) to generate the benchmarks and run `java -jar target/bencharks.jar -h` to see the available command line arguments. In the example below the mode is throughput (-bm thrpt) with 7 warmup iterations (-wi 7) and 20 iterations that are taken into account for the measurement (-i 20).


```XML
<?xml version="1.0" encoding="UTF-8"?>
<historian type="MvnCommitWalker">
        <project name="Protostuff" dir="~/tmp/protostuff">
                <jmh_root dir="~/tmp/protostuff-benchmarks" />
                <junit>
                        <execs>20</execs>
                </junit>
                <versions>
                        <start>1e65a07</start>
                        <end>5bbf909</end>
                </versions>
        </project>
        <jmh_arguments>
                -f 1 -tu s -bm thrpt -wi 7 -i 20 -r 1
        </jmh_arguments>
</historian>
```

### Arguments
The following command line arguments for hopper are available. If not specified otherwise, the arguments are mandatory:

* -f - the path to the configuration file.
* -o - the path to the output file. See below for the output file format.
* -t - the test type to execute. Available options: "unit" and "benchmark".
* -b - the version type to use. Available options: "commits", for git commits, and "versions", for Maven versions. Optional, defaults to "commits".
* -r - the build system type. Available options: "mvn" and "gradle". Optional, defaults to "mvn".
* --step - if specified, only executes every nth versions. Optional, defaults to 1.
* --build-type - defines if builds between versions should be clean or incremental. Available options: "clean" and "inc". Optional, defaults to "clean".
* --skip-noncode - if present, skips versions that do not have a code code (e.g. change only in comment).
* --tests - only execute the specified tests. Takes a comma seperated string of test names. E.g. "BenchA, BenchB, BenchC"

### Output File
hopper generates a CSV file with the minied historical performance data. The file has 6 columns: 

* Project - the name of the project as specified in the configuration file.
* Version - the version of the performance metric.
* SHA - the commit hash of the performance metric. For git-based version history, Version and SHA are equivalent.
* Configuration - the configuration how the metric was obtained.
* Test - the name of the test executed for the performance metric.
* RawVal - the value of the performance metric.

For multiple executions of a particular test in a particular version, multiple lines are present in the output file. [gopper](https://github.com/sealuzh/gopper), a historical performance analysing tool, uses this output format as input.

```CSV
Project;Version;SHA;Configuration;Test;RawVal
Protostuff;277eded;277eded;Duration;io.protostuff.runtime.ProtobufRuntimeObjectSchemaTest.testPojo;0.005
Protostuff;277eded;277eded;Duration;io.protostuff.JsonNumericStandardTest.testPartialEmptyFooInnerWithEmptyString;0.0
...
```

### Run Tests

* prepare config file (see example above) to run
	* change project directory path (may need to download the project from e.g. Github)
	* change JMH root directory
* change to hopper directory on command line
* compile Python files (optional)
	
```bash
python -m compileall ./
```

* run benchmarks (minimum required parameters are -f, -o and -t)
	
```bash
python hopper.py -f input.xml -o output.cvs -t benchmark -b commits
```

* run unit tests (minimum required parameters are -f, -o and -t)
    
```bash
python hopper.py -f input.xml -o output.cvs -t unit -b commits
```

# Maintainers
[Christoph Laaber](https://github.com/chrstphlbr)

[Philipp Leitner](https://github.com/xLeitix)
