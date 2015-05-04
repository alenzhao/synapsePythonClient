import synapseclient.utils as utils
import filecmp
import tempfile
import os
import hashlib

from synapseclient.utils import GB, MB, KB


def setup():
    print '\n'
    print '~' * 60
    print os.path.basename(__file__)
    print '~' * 60


def test_chunks():
    # Read a file in chunks, write the chunks out, and compare to the original
    try:
        filepath = utils.make_bogus_binary_file(n=1*MB)
        with open(filepath, 'rb') as f, tempfile.NamedTemporaryFile(mode='wb', delete=False) as out:
            for chunk in utils.chunks(f, 16*1024):
                buff = chunk.read(4*KB)
                while buff:
                    out.write(buff)
                    buff = chunk.read(4*KB)
        assert filecmp.cmp(filepath, out.name)
    finally:
        if 'filepath' in locals() and filepath:
            os.remove(filepath)
        if 'out' in locals() and out:
            os.remove(out.name)


def test_seek():
    try:
        filepath = utils.make_bogus_data_file(n=1000)
        with open(filepath, 'rb') as f, tempfile.NamedTemporaryFile(mode='wb', delete=False) as out:
            for chunk in utils.chunks(f, 16*1024):
                buff = chunk.read(4*KB)
                chunk.seek(0,2)
                assert chunk.tell() == chunk.size

                chunk.seek(1234)
                assert chunk.tell() == 1234

                buff = chunk.read(4*KB)
                assert chunk.tell() == 1234 + 4*KB

                buff = chunk.read(4*KB)
                assert chunk.tell() == 1234 + 8*KB

                chunk.seek(0)
                assert chunk.tell() == 0

                buff = chunk.read(4*KB)
                while buff:
                    out.write(buff)
                    buff = chunk.read(4*KB)
        assert filecmp.cmp(filepath, out.name)

    finally:
        if 'filepath' in locals() and filepath:
            os.remove(filepath)
        if 'out' in locals() and out:
            os.remove(out.name)


def manualtest_chunks_big(size=3*utils.MB, chunksize=1*utils.MB):
    # Read a file in chunks, write the chunks out, and compare to the original
    try:
        filepath = utils.make_bogus_binary_file(size, printprogress=True)

        import subprocess
        md5_1 = subprocess.check_output(["md5", "-q", filepath]).strip()
        print "md5 = \"%s\"" % md5_1

        m = hashlib.md5()
        with open(filepath, 'rb') as f:
            for i, chunk in enumerate(utils.chunks(f, chunksize)):
                buff = chunk.read(4*KB)
                while buff:
                    m.update(buff)
                    buff = chunk.read(4*KB)
                utils.printTransferProgress((i+1)*chunksize, size, 'Verifying ', filepath)
        print "md5 = \"%s\"" % m.hexdigest()
        assert md5_1 == m.hexdigest()
    finally:
        if 'filepath' in locals() and filepath:
            os.remove(filepath)

