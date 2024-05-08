import os
import finisher
THIS_DIR = os.path.dirname(__file__)

cube_type = "R2"

hostname = "s02105.local"
firmware = os.path.join(THIS_DIR, "payload", "r2_fw_assembly-1.3.37.t2_bare.spr")
expected = "1.3.37"

finisher.prod_reboot(hostname,  os.path.join(THIS_DIR, "payload", "openssh_key"))
