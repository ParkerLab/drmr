========
Usage
========

drmr
====

Submits a pipeline script to a distributed resource manager. By
default all the pipeline's commands are run concurrently, but you can
indicate dependencies by adding ``# drmr:wait`` directives between
jobs. Whenever a wait directive is encountered, the pipeline will wait
for all prior jobs to complete before continuing.

You may also specify job parameters, like CPU or memory requirements,
time limits, etc. in ``# drmr:job`` directives.

You can get help, including a full example, by running ``drmr --help``::

    usage: drmr [-h] [-a ACCOUNT] [-d DESTINATION] [--debug] [-j JOB_NAME]
                [-f FROM_LABEL] [--mail-at-finish] [--mail-on-error]
                [--start-held] [-t TO_LABEL] [-w WAIT_LIST]
                input

    Submit a drmr script to a distributed resource manager.

    positional arguments:
      input                 The file containing commands to submit. Use "-" for
                            stdin.

    optional arguments:
      -h, --help            show this help message and exit
      -a ACCOUNT, --account ACCOUNT
                            The account to be billed for the jobs.
      -d DESTINATION, --destination DESTINATION
                            The queue/partition in which to run the jobs.
      --debug               Turn on debug-level logging.
      -j JOB_NAME, --job-name JOB_NAME
                            The job name.
      -f FROM_LABEL, --from-label FROM_LABEL
                            Ignore script lines before the given label.
      --mail-at-finish      Send mail when all jobs are finished.
      --mail-on-error       Send mail if any job fails.
      --start-held          Submit a held job at the start of the pipeline, which
                            must be released to start execution.
      -t TO_LABEL, --to-label TO_LABEL
                            Ignore script lines after the given label.
      -w WAIT_LIST, --wait-list WAIT_LIST
                            A colon-separated list of job IDs that must complete
                            before any of this script's jobs are started.

    Supported resource managers are:

      Slurm
      PBS

    drmr will read configuration from your ~/.drmrc, which must be
    valid JSON. You can specify your resource manager and default
    values for any job parameters listed below.

    Directives
    ==========

    Your script can specify job control directives in special
    comments starting with "drmr:".

    # drmr:wait

      Drmr by default runs all the script's commands
      concurrently. The wait directive tells drmr to wait for
      any jobs started since the last wait directive, or the
      beginning of the script, to complete successfully.

    # drmr:job

      You can customize the following job parameters:

      time_limit: The maximum amount of time the DRM should allow the job: "12:30:00" or "12h30m".
      working_directory: The directory where the job should be run.
      processor_memory: The amount of memory required per processor.
      node_properties: A comma-separated list of properties each node must have.
      account: The account to which the job will be billed.
      processors: The number of cores required on each node.
      default: Use the resource manager's default job parameters.
      destination: The execution environment (queue, partition, etc.) for the job.
      job_name: A name for the job.
      memory: The amount of memory required on any one node.
      nodes: The number of nodes required for the job.
      email: The submitter's email address, for notifications.

      Whatever you specify will apply to all jobs after the directive.

      To revert to default parameters, use:

      # drmr:job default

      To request 4 CPUs, 8GB of memory per processor, and a
      limit of 12 hours of execution time on one node:

      # drmr:job nodes=1 processors=4 processor_memory=8000 time_limit=12:00:00

    Example
    =======

    A complete example script follows:

    #!/bin/bash

    #
    # Example drmr script. It can be run as a normal shell script, or
    # submitted to a resource manager with the drmr command.
    #

    #
    # You can just write commands as you would in any script. Their output
    # will be captured in files by the resource manager.
    #
    echo thing1

    #
    # You can only use flow control within a command; drmr's parser is not
    # smart enough to deal with conditionals, or create jobs for each
    # iteration of a for loop, or anything like that.
    #
    # You can do this, but it will just all happen in a single job:
    #
    for i in $(seq 1 4); do echo thing${i}; done

    #
    # Comments are OK.
    #
    echo thing2  # even trailing comments

    #
    # Line continuations are OK.
    #
    echo thing1 \
         thing2 \
         thing3

    #
    # Pipes are OK.
    #
    echo funicular berry harvester | wc -w

    #
    # The drmr wait directive makes subsequent tasks depend on the
    # successful completion of all jobs since the last wait directive or
    # the start of the script.
    #

    # drmr:wait
    echo "And proud we are of all of them."

    #
    # You can specify job parameters:
    #

    # drmr:job nodes=1 processors=4 processor_memory=8000 time_limit=12:00:00
    echo "I got mine but I want more."

    #
    # And revert to the defaults defined by drmr or the resource manager.
    #

    # drmr:job default
    echo "This job feels so normal."

    # drmr:wait
    # drmr:job time_limit=00:15:00
    echo "All done!"

    # And finally, a job is automatically submitted to wait on all the
    # other jobs and report success or failure of the entire script.
    # Its job ID will be printed.

