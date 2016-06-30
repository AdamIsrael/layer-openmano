from charmhelpers.core.hookenv import (
    config,
    log,
    open_port,
)

from charmhelpers.fetch import (
    install_remote,
)

from charms.reactive import (
    when,
    when_not,
    set_state,
)

import os
import subprocess

@when('db.connected')
def request_db_name():
    relation_set('database=open_mano')
@when('db.available')
@when_not('layer-openmano.installed')
def install_layer_openmano(db):
    cfg = config()

    tmp_dir = install_remote(
        cfg['openmano-repo'],
        dest='/opt/openmano',
        depth='1',
    )

    # Install the database

    # 109 mysql  $DBHOST_ $DBPORT_ $DBUSER_ $DBPASS_ < ${DIRNAME}/${DBNAME}_structure.sql
    # cmd = "mysql {} {} {} {}".format(
    #     db.host(),
    #     db.port(),
    #     db.user(),
    #     db.password(),
    #     db.database(),
    # )
    # p = _run(cmd, stdin="")
    #
    # 112 ${DIRNAME}/migrate_mano_db.sh $DBHOST_ $DBPORT_ $DBUSER_ $DBPASS_ -d$DBNAME
    #
    cmd = "{}/database_utils/init_mano_db.sh -u {} -p {} -h {} -d {}".format(
        tmp_dir,
        db.user(),
        db.password(),
        db.host(),
        db.database()
    )
    output, err = _run(cmd)


    os.mkdir('/home/ubuntu/bin')
    # su $SUDO_USER -c 'mkdir -p ${HOME}/bin'
    #  277 su $SUDO_USER -c 'rm -f ${HOME}/bin/openmano'
    #  278 su $SUDO_USER -c 'rm -f ${HOME}/bin/service-openmano'

    os.symlink("{}/openmano", "/home/ubuntu/bin/openmano")
    os.symlink("{}/scripts/openmano-report.sh", "/home/ubuntu/bin/openmano-report.sh")
    os.symlink("{}/scripts/service-openmano.sh", "/home/ubuntu/bin/service-openmano.sh")

    #  279 su $SUDO_USER -c 'ln -s ${PWD}/openmano/openmano ${HOME}/bin/openmano'
    #  280 su $SUDO_USER -c 'ln -s '${PWD}'/openmano/scripts/openmano-report.sh   ${HOME}/bin/openmano-report'
    #  281 su $SUDO_USER -c 'ln -s '${PWD}'/openmano/scripts/service-openmano.sh  ${HOME}/bin/service-openmano'

    open_port(9090)
    set_state('layer-openmano.installed')



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
        raise subprocess.CalledProcessError(returncode=retcode,
                                            cmd=cmd,
                                            output=stderr.decode("utf-8").strip())
    return (stdout.decode('utf-8'), stderr.decode('utf-8'))
