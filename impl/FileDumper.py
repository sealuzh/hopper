import api.history as history
from google.cloud import storage
import googleapiclient.discovery
import socket


class FileDumper(history.WalkerCallback):
    """ Implementation of a FileDumper.py that dumps the intermediary results to a CSV file.
    """

    def __init__(self, file, args=None, config=None):
        """ Initialize the file dumper with a given file handle. file needs to be set writable.
            Note that this class does nothing about opening or closing the file. The caller
            is responsible for making sure that the file is closed after usage (but not before).

        :param file:
        :param args: If given, the commandline params are written in a comment at the beginning of
        the file for tracking.
        :param config: If given, the config is used to write a comment at the beginning of
        the file for tracking.
        :return:
        """
        self.file = file
        if args:
            self.write_params(args)
        if config:
            self.write_config(config)
        self.write_header()

    def results_received(self, project, version, sha, results):

        if results.benchmarks:
            for b in results.benchmarks:
                benchmark = b.benchmark
                parameters = b.parameter
                for v in b.individual_results:
                    self.write_line(project, version, sha, parameters, benchmark, v)

    def write_params(self, args):
        for key, val in vars(args).iteritems():
            self.file.write("# %s -> %s\n" % (key, val))
        self.file.flush

    def write_config(self, config):
        # TODO: not yet implemented - add if actually necessary
        pass

    def write_header(self):
        """ Write a standardized CSV header to the file.
        :return: None
        """
        self.write_line("Project", "Version", "SHA", "Configuration", "Test", "RawVal")

    def write_line(self, project, revision, sha, params, test, val):
        """ Write a line of content to the file.
        :return: None
        """
        self.file.write("%s;%s;%s;%s;%s;%s\n"
                        % (_stringify(project), _stringify(revision), _stringify(sha), _stringify(params), _stringify(test), _stringify(val)))
        self.file.flush()
        
class CloudDumper(history.WalkerCallback):
    """ Implementation of a CloudDumper.py that dumps the intermediary results to a CSV file in a bucket storage.
    """

    def __init__(self, project_id):
        """ Initialize the file dumper with a given file handle. file needs to be set writable.
            Note that this class does nothing about opening or closing the file. The caller
            is responsible for making sure that the file is closed after usage (but not before).

        :return:
        """
        self.bucket = self.get_bucket(project_id)
        
    def get_bucket(self, project_id):
        service = googleapiclient.discovery.build('storage', 'v1')
        buckets = service.buckets().list(project=project_id).execute()
        storage_client = storage.Client(project=project_id)
        return storage_client.get_bucket(buckets['items'][0]['name'])
        
    def results_received(self, project, version, sha, results):
        
        if results.benchmarks:
            store_string = self.write_line("Project", "Version", "SHA", "Configuration", "Test", "RawVal")
            for b in results.benchmarks:
                benchmark = b.benchmark
                parameters = b.parameter
                for v in b.individual_results:
                    store_string += self.write_line(project, version, sha, parameters, benchmark, v)
            tmp = socket.gethostname() + '-' + str(version) + ".csv"
            tmp_blob = self.bucket.blob(tmp)
            tmp_blob.upload_from_string(store_string)

    def write_line(self, project, revision, sha, params, test, val):
        """ Write a line of content to the file.
        :return: None
        """
        store_string = "%s;%s;%s;%s;%s;%s\n" % (_stringify(project), _stringify(revision), _stringify(sha), _stringify(params), _stringify(test), _stringify(val))
        return store_string

def _stringify(something):
    return unicode(something).encode('utf-8')
