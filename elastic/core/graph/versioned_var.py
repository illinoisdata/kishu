#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

class VersionedVariable:
    def __init__(self, name: str, vid: int, ver: int) -> None:
        self.name = name
        self.vid = vid
        self.ver = ver
