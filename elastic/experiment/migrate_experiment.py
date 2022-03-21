#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

from core.io.external_storage import ExternalStorage
from core.io.filesystem_adapter import FilesystemAdapter
from experiment.migrate import migrate

import torch 
import torchvision
import os


def main():
    a = 100
    resnet = torchvision.models.resnet18(pretrained=True)
    
    storage = ExternalStorage()
    storage.register("local", FilesystemAdapter())
    
    glbs, locs = globals(), locals()
    context_items = {**glbs, **locs}.items()

    migrate([a, resnet], "", storage, context_items)


if __name__ == '__main__':
    main()
