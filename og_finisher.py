import os
import posixpath
import paramiko

THIS_DIR = os.path.dirname(__file__)

def exec_command(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    retcode = stdout.channel.recv_exit_status()
    return stdin, stdout, stderr

def load_gpg_key(hostname, local_gpg_key_path):
    """ Load GPG public key into /etc/spartan_gpg_leys on remote.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")
    sftp_client = client.open_sftp()

    sftp_client.put(local_gpg_key_path, posixpath.join("/home/daemon-installer", "gpg_key.public"))

    exec_command(client, "gpg --homedir /etc/spartan_gpg_keys --ignore-time-conflict --import gpg_key.public")
    exec_command(client, "echo di^20$ | sudo -S chown spartan:daemon-installer /etc/spartan_gpg_keys/trustdb.gpg")
    exec_command(client, "echo di^20$ | sudo -S chmod 660 /etc/spartan_gpg_keys/trustdb.gpg")

def check_gpg_key(hostname, local_gpg_test_payload):
    """ Check that public key loaded properly. Raises AssertException on fail.

    Checks that specifically signed payload can be checked on remote.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")
    sftp_client = client.open_sftp()

    sftp_client.put(local_gpg_test_payload, posixpath.join("/home/daemon-installer", "test_payload.gpg"))    

    exec_command(client, "rm test_payload.clear")
    exec_command(client, "gpg --homedir /etc/spartan_gpg_keys --ignore-time-conflict --output test_payload.clear test_payload.gpg")
    _, stdout, _ = exec_command(client, "cat test_payload.clear")
    payload_content = stdout.readlines()[0]
    assert "content" in payload_content

def set_support_password(hostname, cube_type):
    """ Set support-user password on remote.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")

    if cube_type == "R3":
        exec_command(client, "echo di^20$ | sudo -S sh -c 'echo support-user:fallingfaster | /usr/sbin/chpasswd'")

def load_ssh_key(hostname, local_ssh_pub_key_path):
    """ Set ssh public key into /home/support-user/.ssh/authorized_keys
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")
    sftp_client = client.open_sftp()

    sftp_client.put(local_ssh_pub_key_path, posixpath.join("/home/daemon-installer", "ssh_key_pub"))

    exec_command(client, "echo di^20$ | sudo -S mkdir -p /home/support-user/.ssh")
    exec_command(client, "echo di^20$ | sudo -S sh -c 'cat ssh_key_pub >> /home/support-user/.ssh/authorized_keys'")
    # force newline
    exec_command(client, "echo di^20$ | sudo -S sh -c 'echo >> /home/support-user/.ssh/authorized_keys'")
    exec_command(client, "echo di^20$ | sudo -S chown support-user:support-user /home/support-user/.ssh/authorized_keys")
    exec_command(client, "echo di^20$ | sudo -S chmod 600 /home/support-user/.ssh/authorized_keys")

def check_ssh_login(hostname, local_ssh_private_key):
    """ Check that support-user can login via OpenSSH key
    """
    if local_ssh_private_key is None:
        local_ssh_private_key = os.path.join(THIS_DIR, "payload", "openssh_key")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="support-user", key_filename=local_ssh_private_key, passphrase="fallingfaster", allow_agent=False, look_for_keys=False)
    client.close()
    
