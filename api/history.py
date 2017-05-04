import api.result as result
import time
import datetime


class Walker:
    """ This is the abstract base class for a history walker. This contains methods to iterate
    over the versions of a software project. Whether those versions are mvn versions, or commits,
    or whatever differs in different implementations.
    """

    def walk(self, versions, testrunner, parser, benchmarks = None, forward = True, callback = None, **kwargs):
        """ This walks through the project history over all versions given.
         What exactly is considered a version differs in different implementations.
         For each version, the given test runner implementation is called
         to execute either all benchmarks, or (if given) the provided subset of benchmarks.

         If a callback is given, the callback is invoked for each version with the
         result for this specific version. If no callback or a None
         callback is given, the results are simply returned as a list after the end of
         the walk. However, results are still returned even if a callback is given/

        :param versions: A list of versions to iterate. Might be dates or mvn versions, depending on backend.
        :param testrunner: The implementation of how to execute the test.
        :param parser: The parser used to extract results.
        :param benchmarks: A list of benchmark names as strings to execute. Optional, if no argument is given, all
        benchmarks are executed.
        :param forward: Run through the version list from first to last, or the other way 'round.
        :param callback: A callback implementation that should be invoked after each version. Mostly used to write
        intermediary results somewhere.
        :return: The results for all versions.
        """
        all_results = result.Project(self.config.project.name)
        if not forward:
            versions.reverse()
        i = 0
        for version in versions:
            start = time.time()
            res = testrunner.run(version, parser, benchmarks, **kwargs)
            end = time.time()
            diff = end - start
            m_diff = int(diff / 60)
            remaining_versions = (len(versions) - i)
            m_projected = m_diff * remaining_versions
            h_projected = int(m_projected/ 60)
            m_projected_rem = int(m_projected % 60)
            now = datetime.datetime.now()
            projected_end = now + datetime.timedelta(minutes = m_projected)
            i += 1
            print "### Execution for version %s took %s minutes. ###" % (version, m_diff)
            if remaining_versions > 0:
               print "### Still have %s versions to go, that will be %s hours and %s minutes. Projected end is %s. ###"\
                     % (remaining_versions, h_projected, m_projected_rem, projected_end)
            if res:
                all_results.versions.append(res)
                if callback:
                    callback.results_received(self.config.project.name, version, res.sha, res)
        return all_results

    def generate_version_list(self, start = None, end = None, step = None, **kwargs):
        """ Generate a concrete list of versions to iterate over. This may be mvn versions,
        dates, or concrete versions in Git.

        :param start: The first version to include in the list.
        :param end: The last version to include in the list.
        :param step: How to iterate (e.g., every other version, every 7 days, ...).
        :param config: A parsed config as understood by the used backend.
        :return: A list of versions.
        """
        pass

    def parse_config(self, config_file):
        """ Parse a given config file, and return a parsed representation for easy usage. This is the responsibility
        of the walker as the concrete file formats and resulting parsed configs vary for different backends.
        :param config_file: A full file name leading to an XML config file.
        :return: The parsed config.
        """
        pass


class WalkerCallback:
    """ This is an optional callback that is given to a HistoryWalker. The callback is invoked
    for each version result after each iteration.
    """

    def results_received(self, project, version, sha, results):
        """ This callback method is to be invoked by the RevisionWalker after an iteration.

        :param project: The identifier of the project
        :param version: The version that this is the result for
        :param sha: The Git version SHA of the revision that we actually executed on.
        :param results: A list of results.
        :return: None
        """
        pass

