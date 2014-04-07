#!/usr/bin/env python
"""Manages the instance storage on aws"""

import urllib2
import urlparse
import time
import logging
import os
import json
from subprocess import check_call, CalledProcessError, Popen, PIPE


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

AWS_METADATA_URL = "http://169.254.169.254/latest/meta-data/"

DEFAULT_MOUNT_POINT = '/mnt/instance_storage'
JACUZZI_MOUNT_POINT = '/builds/slave'
JACUZZI_METADATA_FILE = '/etc/jacuzzi_metadata.json'
ETC_FSTAB = '/etc/fstab'


def get_aws_metadata(key):
    """Gets values form AWS_METADATA_URL"""
    url = urlparse.urljoin(AWS_METADATA_URL, key)
    max_tries = 3
    for _ in range(max_tries):
        log.debug("Fetching %s", url)
        try:
            return urllib2.urlopen(url, timeout=1).read()
        except urllib2.URLError:
            if _ < max_tries - 1:
                log.debug("failed to fetch %s; sleeping and retrying",
                          url, exc_info=True)
                time.sleep(1)
                continue
            return None


def run_cmd(cmd, cwd=None, raise_on_error=True, quiet=True):
    """A subprocess wrapper"""
    if not cwd:
        cwd = os.getcwd()
    log.debug("Running: %s cwd: %s", cmd, cwd)
    stdout = None
    stderr = open(os.devnull, 'w')
    if log.level == logging.DEBUG:
        # enable stderr only when we are in DEBUG mode
        stderr = None
    if quiet:
        stdout = open(os.devnull, 'w')
    try:
        check_call(cmd, cwd=cwd, stdout=stdout, stderr=stderr)
        return True
    except CalledProcessError:
        if raise_on_error:
            raise
        return False


def get_output_from_cmd(cmd, cwd=None, raise_on_error=True):
    """A subprocess wrapper but it returns the stdout"""
    # note this is a simple wrapper, do not try to run this function
    # if command produces a lot of output.
    if not cwd:
        cwd = os.getcwd()
    log.debug("Running %s cwd: %s", cmd, cwd)
    # check_output is not avalilable in prod (python 2.6)
    # return check_output(cmd, cwd=cwd, stderr=None).splitlines()
    proc = Popen(cmd, cwd=cwd, stdout=PIPE)
    output, err = proc.communicate()
    retcode = proc.poll()
    if retcode and raise_on_error:
        log.debug('cmd: %s returned %s (%s)', cmd, retcode, err)
        raise CalledProcessError(retcode, cmd, output)
    return output


def get_ephemeral_devices():
    """Gets the list of ephemeral devices"""
    block_devices_mapping = get_aws_metadata("block-device-mapping/")
    if not block_devices_mapping:
        return []
    block_devices = block_devices_mapping.split("\n")
    names = [b for b in block_devices if b.startswith("ephemeral")]
    retval = []
    for name in names:
        device = get_aws_metadata("block-device-mapping/%s" % name)
        device = "/dev/%s" % device
        if not os.path.exists(device):
            device = aws2xen(device)
        if os.path.exists(device):
            retval.append(device)
        else:
            log.warn("%s doesn't exist", device)
    return retval


def aws2xen(device):
    """"Converts AWS device names (e.g. /dev/sdb)
    to xen block device names (e.g. /dev/xvdb)"""
    return device.replace("/s", "/xv")


def format_device(device):
    """formats the disk with ext4 fs if needed"""
    if is_mounted(device):
        log.debug('%s is mounted: skipping formatting', device)
        return
    # assuming this device needs to be formatted
    need_format = True
    blkid_cmd = ['blkid', '-o', 'udev', device]
    output = get_output_from_cmd(cmd=blkid_cmd, raise_on_error=False)
    if output:
        for line in output.splitlines():
            if 'ID_FS_TYPE=ext4' in line or \
               'ID_FS_TYPE=ext3' in line:
               # if the disk is already ext4 or ext3, do not format
                need_format = False
                log.info('%s no need to format: %s', device, line)
                break
    if need_format:
        log.info('formatting %s', device)
        run_cmd(['mkfs.ext4', device])


def needs_pvcreate(device):
    """checks if pvcreate is needed"""
    output = get_output_from_cmd('pvs')
    log.debug("pvs output for device %s: %s ", device, output)
    for line in output.splitlines():
        if device in line:
            return False
    return True


def _query_vgs(token, device=None):
    """gets token value from vgs -o token device"""
    cmd = ['vgs', '-o', token]
    if device:
        cmd.append(device)
    try:
        value = get_output_from_cmd(cmd)
        value = value.split('\n')[1].strip()
        log.debug('vgs: %s = %s', token, value)
        return value
    except (CalledProcessError, IndexError):
        # vgs command failed, no volume groups
        log.debug('No %s for device %s', token, device)
        return None


