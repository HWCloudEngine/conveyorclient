# Copyright 2011 Denali Systems, Inc.
# All Rights Reserved.
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

"""
Volume interface (1.1 extension).
"""

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
import six
from conveyorclient import base


class Resource(base.Resource):
    def __repr__(self):
        if getattr(self, 'name', None):
            return "<Resource: %s>" % self.name
        elif getattr(self, 'id', None):
            return "<Resource: %s>" % self.id
        elif getattr(self, 'zoneName', None):
            return "<Resource: %s>" % self.zoneName
        else:
            return "<Resource>"

class ResourceType(base.Resource):
    def __repr__(self):
        return "<ResourceType: %s>" % self.type


class ResourceManager(base.ManagerWithFind):
    """
    Manage :class:`Resource` resources.
    """
    resource_class = Resource

    def get_resource_detail(self, res_type, res_id):
        """
        Get the details of specified resource in a plan.
        :param res_type: The type of resource.
        :param id: The id of resource.
        :rtype: :class:`Resource`
        """
        body = {"get_resource_detail": {"type": res_type}}
        resp, body = self.api.client.post("/resources/%s/action" % res_id, body=body)
        return body['resource']


    def get_resource_detail_from_plan(self, res_id, plan_id):
        """
        Get the details of specified resource in a plan.
        :param id: The identifier of the resource to get.
        :param plan_id: The ID of the plan.
        :rtype: :class:`Resource`
        """
        body = {"get_resource_detail_from_plan": {"plan_id": plan_id}}
        resp, body = self.api.client.post("/resources/%s/action" % res_id, body=body)
        return body['resource']


    def list(self, search_opts):
        """
        Get a list of resources with a specified type. Type is required in search_opts.
        :rtype: list of :class:`Resource`
        """
        
        if search_opts is None:
            search_opts = {}
        qparams = {}
        for opt, val in search_opts.items():
            if val:
                qparams[opt] = val
        query_string = "?%s" % urlencode(qparams) if qparams else ""
        return self._list("/resources/detail%s" % query_string, "resources")


    def resource_type_list(self):
        """
        Get the types of resources which can be cloned or migrated.
        :rtype: :class:`ResourceType`
        """
        return self._list("/resources/types", "types", obj_class=ResourceType)
        
