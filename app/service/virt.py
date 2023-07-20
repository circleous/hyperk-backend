from enum import IntFlag
from typing import Any, List
from uuid import UUID
from uuid import uuid4

import libvirt


class VirtMode(IntFlag):
    UNKNOWN = 0
    READ = 1
    WRITE = 2


class Virt:
    mode: VirtMode
    conn: libvirt.virConnect

    def __init__(self,
                 uri: str,
                 mode: VirtMode = VirtMode.READ,
                 auth: Any = None) -> None:
        if mode & (VirtMode.READ | VirtMode.WRITE):
            self.conn = libvirt.open(uri)
        elif mode & (VirtMode.READ | VirtMode.WRITE) and auth is not None:
            raise NotImplementedError("auth is not supported yet!")
        elif mode & VirtMode.READ:
            self.conn = libvirt.openReadOnly(uri)
        self.mode = mode

    def get_vm_by_name(self, name: str) -> libvirt.virDomain:
        return self.conn.lookupByName(name)

    def get_vm_by_id(self, id: UUID) -> libvirt.virDomain:
        return self.conn.lookupByUUIDString(str(id))

    def get_vms(self) -> List[libvirt.virDomain]:
        return self.conn.listAllDomains()

    def define_vm(self, xml: str) -> libvirt.virDomain:
        if not (self.mode & VirtMode.WRITE):
            raise RuntimeError(
                "tying to write access while VirtConnect are read only mode")
        domain = self.conn.defineXML(xml)
        return domain

    def close(self) -> None:
        self.conn.close()


if __name__ == "__main__":
    pass