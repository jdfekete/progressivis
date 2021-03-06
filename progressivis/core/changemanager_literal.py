"Change Manager for literal values (supporting ==)"

from .bitmap import bitmap
from .index_update import IndexUpdate
from .changemanager_base import BaseChangeManager


class LiteralChangeManager(BaseChangeManager):
    """
    Manage changes that occured in a literal value between runs.
    """
    VALUE = bitmap([0])

    def __init__(self,
                 slot,
                 buffer_created=True,
                 buffer_updated=False,
                 buffer_deleted=True):
        super(LiteralChangeManager, self).__init__(
            slot,
            buffer_created,
            buffer_updated,
            buffer_deleted)
        self._last_value = None

    def reset(self, name=None):
        super(LiteralChangeManager, self).reset(name)
        self._last_value = None

    def compute_updates(self, data):
        last_value = self._last_value
        changes = IndexUpdate()
        if last_value == data:
            return changes
        if last_value is None:
            if self.created.buffer:
                changes.created.update(self.VALUE)
        elif data is None:
            if self.deleted.buffer:
                changes.deleted.update(self.VALUE)
        elif self.updated.buffer:
            changes.updated.update(self.VALUE)
        self._last_value = data
        return changes

    def update(self, run_number, data, mid):
        # pylint: disable=unused-argument
        assert isinstance(data, bitmap)
        if run_number != 0 and run_number <= self._last_update:
            return

        changes = self.compute_updates(data)
        self._last_update = run_number
        self._row_changes.combine(changes,
                                  self.created.buffer,
                                  self.updated.buffer,
                                  self.deleted.buffer)
