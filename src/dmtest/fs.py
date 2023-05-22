import dmtest.process as process
import dmtest.utils as utils

from contextlib import contextmanager
import os


class BaseFS:
    def __init__(self, dev, mount_point=None):
        self._dev = dev
        self._mount_point = mount_point

    def format(self, **opts):
        cmd = self.mkfs_cmd(opts)
        _ = process.run(cmd)

    def mount(self, mount_point, **opts):
        self._mount_point = mount_point
        os.makedirs(mount_point, exist_ok=True)
        cmd = self.mount_cmd(mount_point, opts)
        _ = process.run(cmd)

    def umount(self):
        process.run(f"umount {self._mount_point}")
        os.rmdir(self._mount_point)
        self.check()

    def check(self):
        process.run("echo 1 > /proc/sys/vm/drop_caches")
        process.run(self.check_cmd())

    @contextmanager
    def mount_and_chdir(self, mount_point, **opts):
        self.mount(mount_point, **opts)
        try:
            cwd = os.getcwd()  # store current working directory
            os.chdir(mount_point)  # change current working directory to mount point
            yield
        finally:
            os.chdir(cwd)  # restore original working directory
            self.umount()


class Ext4(BaseFS):
    def mount_cmd(self, mount_point, opts):
        return f"mount {self._dev} {mount_point} {'-o discard' if opts.get('discard', False) else ''}"

    def check_cmd(self):
        return f"fsck.ext4 -fn {self._dev}"

    def mkfs_cmd(self, opts):
        discard_arg = "discard" if opts.get("discard", True) else "nodiscard"
        return f"mkfs.ext4 -F -E lazy_itable_init=1,{discard_arg} {self._dev}"


class Xfs(BaseFS):
    def mount_cmd(self, mount_point, opts):
        discard_arg = ",discard" if opts.get("discard", False) else ""
        return f"mount -o nouuid{discard_arg} {self._dev} {self._mount_point}"

    def check_cmd(self):
        return f"xfs_repair -n {self._dev}"

    def mkfs_cmd(self, opts):
        discard_arg = "" if opts.get("discard", True) else "-K"
        return f"mkfs.xfs -f {self._dev} {discard_arg}"
