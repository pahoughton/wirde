#!/usr/bin/env python
'''Install puppet and other dependencies based on operating system.

Once puppet is installed it apply's deps.pp to install the rest of
the product's dependencies.
'''
import os
import sys
import platform
import urllib
import subprocess as sp
import re

def which(filename):
    """docstring for which"""
    locs = os.environ.get("PATH").split(os.pathsep)
    for loc in locs:
        fn = os.path.join(loc, filename)
        if os.path.isfile(fn) and os.access(fn, os.X_OK):
            print 'found:',fn
            return fn
    return None

def sysdo(cmd):
    print 'run:',' '.join(cmd)
    sout = sp.check_output(cmd).decode('utf-8')
    print repr(sout)

def install_osx_package(pkgfn):
    '''install an osx .pkg file
    '''
    instcmd = ['installer',
               '-pkg',
               pkgfn,
               '-target',
               '/']
    print 'install:',' '.join(instcmd)
    sout = None
    installed = False
    try:
        sout = sp.check_output(instcmd)
        print sout
        installed = True
    except Exception,e:
        print 'FAILED',e
        if sout:
            print sout

    return installed

def install_puppet():
    '''install puppet

    returns true on success, false on failure
    '''
    print 'Installing puppet'
    if platform.system() == 'Darwin':
        tmpdir = 'build/tmp'
        mntdir = os.path.join(tmpdir,'mount')

        if not os.path.isdir(mntdir):
            os.makedirs(mntdir)

        url_base = 'http://downloads.puppetlabs.com/mac/'
        files = ['puppet-3.3.0.dmg',
                 'facter-1.7.3.dmg',
                 'hiera-1.2.1.dmg']

        for fn in files:
            dmgfn = os.path.join(tmpdir,fn)
            pkgfn = os.path.join(mntdir,fn.replace('.dmg','.pkg'))

            if not os.path.isfile(dmgfn):
                print 'Downloading',fn,' ...'
                urllib.urlretrieve(url_base+fn,
                                   os.path.join(tmpdir,fn))

            mntcmd = ['hdiutil',
                      'attach',
                      '-mountpoint',
                      mntdir,
                      os.path.join(tmpdir,fn)]
            sysdo(mntcmd)

            didinstall = install_osx_package(pkgfn)
            umntcmd = ['hdiutil',
                       'detach',
                       mntdir]
            sysdo(umntcmd)
            if not didinstall:
                sys.exit(1)

    elif platform.system() == 'Linux':
        yum_platforms = ['fedora','centos','redhat']
        if platform.dist()[0] in yum_platforms:
            repourl = 'http://yum.puppetlabs.com/'
            repoloc = None
            (os_name, os_ver, os_vername) = platform.dist()
            if os_name in ['centos','redhat']:
                repoloc = '/'.join(['el',
                                   os_ver,
                                   'products',
                                   'i386',
                                   'puppetlabs-release-'
                                   +os_ver
                                   +'-7.noarch.rpm'])
            elif os_name == 'fedora':
                repoloc = '/'.join(['fedora',
                                    'f'+os_ver,
                                    'products',
                                    'i386',
                                    'puppetlabs-release-'])
                if os_ver in ['17','18']:
                    repoloc += os_ver + '-7'
                elif os_ver == '19':
                    repoloc += os_ver + '-2'
                else:
                    print 'Unsupported OS:',os_name,' ',os_ver
                    sys.exit(1)
                repoloc +='.noarch.rpm'
            else:
                print 'Unsupported OS:',os_name,' ',os_ver
                sys.exit(1)

            sysdo(['rpm', '-ivh', repourl+repoloc])
            sysdo(['yum', '-y','install', 'puppet'])

        elif platform.dist()[0] in ['Ubuntu','debian']:
            fname = 'puppetlabs-release-'+platform.dist()[2]+'.deb'
            url = 'http://apt.puppetlabs.com/'

            sysdo(['wget', url+fname])
            sysdo(['dpkg','-i',fname])
            sysdo(['apt-get','-y','update'])
            sysdo(['apt-get','-y','install','puppet'])

        else:
            print 'Unsupported platform: '+platform.system()
            sys.exit( 1 )

    else:
        print 'Unsupported platform: '+platform.system()
        sys.exit( 1 )

def install_macports():
    '''install macports

    Not this requires xcode install and automated installation
    is not possible

    returns true on success, false on failure
    '''
    if not which('xcode-select'):
        print 'A current version of xcode is required to install macports'
        sys.exit(1)

        os_ver = platform.mac_ver()
        os_ver = re.sub(r'^(\d+)\.(\d+).*',r'\1.\2',os_ver)
        pkgfn = 'MacPorts-2.2.0-'

        if os_ver == '10.8':
            pkgfn += os_ver+'-MountainLion.pkg'
        elif os_ver in ['10.7','10.6']:
            pkgfn += '10.6-SnowLeopard.pkg'
        else:
            print 'Unsupported mac os version:',os_ver

        macports_url = 'https://distfiles.macports.org/MacPorts/'+pkgfn

        tmpdir = 'build/tmp'
        if not os.path.isdir(tmpdir):
            os.makedirs(tmpdir)

        # from pkgname.pkg to build/tmp/pkgname.pkg
        pkgfn = os.path.join(tmpdir,pkgfn)

        if not os.path.isfile(pkgfn):
            print 'Downloading',pkgfn,' ...'
            urllib.urlretrieve(macports_url, pkgfn)

        if not install_osx_package(pkgfn):
            sys.exit(1)


# Only run in my toplevel directory
if not os.path.isfile('deps.pp'):
    print 'deps.pp not found. Only run this script in product top directory'
    sys.exit( 1 )

if which('puppet'):
    sout = sp.check_output(['puppet','--version']).decode('utf-8')
    if '3.3' in sout:
        print 'Puppet 3.3 found'
    else:
        install_puppet()
else:
    install_puppet()

if platform.system() == 'Darwin' and not which('port'):
    # need macports for os x
    install_macports()

cmd = ['puppet','apply','deps.pp']
print 'run:',' '.join(cmd)
sout = sp.check_output(cmd)
print sout
print 'Dependencies installed, enjoy ;)'
