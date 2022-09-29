#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.io.external_storage import ExternalStorage
from core.io.filesystem_adapter import FilesystemAdapter
from core.io.migrate import migrate
from core.io.recover import resume

import torchvision


def main():
    a = [[1], [2], [3]]
    b = [a[0], a[1]] # fundamental limitation? when a and b are restored, they will no longer be sharing items

    # (a, b)
    # is pickle able to preserve the underlying object id when pickling `c`?
    # suppose pickle has the ability to magically figure out the dependencies when restoring 
    #
    c = (a, b)
    
    # [resnet, net]

    resnet = torchvision.models.resnet18(pretrained=True)
    net = resnet
    nn = [resnet, [net]]

    storage = ExternalStorage()
    storage.register("local", FilesystemAdapter())
    
    glbs, locs = globals(), locals()
    context_items = {**glbs, **locs}.items()

    # TODO: modify migrate and recover to wrap all migrated objects in a single list
    migrate([a, nn], "", storage, context_items)
    resume(storage)


if __name__ == '__main__':
    main()
