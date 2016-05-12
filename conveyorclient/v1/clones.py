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


class ClonesService(base.Resource):
    """A resource is an clone plan for openstack resources."""
    def __repr__(self):
        return "<plan: %s>" % self.id

    def export_clone_template(self, update_resources):
        """export clone template for this resource."""
        self.manager.export_clone_template(self, update_resources)
        
    def clone(self, destination, update_resources):
        """clone plan."""
        self.manager.clone(self, destination, update_resources)

class ClonesServiceManager(base.ManagerWithFind):
    """
    Manage :class:`Clones` resources.
    """
    resource_class = ClonesService
   
        
    def list(self):
        pass
    def export_clone_template(self, plan, update_resources):
        """
        export the template of clone plan
        
        :param plan: The :class:`Plan` to update.
        """
        return self._action('export_clone_template',
                            plan,
                            {'update_resources': update_resources
                            })
        
    def clone(self, plan, destination, update_resources):
        return self._action('clone',
                            plan,
                            {
                              'destination':destination,
                             'update_resources': update_resources
                            })

    def _action(self, action, plan, info=None, **kwargs):
        """
        Perform a plan "action" -- export_clone_template/import_clone_templateetc.
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/clones/%s/action' % base.getid(plan)
        return self.api.client.post(url, body=body)
    
    def start_clone_template(self, plan_id, disable_rollback, template, **kwargs):
        
        body = {"clone_element_template":{"disable_rollback": disable_rollback,
                                          "plan_id": plan_id,
                                          "template":template
                                          }
                }
        
        url = '/clones/%s/action' % plan_id
        return self.api.client.post(url, body=body)
