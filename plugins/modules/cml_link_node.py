#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Cisco and/or its affiliates.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = r"""
---
module: cml_link_node
short_description: Create, update or delete a link between two nodes in a CML Lab
description:
  - Create, update or delete a link between two nodes in a CML Lab
  - Establishes a link between two nodes
  - Node names need to be specified to create the link
  - Node links can be updated to point to different nodes: node1->node2 is changed to node1->node3
  - Node links can be deleted
  - Note: when updating, all three nodes must be specified
author:
  - Paul Pajerski (@ppajersk)
requirements:
  - virl2_client
version_added: '0.1.0'
options:
    state:
        description: The desired state of the link
        required: false
        type: str
        choices: ['present', 'updated', 'absent']
        default: present

    lab:
        description: The name of the CML lab (CML_LAB)
        required: true
        type: str

    source_node:
        description: The name of the first node
        required: true
        type: str

    source_interface:
        description: The name/label of the first node's interface. Mutually exclusive with source_interface_slot
        required: false
        type: str

    source_interface_slot:
        description: The slot number of the first node's interface. Mutually exclusive with source_interface
        required: false
        type: int

    destination_node:
        description: The name of the second node
        required: true
        type: str

    destination_interface:
        description: The name/label of the second node's interface. Mutually exclusive with destination_interface_slot
        required: false
        type: str

    destination_interface_slot:
        description: The slot number of the second node's interface. Mutually exclusive with destination_interface
        required: false
        type: int

    update_node:
        description: The name of the third node, this node is only used in update commands
        where if provided alongside the updated state, will update the link between source_node and destination_node
        to link between source_node and update_node
        required: false
        type: str

    update_interface:
        description: The name/label of the third node's interface. Mutually exclusive with update_interface_slot
        required: false
        type: str

    update_interface_slot:
        description: The slot number of the third node's interface. Mutually exclusive with update_interface
        required: false
        type: int
"""

EXAMPLES = r"""
- name: Link two CML nodes
  hosts: cml_hosts
  connection: local
  gather_facts: no
  tasks:
    - name: Link nodes
      cisco.cml.cml_link_node:
        host: "{{ cml_host }}"
        user: "{{ cml_username }}"
        password: "{{ cml_password }}"
        lab: "{{ cml_lab }}"
        source_node: "{{ source_node }}"
        destination_node: "{{ destination_node }}"
        state: present

- name: Update a link between two CML nodes
  hosts: cml_hosts
  connection: local
  gather_facts: no
  tasks:
    - name: Link nodes
      cisco.cml.cml_link_node:
        host: "{{ cml_host }}"
        user: "{{ cml_username }}"
        password: "{{ cml_password }}"
        lab: "{{ cml_lab }}"
        source_node: "{{ source_node }}"
        destination_node: "{{ destination_node }}"
        update_node: "{{ update_node }}"
        state: updated

- name: Delete a link between two CML nodes
  hosts: cml_hosts
  connection: local
  gather_facts: no
  tasks:
    - name: Link nodes
      cisco.cml.cml_link_node:
        host: "{{ cml_host }}"
        user: "{{ cml_username }}"
        password: "{{ cml_password }}"
        lab: "{{ cml_lab }}"
        source_node: "{{ source_node }}"
        destination_node: "{{ destination_node }}"
        state: absent
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.cisco.cml.plugins.module_utils.cml_utils import cmlModule, cml_argument_spec

