# Copyright (c) 2017 Huawei, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import print_function

import argparse
import os
import re
import six
import sys
import time

from conveyorclient.common import constants
from conveyorclient.common.gettextutils import _
from conveyorclient.common import template_utils
from conveyorclient import exceptions
from conveyorclient import utils

DEFAULT_V2V_SERVICE_TYPE = 'conveyor'


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Blocks while an action occurs. Periodically shows progress."""
    def print_progress(progress):
        if show_progress:
            msg = ('\rInstance %(action)s... %(progress)s%% complete'
                   % dict(action=action, progress=progress))
        else:
            msg = '\rInstance %(action)s...' % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    print()
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print("\nFinished")
            break
        elif status == "error":
            print("\nError %(action)s instance" % {'action': action})
            break
        else:
            print_progress(progress)
            time.sleep(poll_period)


def _print_resource(resource):
    utils.print_dict(resource._info)


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])


def _extract_metadata(args):
    metadata = {}
    for metadatum in args.metadata:
        # unset doesn't require a val, so we have the if/else
        if '=' in metadatum:
            (key, value) = metadatum.split('=', 1)
        else:
            key = metadatum
            value = None

        metadata[key] = value
    return metadata


@utils.arg(
    'plan',
    metavar='<plan>',
    help=_('Name or ID of plan.'))
@utils.arg(
    '--sys-clone',
    metavar='<sys_clone>',
    default=False,
    help='Clone the system volume as well or not.')
@utils.arg(
    '--copy-data',
    metavar='<copy_data>',
    default=False,
    help='Copy the volume data as well or not.')
def do_export_clone_template(cs, args):
    """export a clone template. """
    cs.clones.export_clone_template(args.plan, args.sys_clone, args.copy_data)


@utils.arg(
    'plan',
    metavar='<plan>',
    help=_('ID of plan.'))
@utils.arg(
    '--clone_resources',
    metavar="<type=resource_type,id=resource_id>",
    action='append',
    dest='clone_resources',
    default=[],
    help="Add clone or migrate object. Specify option multiple times "
         "to clone or migrate multiple resources. <type>: the type of "
         "object, you can get the types by the command: conveyor "
         "resource-type-list. <id>: the id of object. Both type and id "
         "must be provided")
@utils.arg(
    '--clone_links',
    metavar="<src_id=resource_type,attach_id=resource_id,"
            "src_type=resource_type, attach_type=resource_type>",
    action='append',
    dest='clone_links',
    default=[],
    help="")
@utils.arg(
    '--update_resources',
    metavar="<id=resource_id,type=resource_type>",
    action='append',
    dest='update_resources',
    default=[],
    help="")
@utils.arg(
    '--replace_resources',
    metavar="<src_id=src_resource_id,des_id=des_resource_id,"
            "resource_type=resource_type>",
    action='append',
    dest='replace_resources',
    default=[],
    help="")
@utils.arg(
    'destination',
    metavar="<destination>",
    help="The destination of clone plan")
@utils.arg(
    '--sys-clone',
    metavar='<sys_clone>',
    default=False,
    help='Clone the system volume as well or not.')
@utils.arg(
    '--copy-data',
    metavar='<copy_data>',
    default=False,
    help='Copy the volume data as well or not.')
def do_clone(cs, args):
    """clone resources """
    destination = args.destination
    dst_dict = {}
    for item in destination.split(','):
        key_value = item.split(':')
        if len(key_value) != 2:
            raise exceptions.CommandError(
                "Invalid format. destination format is "
                "<src_az>:<dst_az>[,<src_az>:<dst_az>]")
        dst_dict[key_value[0]] = key_value[1]
    if args.clone_resources:
        res_types = cs.resources.resource_type_list()
        res_type_list = [t.type for t in res_types]
        clone_resources = \
            _extract_clone_resources_argument(args.clone_resources,
                                              res_type_list)
    cs.clones.clone(args.plan, dst_dict, clone_resources,
                    sys_clone=args.sys_clone,
                    copy_data=args.copy_data)


@utils.arg(
    'plan',
    metavar='<plan>',
    help=_('Name or ID of plan.'))
def do_export_migrate_template(cs, args):
    """export a migrate template. """
    cs.migrates.export_migrate_template(args.plan)


@utils.arg(
    'plan',
    metavar='<plan>',
    help=_('Name or ID of plan.'))
@utils.arg(
    'destination',
    metavar="<destination>",
    help="The destination of clone plan")
def do_migrate(cs, args):
    """migrate resources """
    destination = args.destination
    dst_dict = {}
    for item in destination.split(','):
        key_value = item.split(':')
        if len(key_value) != 2:
            raise exceptions.CommandError(
                "Invalid format. destination format is "
                "<src_az>:<dst_az>[,<src_az>:<dst_az>]")
        dst_dict[key_value[0]] = key_value[1]
    cs.migrates.migrate(args.plan, dst_dict)


def do_endpoints(cs, args):
    """Discovers endpoints registered by authentication service."""
    catalog = cs.client.service_catalog.catalog
    for e in catalog['serviceCatalog']:
        utils.print_dict(e['endpoints'][0], e['name'])


@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_resource_type_list(cs, args):
    """Get the types of resources which can be cloned or migrated."""
    types = cs.resources.resource_type_list()
    utils.print_list(types, ["type"])


@utils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Shows details for all tenants. Admin only.')
@utils.arg(
    '--all_tenants',
    nargs='?',
    type=int,
    const=1,
    help=argparse.SUPPRESS)
@utils.arg(
    'type',
    metavar="<type>",
    help="The type of resource, eg: OS::Nova::Server")
@utils.arg(
    '--name',
    metavar="<name>",
    help="The name of resource")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_resource_list(cs, args):
    """Get a list of resources with a specified type."""
    search_opts = {}
    if args.name:
        search_opts["name"] = args.name
    search_opts["type"] = args.type

    resources = cs.resources.list(search_opts)
    _print_resources(resources, args.type)


@utils.arg(
    'type',
    metavar="<type>",
    help="The type of resource.")
@utils.arg(
    'id',
    metavar="<id>",
    help="The id of resource.")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_resource_show(cs, args):
    """Get resource details of specified type."""
    resource = cs.resources.get_resource_detail(args.type, args.id)
    utils.print_json(resource)


@utils.arg(
    'plan_id',
    metavar="<plan_id>",
    help="The id of plan.")
@utils.arg(
    'az_map',
    metavar="<az_map>",
    help="The map of az.")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_show_resource_topo(cs, args):
    """Get resource details of specified type."""
    az_str = args.az_map
    plan_id = args.plan_id
    az_str_list = az_str.split('=')
    az_map = {}
    az_map[az_str_list[0]] = az_str_list[1]
    resource = cs.resources.build_resources_topo(plan_id, az_map)
    utils.print_json(resource)


@utils.arg(
    'plan_id',
    metavar="<plan_id>",
    help="The id of plan.")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_delete_cloned_resources(cs, args):
    """Get resource details of specified type."""
    plan_id = args.plan_id
    cs.resources.delete_cloned_resources(plan_id)


@utils.arg(
    'plan_id',
    metavar="<plan_id>",
    help="The id of plan.")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_list_plan_zone(cs, args):
    """Get resource details of specified type."""
    plan_id = args.plan_id
    az = 'availability_zone'
    resource = cs.resources.list_clone_resources_attribute(plan_id, az)
    utils.print_json(resource)


@utils.arg(
    '--plan-name',
    dest='plan_name',
    metavar='<plan_plan>',
    default=None,
    help='Search with plan name')
@utils.arg(
    '--plan-status',
    dest='plan_status',
    metavar='<plan_status>',
    default=None,
    help='Filter results by plan_status')
@utils.arg(
    '--plan-type',
    dest='plan_type',
    metavar='<plan_type>',
    choices=['clone', 'migrate'],
    help='Filter results by plan_type')
@utils.arg(
    '--all-tenants',
    dest='all_tenants',
    metavar='<0|1>',
    nargs='?',
    type=int,
    const=1,
    default=0,
    help='Show details for all tenants. Admin only.')
@utils.arg(
    '--all_tenants',
    nargs='?',
    type=int,
    const=1,
    help=argparse.SUPPRESS)
@utils.arg(
    '--sort-key',
    dest='sort_key',
    metavar='<sort_key>',
    default=None,
    help='Key to be sorted, available keys are %(keys)s. '
         'OPTIONAL: Default=None.' % {'keys': constants.PLAN_SORT_KEY_VALUES})
@utils.arg(
    '--sort-dir',
    dest='sort_dir',
    metavar='<dort_dir>',
    default=None,
    help='Sort direction, available values are %(values)s. '
         'OPTIONAL: Default=None.' % {'values': constants.SORT_DIR_VALUES})
@utils.arg(
    '--marker',
    dest='marker',
    metavar='<marker>',
    default=None,
    help='The last plan UUID of the previous page; displays list of '
         'plans after "marker".')
@utils.arg(
    '--limit',
    dest='limit',
    metavar='<limit>',
    type=int,
    default=None,
    help='Maximum number of plans to display. If limit == -1, all plans '
         'will be displayed. If limit is bigger than "osapi_max_limit" '
         'option of Conveyor API, limit "osapi_max_limit" will be used '
         'instead.'
)
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_plan_list(cs, args):
    """Get a list of all plans."""
    all_tenants = int(os.environ.get("ALL_TENANTS", args.all_tenants))

    search_opts = {
        'all_tenants': all_tenants,
        'plan_name': args.plan_name,
        'plan_type': args.plan_type,
        'plan_status': args.plan_status
    }

    plans = cs.plans.list(search_opts=search_opts,
                          marker=args.marker,
                          limit=args.limit,
                          sort_key=args.sort_key,
                          sort_dir=args.sort_dir)
    key_list = ['plan_id', 'plan_name', 'plan_type', 'plan_status',
                'task_status', 'created_at']
    if all_tenants:
        key_list.append('project_id')
    utils.print_list(plans, key_list)


@utils.arg('plan', metavar="<plan>", help="UUID of plan to show")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_plan_show(cs, args):
    """Shows plan details."""
    utils.isUUID(args.plan, "plan")
    plan = cs.plans.get(args.plan)
    _print_plan(plan)


@utils.arg('plan', metavar="<plan>", nargs='+', help="UUID of plan to delete")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_plan_delete(cs, args):
    """Delete a plan."""
    failure_count = 0
    for plan in args.plan:
        try:
            utils.isUUID(plan, "plan")
            cs.plans.delete(plan)
        except Exception as e:
            failure_count += 1
            print("Delete for plan %s failed: %s" % (plan, e))
    if failure_count == len(args.plan):
        raise exceptions.CommandError(
            "Unable to delete any of specified plans.")


@utils.arg('plan', metavar="<plan>", nargs='+', help="UUID of plan to delete")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_plan_force_delete(cs, args):
    """Delete a plan."""
    failure_count = 0
    for plan in args.plan:
        try:
            utils.isUUID(plan, "plan")
            cs.plans.force_delete_plan(plan)
        except Exception as e:
            failure_count += 1
            print("Force delete for plan %s failed: %s" % (plan, e))
    if failure_count == len(args.plan):
        raise exceptions.CommandError(
            "Unable to delete any of specified plans.")


@utils.arg(
    '--resources',
    metavar="<obj_type=resource_type,obj_id=resource_id>",
    action='append',
    dest='resources',
    default=[],
    help="Add clone or migrate object. Specify option multiple times "
         "to clone or migrate multiple resources. <type>: the type of "
         "object, you can get the types by the command: conveyor "
         "resource-type-list. <id>: the id of object. Both type and id "
         "must be provided")
@utils.arg(
    '--plan-type',
    dest='plan_type',
    metavar='<plan_type>',
    choices=['clone', 'migrate'],
    help='plan type')
@utils.arg(
    '--plan-name',
    dest='plan_name',
    metavar='<plan_name>',
    default=None,
    help='Create with plan name')
@utils.arg('-f', '--template-file', metavar='<FILE>',
           help='Path to the template.')
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_plan_create(cs, args):
    """Create a plan."""
    plan_name = None
    if args.plan_name:
        plan_name = args.plan_name
    if args.plan_type and args.resources:
        res_types = cs.resources.resource_type_list()
        res_type_list = [t.type for t in res_types]
        resources = _extract_resource_argument(args.resources, res_type_list)

        if args.plan_type not in ["clone", "migrate"]:
            err_msg = ("Invalid type argument! Type should be "
                       "'clone' or 'migrate'.")
            raise exceptions.CommandError(err_msg)

        plan = cs.plans.create(args.plan_type, resources, plan_name=plan_name)
    elif args.template_file:
        tpl_files, template = template_utils.get_template_contents(
            args.template_file)
        plan = cs.plans.create_plan_by_template(template, plan_name=plan_name)
        plan = cs.plans.get(plan.get('plan_id'))
        _print_plan(plan)
    else:
        err_msg = "template file or (type, resources) argument is required! "
        raise exceptions.CommandError(err_msg)


@utils.arg('plan', metavar='<plan>', nargs='+',
           help='ID of plan to modify.')
@utils.arg('--state', metavar='<state>', default='available',
           help=('The state to assign to the volume. Valid values are '
                 '"creating", "available", "cloning", "migrating",'
                 '"finished", "deleting", "error_deleting", "expired" and '
                 '"error." '
                 'Default=available.'))
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_reset_plan_state(cs, args):
    """Explicitly updates the plan state."""
    failure_flag = False

    for plan in args.plan:
        try:
            utils.find_plan(cs, plan).reset_plan_state(args.state)
        except Exception as e:
            failure_flag = True
            msg = "Reset state for plan %s failed: %s" % (plan, e)
            print(msg)

    if failure_flag:
        msg = "Unable to reset the state for the specified plan(s)."
        raise exceptions.CommandError(msg)


@utils.arg(
    '-p', '--properties',
    metavar='<key=value>',
    action='append',
    help='Key/value pair describing the configurations of the '
         'conveyor service.')
@utils.service_type('conveyorConfig')
def do_update_configs(cs, args):

    fields_list = ['properties']
    fields = dict((k, v) for (k, v) in vars(args).items()
                  if k in fields_list and not (v is None))

    fields = utils.args_array_to_dict(fields, 'properties')
    fields = fields.get('properties', {})
    input_dict = {}

    try:
        for k, v in fields.items():
            input_dict[k] = _translate_string_dict(v)
    except ValueError:
        msg = "Input configure key value must be like 'v' or 'k:v' or 'v1,v2'"
        raise exceptions.CommandError(msg)

    if input_dict:
        param = {}
        param['config_file'] = input_dict.pop('config-file', None)
        param['config_info'] = input_dict
        cs.configs.update_configs(**param)
    else:
        msg = "Update configuration info properties is empty"
        raise exceptions.CommandError(msg)


@utils.arg(
    '-p', '--properties',
    metavar='<key=value>',
    action='append',
    help='Key/value pair describing the configurations of the '
         'conveyor service.')
@utils.service_type('conveyorConfig')
def do_config_register(cs, args):

    fields_list = ['properties']
    fields = dict((k, v) for (k, v) in vars(args).items()
                  if k in fields_list and not (v is None))

    fields = utils.args_array_to_dict(fields, 'properties')
    fields = fields.get('properties', {})
    input_dict = {}

    try:
        for k, v in fields.items():
            input_dict[k] = _translate_string_dict(v)
    except ValueError:
        msg = "Input configure key value must be like 'v' or 'k:v' or 'v1,v2'"
        raise exceptions.CommandError(msg)

    if input_dict:
        cs.configs.register_configs(**input_dict)
    else:
        msg = "Update configuration info properties is empty"
        raise exceptions.CommandError(msg)


def _extract_plan_resource_update_args(res_args):
    res = []

    if len(res_args) < 1:
        raise exceptions.CommandError("'resource' argument must be provided.")

    for items in res_args:

        def _replace(m):
            s = m.group(0)
            if s[0] in "\"'":
                return s
            if m.group(1):
                return '"%s"' % s if s != ':' else s
            return s.replace('=', ':')

        new_items = re.sub(r""""[^"]*"|'[^']*'|([:A-Za-z0-9./_-]+)|.""",
                           _replace, items)

        try:
            attrs = eval("{ %s }" % new_items)
        except Exception as e:
            msg = "Invalid resource: %s. %s" % (items, unicode(e))
            raise exceptions.CommandError(msg)

        special_fields = ('user_data', 'public_key')
        for sf in special_fields:
            special_value = attrs.get(sf)
            if special_value and isinstance(special_value, six.string_types):
                if special_value.startswith('/'):
                    with open(special_value, 'r') as f:
                        attrs[sf] = f.read()

        res.append(attrs)

    return res


