import subprocess

ret = subprocess.run("git rev-parse HEAD", stdout=subprocess.PIPE)
git_hash = ret.stdout.decode('utf-8')

with open("__version__", "w") as f:
    f.write(git_hash)
    f.truncate()