import json

import untangle

import api.result as result


class JMHJSON(result.Parser):
    """ Implementation  of a result parser that parses the JSON file produced by JMH
    if started with the "-rf json" option.
    """

    def parse_result(self, file_name):
        try:
            with open(file_name) as file:
                data = json.load(file)
                parsed_results = []
                for run in data:
                    benchmark = run["benchmark"]
                    if "params" in run:
                        params = ""
                        for p,v in run["params"].iteritems():
                             params = params + " %s=%s " % (p,v)
                        params = params.strip()
                    else:
                        params = "-"
                    values = [ val for raw in run["primaryMetric"]["rawData"] for val in raw ]
                    # note that this breaks down horribly when we have more than one rawData block
                    # better print a warning in this case
                    if len(run["primaryMetric"]["rawData"]) > 1:
                        self.warn(benchmark, data)
                    res = result.Benchmark(benchmark, params)
                    res.individual_results  = values
                    parsed_results.append(res)
                return parsed_results
        except Exception as error:
            print 'JMHJSON parser error: {}'.format(error)
            return None

    def warn(self, benchmark, data):
        with open("warning.log", "a+") as file:
            file.write("WARNING - duplicate raw data block\n")
            file.write(benchmark + "\n")
            file.write("------------------------------------")
            file.write(str(data))
            file.write("------------------------------------")


class JUnitSurefire(result.Parser):
    """
    JUnitSurefire implements a parser which extracts runtime of JUnit tests from generated Surefire XML files.
    """
    def parse_result(self, file_name):
        """"
        parse_result returns the the results (BenchmarkResult) for the specified file_name.
        :param file_name accepts a file pattern which is forwarded to glob:
        :return results of potentially multiple test results as dictionary:
        """
        results = {}
        files = file_name
        try:
            iter(files)
        except TypeError, te:
            assert(False, te)
        for file in files:
            report = untangle.parse(file)
            for test in report.testsuite.testcase:
                fqn = test['classname']+"."+test['name']
                time = float(test['time'])
                r = result.Benchmark(fqn, 'Duration', [time])
                results[fqn] = r
        return results
