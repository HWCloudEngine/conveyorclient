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


class VService(base.Resource):
    """A resource is an extra block level storage to the OpenStack instances."""
    def __repr__(self):
        return "<Volume: %s>" % self.id

    def delete(self):
        """Delete this resource."""
        self.manager.delete(self)

    def update(self, **kwargs):
        """Update the display_name or display_description for this resource."""
        self.manager.update(self, **kwargs)

    def attach(self, instance_uuid, mountpoint, mode='rw'):
        """Set attachment metadata.

        :param instance_uuid: uuid of the attaching instance.
        :param mountpoint: mountpoint on the attaching instance.
        :param mode: the access mode
        """
        return self.manager.attach(self, instance_uuid, mountpoint, mode)

    def detach(self):
        """Clear attachment metadata."""
        return self.manager.detach(self)

    def reserve(self, volume):
        """Reserve this resource."""
        return self.manager.reserve(self)

    def unreserve(self, volume):
        """Unreserve this resource."""
        return self.manager.unreserve(self)

    def begin_detaching(self, volume):
        """Begin detaching resource."""
        return self.manager.begin_detaching(self)

    def roll_detaching(self, volume):
        """Roll detaching resource."""
        return self.manager.roll_detaching(self)

    def initialize_connection(self, volume, connector):
        """Initialize a volume connection.

        :param connector: connector dict from nova.
        """
        return self.manager.initialize_connection(self, connector)

    def terminate_connection(self, volume, connector):
        """Terminate a volume connection.

        :param connector: connector dict from nova.
        """
        return self.manager.terminate_connection(self, connector)

    def set_metadata(self, volume, metadata):
        """Set or Append metadata to a resource.

        :param resource : The :class: `Vservice` to set metadata on
        :param metadata: A dict of key/value pairs to set
        """
        return self.manager.set_metadata(self, metadata)

    def upload_to_image(self, force, image_name, container_format,
                        disk_format):
        """Upload a resource to image service as an image."""
        return self.manager.upload_to_image(self, force, image_name,
                                            container_format, disk_format)

    def force_delete(self):
        """Delete the specified resource ignoring its current state.

        :param resource: The UUID of the resource to force-delete.
        """
        self.manager.force_delete(self)

    def reset_state(self, state):
        """Update the volume with the provided state."""
        self.manager.reset_state(self, state)

    def extend(self, volume, new_size):
        """Extend the size of the specified volume.

        :param volume: The UUID of the volume to extend.
        :param new_size: The desired size to extend volume to.
        """
        self.manager.extend(self, new_size)

    def migrate_volume(self, host, force_host_copy):
        """Migrate the volume to a new host."""
        self.manager.migrate_volume(self, host, force_host_copy)

#    def migrate_volume_completion(self, old_volume, new_volume, error):
#        """Complete the migration of the volume."""
#        self.manager.migrate_volume_completion(self, old_volume,
#                                               new_volume, error)

    def update_all_metadata(self, metadata):
        """Update all metadata of this volume."""
        return self.manager.update_all_metadata(self, metadata)

    def update_readonly_flag(self, volume, read_only):
        """Update the read-only access mode flag of the specified volume.

        :param volume: The UUID of the volume to update.
        :param read_only: The value to indicate whether to update volume to
            read-only access mode.
        """
        self.manager.update_readonly_flag(self, read_only)


class VServiceManager(base.ManagerWithFind):
    """
    Manage :class:`VService` resources.
    """
    resource_class = VService

    def create(self, size, snapshot_id=None, source_volid=None,
               display_name=None, display_description=None,
               volume_type=None, user_id=None,
               project_id=None, availability_zone=None,
               metadata=None, imageRef=None):
        """
        Creates a volume.

        :param size: Size of volume in GB
        :param snapshot_id: ID of the snapshot
        :param display_name: Name of the volume
        :param display_description: Description of the volume
        :param volume_type: Type of volume
        :param user_id: User id derived from context
        :param project_id: Project id derived from context
        :param availability_zone: Availability Zone to use
        :param metadata: Optional metadata to set on volume creation
        :param imageRef: reference to an image stored in glance
        :param source_volid: ID of source volume to clone from
        :rtype: :class:`Volume`
        """

        if metadata is None:
            volume_metadata = {}
        else:
            volume_metadata = metadata

        body = {'volume': {'size': size,
                           'snapshot_id': snapshot_id,
                           'display_name': display_name,
                           'display_description': display_description,
                           'volume_type': volume_type,
                           'user_id': user_id,
                           'project_id': project_id,
                           'availability_zone': availability_zone,
                           'status': "creating",
                           'attach_status': "detached",
                           'metadata': volume_metadata,
                           'imageRef': imageRef,
                           'source_volid': source_volid,
                           }}
        return self._create('/volumes', body, 'volume')

    def get(self, id):
        """
        Get a volume.

        :param id: The ID of the resource to get.
        :rtype: :class:`Resource`
        """
        return self._get("/services/%s" % id, "resource")

    def list(self, detailed=True, search_opts=None):
        """
        Get a list of all resources.

        :rtype: list of :class:`resources`
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in six.iteritems(search_opts):
            if val:
                qparams[opt] = val

        query_string = "?%s" % urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        return self._list("/services%s%s" % (detail, query_string),
                          "resources")

    def delete(self, volume):
        """
        Delete a volume.

        :param volume: The :class:`Volume` to delete.
        """
        self._delete("/services/%s" % base.getid(volume))

    def update(self, volume, **kwargs):
        """
        Update the display_name or display_description for a volume.

        :param volume: The :class:`Volume` to update.
        """
        if not kwargs:
            return

        body = {"volume": kwargs}

        self._update("/services/%s" % base.getid(volume), body)










 