def query_lv_path(device=None):
    """returns the ouptut of vgs -o lv_path <device>"""
    return _query_vgs(token='lv_path', device=device)


def query_vg_name(device=None):
    """checks if vg already exists and returns its name.
       returns None if there are no vg"""
    return _query_vgs(token='vg_name', device=device)


def create_vg(vg_name, devices):
    """creates a volume group"""
    log.info('creating a new volume group, %s with %s', vg_name, devices)
    run_cmd(['vgcreate', vg_name] + devices)


def remove_vg(vg_name):
    """removes a volume group"""
    if vg_name is None:
        log.debug('remove_vg: vg_name is None, nothing to do here')
    log.info('removing volume group: %s', vg_name)
    run_cmd(['vgremove', '-f', vg_name])


def lvmjoin(devices):
    "Creates a single lvm volume from a list of block devices"
    for device in devices:
        if needs_pvcreate(device):
            log.info('clearing the partition table for %s', device)
            run_cmd(['dd', 'if=/dev/zero', 'of=%s' % device,
                     'bs=512', 'count=1'])
            log.info('creating a new physical volume for: %s', device)
            run_cmd(['pvcreate', '-ff', '-y', device])
    # Volume Group
    vg_name = 'vg'
    lv_name = 'local'
    old_vg = query_vg_name()
    if not old_vg:
        create_vg(vg_name, devices)
    elif old_vg != vg_name:
        # vg already exists with a different name;
        old_lv = query_lv_path()
        # maps output from vgs -> fstab_entry
        fstab_entry = is_dev_in_fstab(old_lv)
        if is_mounted(fstab_entry):
            disable_swap()
            umount(fstab_entry)
        remove_from_fstab(old_vg)
        remove_vg(old_vg)
        create_vg(vg_name, devices)
    else:
        # a volume group with the same name already exists
        # ... there is nothing to do
        pass
    # Logical Volume
    lv_path = "/dev/mapper/%s-%s" % (vg_name, lv_name)
    if not run_cmd(['lvdisplay', lv_path], raise_on_error=False):
        log.info('creating a new logical volume')
        run_cmd(['lvcreate', '-l', '100%VG', '--name', lv_name, vg_name])
        format_device(lv_path)
    return lv_path


def fstab_line(device):
    """check if device is in fstab"""
    is_fstab_line = False
    for line in read_fstab():
        if not line.startswith('#') \
           and device in line:
            log.debug("%s already in %s:", device.strip(), ETC_FSTAB)
            is_fstab_line = line
            break
    return is_fstab_line


def read_fstab():
    """"returns a list of lines in fstab"""
    with open(ETC_FSTAB, 'r') as f_in:
        return f_in.readlines()


def remove_from_fstab(device):
    """removes device from fstab"""
    old_fstab_line = fstab_line(device)
    if not old_fstab_line:
        log.debug('remove_from_fstab: %s is not in fstab', device)
        return
    import tempfile
    try:
        temp_fstab = tempfile.NamedTemporaryFile(delete=False)
        with open(temp_fstab.name, 'w') as out_fstab:
            for line in read_fstab():
                if old_fstab_line not in line:
                    out_fstab.write(line)
        log.debug('removed %s from %s', old_fstab_line.strip(), ETC_FSTAB)
        os.rename(temp_fstab.name, ETC_FSTAB)
    except (OSError, IOError):
        # IOError => error opening temp_fstab
        # OSError => error renaming files
        log.debug('Unable to read/rename temporary fstab file')
        os.remove(temp_fstab.name)
        log.debug('deleted temporary file: %s', temp_fstab.name)


def append_to_fstab(device, mount_location):
    """append device to fstab"""
    new_fstab_line = get_fstab_line(device, mount_location)
    with open(ETC_FSTAB, 'a') as out_f:
        out_f.write(new_fstab_line)
    log.debug('added %s in %s', new_fstab_line, ETC_FSTAB)


def get_fstab_line(device, mount_location):
    """returns an entry for fstab"""
    return '%s %s ext4 defaults,noatime 0 0\n' % (device, mount_location)


def update_fstab(device, mount_location):
    """Updates /etc/fstab if needed"""
    # example:
    # /dev/sda / ext4 defaults,noatime  1 1
    new_fstab_line = get_fstab_line(device, mount_location)
    old_fstab_line = fstab_line(device)
    if old_fstab_line == new_fstab_line:
        # nothing to do..
        log.debug('%s already in %s', new_fstab_line.strip(), ETC_FSTAB)
        return
    # needs to be added
    if not old_fstab_line:
        append_to_fstab(device, mount_location)
        return
    # just in case...
    # log fstab content before updating it
    log.debug(read_fstab())
    remove_from_fstab(device)
    append_to_fstab(device, mount_location)


