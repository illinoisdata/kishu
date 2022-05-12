#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

import argparse
from datetime import datetime
import logging
import os
import sys

# experiment constants
MODE_LOCAL, MODE_REMOTE = "local", "remote"
MODES = [MODE_LOCAL, MODE_REMOTE]

# begin configure logging
CUR_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_DIR = "{}/logs".format(CUR_DIR)
os.makedirs(LOG_DIR, exist_ok=True)

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

for HDL in [
    logging.StreamHandler(sys.stdout), 
    logging.FileHandler("{}/{}".format(LOG_DIR, datetime.now().isoformat()))
]:
    HDL.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    LOG.addHandler(HDL)
# end configure logging


def parse_args():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--destination", help="public ip of the destination server")
    
    return parser.parse_args()

def validate_args(args):
    LOG.info("Running in {} mode.".format(args.mode))
    if args.mode == MODE_REMOTE:
        if args.destination is None:
            raise RuntimeError("Destination server ip must be provided in remote mode.")
        LOG.info("Migrating to destination server {}".format(args.destination))

def main(args):
    try:
        validate_args(args)
    except Exception as e:
        LOG.error(e)
        LOG.error("Exiting due to expected error.")

if __name__ == "__main__":
    args = parse_args()
    main(args)
