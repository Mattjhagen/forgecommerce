import sqlite3, tempfile, unittest
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

if __name__=='__main__': unittest.main()
