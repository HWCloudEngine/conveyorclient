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

import base64
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import six
from oslo_utils import encodeutils

from conveyorclient import base
from conveyorclient.common import constants


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

            # verify keys
            if "action" not in attrs.keys() \
                    or attrs["action"] not in allowed_actions:
                msg = ("'action' not found or not supported. "
                       "'action' must be one of %s" % allowed_actions)
                raise base.exceptions.BadRequest(msg)
            # verify actions
            if attrs["action"] == "add" \
                    and ("id" not in attrs.keys()
                         or "resource_type" not in attrs.keys()):
                msg = ("'id' and 'resource_type' of new resource "
                       "must be provided when adding a new resource.")
                raise base.exceptions.BadRequest(msg)
            elif attrs["action"] == "edit" \
                    and (len(attrs.keys()) < 2
                         or "resource_id" not in attrs.keys()):
                msg = ("'resource_id' and the fields to be edited "
                       "must be provided when editing resources.")
                raise base.exceptions.BadRequest(msg)
            elif attrs["action"] == "delete" \
                    and "resource_id" not in attrs.keys():
                msg = ("'resource_id' must be provided when deleting "
                       "resources.")
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

    def list(self, search_opts=None, marker=None, limit=None, sort_key=None,
             sort_dir=None):
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

        if marker:
            qparams['marker'] = marker

        if limit and limit != -1:
            qparams['limit'] = limit

        if sort_key is not None:
            if sort_key in constants.PLAN_SORT_KEY_VALUES:
                qparams['sort_key'] = sort_key
            else:
                raise ValueError('sort_key must be one of the following: %s.'
                                 % ', '.join(constants.PLAN_SORT_KEY_VALUES))

        if sort_dir is not None:
            if sort_dir in constants.SORT_DIR_VALUES:
                qparams['sort_dir'] = sort_dir
            else:
                raise ValueError('sort_dir must be one of the following: %s.'
                                 % ', '.join(constants.SORT_DIR_VALUES))

        if qparams:
            query_string = "?%s" % urlencode(
                sorted(list(qparams.items()), key=lambda x: x[0]))
        else:
            query_string = ""
        return self._list("/plans/detail%s" % query_string, "plans")

    def create(self, type, resources, plan_name=None):
        """
        Create a clone or migrate plan.
        :param type: plan type. 'clone' or 'migrate'
        :param resources: A list of resources. "
                        "Eg: [{'type':'OS::Nova::Server', 'id':'xx'}]
        :param name: plan name.
        :rtype: :class:`Plan (Actually, only plan_id and
                       resource_dependencies)`
        """
        if not resources or not isinstance(resources, list):
            raise base.exceptions.BadRequest("'resources' must be a list.")

        body = {"plan": {"type": type, "resources": resources,
                         "plan_name": plan_name}}
        return self._create('/plans', body, 'plan')

    def create_plan_by_template(self, template):
        """
        Create a clone or migrate plan by template.
        :rtype: :class:`Plan`
        """
        body = {"plan": {"template": template}}
        resp, body = self.api.client.post("/plans/create_plan_by_template",
                                          body=body)
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

    def force_delete_plan(self, plan):
        self._action('force_delete-plan', plan, {'plan_id': plan})

    def get_resource_detail_from_plan(self, res_id, plan_id, is_original=True):
        """
        Get the details of specified resource in a plan.
        :param id: The identifier of the resource to get.
        :param plan_id: The ID of the plan.
        :rtype: :class:`Resource`
        """
        body = {
            "get_resource_detail_from_plan": {
                "plan_id": plan_id,
                "is_original": is_original
            }
        }

        resp, body = self.api.client.post("/plans/%s/action" % res_id,
                                          body=body)
        return body['resource']

    def _action(self, action, plan, info=None, **kwargs):
        """
        Perform a plan "action" -- download_templdate etc.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/plans/%s/action' % base.getid(plan)
        return self.api.client.post(url, body=body)
