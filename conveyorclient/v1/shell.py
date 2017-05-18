# Copyright 2010 Jacob Kaplan-Moss
#
# Copyright (c) 2011-2014 OpenStack Foundation
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import argparse
import copy
import os
import sys
import time
import six
import re

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

 
@utils.arg('plan',
    metavar='<plan>',
    help=_('Name or ID of plan.'))
@utils.arg('--sys_clone',  
           metavar='<sys_clone>',
           default=False,
           help='Clone the system volume as well or not.')
def do_export_clone_template(cs, args):
    """export a clone template. """
    cs.clones.export_clone_template(args.plan, args.sys_clone)

@utils.arg('plan',
    metavar='<plan>',
    help=_('Name or ID of plan.'))
@utils.arg('destination',
     metavar="<destination>",
     help="The destination of clone plan")
@utils.arg('--sys_clone',  
           metavar='<sys_clone>',
           default=False,
           help='Clone the system volume as well or not.')
def do_clone(cs, args):
    """clone resources """
    cs.clones.clone(args.plan, args.destination, args.sys_clone)

@utils.arg('plan',
    metavar='<plan>',
    help=_('Name or ID of plan.'))
def do_export_migrate_template(cs, args):
    """export a migrate template. """
    cs.migrates.export_migrate_template(args.plan)

@utils.arg('plan',
    metavar='<plan>',
    help=_('Name or ID of plan.'))
@utils.arg('destination',
     metavar="<destination>",
     help="The destination of clone plan")
def do_migrate(cs, args):
    """migrate resources """
    cs.migrates.migrate(args.plan, args.destination)
    

def do_endpoints(cs, args):
    """Discovers endpoints registered by authentication service."""
    catalog = cs.client.service_catalog.catalog
    for e in catalog['serviceCatalog']:
        utils.print_dict(e['endpoints'][0], e['name'])



@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_resource_type_list(cs, args):
    """Get the types of resources which can be cloned or migrated."""
    types = cs.resources.resource_type_list()
    #print(types)
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
@utils.arg('type',
     metavar="<type>",
     help="The type of resource, eg: OS::Nova::Server")
