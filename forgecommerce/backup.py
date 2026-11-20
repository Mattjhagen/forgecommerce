import os, sqlite3, sys, tempfile
def backup(source, destination):
    destination_dir=os.path.dirname(os.path.abspath(destination)) or "."
    fd,temp_destination=tempfile.mkstemp(prefix=".forgecommerce-backup-",suffix=".sqlite3",dir=destination_dir)
    os.close(fd)
    src=None; dst=None
    try:
        src=sqlite3.connect(source); src.execute("PRAGMA integrity_check").fetchone()
        dst=sqlite3.connect(temp_destination)
        with dst: src.backup(dst)
        dst.close(); dst=None; src.close(); src=None
        os.replace(temp_destination,destination)
    finally:
        if src is not None: src.close()
        if dst is not None: dst.close()
        if os.path.exists(temp_destination): os.unlink(temp_destination)
if __name__ == "__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: python3 -m forgecommerce.backup SOURCE DESTINATION")
    backup(sys.argv[1],sys.argv[2])
