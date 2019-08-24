_There are two releases of Cedar Backup: version 2 and version 3.
This project (Cedar Backup v2) uses the Python 2 interpreter, and 
[Cedar Backup v3](https://github.com/cedarsolutions/cedar-backup3) 
uses the Python 3 interpreter.   Because Python 2 is 
approaching its [end of life](http://legacy.python.org/dev/peps/pep-0373/#id2), 
and Cedar Backup v3 has been available since July of 2015, 
**Cedar Backup v2 is unsupported as of 11 Nov 2017**.  There will 
be no additional releases, and users who report problems will be
referred to the new version.  Please move to Cedar Backup v3._

# Cedar Backup v2 - _UNSUPPORTED_

## What is Cedar Backup?

Cedar Backup v2 is a software package designed to manage system backups for a pool
of local and remote machines. The project was originally maintained at 
[SourceForge](http://sourceforge.net/projects/cedar-backup/), 
and historical releases still exist there. The project was moved to BitBucket in
mid-2015, and from there to GitHub in mid-2019 when BitBucket stopped supporting
Mercurial.

Cedar Backup understands how to back up filesystem data as well as MySQL and
PostgreSQL databases and Subversion repositories. It can also be easily extended 
to support other kinds of data sources.  The backup process is focused around 
weekly backups to a single CD or DVD disc, with the expectation that the disc 
will be changed or overwritten at the beginning of each week. Alternately, 
Cedar Backup can write your backups to the Amazon S3 cloud rather than relying 
on physical media.

Besides offering command-line utilities to manage the backup process, Cedar
Backup provides a well-organized library of backup-related functionality,
written in the Python 2 programming language.

There are many different backup software implementations out there in the open 
source world. Cedar Backup aims to fill a niche: it aims to
be a good fit for people who need to back up a limited amount of important data
on a regular basis. Cedar Backup isn't for you if you want to back
up your huge MP3 collection every night, or if you want to back up a few hundred
machines. However, if you administer a small set of machines and you want to
run daily incremental backups for things like system configuration, current
email, small web sites, Subversion or Mercurial repositories, or small MySQL
databases, then Cedar Backup is probably worth your time.

Cedar Backup has been developed on a 
[Debian GNU/Linux](http://www.debian.org/)
system and is primarily supported on Debian and other Linux systems.
However, since it is written in portable 
[Python 2](http://www.python.org), it should run without problems on
just about any UNIX-like operating system. In particular, full Cedar
Backup functionality is known to work on Debian and SuSE Linux, and client 
functionality is also known to work on FreeBSD and MacOS systems.

## Library Code

The Cedar Backup 2 has been designed as both an application and a
library of backup-related functionality.  The `CedarBackup2` Python 
package contains a variety of useful backup-related classes and functions.  For
instance: the `IsoImage` class represents an ISO CD image;
the `CdWriter` class represents a CD-R/CD-RW writer device; and the
`FilesystemList` class represents a list of files and directories on a
filesystem.  For more information, see the 
[public interface documentation](https://cedarsolutions.github.io/cedar-backup2/docs/interface/index.html), 
generated from the source code using [Epydoc](http://epydoc.sourceforge.net).

## Documentation

See the [Changelog](https://github.com/cedarsolutions/cedar-backup2/blob/master/Changelog) for
recent changes.

The Cedar Backup Software Manual documents the process of setting up and using
Cedar Backup.  In the manual, you can find information about how Cedar Backup
works, how to install and configure it, how to schedule backups, how to restore
data, and how to get support.

The following versions of the manual are available:

* [Single-page HTML](https://cedarsolutions.github.io/cedar-backup2/docs/manual/manual.html)
* [Multiple-page HTML](https://cedarsolutions.github.io/cedar-backup2/docs/manual/index.html)

Most users will want to look at the multiple-page HTML version.

## Package Distributions

Cedar Backup is primarily distributed as a Python 2 source package.  You can
download the latest release from the BitBucket download page.

The official Debian packages for Cedar Backup v2 are called called 
`cedar-backup2` and `cedar-backup2-doc`.  The Debian _buster_ release 
was the last release that includedpackages for Cedar Backup v2.  

## Support

As of 11 Nov 2017, Cedar Backup v2 is unsupported.  Please move to 
[Cedar Backup v3](https://github.com/cedarsolutions/cedar-backup3), 
which uses the Python 3 interpreter.

## Migrating from Version 2 to Version 3

The main difference between Cedar Backup version 2 and Cedar Backup version 3
is the targeted Python interpreter.  Cedar Backup version 2 was designed for
Python 2, while version 3 is a conversion of the original code to Python 3.
Other than that, both versions are functionally equivalent.  The configuration
format is unchanged, and you can mix-and-match masters and clients of different
versions in the same backup pool.

A major design goal for version 3 was to facilitate easy migration testing for
users, by making it possible to install version 3 on the same server where
version 2 was already in use.  A side effect of this design choice is that all
of the executables, configuration files, and logs changed names in version 3.
Where version 2 used `cback`, version 3 uses `cback3`: `cback3.conf` instead of
`cback.conf`, `cback3.log` instead of `cback.log`, etc.

So, while migrating from version 2 to version 3 is relatively straightforward,
you will have to make some changes manually.  You will need to create a new
configuration file (or soft link to the old one), modify your cron jobs to use
the new executable name, etc.  You can migrate one server at a time in your
pool with no ill effects, or even incrementally migrate a single server by
using version 2 and version 3 on different days of the week or for different
parts of the backup.