drmrarray
=========

Submits an entire script in a job array. The script cannot contain
dependencies. Job parameters can only be specified at the top of the
script, and will apply to all jobs in the array.

You can get help, including a full example, by running `drmrarray --help`::

    usage: drmrarray [-h] [-a ACCOUNT] [-d DESTINATION] [--debug] [-f]
                     [-j JOB_NAME] [--mail-at-finish] [--mail-on-error]
                     [-s SLOT_LIMIT] [-w WAIT_LIST]
                     input

    Submit a drmr script to a distributed resource manager as a job array.

    positional arguments:
      input                 The file containing commands to submit. Use "-" for
                            stdin.

    optional arguments:
      -h, --help            show this help message and exit
      -a ACCOUNT, --account ACCOUNT
                            The account to be billed for the jobs.
      -d DESTINATION, --destination DESTINATION
                            The queue/partition in which to run the jobs.
      --debug               Turn on debug-level logging.
      -f, --finish-jobs     If specified, two extra jobs will be queued after the
                            main array, to indicate success and completion.
      -j JOB_NAME, --job-name JOB_NAME
                            The job name.
      --mail-at-finish      Send mail when all jobs are finished.
      --mail-on-error       Send mail if any job fails.
      -s SLOT_LIMIT, --slot-limit SLOT_LIMIT
                            The number of jobs that will be run concurrently when
                            the job is started, or 'all' (the default).
      -w WAIT_LIST, --wait-list WAIT_LIST
                            A colon-separated list of job IDs that must complete
                            before any of this script's jobs are started.

    Supported resource managers are:

      Slurm
      PBS

    drmrarray will read configuration from your ~/.drmrc, which must be valid
    JSON. You can specify your resource manager and default values for any job
    parameters listed below.

    Directives
    ==========

    Your script can specify job parameters in special comments starting
    with "drmr:job".

    # drmr:job

      You can customize the following job parameters:

      time_limit: The maximum amount of time the DRM should allow the job: "12:30:00" or "12h30m".
      working_directory: The directory where the job should be run.
      processor_memory: The amount of memory required per processor.
      node_properties: A comma-separated list of properties each node must have.
      account: The account to which the job will be billed.
      processors: The number of cores required on each node.
      default: Use the resource manager's default job parameters.
      destination: The execution environment (queue, partition, etc.) for the job.
      job_name: A name for the job.
      memory: The amount of memory required on any one node.
      nodes: The number of nodes required for the job.
      email: The submitter's email address, for notifications.

      Whatever you specify will apply to all jobs after the directive.

      To revert to default parameters, use:

      # drmr:job default

      To request 4 CPUs, 8GB of memory per processor, and a
      limit of 12 hours of execution time on one node:

      # drmr:job nodes=1 processors=4 processor_memory=8000 time_limit=12:00:00


drmr_configure
==============

Creates the drmr configuration file, `.drmrc`. It will try to detect
the DRM in use on your system, but you can specify it explicitly, as
well as a default account or destination for your jobs.

Help is available by running `drmr_configure --help`::

    usage: drmr_configure [-h] [-a ACCOUNT] [-d DESTINATION] [-o]
                          [-r RESOURCE_MANAGER]

    Generate a drmr configuration file for your local environment.

    optional arguments:
      -h, --help            show this help message and exit
      -a ACCOUNT, --account ACCOUNT
                            The account to which jobs will be charged by default.
      -d DESTINATION, --destination DESTINATION
                            The default queue/partition in which to run jobs.
      -o, --overwrite       Overwrite any existing configuration file.
      -r RESOURCE_MANAGER, --resource-manager RESOURCE_MANAGER
                            If you have more than one resource manager available,
                            you can specify it.
