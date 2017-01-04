class Parser:
    """ This is the interface of a parser that extracts one or more benchmarking results
    from a file.
    """

    def parse_result(self, file_name):
        """ Parses the file.
        :param file_name:
        :return:
        """
        pass


class Project:
    def __init__(self, project, versions=None):
        self.project = project
        if versions:
            self.versions = versions
        else:
            self.versions = []

    def __str__(self):
        string = """###################
Results for project %s:
""" % self.project
        for version in self.versions:
            string += str(version)
        string +=  '###################\n'
        return string


class Version:
    def __init__(self, version, sha, benchmarks=None):
        self.version = version
        self.sha = sha
        if benchmarks:
            self.benchmarks = benchmarks
        else:
            self.benchmarks = []

    def __str__(self):
        string = """-------------------
Results for version %s (%s):
""" % (self.version, self.sha)
        for benchmark in self.benchmarks:
            string += str(benchmark)
        return string


class Benchmark:
    def __init__(self, benchmark, parameter, individual_results=None):
        self.benchmark = benchmark
        self.parameter = parameter
        if individual_results:
            self.individual_results = individual_results
        else:
            self.individual_results = []

    def __str__(self):
        string = """....................
Results for Benchmark %s and Parameter %s:
""" % (self.benchmark, self.parameter)
        for result in self.individual_results:
            string += str(result)
            string += "\n"
        return string
