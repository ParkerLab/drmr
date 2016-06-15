============
Introduction
============


Drmr (pronounced 'drummer') lets you write computational pipelines in
simple shell scripts. It's designed to work with common distributed
resource management (DRM) systems (Slurm and PBS so far).

What's in the box?
------------------

* drmrc

    A tool to generate the drmr configuration file, ``.drmrc``. It
    will try to detect your DRM automatically. You can also specify
    default accounts and destinations for running jobs.

* drmr

    The most capable way of submitting jobs, drmr scripts can specify
    job parameters for each command, and also express dependencies,
    where the pipeline should wait for previous jobs to complete
    before continuing.

* drmrarray

    For simple scripts whose every command can run concurrently with
    the same job parameters. If commands have different requirements,
    use drmr.

* drmrm

    A utility to make it easier to delete jobs from your DRM.


License
-------

GPLv3 or any later version.
