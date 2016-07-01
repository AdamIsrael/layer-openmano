import os
import subprocess

from charmhelpers.core import host
from charmhelpers.core import hookenv
from charmhelpers.core import templating
from charmhelpers.core.unitdata import kv
from charmhelpers.core.hookenv import (
    config,
    log,
    open_port,
    status_set,
)

from charmhelpers.fetch import (
    install_remote,
)

from charms.reactive import (
    when,
    when_not,
    set_state,
    is_state,
)

kvdb = kv()

INSTALL_PATH = '/opt/openmano'
USER = 'openmanod'


@when('openmano.installed')
@when('openmano.available')
def openmano_available(openmano):
    # TODO make this configurable via charm config
    openmano.configure(port=9090)


@when('openmano.installed')
@when('openvim-controller.available')
def openvim_available(openvim):
    for service in openvim.services():
        for endpoint in service['hosts']:
            host = endpoint['hostname']
            port = endpoint['port']
            user = endpoint['user']

            openvim_uri = '{}:{}'.format(host, port)
            if kvdb.get('openvim_uri') == openvim_uri:
                return

            out, err = _run(
                './scripts/create-datacenter.sh {} {} {} {}'.format(
                    host, port, user, kvdb.get('openmano-tenant')))

            kvdb.set('openvim_uri', openvim_uri)
            if not is_state('db.available'):
                status_set('waiting', 'Waiting for database')
            break
        break


@when('openmano.installed')
@when('db.available')
@when('openvim-controller.available')
@when_not('openmano.running')
def start(*args):
    cmd = "/home/{}/bin/service-openmano start".format(USER)
    out, err = _run(cmd)

    if not kvdb.get('openmano-tenant'):
        out, err = _run('./scripts/create-tenant.sh')
        kvdb.set('openmano-tenant', out.strip())

    status_set(
        'active',
        'Up on {host}:{port}'.format(
            host=hookenv.unit_public_ip(),
            port='9090'))

    set_state('openmano.running')


@when('openmano.installed')
@when('db.available')
def setup_db(db):
    """Setup the database

    """
    db_uri = 'mysql://{}:{}@{}:{}/{}'.format(
        db.user(),
        db.password(),
        db.host(),
        db.port(),
        db.database(),
    )

    if kvdb.get('db_uri') == db_uri:
        # We're already configured
        return

    status_set('maintenance', 'Initializing database')

    cmd = "{}/database_utils/init_mano_db.sh ".format(kvdb.get('repo'))
    cmd += "-u {} -p{} -h {} -d {} -P {}".format(
        db.user(),
        db.password(),
        db.host(),
        db.database(),
        db.port(),
    )
    output, err = _run(cmd)

    context = {
        'user': db.user(),
        'password': db.password(),
        'host': db.host(),
        'database': db.database(),
        'port': db.port(),
    }
    templating.render(
        'openmanod.cfg',
        os.path.join(kvdb.get('repo'), 'openmanod.cfg'),
        context,
        owner=USER,
        group=USER,
    )
    kvdb.set('db_uri', db_uri)


@when_not('openvim-controller.available')
def need_openvim():
    status_set('waiting', 'Waiting for vim')


@when_not('db.available')
def need_db():
    status_set('waiting', 'Waiting for database')


@when_not('db.available')
@when_not('openvim-controller.available')
def need_everything():
    status_set('waiting', 'Waiting for database and vim')


@when_not('openmano.installed')
def install_layer_openmano():
    status_set('maintenance', 'Installing')

    cfg = config()

    # TODO change user home
    # XXX security issue!
    host.adduser(USER, password=USER)

    # TODO check out a branch
    dest_dir = install_remote(
        cfg['source'],
        dest=INSTALL_PATH,
        depth='1',
        branch='master',
    )
    host.chownr(dest_dir, USER, USER)
    kvdb.set('repo', dest_dir)

    os.mkdir('/home/{}/bin'.format(USER))

    os.symlink(
        "{}/openmano".format(dest_dir),
        "/home/{}/bin/openmano".format(USER))
    os.symlink(
        "{}/scripts/openmano-report.sh".format(dest_dir),
        "/home/{}/bin/openmano-report.sh".format(USER))
    os.symlink(
        "{}/scripts/service-openmano.sh".format(dest_dir),
        "/home/{}/bin/service-openmano".format(USER))

    open_port(9090)
    set_state('openmano.installed')


def _run(cmd, env=None):
    if isinstance(cmd, str):
        cmd = cmd.split() if ' ' in cmd else [cmd]

    log(cmd)
    p = subprocess.Popen(cmd,
                         env=env,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    retcode = p.poll()
    if retcode > 0:
        raise subprocess.CalledProcessError(
            returncode=retcode,
            cmd=cmd,
            output=stderr.decode("utf-8").strip())
    return (stdout.decode('utf-8'), stderr.decode('utf-8'))
