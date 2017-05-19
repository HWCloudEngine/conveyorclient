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


class ConfigurationService(base.Resource):
    """A resource is an clone plan for openstack resources."""


class ConfigurationServiceManager(base.ManagerWithFind):
    """
    Manage :class:`Clones` resources.
    """
    resource_class = ConfigurationService

    def list(self):
        pass

    def update_configs(self, **configs):

        config_file = configs.get('config_file', None)
        config_info = []
        config_info.append(configs.get('config_info', {}))

        body = {
            "configurations": {
                "config_file": config_file,
                "config_info": config_info
            }
        }
        if not config_file:
            body.get("configurations").pop("config_file")

        url = '/configurations'

        return self.api.client.post(url, body=body)
