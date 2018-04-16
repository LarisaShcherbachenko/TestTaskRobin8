import filecmp
import os
import unittest

from main import *

class TestBenchmark(unittest.TestCase):

    def setUp(self):
        init_directories()

    @classmethod
    def tearDownClass(cls):
        init_directories()

        super().tearDownClass()

    def test_init_direcoties(self):
        init_directories()

        self.assertTrue(os.path.exists(PLAIN_FILES_PATH), \
            "Directory {} doesn't exist".format(PLAIN_FILES_PATH))
        self.assertTrue(os.path.exists(ENC_FILES_PATH), \
            "Directory {} doesn't exist".format(ENC_FILES_PATH))
        self.assertTrue(os.path.exists(DEC_FILES_PATH), \
            "Directory {} doesn't exist".format(DEC_FILES_PATH))

    def test_generate_file(self):
        fname = 'f1.txt'
        fsize = 1

        generate_file(fname, fsize)

        self.assertTrue(os.path.isfile(PLAIN_FILES_PATH + fname), \
            "File {} doesn't exist".format(PLAIN_FILES_PATH + fname))
        fsize_new = os.path.getsize(PLAIN_FILES_PATH + fname) / 1000 / 1000
        self.assertEqual(fsize_new, fsize, \
            "File {} has wrong size: {} mb not {} mb".format(PLAIN_FILES_PATH + fname, fsize_new, fsize))

    def test_generate_files(self):

        files_size_list=[x * 10 for x in range(1, 6)]

        generate_files(files_size_list)

        files = sorted([f for f in os.listdir(PLAIN_FILES_PATH) if os.path.isfile(os.path.join(PLAIN_FILES_PATH, f))])
        fsizes = sorted([os.path.getsize(PLAIN_FILES_PATH + f) / 1000 / 1000 for f in files])

        self.assertTrue(len(files) == len(files_size_list))
        self.assertTrue(bool(set(files_size_list).intersection(fsizes)))

    def test_encrypt_file(self):
        fname = 'f1.txt'
        fsize = 1
        fname_enc = ENC_FILES_PATH + fname + '.enc'
        generate_file(fname, fsize)

        password = 'kitty'
        key = hashlib.sha256(password.encode()).digest()

        encrypt_file(key, PLAIN_FILES_PATH + fname, fname_enc)

        self.assertTrue(os.path.isfile(fname_enc), \
            "Encoded file {} doesn't exist".format(fname_enc))
        with open(fname_enc, 'rb') as infile:
            origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0] / 1000 / 1000
            iv = infile.read(16)
            self.assertEqual(origsize, fsize, \
                "File size in encoded file ({}) is different to the original file size {}".format(fname_enc, origsize, fsize))
            self.assertNotEqual(iv, None, \
                "iv is None")

    def test_decrypt_file(self):
        fname = 'f1.txt'
        fsize = 1
        fname_enc = ENC_FILES_PATH + fname + '.enc'
        fname_dec = DEC_FILES_PATH + fname
        generate_file(fname, fsize)

        password = 'kitty'
        key = hashlib.sha256(password.encode()).digest()

        encrypt_file(key, PLAIN_FILES_PATH + fname, fname_enc)
        decrypt_file(key, fname_enc, fname_dec)

        self.assertTrue(os.path.isfile(fname_dec), \
            "Encoded file {} doesn't exist".format(fname_enc))
        fsize_new = os.path.getsize(fname_dec) / 1000 / 1000
        self.assertEqual(fsize_new, fsize, \
            "File {} has size {} mb which is different from plain file size {} mb".format(fname_dec, fsize_new, fsize))
        self.assertTrue(filecmp.cmp(PLAIN_FILES_PATH + fname, fname_dec), 'Plain file is different from decrypted')

if __name__ == '__main__':
    unittest.main()
