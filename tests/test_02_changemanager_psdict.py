from collections import namedtuple
from progressivis.core.bitmap import bitmap
from progressivis.core.changemanager_dict import DictChangeManager
from progressivis.utils.psdict import PsDict
from . import ProgressiveTest


class FakeSlot(namedtuple('FakeSlot', ['table'])):
    def data(self):
        return self.table

class TestDictChangeManager(ProgressiveTest):
    def test_dictchangemanager(self):
        mid1 = 1
        d = PsDict(a=1, b=2, c=3)
        slot = FakeSlot(d)
        cm = DictChangeManager(slot)
        self.assertEqual(cm.last_update(), 0)
        self.assertEqual(cm.created.length(), 0)
        self.assertEqual(cm.updated.length(), 0)
        self.assertEqual(cm.deleted.length(), 0)

        cm.update(1, d, mid1)
        self.assertEqual(cm.last_update(), 1)
        self.assertEqual(cm.created.length(), 3)
        self.assertEqual(cm.updated.length(), 0)
        self.assertEqual(cm.deleted.length(), 0)
        d = PsDict(a=1, b=2+1, c=3+1, d=4, e=5)
        
        cm.update(2, d, mid1)
        self.assertEqual(cm.last_update(), 2)
        self.assertEqual(cm.created.next(), slice(0, 5)) # 3 + 2 
        self.assertEqual(cm.updated.next(), slice(0, 0)) # already counted as creations
        self.assertEqual(cm.deleted.length(), 0)
        d['c'] *= 2
        d['e'] *= 3
        d['x'] = 42
        cm.update(3, d, mid1)
        self.assertEqual(cm.last_update(), 3)
        self.assertEqual(cm.created.next(), slice(5, 6))
        self.assertEqual(cm.updated.next(), bitmap([2, 4]))
        self.assertEqual(cm.deleted.length(), 0)
if __name__ == '__main__':
    ProgressiveTest.main()