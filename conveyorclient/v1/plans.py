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


class Plan(base.Resource):
    def __repr__(self):
        return "<Plan: %s>" % self.plan_id


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
        :param type: Operation type. 'clone' or migrate
        :param resources: A list of resources. Eg: [{'type':'OS::Nova::Server', 'id':'xx'}]
        :rtype: :class:`Plan (Actually, only plan_id and resource_dependencies)`
        """
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
        return self._action('download_template',
                            plan)

    def _action(self, action, plan, info=None, **kwargs):
        """
        Perform a plan "action" -- download_templdate etc.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/plans/%s/action' % base.getid(plan)
        return self.api.client.post(url, body=body)
    