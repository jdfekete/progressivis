from . import ProgressiveTest


from progressivis.core.bitmap import bitmap
from progressivis.core.changemanager_bitmap import BitmapChangeManager

class FakeSlot(object):
    def __init__(self, scheduler, table):
        self.scheduler = scheduler
        self.table = table

    def data(self):
        return self.table

class TestBitmapChangeManager(ProgressiveTest):
    def test_bitmapchangemanager(self):
        #pylint: disable=protected-access
        mid1 = 1
        bm = bitmap([1,2,3])
        slot = FakeSlot(None, bm)
        
        cm = BitmapChangeManager(slot)
        self.assertEqual(cm.last_update(), 0)
        self.assertEqual(cm.created.length(), 0)
        self.assertEqual(cm.updated.length(), 0)
        self.assertEqual(cm.deleted.length(), 0)

        cm.update(1, bm)
        self.assertEqual(cm.last_update(), 1)
        self.assertEqual(cm.created.length(), 3)
        self.assertEqual(cm.updated.length(), 0)
        self.assertEqual(cm.deleted.length(), 0)

        bm = bitmap([2,3,4])
        cm.update(2, bm)
        self.assertEqual(cm.last_update(), 2)
        # 1 should be removed because deleted at ts=2
        self.assertEqual(cm.created.next(), slice(2,5))
        self.assertEqual(cm.updated.length(), 0)
        # 0 has been created then deleted before it got consumed
        self.assertEqual(cm.deleted.length(), 0)

        bm = bitmap([3,4,5])
        cm.update(3, bm)
        self.assertEqual(cm.last_update(), 3)
        self.assertEqual(cm.created.next(), slice(5,6))
        self.assertEqual(cm.updated.length(), 0)
        self.assertEqual(cm.deleted.length(), 1) # 2 is deleted but buffered
        
        bm = bitmap([2,3,4])
        cm.update(4, bm)
        self.assertEqual(cm.last_update(), 4)
        # 2 has been created before it was consumed so it becomes updated
        self.assertEqual(cm.created.length(), 0)
        self.assertEqual(cm.updated.length(), 0) # updates are ignored by default
        # 2 should be removed because added at ts=4
        self.assertEqual(cm.deleted.next(), slice(5,6)) 

if __name__ == '__main__':
    ProgressiveTest.main()