@utils.arg('--name',
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


@utils.arg('type',
     metavar="<type>",
     help="The type of resource.")
@utils.arg('id',
     metavar="<id>",
     help="The id of resource.")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_resource_show(cs, args):
    """Get resource details of specified type."""
    resource = cs.resources.get_resource_detail(args.type, args.id)
    #print(resource)
    utils.print_json(resource)


@utils.arg('plan_id',
     metavar="<plan-id>",
     help="The uuid of plan")
@utils.arg('resource_id',
     metavar="<resource-id>",
     help="The identifier of resource, eg: server_0, volume_4")
@utils.arg('--original',
    dest='original',
    metavar='<0|1>',
    default=True,
    nargs='?',
    type=int,
    const=1,
    help=_('Get resource details from original resources ' 
           'or updated resources.'))
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_plan_resource_show(cs, args):
    """Get the details of specified resource in a plan."""
    resource_id = args.resource_id
    plan_id = args.plan_id
    utils.isUUID(plan_id, "plan")
    resource = cs.resources.get_resource_detail_from_plan(resource_id, plan_id, 
                                                          args.original)
    #print result
    attr = resource.get("properties", {})
    attr["id"] = resource.get("id", "")
    attr["resource_type"] = resource.get("type", "")
    attr["resource_name"] = resource.get("name", "")
    parameters = []
    for opt, value in resource.get("parameters", {}).items():
        parameters.append({opt: value.get("default")})
    attr["parameters"] = parameters
    utils.print_dict(attr)


@utils.arg('plan_id',
     metavar="<plan-id>",
     help="The uuid of plan")
@utils.arg('--resource',
     metavar="action=action-type,key1=value1[,key2=value2...]",
     action='append',
     dest='resource',
     default=[],
     help=_("Specify option multiple times to update multiple resources. "
     "The keys can be chose from (resource_id, id and the fields of specific resource)."
     "'resource_id' is the identifier of resource in plan, such as OS::Nova::Server. "
     "'id' is the actual id, it's uuid of most resources, "
     "or name of special resources, such as keypair. "
     "action: resource operation type (add, edit or delete)."
     "If action is add, id and resource_type of new resource must be provided. "
     "If action is edit, resource_id and the fields to be edited must be provided. "
     "If action is delete, resource_id must be provided."
     "Notice that if you want update some non-independent resources, "
     "you'd better update all corresponding resources in order of the "
     "dependencies at the same time. "
     "For example, you can update port resource by providing "
     "(network, subnet, port) resources in order."))
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_plan_resource_update(cs, args):
    """Update resources of specific plan."""
    utils.isUUID(args.plan_id, "plan")
    res = _extract_plan_resource_update_args(args.resource)
    cs.plans.update_plan_resource(args.plan_id, res)


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
    key_list = ['plan_id', 'plan_type', 'plan_status', 
                'task_status', 'created_at', 'expire_at']
    if all_tenants:
        key_list.append('project_id')
    utils.print_list(plans, key_list)
    

@utils.arg('plan',
     metavar="<plan>",
     help="UUID of plan to show")
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_plan_show(cs, args):
    """Shows plan details."""
    utils.isUUID(args.plan, "plan")
    plan = cs.plans.get(args.plan)
    _print_plan(plan)
    
@utils.arg('plan',
     metavar="<plan>",
     nargs='+',
     help="UUID of plan to delete")
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
        raise exceptions.CommandError("Unable to delete any of specified plans.")

@utils.arg('plan',
     metavar="<plan>",
     nargs='+',
     help="UUID of plan to delete")
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
        raise exceptions.CommandError("Unable to delete any of specified plans.")

@utils.arg('--resources',
     metavar="<type=resource_type,id=resource_id>",
     action='append',
     dest='resources',
     default=[],
     help="Add a resource to clone or migrate. "
     "Specify option multiple times to clone or migrate multiple resources. "
     "<type>: the type of resource, you can get the types by the command: conveyor resource-type-list. "
     "<id>: the id of resource. "
     "Both type and id must be provided")
@utils.arg('--type',
     metavar="<type>",
     help="clone or migrate")
@utils.arg('-f', '--template-file', metavar='<FILE>',
           help='Path to the template.')
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_plan_create(cs, args):
    """Create a plan."""
    if args.type and args.resources:
        res_types = cs.resources.resource_type_list()
        res_type_list = [t.type for t in res_types]
        resources = _extract_resource_argument(args.resources, res_type_list)
        
        if args.type not in ["clone", "migrate"]:
            err_msg = ("Invalid type argument! Type should be 'clone' or 'migrate'.")
            raise exceptions.CommandError(err_msg)
        
        plan = cs.plans.create(args.type, resources)
        
        print("plan_id: %s" % plan.plan_id)
        utils.print_json(plan.original_dependencies)
    elif args.template_file:
        tpl_files, template = template_utils.get_template_contents(
                                                        args.template_file)
        plan = cs.plans.create_plan_by_template(template)
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


@utils.arg('--plan-id',
     metavar="<plan-id>",
     help="The uuid of plan")
@utils.arg('-f', '--template-file', metavar='<FILE>',
           help='Path to the template.')
@utils.arg('-r', '--enable-rollback', default=False, action="store_true",
           help='Enable rollback on create/update failure.')
@utils.service_type(DEFAULT_V2V_SERVICE_TYPE)
def do_template_clone(cs, args):
    '''Clone resource'''
    tpl_files, template = template_utils.get_template_contents(
        args.template_file)
   
    disable_rollback =  not(args.enable_rollback)
    plan_id = args.plan_id
    cs.clones.start_clone_template(plan_id, disable_rollback, template)

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
            input_dict[k] =  _translate_string_dict(v)
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
                #return '"%s"' % s.replace('-', '_')
                return '"%s"' % s if s != ':' else s
            return s.replace('=', ':')
        
        new_items = re.sub(r""""[^"]*"|'[^']*'|([:A-Za-z0-9./_-]+)|.""", _replace, items)

        try:
            attrs = eval("{ %s }"  % new_items)
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
        
        res_opts = {'type': '', 'id':''}
        
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
            msg = "Type unsupported! You can get the types by the command: conveyor resource-type-list"
            raise exceptions.CommandError(msg)
        
        utils.isUUID(res_opts['id'], "id")
        
        resources.append(res_opts) 
    return resources

def _print_plan(plan):
    print("%s:" % plan.plan_id)
    res = {'plan_id': plan.plan_id,
           'plan_type': plan.plan_type,
           'plan_status':plan.plan_status,
           'task_status': plan.task_status,
           'created_at': plan.created_at,
           'updated_at': plan.updated_at,
           'expire_time': plan.expire_at,
           'project_id': plan.project_id,
           'user_id': plan.user_id,
           'stack_id': plan.stack_id,
           'original_resources': plan.original_resources,
           'updated_resources': plan.updated_resources,
           #'original_dependencies': plan.original_dependencies,
           #'updated_dependencies': plan.updated_dependencies
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
                power_states[getattr(item, 'power_state')]
            )
        except AttributeError:
            setattr(item, 'power_state', "N/A")
        try:
            getattr(item, 'task_state')
        except AttributeError:
            setattr(item, 'task_state', "N/A")

def _translate_string_dict(string):
    
    # if dict
    if (':' in string):
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