def get_builders_from(jacuzzi_metadata_file):
    """returns the builders list for the metadata file.
       If the input file cannot be decoded or it does not exist, returns []"""
    try:
        with open(jacuzzi_metadata_file) as data_file:
            json_data = json.load(data_file)
    except (IOError, ValueError, AttributeError):
        log.debug('%s does not exist or it cannot be decoded or is None',
                  jacuzzi_metadata_file)
        return []
    try:
        return json_data['builders']
    except (TypeError, KeyError):
        # json_data is not a dictionary or no keys
        return []


def mount_point():
    """Checks if this machine is part of any jacuzzi pool"""
    # default mount point
    _mount_point = DEFAULT_MOUNT_POINT
    if len(get_builders_from(JACUZZI_METADATA_FILE)) in range(1, 4):
        # if there are 1, 2 or 3 builders: I am a Jacuzzi!
        log.debug('jacuzzi:    yes')
        _mount_point = JACUZZI_MOUNT_POINT
    # parse slave-trustlevel file
    else:
        log.debug('jacuzzi:    no')
    try:
        with open('/etc/slave-trustlevel', 'r') as trustlevel_in:
            trustlevel = trustlevel_in.read().strip()
        log.debug('trustlevel: %s', trustlevel)
        if trustlevel == 'try':
            _mount_point = JACUZZI_MOUNT_POINT
    except IOError:
        # IOError   => file does not exist
        log.debug('/etc/slave-trustlevel does not exist')
    log.debug('mount point: %s', _mount_point)
    return _mount_point


def is_mounted(device):
    """checks if a device is mounted"""
    if not device:
        log.debug('refusing to check if None device is mounted')
        return False
    mount_out = get_output_from_cmd('mount')
    log.debug("mount: %s", mount_out)
    for line in mount_out.splitlines():
        log.debug(line)
        if device in line:
            log.debug('device: %s is mounted', device)
            return True
    log.debug('device: %s is not mounted', device)
    return False


def umount(device):
    """umounts device"""
    if not device:
        log.debug('umount: device in None, returning')
        return
    try:
        get_output_from_cmd(['umount', device])
        log.debug('%s umounted', device)
    except CalledProcessError:
        # unable to umount, pass?
        pass


def disable_swap():
    """disable swap file"""
    log.debug('disabling swap files')
    run_cmd(['swapoff', '-a'])


def get_swap_file():
    """gets the swapfile"""
    try:
        swapfile = get_output_from_cmd(['swapon', '-s'])
        swapfile = swapfile.split('\n')[1].strip()
    except (KeyError, CalledProcessError):
        # KeyError => just a single line
        # CalledProcessError => error executing swapon
        swapfile = None
    log.debug('swapfile => %s', swapfile)
    return swapfile


def real_path(path):
    """path -> real path following symlinks (if any)"""
    try:
        realpath = get_output_from_cmd(['readlink', '-f', path]).strip()
        log.debug('%s => %s', path, realpath)
        return realpath
    except CalledProcessError:
        # file does not exist
        return path


def is_dev_in_fstab(path):
    """checks if a path is mounted
        e.g. /dev/mapper/vg-local and /dev/vg/local are both links to /dev/dm-0
        but only /dev/mapper is in fstab
    """
    # discard /
    fstab = [item.strip() for item in read_fstab()
             if not item.startswith('LABEL=root_dev')]
    # remove special mount points
    fstab = [item for item in fstab if 'none' not in item]
    for item in fstab:
        fstab_entry = item.partition(' ')[0]
        if fstab_entry:
            if real_path(fstab_entry) == real_path(path):
                log.debug('%s and %s point to the same device',
                          fstab_entry, path)
                return fstab_entry
    return None


def mount(device):
    """mounts device according to fstab"""
    mount_p = mount_point()
    if not os.path.exists(mount_p):
        log.debug('Creating directory %s', mount_p)
        os.makedirs(mount_p)
    log.info('mounting %s', device)
    run_cmd(['mount', device])


def main():
    """Prepares the ephemeral devices"""
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
    devices = get_ephemeral_devices()
    if not devices:
        # no ephemeral devices, nothing to do, quit
        log.info('no ephemeral devices found')
        return
    if len(devices) > 1:
        # requires lvm
        log.info('found devices: %s', devices)
        device = lvmjoin(devices)
    else:
        # single device no need for lvm, just format
        device = devices[0]
        log.info('found device: %s', device)
        format_device(device)
    log.info("Got %s", device)
    update_fstab(device, mount_point())
    if not is_mounted(device):
        mount(device)


if __name__ == '__main__':
    main()