def run_module():
    # define available arguments/parameters a user can pass to the module
    argument_spec = cml_argument_spec()
    argument_spec.update(
        lab=dict(type='str', required=True, fallback=(env_fallback, ['CML_LAB'])),
        state=dict(type='str', required=True, choices=['present', 'updated', 'absent'], default='present'),
        source_node=dict(type='str', required=True),
        source_interface=dict(type='str', required=False),
        source_interface_slot=dict(type='int', required=False),
        destination_node=dict(type='str', required=True),
        destination_interface=dict(type='str', required=False),
        destination_interface_slot=dict(type='int', required=False),
        update_node=dict(type='str', required=False),
        update_interface=dict(type='str', required=False),
        update_interface_slot=dict(type='int', required=False),
    )

    required_if = [
        ['state', 'updated', ['update_node']],
    ]

    required_by = {
        'update_interface': ('update_node', ),
    }

    mutually_exclusive = [
        ['source_interface', 'source_interface_slot'],
        ['destination_interface', 'destination_interface_slot'],
        ['update_interface', 'update_interface_slot'],
    ]

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        required_by=required_by,
        mutually_exclusive=mutually_exclusive,
    )
    cml = cmlModule(module)
    cml.result['changed'] = False
    cml.result['state'] = cml.params['state']

    labs = cml.client.find_labs_by_title(cml.params['lab'])
    if len(labs) > 0:
        lab = labs[0]
    else:
        cml.fail_json("Cannot find lab {0}".format(cml.params['lab']))

    # get both nodes by name
    source_node = cml.get_node_by_name(lab, cml.params['source_node'])
    destination_node = cml.get_node_by_name(lab, cml.params['destination_node'])
    update_node = cml.get_node_by_name(lab, cml.params['update_node'])

    if source_node == None or destination_node == None:
        cml.fail_json("One or more nodes cannot be found. Nodes need to be created before a link can be established")

    if source_node == destination_node:
        cml.fail_json("Source and destination nodes cannot be the same")

    if cml.params['state'] == 'updated' and update_node is None:
        cml.fail_json("State set to updated, but source_node was not found")
    if cml.params['update_node'] and update_node is None:
        cml.fail_json("Update_node specified, but it was not found")

    link = source_node.get_link_to(destination_node)

    # get specified interfaces by label or slot
    source_interface, destination_interface, update_interface = None, None, None
    if cml.params['source_interface'] is not None or cml.params['source_interface_slot'] is not None:
        if cml.params['source_interface'] is not None:
            source_interface = source_node.get_interface_by_label(cml.params['source_interface'])
        elif cml.params['source_interface_slot'] is not None:
            source_interface = source_node.get_interface_by_slot(cml.params['source_interface_slot'])
        if source_interface is None:
            cml.fail_json("Source interface specified, but not found")

    if cml.params['destination_interface'] is not None or cml.params['destination_interface_slot'] is not None:
        if cml.params['destination_interface'] is not None:
            destination_interface = destination_node.get_interface_by_label(cml.params['destination_interface'])
        elif cml.params['destination_interface_slot'] is not None:
            destination_interface = destination_node.get_interface_by_slot(cml.params['destination_interface_slot'])
        if destination_interface is None:
            cml.fail_json("Destination interface specified, but not found")

    if cml.params['update_interface'] is not None or cml.params['update_interface_slot'] is not None:
        if cml.params['update_interface'] is not None:
            update_interface = update_node.get_interface_by_label(cml.params['update_interface'])
        elif cml.params['update_interface_slot'] is not None:
            update_interface = update_node.get_interface_by_slot(cml.params['update_interface_slot'])
        if update_interface is None:
            cml.fail_json("Update interface specified, but not found")

    # Get all links between nodes
    link = None
    links = source_node.get_links_to(destination_node)
    if links:
        if source_interface is None and destination_interface is None:
            # no specific interface specified, just get the first existing link
            link = links[0]
        else:
            # specific interface is specified so need to find the link with matching interfaces
            for ln in links:
                if source_interface is not None and source_interface in ln.interfaces:
                    # source interface is specified and found in link
                    # link between two nodes found with matching source interface
                    # verify destination interface if specified
                    if destination_interface is not None and destination_interface not in ln.interfaces:
                        # destination interface is not found in link
                        cml.fail_json("Link found between nodes but destination interface does not match")
                    link = ln
                    break
                if destination_interface is not None and destination_interface in ln.interfaces:
                    # destination interface is specified and found in link
                    # link between two nodes found with matching destination interface
                    # verify source interface if specified
                    if source_interface is not None and source_interface not in ln.interfaces:
                        # source interface is not found in link
                        cml.fail_json("Link found between nodes but source interface does not match")
                    link = ln
                    break
            else:
                # no existing link found with matching interfaces
                # check if specified interfaces are not used in other links
                if source_interface is not None and source_interface.link is not None:
                    cml.fail_json("Source interface is already used in another link")
                if destination_interface is not None and destination_interface.link is not None:
                    cml.fail_json("Destination interface is already used in another link")

    if cml.params['state'] == 'present':
        if link is None: # if the link does not exist
            if module.check_mode:
                cml.exit_json(changed=True)
            # find source_interface if not specified
            if source_interface is None:
                source_interface = source_node.next_available_interface() or source_node.create_interface()
            # find destination_interface if not specified
            if destination_interface is None:
                destination_interface = destination_node.next_available_interface() or destination_node.create_interface()
            # create link
            link = lab.create_link(source_interface, destination_interface)
            cml.result['changed'] = True
    elif cml.params['state'] == 'updated':
        if link is not None:
            if update_interface is not None and update_interface.link is not None:
                cml.fail_json("Update interface is already used in another link")
            if module.check_mode:
                cml.exit_json(changed=True)
            # remove current link
            lab.remove_link(link)
            # find update_interface if not specified
            if update_interface is None:
                update_interface = update_node.next_available_interface() or update_node.create_interface()
            # create new link
            link = lab.create_link(source_interface, update_interface)
            cml.result['changed'] = True
        else:
            cml.fail_json("Link between nodes does not exist so cannot be updated")
    elif cml.params['state'] == 'absent':
        if link is not None:
            if module.check_mode:
                cml.exit_json(changed=True)
            # remove current link
            lab.remove_link(link)
            cml.result['changed'] = True
    cml.exit_json(**cml.result)

def main():
    run_module()

if __name__ == '__main__':
    main()
