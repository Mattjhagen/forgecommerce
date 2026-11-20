import tempfile, threading, unittest
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from forgecommerce.app import make_server
from forgecommerce.config import Settings

class LoadTests(unittest.TestCase):
    def test_health_handles_concurrent_local_requests(self):
        db=tempfile.NamedTemporaryFile(suffix='.sqlite3'); server=make_server(Settings(db_path=db.name,host='127.0.0.1',port=0)); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start(); url=f'http://127.0.0.1:{server.server_address[1]}/health'
        try:
            with ThreadPoolExecutor(max_workers=16) as pool:
                results=list(pool.map(lambda _: urlopen(url,timeout=5).read(),range(32)))
            self.assertEqual(len(results),32); self.assertTrue(all(b'"status":"ok"' in body for body in results))
        finally: server.shutdown(); server.server_close(); db.close()

if __name__=='__main__': unittest.main()
