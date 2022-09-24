from typing import Container
from core.container import DataContainer
from core.event import data_containers, data_events
from core.graph.node import Node
from core.graph.versioned_var import VersionedVariable

def node_creation():
    output_list = {}
    latest_node = {}
    data_event_map = {}
    for dc in data_containers:
        map_id = dc.get_related_oe().exec_uuid

        if map_id not in output_list:
            output_list[map_id] = []

        if dc.get_base_id() not in latest_node:
            nd = Node(VersionedVariable(dc.get_name(), dc.get_base_id(), 1))

        else:
            nd = Node(VersionedVariable(dc.get_base_id(), latest_node[dc.get_base_id()].var.ver + 1))

        latest_node[dc.get_base_id()] = nd
        output_list[map_id].append(nd)

        for de in data_events:
            if de.container_id == dc.get_base_id():
                data_event_map[de.get_data_event_id()] = nd
                break

    return output_list, latest_node, data_event_map