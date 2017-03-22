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
import base64

from oslo_utils import encodeutils
from conveyorclient import base


class Plan(base.Resource):
    def __repr__(self):
        return "<Plan: %s>" % self.plan_id

    def reset_plan_state(self, state):
        self.manager.reset_plan_state(self.plan_id, state)

class PlanManager(base.ManagerWithFind):
    """
    Manage :class:`Resource` resources.
    """
    resource_class = Plan

    def get(self, plan):
        """
        Get a plan.
        :param plan: The ID of the plan.
        :rtype: :class:`Plan`
        """
        return self._get("/plans/%s" % plan, "plan")


    def delete(self, plan):
        """
        Delete a plan.
        :param plan: The :class:`Plan` to delete.
        """
        return self._delete("/plans/%s" % plan)


    def update(self, plan, values):
        """
        Update a plan.
        :param plan: The :class:`Plan` to update.
        :param values: key-values to update.
        """
        if not values or not isinstance(values, dict):
            return

        body = {"plan": values}
        self._update("/plans/%s" % plan, body)
    
    
    def update_plan_resource(self, plan, resources):
        """
        Update resources of a plan.
        :param plan: The :class:`Plan` to update.
        :param resources: a list of resources to update. 
        """
        resources = self._process_update_resources(resources)
        body = {"update_plan_resources": {"resources": resources}}
        return self.api.client.post("/plans/%s/action" % plan, body=body)
        

    def _process_update_resources(self, resources):
        
        if not resources or not isinstance(resources, list):
            raise base.exceptions.BadRequest("'resources' must be a list.")
        
        allowed_actions = ["add", "edit", "delete"]
        
        for attrs in resources:
            
            if not isinstance(attrs, dict):
                raise base.exceptions.BadRequest("Every item in resources "
                                                 "must be a dict.")
            
            #verify keys
            if "action" not in attrs.keys() or attrs["action"] not in allowed_actions:
                msg = ("'action' not found or not supported. "
                        "'action' must be one of %s" % allowed_actions)
                raise base.exceptions.BadRequest(msg)
            #verify actions
            if attrs["action"] == "add" and ("id" not in attrs.keys() or 
                                             "resource_type" not in attrs.keys()):
                msg = ("'id' and 'resource_type' of new resource "
                       "must be provided when adding a new resource.")
                raise base.exceptions.BadRequest(msg)
            elif attrs["action"] == "edit" and (len(attrs.keys()) < 2 
                                            or "resource_id" not in attrs.keys()):
                msg = ("'resource_id' and the fields to be edited "
                       "must be provided when editing resources.")
                raise base.exceptions.BadRequest(msg)
            elif attrs["action"] == "delete" and "resource_id" not in attrs.keys():
                msg = ("'resource_id' must be provided when deleting resources.")
                raise base.exceptions.BadRequest(msg)
            
            userdata = attrs.get("user_data")
            if userdata:
                if six.PY3:
                    userdata = userdata.encode("utf-8")
                else:
                    userdata = encodeutils.safe_encode(userdata)
                userdata_b64 = base64.b64encode(userdata).decode('utf-8')
                attrs["user_data"] = userdata_b64

        return resources
    
    
    def list(self, search_opts=None):
        """
        Get a list of all plans.
        :rtype: list of :class:`Plan`
        """
        if search_opts is None:
            search_opts = {}
        qparams = {}
        for opt, val in search_opts.items():
            if val:
                qparams[opt] = val
        query_string = "?%s" % urlencode(qparams) if qparams else ""
        return self._list("/plans/detail%s" % query_string, "plans")


    def create(self, type, resources):
        """
        Create a clone or migrate plan.
        :param type: plan type. 'clone' or 'migrate'
        :param resources: A list of resources. "
                        "Eg: [{'type':'OS::Nova::Server', 'id':'xx'}]
        :rtype: :class:`Plan (Actually, only plan_id and resource_dependencies)`
        """
        if not resources or not isinstance(resources, list):
            raise base.exceptions.BadRequest("'resources' must be a list.")
        
        body = {"plan": {"type": type, "resources": resources}}
        return self._create('/plans', body, 'plan')
        

    def create_plan_by_template(self, template):
        """
        Create a clone or migrate plan by template.
        :rtype: :class:`Plan`
        """
        body = {"plan": {"template": template}}
        resp, body = self.api.client.post("/plans/create_plan_by_template", body=body)
        return body['plan']

    def download_template(self, plan):
        """
        Create a clone or migrate plan by template.
        :param plan:The ID of the plan.
        :rtype: :dict
        """
        return self._action('download_template', plan)

    def reset_plan_state(self, plan, state):
        
        self._action("os-reset_state", plan, {"plan_status": state})

    def _action(self, action, plan, info=None, **kwargs):
        """
        Perform a plan "action" -- download_templdate etc.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/plans/%s/action' % base.getid(plan)
        return self.api.client.post(url, body=body)
    