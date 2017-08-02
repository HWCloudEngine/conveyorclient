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

from conveyorclient import base


class ClonesService(base.Resource):
    """A resource is an clone plan for openstack resources."""
    def __repr__(self):
        return "<plan: %s>" % self.id

    def export_clone_template(self, sys_clone=False, copy_data=True):
        """export clone template for this resource."""
        self.manager.export_clone_template(self, sys_clone, copy_data)

    def clone(self, destination, sys_clone, copy_data=True):
        """clone plan."""
        self.manager.clone(self, destination, sys_clone=sys_clone,
                           copy_data=copy_data)

    def export_template_and_clone(self, destination, resources={},
                                  sys_clone=False, copy_data=True):
        """clone plan."""
        self.manager.export_template_and_clone(self, destination,
                                               resources=resources,
                                               sys_clone=sys_clone,
                                               copy_data=copy_data)


class ClonesServiceManager(base.ManagerWithFind):
    """
    Manage :class:`Clones` resources.
    """
    resource_class = ClonesService

    def list(self):
        pass

    def export_clone_template(self, plan, sys_clone=False, copy_data=True):
        """
        export the template of clone plan

        :param plan: The :class:`Plan` to update.
        """
        return self._action('export_clone_template',
                            plan,
                            {
                                'sys_clone': sys_clone,
                                'copy_data': copy_data
                            })

    def clone(self, plan, destination,
              clone_resources,
              update_resources=[],
              replace_resources=[],
              clone_links=[],
              sys_clone=False, copy_data=True):
        return self._action('clone',
                            plan,
                            {
                                'plan_id': plan,
                                'clone_resources': clone_resources,
                                'update_resources': update_resources,
                                'replace_resources': replace_resources,
                                'clone_links': clone_links,
                                'availability_zone_map': destination,
                                'sys_clone': sys_clone,
                                'copy_data': copy_data
                            })

    def _action(self, action, plan, info=None, **kwargs):
        """
        Perform a plan "action" export_clone_template/clone etc.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/clones/%s/action' % base.getid(plan)
        return self.api.client.post(url, body=body)

    def export_template_and_clone(self, plan, destination,
                                  resources={},
                                  sys_clone=False,
                                  copy_data=True):
        return self._action('export_template_and_clone',
                            plan,
                            {
                                'destination': destination,
                                'resources': resources,
                                'sys_clone': sys_clone,
                                'copy_data': copy_data
                            })