def _extract_resource_argument(arg_res, res_type_list):
    resources = []

    for res in arg_res:
        err_msg = ("Invalid resource argument '%s'. "
                   "Resource arguments must contain both type and id! "
                   "Eg: --resource type=OS::Nova::Server,id=xxxxx.") % res

        res_opts = {'obj_type': '', 'obj_id': ''}

        for param in res.split(","):
            try:
                k, v = param.split("=", 1)
            except ValueError:
                raise exceptions.CommandError(err_msg)
            if k in res_opts.keys():
                res_opts[k] = v
            else:
                raise exceptions.CommandError(err_msg)

        if not res_opts['obj_type'] or not res_opts['obj_id']:
            raise exceptions.CommandError(err_msg)

        if res_opts['obj_type'] not in res_type_list:
            msg = ("Type unsupported! You can get the types by the "
                   "command: conveyor resource-type-list")
            raise exceptions.CommandError(msg)

        utils.isUUID(res_opts['obj_id'], "id")

        resources.append(res_opts)
    return resources


def _extract_clone_resources_argument(arg_res, res_type_list):
    resources = []

    for res in arg_res:
        err_msg = ("Invalid resource argument '%s'. "
                   "Resource arguments must contain both type and id! "
                   "Eg: --resource type=OS::Nova::Server,id=xxxxx.") % res

        res_opts = {'type': '', 'id': ''}

        for param in res.split(","):
            try:
                k, v = param.split("=", 1)
            except ValueError:
                raise exceptions.CommandError(err_msg)
            if k in res_opts.keys():
                res_opts[k] = v
            else:
                raise exceptions.CommandError(err_msg)

        if not res_opts['type'] or not res_opts['id']:
            raise exceptions.CommandError(err_msg)

        if res_opts['type'] not in res_type_list:
            msg = ("Type unsupported! You can get the types by the "
                   "command: conveyor resource-type-list")
            raise exceptions.CommandError(msg)

        utils.isUUID(res_opts['id'], "id")

        resources.append(res_opts)
    return resources


