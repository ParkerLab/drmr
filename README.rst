======
drmr
======

A tool for submitting pipeline scripts to distributed resource
managers.

Introduction
============

Drmr (pronounced 'drummer') lets you write computational pipelines in
simple shell scripts. It's designed to work with common distributed
resource management (DRM) systems (Slurm and PBS so far).

Why another pipeline tool?
--------------------------

Because of a quirk in our local environment, really. Most of the
packages I evaluated required a persistent supervisor process to
manage pipelines. The cluster we have ready access to kills any
process that accumulates 15 minutes of CPU time on the login
nodes. That's not usually a problem, but for big important jobs, we
didn't want to worry about it. With drmr, it's fire and forget: the
pipeline management is delegated to the DRM via job dependencies.

Most of the more capable tools also have a bigger learning curve. With
drmr, you start with a regular sequential shell script, and add DRM
directives as you need to. By default every line in the script will be
submitted as a concurrent job (in an array, if the DRM supports
them).

You can also use directives in special comments to specify limits or
required resources for subsequent tasks. If steps in your pipeline
depend on the completion of earlier tasks, you can insert wait
directives, which act as checkpoints.

You can also label sections of the pipeline; each section will be
managed like a single job, so they can execute in parallel. Within a
section, you can still use directives to control concurrency. It's
turtles all the way down.

Requirements
============

* Python. We've run it successfully under versions 2.7.10 and 3.5.

Installation
============

At the command line::

  git clone https://github.com/ParkerLab/drmr
  pip install ./drmr

License
=======

GPL version 3 (or any later version).