def load_sshd_config(hostname, local_sshd_config_path):
    """ Load appropiate sshd_config onto remote. Does not restart ssh.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")
    sftp_client = client.open_sftp()

    sftp_client.put(local_sshd_config_path, posixpath.join("/home/daemon-installer", "sshd_config"))

    exec_command(client, "echo di^20$ | sudo -S cp /etc/ssh/sshd_config /etc/ssh/sshd_config.orig")
    exec_command(client, "echo di^20$ | sudo -S mv /home/daemon-installer/sshd_config /etc/ssh/sshd_config")
    exec_command(client, "echo di^20$ | sudo -S chown root:root /etc/ssh/sshd_config")
    exec_command(client, "echo di^20$ | sudo -S chmod 644 /etc/ssh/sshd_config")

def set_tmptransfer_fs(hostname):
    """ Make filesystem modifications so that `tmptransfer` user works properly.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")
    sftp_client = client.open_sftp()

    # creating chroot jail for tmptransfer and mounting points
    exec_command(client, "echo di^20$ | sudo -S chmod 755 /")
    exec_command(client, "echo di^20$ | sudo -S mkdir -p /transfer")
    exec_command(client, "echo di^20$ | sudo -S 755 /transfer")
    exec_command(client, "echo di^20$ | sudo -S mkdir -p /transfer/home/spartan/runscript_tmp")
    exec_command(client, "echo di^20$ | sudo -S mkdir -p /transfer/nfs/working")

    # setting mount bind to chroot mounting points
    m1 = "/home/spartan/runscript_tmp /transfer/home/spartan/runscript_tmp none bind 0 0"
    m2 = "/nfs/working /transfer/nfs/working none bind 0 0"

    m1_found = False
    m2_found = False

    _, stdout, _ = client.exec_command("cat /etc/fstab")
    fstab_contents = stdout.readlines()
    print(fstab_contents)
    for line in fstab_contents:
        if line.startswith(m1):
            m1_found = True
        if line.startswith(m2):
            m2_found = True
    
    if not m1_found:
        _, stdout, stderr = exec_command(client, """echo di^20$ | sudo -S sh -c 'echo "{}" >> /etc/fstab'""".format(m1))
        stdout.readlines()
        stderr.readlines()
    if not m2_found:
        _, stdout, stderr = exec_command(client, """echo di^20$ | sudo -S sh -c 'echo "{}" >> /etc/fstab'""".format(m2))
        stdout.readlines()
        stderr.readlines()

    _, stdout, stderr = exec_command(client, "echo di^20$ | sudo -S mount -a")
    stdout.readlines()

def unset_tmptransfer_fs(hostname):
    """ Undo changes from `set_tmptransfer_fs`
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")
    sftp_client = client.open_sftp()

    _, stdout, _ = exec_command(client, "echo di^20$ | df /transfer/home/spartan/runscript_tmp")
    for line in stdout.readlines():
        if "No such file or directory" in line:
            # mount point doesn't exist, we don't need to clean up
            pass            
        elif "/transfer/home/spartan/runscript_tmp" in line:
            # bind mount active
            exec_command(client, "echo di^20$ | umount /transfer/home/spartan/runscript_tmp")
            pass
        else:
            # infer that mount point exists, but not bound
            pass
    _, stdout, _ = exec_command(client, "echo di^20$ | df /transfer/nfs/working")
    for line in stdout.readlines():
        if "No such file or directory" in line:
            # mount point doesn't exist, we don't need to clean up
            pass            
        elif "/transfer/nfs/working" in line:
            # bind mount active - let's umount
            exec_command(client, "echo di^20$ | umount /transfer/nfs/working")
            pass
        else:
            # infer that mount point exists, but not bound
            pass

    # unset /etc/fstab
    m1_delete = """ sed -i '\?/home/spartan/runscript_tmp /transfer/home/spartan/runscript_tmp none bind 0 0?d' /etc/fstab"""
    m2_delete = """ sed -i '\?/nfs/working /transfer/nfs/working none bind 0 0?d' /etc/fstab"""

    exec_command(client, "echo di^20$ | sudo -S {}".format(m1_delete))
    exec_command(client, "echo di^20$ | sudo -S {}".format(m2_delete))

def test_tmptransfer(hostname):
    """ Test that tmptranser user works properly.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="tmptransfer", password="precession")
    sftp_client = client.open_sftp()
    payload =  sftp_client.listdir()
    print(payload)
    client.close()
    return payload

def restart_ssh(hostname):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")

    exec_command(client, "echo di^20$ | sudo -S /etc/init.d/sshd restart")

