class Test:
    """ This is the interface of a benchmark runner, i.e., the logic that knows how to
    actually execute e.g., JMH tests using Maven. In practice this will be sort of
    tightly bound to the used backend, but I can forsee situation where runners and
    backends can be mixed-and-matched.
    """

    def run(self, version, parser, run=None, **kwargs):
        """ Run the benchmark(s) for the specified version, and parse the results
        using the given parser. If no benchmarks are specified, all benchmarks
        will be executed.
        :param version:
        :param parser:
        :return:
        """
        pass
