import os, sqlite3, tempfile, unittest
from forgecommerce.backup import backup
from forgecommerce.db import connect
from forgecommerce.services import Commerce

class BackupTests(unittest.TestCase):
    def test_backup_restore_preserves_tenant_and_catalog(self):
        source=tempfile.NamedTemporaryFile(suffix='.sqlite3'); restored=tempfile.NamedTemporaryFile(suffix='.sqlite3')
        try:
            c=Commerce(connect(source.name)); auth=c.register('backup@example.com','long enough password','Backup Shop'); session=c.authenticate(auth['token']); c.product_create(session,{'name':'Restore Me','price_cents':100,'inventory':1})
            backup(source.name,restored.name)
            db=sqlite3.connect(restored.name); self.assertEqual(db.execute('SELECT COUNT(*) FROM tenants').fetchone()[0],1); self.assertEqual(db.execute('SELECT COUNT(*) FROM products').fetchone()[0],1); db.close()
        finally: source.close(); restored.close()

    def test_corrupt_source_does_not_replace_existing_backup(self):
        source=tempfile.NamedTemporaryFile(suffix='.sqlite3',delete=False); destination=tempfile.NamedTemporaryFile(suffix='.sqlite3',delete=False)
        try:
            source.write(b'not a sqlite database'); source.close()
            destination.write(b'keep this backup'); destination.close()
            with self.assertRaises(sqlite3.DatabaseError): backup(source.name,destination.name)
            with open(destination.name,'rb') as preserved: self.assertEqual(preserved.read(),b'keep this backup')
        finally:
            os.unlink(source.name); os.unlink(destination.name)

if __name__=='__main__': unittest.main()