def _print_plan(plan):
    print("%s:" % plan.plan_id)
    res = {'plan_id': plan.plan_id,
           'plan_name': plan.plan_name,
           'plan_type': plan.plan_type,
           'plan_status': plan.plan_status,
           'task_status': plan.task_status,
           'created_at': plan.created_at,
           'updated_at': plan.updated_at,
           'project_id': plan.project_id,
           'user_id': plan.user_id,
           'stack_id': plan.stack_id,
           'clone_obj': plan.clone_resources,
           }
    utils.print_json(res)


def _print_resources(resources, type):
    if "OS::Nova::Server" == type:
        convert = [('OS-EXT-SRV-ATTR:host', 'host'),
                   ('OS-EXT-STS:task_state', 'task_state'),
                   ('OS-EXT-SRV-ATTR:instance_name', 'instance_name'),
                   ('OS-EXT-STS:power_state', 'power_state'),
                   ('hostId', 'host_id')]
        _translate_keys(resources, convert)
        _translate_server_networks(resources)
        _translate_extended_states(resources)
        columns = [
            'id',
            'Name',
            'Status',
            'Task State',
            'Power State',
            'Networks'
            ]
        formatters = {}
        formatters['Networks'] = utils._format_servers_list_networks
        utils.print_list(resources, columns, formatters)
    else:
        print(resources)


def _translate_server_networks(servers):
    for server in servers:
        networks = {}
        try:
            for network_label, address_list in server.addresses.items():
                networks[network_label] = [a['addr'] for a in address_list]
        except Exception:
            pass
        setattr(server, "networks", networks)


def _translate_extended_states(collection):
    power_states = [
        'NOSTATE',      # 0x00
        'Running',      # 0x01
        '',             # 0x02
        'Paused',       # 0x03
        'Shutdown',     # 0x04
        '',             # 0x05
        'Crashed',      # 0x06
        'Suspended'     # 0x07
    ]

    for item in collection:
        try:
            setattr(item, 'power_state',
                    power_states[getattr(item, 'power_state')])
        except AttributeError:
            setattr(item, 'power_state', "N/A")
        try:
            getattr(item, 'task_state')
        except AttributeError:
            setattr(item, 'task_state', "N/A")


def _translate_string_dict(string):

    # if dict
    if ':' in string:
        if '{' == string[0] and '}' == string[-1]:
            result = eval(string)
        else:
            str_dict = '{' + string + '}'
            result = eval(str_dict)
    # if list
    elif ',' in string:
        result = []
        split_list = string.split(',')
        for l in split_list:
            result.append(l)
    # if string
    else:
        result = string

    return result
