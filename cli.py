import argparse
import os
import finisher

THIS_DIR = os.path.dirname(__file__)

def do_main_work(hostname, cube_type):
    import warnings
    warnings.filterwarnings(action='ignore', module='.*paramiko.*')
    
    load_keys(hostname, cube_type)
    
    if cube_type == "R3":
        firmware = os.path.join(THIS_DIR, "payload", "r3_fw_assembly-1.4.17.t2_bare.spr")
        expected = "1.4.17" #Firmware Ver
    
    print("Loading Firmware")
    _, stdout, stderr = finisher.install_firmware(hostname, firmware)
    print(stdout.readlines())
    print(stderr.readlines())

    print("Checking Firmware")
    finisher.check_firmware(hostname, expected)
    print("Firmware GOOD")

    print("Setting spartan-prod")
    finisher.set_spartan_prod(hostname)

    print("Setting sshd_config")
    if cube_type == "R3":
        finisher.load_sshd_config(hostname, os.path.join(THIS_DIR, "payload", "sshd_config.r3.prod"))

    print("Setting tmptransfer")
    finisher.set_tmptransfer_fs(hostname)

    print("Restarting ssh")
    finisher.restart_ssh(hostname)

    import time
    time.sleep(5.0)
    print("Testing SFTP tmptransfer")
    finisher.test_tmptransfer(hostname)
    print("SFTP tmptransfer GOOD")

    print("Rebooting...")
    finisher.prod_reboot(hostname,  os.path.join(THIS_DIR, "payload", "openssh_key"))
    
def load_keys(hostname, cube_type):
    import finisher
    import warnings
    print("Loading GPG keys")
    finisher.load_gpg_key(hostname, os.path.join(THIS_DIR, "payload", "fw-sign-prod-01.pub"))

    print("Checking GPG key")
    finisher.check_gpg_key(hostname, os.path.join(THIS_DIR, "payload", "test_payload.gpg"))
    print("GPG Key GOOD")

    print("Setting support-user password")
    finisher.set_support_password(hostname, cube_type)

    print("Loading SSH Keys")
    finisher.load_ssh_key(hostname, os.path.join(THIS_DIR, "payload", "auth_key_format.pub"))

    print("Checking SSH Key Login")
    finisher.check_ssh_login(hostname, os.path.join(THIS_DIR, "payload", "openssh_key"))
    print("SSH Key GOOD")

def main():
    parser = argparse.ArgumentParser("Cube Finishing Tool")
    parser.add_argument("hostname", help="Hostname of cube. Can ommit .local")
    parser.add_argument("--cube-type", help="Cube Type")
    parser.add_argument("--undo-ssh", help="Undo sshd_config", action='store_true')
    parser.add_argument("--keys-only", help="Upload keys only", action='store_true')
    parser.add_argument("--undo-sftp", help="Undo tmptransfer filesystem changes", action="store_true")

    opts = parser.parse_args()

    hostname = opts.hostname
    if hostname.endswith(".local"):
        pass
    else:
        hostname = hostname + ".local"

    CUBE_TYPE = "R3"

    if opts.cube_type is not None:
        CUBE_TYPE = opts.cube_type

    if opts.keys_only:
        print("Setting GPG and SSH Keys only")
        load_keys(hostname, CUBE_TYPE)
    elif opts.undo_ssh or opts.undo_sftp:
        if opts.undo_ssh:
            print("Undoing production sshd_config")
            finisher.undo_ssh_config(hostname,  os.path.join(THIS_DIR, "payload", "openssh_key"), CUBE_TYPE)
        if opts.undo_sftp:
            print("Undoing tmptransfer")
            finisher.unset_tmptransfer_fs(hostname)
    else:
        print("Doing everything")
        do_main_work(hostname, CUBE_TYPE)


if __name__ == "__main__":
    main()