import csv
import hashlib
import operator
import os
import numpy as np
import random
import shutil
import string
import struct
import time
from Crypto.Cipher import AES
import matplotlib.patches as mpatches
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')
import matplotlib.pyplot as plt

# Size will start from 10 mb with step 10 mb
NUMBER_OF_GENERATED_FILES = 3

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
PLAIN_FILES_PATH = BASE_DIR + '/files/plain/'
ENC_FILES_PATH = BASE_DIR + '/files/enc/'
DEC_FILES_PATH = BASE_DIR + '/files/dec/'

def init_directories():
    shutil.rmtree(PLAIN_FILES_PATH)
    shutil.rmtree(ENC_FILES_PATH)
    shutil.rmtree(DEC_FILES_PATH)

    if not os.path.exists(BASE_DIR + '/files/'):
        os.makedirs(BASE_DIR + '/files/')
    if not os.path.exists(PLAIN_FILES_PATH):
        os.makedirs(PLAIN_FILES_PATH)
    if not os.path.exists(ENC_FILES_PATH):
        os.makedirs(ENC_FILES_PATH)
    if not os.path.exists(DEC_FILES_PATH):
        os.makedirs(DEC_FILES_PATH)

def generate_file(file_name, size=0): # type: (str, int) -> None
    """Generate file with file name file_name and given size.

        file_name:
            Name of the generated file
        size:
            File size of the generated file in megabyte (default 0)
    """

    alphabet = string.ascii_letters + string.punctuation + string.digits
    with open(PLAIN_FILES_PATH + file_name, 'w') as fd:
        for _ in range(1000 * size):
            block = random.choice(alphabet) * 1000
            fd.write(block)

def generate_files(files_size_list = []):
    for i in files_size_list:
        generate_file('f_{}mb.txt'.format(i), i)

def encrypt_file(key, in_filename, out_filename=None, chunksize=64*1024):
    """ Encrypts a file using AES (CBC mode) with the
        given key.

        key:
            The encryption key - a string that must be
            either 16, 24 or 32 bytes long. Longer keys
            are more secure.

        in_filename:
            Name of the input file

        out_filename:
            If None, '<in_filename>.enc' will be used.

        chunksize:
            Sets the size of the chunk which the function
            uses to read and encrypt the file. Larger chunk
            sizes can be faster for some files and machines.
            chunksize must be divisible by 16.
    """
    if not out_filename:
        out_filename = in_filename + '.enc'

    iv = os.urandom(16)
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            outfile.write(struct.pack('<Q', filesize))
            outfile.write(iv)

            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += ' ' * (16 - len(chunk) % 16)

                outfile.write(encryptor.encrypt(chunk))

def decrypt_file(key, in_filename, out_filename=None, chunksize=24*1024):
    """ Decrypts a file using AES (CBC mode) with the
        given key. Parameters are similar to encrypt_file,
        with one difference: out_filename, if not supplied
        will be in_filename without its last extension
        (i.e. if in_filename is 'aaa.zip.enc' then
        out_filename will be 'aaa.zip')
    """
    if not out_filename:
        out_filename = os.path.splitext(in_filename)[0] + '.dec'

    with open(in_filename, 'rb') as infile:
        origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        with open(out_filename, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))

            outfile.truncate(origsize)

def save_to_csv(benchmark_res):
    with open(BASE_DIR + '/benchmark_res.csv', 'w') as f:
        print("Benchmark results were written to the {}.".format(f.name))
        writer = csv.writer(f)
        writer.writerows(benchmark_res)

def plot_benchmark_res(benchmark_res):
    t = np.array([row[0] for row in benchmark_res][1:])
    a = np.array([row[1] for row in benchmark_res][1:])
    b = np.array([row[2] for row in benchmark_res][1:])

    ax = plt.subplot(211)
    plt.plot(t, a, 'g', label="Enc time (sec)")
    plt.plot(t, b, 'b', label="Dec time (sec)")
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=2, mode="expand", borderaxespad=0.)

    ax.grid()
    ax.set_xlabel("File size (mb)")
    ax.set_ylabel(r"Execution time (sec)")

    plt.show()

def main():
    start_time_app = time.time()

    print('Init directories')
    init_directories()
    print('Start files generation')
    generate_files([x * 10 for x in range(1, NUMBER_OF_GENERATED_FILES + 1)])

    print('Start benchmark')

    password = 'kitty'
    key = hashlib.sha256(password.encode()).digest()

    benchmark_res = [("Size (Mb)", "Enc time (sec)", "Dec time (sec)")]
    tmpl = "%-15s%-15.6f%-15.6f"
    print("%-15s%-15s%-15s" % ("Size (Mb)", "Enc time (sec)", "Dec time (sec)"))

    plain_files = {f: os.path.getsize(PLAIN_FILES_PATH + f) / 1000 / 1000 \
        for f in os.listdir(PLAIN_FILES_PATH) if os.path.isfile(os.path.join(PLAIN_FILES_PATH, f))}
    files = sorted(plain_files, key=lambda x: plain_files[x])

    for f in files:
        filesize = plain_files[f]
        start_time = time.time()
        encrypt_file(key, PLAIN_FILES_PATH + f, ENC_FILES_PATH + f + '.enc')
        enc_time = time.time() - start_time

        start_time = time.time()
        decrypt_file(key, ENC_FILES_PATH + f + '.enc', DEC_FILES_PATH + f)
        dec_time = time.time() - start_time

        benchmark_res.append((filesize, enc_time, dec_time))
        print(tmpl % (filesize, enc_time, dec_time))

    plot_benchmark_res(benchmark_res)

    save_to_csv(benchmark_res)

    print('Program is executed in {} seconds.'.format(time.time() - start_time_app))

if __name__ == "__main__":
    main()
