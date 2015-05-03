import synapseclient
from synapseclient import Project, File
import synapseclient.utils as utils
from datetime import datetime
import filecmp
import os, traceback
import argparse
import random


syn = None


def setup(module):
    print '\n'
    print '~' * 60
    print os.path.basename(__file__)
    print '~' * 60
    module.syn = synapseclient.Synapse()
    module.syn.login()


def test_large_file_upload(file_to_upload_size=11*utils.KB):

    try:
        project = syn.store(Project("File Upload Load Test " +  datetime.now().strftime("%Y-%m-%d %H%M%S%f")))

        filepath = utils.make_bogus_binary_file(file_to_upload_size)
        print 'Made bogus file: ', filepath

        try:
            junk = syn.store(File(filepath, parent=project))

            fh = syn._getFileHandle(junk['dataFileHandleId'])
            syn.printEntity(fh)

        finally:
            try:
                if 'junk' in locals():
                    syn.delete(junk)
            except Exception:
                print traceback.format_exc()
    finally:
        try:
            if 'filepath' in locals():
                os.remove(filepath)
        except Exception:
            print traceback.format_exc()




def main():

    global syn

    parser = argparse.ArgumentParser(description='Tests uploading large files to Synapse.')
    parser.add_argument('--version',  action='version',
            version='Synapse Client %s' % synapseclient.__version__)
    parser.add_argument('-u', '--username',  dest='user',
            help='Username used to connect to Synapse')
    parser.add_argument('-p', '--password', dest='password',
            help='Password used to connect to Synapse')
    parser.add_argument('--debug', dest='debug',  action='store_true')
    parser.add_argument('--staging', dest='staging',  action='store_true', default=True)
    parser.add_argument('--prod', dest='staging',  action='store_false', default=True)
    parser.add_argument('-s', '--skip-checks', dest='skip_checks', action='store_true',
            help='suppress checking for version upgrade messages and endpoint redirection')

    parser.add_argument('--size-mb', type=int, dest='size_mb')
    parser.add_argument('--size-gb', type=int, dest='size_gb')

    args = parser.parse_args()

    if args.size_mb:
        args.file_to_upload_size = args.size_mb * utils.MB
    elif args.size_gb:
        args.file_to_upload_size = args.size_gb * utils.GB
    else:
        args.file_to_upload_size = 11*utils.KB

    synapseclient.USER_AGENT['User-Agent'] = "test-large-file-upload " + synapseclient.USER_AGENT['User-Agent']
    syn = synapseclient.Synapse(debug=args.debug, skip_checks=args.skip_checks)
    if args.staging:
        print "switching to STAGING endpoints"
        syn.setEndpoints(**synapseclient.client.STAGING_ENDPOINTS)
    syn.login(args.user, args.password, silent=True)

    test_large_file_upload(file_to_upload_size=args.file_to_upload_size)


if __name__ == "__main__":
    main()

