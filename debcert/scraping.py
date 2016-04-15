import re
import requests

from bs4 import BeautifulSoup

def get_buildlog(sourcepkg_url, arch='amd64'):
    # scraping fun yeah!
    html_doc = requests.get(sourcepkg_url)
    soup = BeautifulSoup(html_doc.text, 'html.parser')
    a = [x for x in soup.select("#source-builds a") if arch in x][0]
    amd64url = 'https://launchpad.net' + a.attrs['href']

    amd64 = requests.get(amd64url).text
    soup = BeautifulSoup(amd64, 'html.parser')

    a = [x for x in soup.select('a.sprite.download') if 'buildlog' in x][0]
    buildlog_url = a.attrs['href']

    return buildlog_url, requests.get(buildlog_url).text

def parse_buildlog(build, fname):
    # There's a lot of stuff in the build log, this is just a parser
    # that has worked in a single testcase

    lines = build.splitlines()
    # Containers for both binary and package cert stuff
    binary = dict()
    package = dict()

    cflags = ''
    curline = [x for x in lines if x.startswith('CFLAGS')]
    if curline:
        curline = curline[0]
        cflags = curline.strip()
        while curline.endswith('\\'):
            cflags = cflags.rstrip('\\')
            cindex = lines.index(curline)
            curline = lines[cindex+1]
            cflags += curline.strip()

        binary['cflags'] = cflags

    buildcmd = ''
    buildfile = [x for x in lines if x.endswith(fname) and ' as ' in x]
    if buildfile:
        buildfile = buildfile[0].split()
        if len(buildfile) > 2:
            buildfile = buildfile[2]
            buildcmd = re.findall('^.+-o \S+{} .+$'.format(buildfile), 
                                  build, re.M)
    if not buildcmd:
        buildcmd = re.findall('^.+-o \S*{} .+$'.format(fname.split('/')[-1]), 
                              build, re.M)

    if buildcmd:
        binary['buildcmd'] = buildcmd

    return binary, package

