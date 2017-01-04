import argparse

from impl import MvnGit
from impl import ResultParser
from impl.FileDumper import FileDumper
from impl.GradleCommitWalker import GradleJMHGitRunner
from impl.MvnCommitWalker import MvnCommitWalker
from impl.MvnVersionWalker import MvnVersionWalker, JMHMvnRunner


def parse_cmd_params():
    '''
    Wrap the ugly cmd param parsing into a separate function.
    '''
    parser = argparse.ArgumentParser(description='Historian of Performance.')
    parser.add_argument('-f', '--configfile', required=True, dest='config')
    parser.add_argument('-o', '--outfile', required=True, dest='outfile')
    parser.add_argument('-t', '--type', required=True, choices=('unit', 'benchmark'), dest="type")
    parser.add_argument('-b', '--backend', choices=('versions', 'commits'), default='commits', dest='backend')
    parser.add_argument('-r', '--runner', choices=('mvn', 'gradle'), default='mvn', dest='runner')
    parser.add_argument('--from', dest='start')
    parser.add_argument('--to', dest='to')
    parser.add_argument('--step', dest='step', type=int)
    parser.add_argument('-i', '--invert-order', type=bool, dest='invert', default=False)
    parser.add_argument('--tests', dest='tests')
    parser.add_argument('--mode', choices=('time-mode', 'commit-mode'), default='commit-mode', dest='mode')
    parser.add_argument('--skip-noncode', type=bool, dest='codeonly', default=False)
    parser.add_argument('--build-type', choices=('inc', 'clean'), default='clean', dest='build_type')
    return parser.parse_args()


def print_and_exit(msg):
    print msg
    exit(-1)


def create_backend_runner(args):
    ret = {}
    custom_args = {}

    if args.type == 'benchmark':
        if args.backend == 'versions':
            backend = MvnVersionWalker(args.config)
            runner = JMHMvnRunner(backend.config)
        elif args.backend == 'commits':
            backend = MvnCommitWalker(args.config)
            if args.runner == 'mvn':
                runner = MvnGit.JMHRunner(backend.config)
            elif args.runner == 'gradle':
                runner = GradleJMHGitRunner(backend.config)
        else:
            print_and_exit("unsupported backend (" + args.backend + ") for type (" + args.type + ")")
    elif args.type == 'unit':
        if args.backend == 'commits':
            if args.runner == 'mvn':
                backend = MvnCommitWalker(args.config)
                print "### single test case executions: " + str(backend.config.project.junit['execs'])
                runner = MvnGit.JUnitRunner(backend.config)
            else:
                print_and_exit("unsupported runner (" + args.runner+ ") for backend (" + args.backend + ") and type (" + args.type + ")")
        elif args.backend == 'versions':
            print_and_exit("unsupported backend (" + args.backend + ") for type (" + args.type + ")")
        else:
            print_and_exit("unsupported backend (" + args.backend + ") for type (" + args.type + ")")
    else:
        print_and_exit('unsupported type: ' + args.type)

    ret['backend'] = backend
    ret['runner'] = runner
    ret['custom_args'] = {'mode': args.mode, 'skip-noncode': args.codeonly, 'build': args.build_type}

    return ret

'''
Beginning of main Hopper script.
'''

# parse commandline parameters
args = parse_cmd_params()

with open(args.outfile, "w") as file:

    ret = create_backend_runner(args)
    backend = ret['backend']
    runner = ret['runner']
    custom_args = ret['custom_args']

    config = backend.config

    callback = FileDumper(file, args, config)
    versions = backend.generate_version_list(start=args.start, end=args.to, step=args.step, **custom_args)
    print "### We will be looking at %s distinct commits. ###" % len(versions)
    print versions

    if args.type == 'benchmark':
        parser = ResultParser.JMHJSON()
        results = backend.walk(versions, runner, parser, args.tests, not args.invert, callback, **custom_args)
    elif args.type == 'unit':
        parser = ResultParser.JUnitSurefire()
        results = backend.walk(versions, runner, parser, args.tests, not args.invert, callback, **custom_args)
    else:
        print_and_exit('unsupported type: ' + args.type)
