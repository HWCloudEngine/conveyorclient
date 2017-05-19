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


class MigratesService(base.Resource):
    """A resource is an migrate plan for openstack resources."""
    def __repr__(self):
        return "<plan: %s>" % self.id

    def export_migrate_template(self):
        """export migrate template for this plan."""
        self.manager.export_migrate_template(self)

    def migrate(self, destination):
        """migrate plan."""
        self.manager.migrate(self, destination)


class MigratesServiceManager(base.ManagerWithFind):
    """
    Manage :class:`Clones` resources.
    """
    resource_class = MigratesService

    def list(self):
        pass

    def export_migrate_template(self, plan):
        """
        export the template of migrate plan

        :param plan: The :class:`Plan` to update.
        """
        return self._action('export_migrate_template',
                            plan)

    def migrate(self, plan, destination):
        return self._action('migrate',
                            plan,
                            {
                                'destination': destination
                            })

    def _action(self, action, plan, info=None, **kwargs):
        """
        Perform a plan "action" -- export_migrate_template/migrate etc.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/migrates/%s/action' % base.getid(plan)
        return self.api.client.post(url, body=body)
