import sys
import json
import os

from time import gmtime, strftime
from hashlib import sha1
from subprocess import Popen

from debcert.scraping import get_buildlog, parse_buildlog
from debcert.apttools import (find_package_for_installed_file,
                              verify_file_integrity,
                              find_installed_package_version,
                              find_installed_package_meta)

def usage():
    print >>sys.stderr, "Usage: {} <file>".format(sys.argv[0])
    sys.exit(1)

def hashfile(filepath):
    s = sha1()
    with file(filepath, 'rb') as f:
        try:
            s.update(f.read())
        finally:
            f.close()
        return s.hexdigest()

def has_tool(name):
    try:
        devnull = open(os.devnull)
        Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            return False
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()

    fname = sys.argv[1]

    if not os.path.isfile(fname):
        print >>sys.stderr, "{}: no such file".format(fname)
        usage()

    bincert = dict()
    bincert['analyzed'] = strftime('%Y-%m-%dT%H:%M:%S', gmtime())
    bincert['filename'] = fname
    bincert['sha1'] = hashfile(fname)

    if not has_tool('apt-file'):
        print >>sys.stderr, "apt-file not installed, exiting"
        sys.exit(2)
        
    package = find_package_for_installed_file(fname)
    if not package:
        print >>sys.stderr, \
            "{}: did not find installation package".format(fname)
    
    if not has_tool('debsums'):
        print >>sys.stderr, "debsums not installed, not verifying integrity"
    elif not verify_file_integrity(package, fname):
        print >>sys.stderr, \
            "{} does not match package, cowardly refusing to run".format(fname)
        sys.exit(3)

    version = find_installed_package_version(package)
    if not version:
        print >>sys.stderr, \
            'Could not find version for package {}'.format(package)
        sys.exit(4)

    bincert['package'] = "{} {}".format(package, version)

    sourcepackage, packagecert = find_installed_package_meta(package, version)
    if not sourcepackage:
        print >>sys.stderr, \
            "{} {}: version not found (apt-cache)".format(
                package, version)
        sys.exit(5)

    bincert['source package'] = sourcepackage

    sourcepkg_url = 'https://launchpad.net/ubuntu/+source/{}/{}'.format(
        sourcepackage, version)
    packagecert['source package url'] = sourcepkg_url

    buildlog_url, build = get_buildlog(sourcepkg_url)
    packagecert['buildlog url'] = buildlog_url

    binary, package = parse_buildlog(build, fname)
    bincert.update(binary)
    packagecert.update(package)

    print json.dumps(bincert)
    print json.dumps(packagecert)
