#!/usr/bin/env python3

import argparse
from random import randrange
import shutil
import socket
from subprocess import check_call
import tempfile
import time
from typing import Optional

import libvirt

from app.service.virt import Virt
from app.service.virt import VirtMode
from app.settings import get_config


class Namespace(argparse.Namespace):
    name: str
    vcpu: str
    ram: str
    size: str
    os: str
    new_password: str
    hostname: Optional[str]


def rand_byte():
    return randrange(0, 0xFF, 1)


def gen_mac():
    return "52:54:%02x:%02x:%02x:%02x" % (rand_byte(), rand_byte(), rand_byte(),
                                          rand_byte())


def create_xml(name, ram_unit, ram, vcpu, mac):
    with open("task/template.xml", "r") as f:
        xml = f.read()
    xml = xml.format(
        name=name,
        ram_unit=ram_unit,
        ram=ram,
        vcpu=vcpu,
        mac=mac,
    )
    return xml


def gen_inventory(file, ip, password):
    file.write(
        f"[all]\ntarget ansible_host={ip} ansible_user=root ansible_ssh_pass={password}"
        .encode())


def create_image(os, size, name):
    target = f"/usr/local/var/lib/libvirt/images/{name}"
    shutil.copyfile(os.path, target)
    check_call(["qemu-img", "resize", target, size])


def wait_for_ssh(host: str = 'localhost', timeout: float = 5.0):
    while True:
        try:
            print("wait")
            with socket.create_connection((host, 22), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(5)


def main(args: Namespace):
    virt = Virt("qemu:///system", VirtMode.READ | VirtMode.WRITE)

    config = get_config()

    os = config.images.get(args.os)
    if os is None:
        print("OS NOT FOUND")
        return

    create_image(os, args.size, args.name)

    ram = args.ram[:-3]
    ram_unit = args.ram[-3:]

    xml = create_xml(
        name=args.name,
        ram_unit=ram_unit,
        ram=ram,
        vcpu=args.vcpu,
        mac=gen_mac(),
    )

    domain = virt.define_vm(xml)
    domain.create()

    # WAIT FOR IP
    iface = None
    while True:
        time.sleep(5)
        iface = domain.interfaceAddresses(
            libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
        if len(list(iface.items())) > 0:
            break
    iface, val = list(iface.items())[0]
    ip = val["addrs"][0]["addr"]

    wait_for_ssh(ip)

    # RUN ANSIBLE
    hostname = args.hostname if args.hostname is not None else args.name

    with tempfile.NamedTemporaryFile() as f:
        check_call([
            "ansible-playbook",
            "-vvv",
            "task/playbook.yml",
            "-e",
            f"newhost={ip}",
            "-e",
            f"defaultpass={os.root_password}",
            "-e",
            f"newpassword={args.new_password}",
            "-e",
            f"newhostname={hostname}",
        ])


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--vcpu", required=True)
    parser.add_argument("--ram", required=True)
    parser.add_argument("--size", required=True)
    parser.add_argument("--os", required=True)
    parser.add_argument("--new-password", required=True)
    parser.add_argument("--hostname")
    return parser.parse_args(namespace=Namespace())


if __name__ == "__main__":
    args = setup()

    main(args)