import re

from subprocess import Popen, PIPE, STDOUT

PACKAGE_INSTALLED_RE = re.compile('  Installed: (.+)\n', re.M)

def run_command(cmd):
    p = Popen(cmd, stdout=PIPE, stderr=STDOUT,
              shell=True, close_fds=True)
    return p.stdout.read(), p.returncode

def find_package_for_installed_file(fname):
    out, rcode = run_command('apt-file search {}'.format(fname))
    package = ''
    if rcode:
        return package

    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.split(': ')
        if len(line) != 2:
            continue
        if line[1] == fname:
            package = line[0].strip()
            break
    return package

def verify_file_integrity(package, fname):
    # Not that useful in a running system as we're backdoored anyway
    results = []
    out, rcode = run_command('debsums {}'.format(package))
    results = re.findall('^{}\s+OK$'.format(fname), out, re.M)
    return results

def find_installed_package_version(package):
    version = ''
    out, rcode = run_command('apt-cache policy {}'.format(package))
    if rcode:
        return version
    version = PACKAGE_INSTALLED_RE.findall(out)
    if not version:
        return version
    return version[0]

def find_installed_package_meta(package, version):
    sourcepackage = ''
    packagemeta = {}

    found = ''
    desired = 'Version: {}'.format(version)

    out, rcode = run_command('apt-cache show {}'.format(package))

    for vers in out.split('\n\n'):
        if desired in vers:
            found = vers
            break
    if not found:
        return sourcepackage, package

    for line in found.splitlines():
        if not line:
            continue
        if not line[0].isalnum():
            continue
        line = line.split(': ')
        if len(line) != 2:
            continue
        key, value = line
        if key == 'Source':
            sourcepackage = value
        elif key == "Depends":
            packagemeta['bom-depends'] = value.split(', ')
        elif key == "SHA1":
            packagemeta['sha1'] = value.split(', ')
        elif key == "Filename":
            packagemeta['filename'] = value

    if not sourcepackage:
        sourcepackage = package

    return sourcepackage, packagemeta
