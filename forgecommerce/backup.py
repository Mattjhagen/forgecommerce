import sqlite3, sys
def backup(source, destination):
    src=sqlite3.connect(source); dst=sqlite3.connect(destination)
    with dst: src.backup(dst)
    src.close(); dst.close()
if __name__ == "__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: python3 -m forgecommerce.backup SOURCE DESTINATION")
    backup(sys.argv[1],sys.argv[2])