def reboot(hostname):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")

    exec_command(client, "echo di^20$ | sudo -S /sbin/reboot")

def prod_reboot(hostname, local_ssh_private_key):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="support-user", key_filename=local_ssh_private_key, 
        passphrase="fallingfaster", look_for_keys=False, allow_agent=False)

    channel = client.invoke_shell()
    channel_execute(channel, "su daemon-installer")
    channel_execute(channel, "di^20$")
    channel_execute(channel, "echo di^20$ | sudo -S /sbin/reboot")

def install_firmware(hostname, local_fw_file_path):
    fn = os.path.basename(local_fw_file_path)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")
    sftp_client = client.open_sftp()

    sftp_client.put(local_fw_file_path, posixpath.join("/home/daemon-installer", fn))

    return exec_command(client, "echo di^20$ | sudo -S bash /home/daemon-installer/{}".format(fn))

def check_firmware(hostname, expected):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")

    _, stdout, _ = exec_command(client, "if [ -d /nfs/app_data/{} ]; then echo 'ok'; fi".format(expected))
    assert "ok" in stdout.readlines()[0]
    
def set_spartan_prod(hostname):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")
    sftp_client = client.open_sftp()

    exec_command(client, """echo di^20$ | sudo -S sed -i 's/TYPE=.*/TYPE="spartan-prod"/' /etc/spartan_fs_version""")

def set_spartan_devel(hostname):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="daemon-installer", password="di^20$")
    sftp_client = client.open_sftp()

    exec_command(client, """echo di^20$ | sudo -S sed -i 's/TYPE=.*/TYPE="spartan-devel"/' /etc/spartan_fs_version""")    

def channel_execute(channel, cmd, sleep=5, buffer=1024):
    import time
    if cmd[-1] != '\n':
        cmd +=  '\n'
    print(">>> " + cmd[:-1])
    channel.send(cmd)
    time.sleep(sleep)
    return channel.recv(buffer)

def undo_ssh_config(hostname, local_ssh_private_key, cube_type):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="support-user", key_filename=local_ssh_private_key, 
        passphrase="fallingfaster", look_for_keys=False, allow_agent=False)
    sftp_client = client.open_sftp()

    if cube_type == "R3":
        fn = "sshd_config.r3.original"
    sftp_client.put(os.path.join(THIS_DIR, "payload", fn), posixpath.join("/home/support-user/sshd_config"))
    
    channel = client.invoke_shell()
    channel_execute(channel, "su daemon-installer")
    channel_execute(channel, "di^20$")
    channel_execute(channel, "echo di^20$ | sudo -S cp /home/support-user/sshd_config /etc/ssh/sshd_config")
    channel_execute(channel, "echo di^20$ | sudo -S /sbin/reboot")

def prod_check(hostname):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username="support-user", key_filename=os.path.join(THIS_DIR, "payload", "openssh_key"), 
        passphrase="fallingfaster")

def done_check(hostname):
    # check ssh log in with support-user
    print("Checking SSH support-user")
    check_ssh_login(hostname, None)
    print("SSH support-user: PASS")

    # check sftp login with tmptransfer
    print("Checking SFTP tmptransfer")
    payload = test_tmptransfer(hostname)
    assert "nfs" in payload
    assert "home" in payload
    assert "etc" not in payload
    print("SFTP tmptransfer: PASS")

    # check firmware version
    import http.client
    import ssl
    import json

    conn = http.client.HTTPSConnection(hostname, 8080, context=ssl._create_unverified_context())
    conn.request("GET", "/version")
    resp = conn.getresponse()
    data = resp.read().decode('utf-8')
    data = json.loads(data)
    print(data)
    assert 'cube_type' not in data.keys()
    assert data['firmware_assembly_version'] in ('1.4.17')
    print("Assembly Version: {}".format(data['firmware_assembly_version']))
    print("Firmware Check: PASS")