# -*- coding: utf-8 -*-
# last updated:<2023/11/02/Thu 17:52:17 from:tuttle-desktop>

import argparse
import itertools
from tqdm import tqdm
import zipfile
import msoffcrypto
import tempfile
from concurrent.futures.process import ProcessPoolExecutor
import multiprocessing

NUMBERS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
ALPHABETS_LOWER = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
ALPHABETS_UPPER = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
SYMBOLS = ["`", "~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+", "-", "=", "{", "}", "[", "]", "\\", "|", ":", ";", "\"", "'", "<", ">", ",", ".", "?", "/"]
NUMBER_OF_CPUS = multiprocessing.cpu_count()
q = multiprocessing.Queue()

def main(args):
    char_list = []
    char_list += NUMBERS if args.numbers else []
    char_list += ALPHABETS_LOWER if args.alphabets_lower else []
    char_list += ALPHABETS_UPPER if args.alphabets_upper else []
    char_list += SYMBOLS if args.symbols else []

    if args.type == "zip":
        crack_function = crack_zip
    if args.type == "msoffice":
        crack_function = crack_excel
        args.chunk_size = min(args.chunk_size, 1000)

    for n in range(args.min_len, args.max_len+1):
        print("checking {}-digit password ...".format(n), flush=True)
        check_n_digit_passwd(crack_function, char_list, n, args)
        if q.qsize() == 1:
            break
    print("The extract is completed.")
    if 1 <= q.qsize():
        print("Password:", q.get())
    else:
        print("Password: Not found")

def check_n_digit_passwd(crack_function, char_list, n, args):
    futures_len = NUMBER_OF_CPUS*10000
    candidates = len(char_list)**n
    with ProcessPoolExecutor() as executor:
        futures = []
        progress = tqdm(total = candidates)
        for pwd in itertools.product(char_list, repeat=n):
            if q.qsize() == 1:  # found correct password
                [f.cancel() for f in futures]
                break
            progress.update()
            progress.refresh()
            pwd = "".join(pwd)
            future = executor.submit(crack_function, pwd)
            if len(futures) < futures_len:
                futures.append(future)
            else:
                while 1:
                    for i, f in enumerate(futures):
                        if f.running() == False:
                            futures[i] = future
                            break
                    else:
                        continue
                    break
    progress.close()

def crack_zip(pwd):
    with zipfile.ZipFile(INPUT_FILE, "r") as f:
        try:
            f.extractall(pwd=pwd.encode("utf-8"))
        except RuntimeError as e:
            pass
        else:
            q.put(pwd)

def crack_excel(pwd):
    with open(INPUT_FILE, "rb") as f, tempfile.TemporaryFile() as tf:
        msfile = msoffcrypto.OfficeFile(f)
        try:
            msfile.load_key(password=pwd)
            msfile.decrypt(tf)
        except:
            pass
        else:
            q.put(pwd)

def parser():
    parser = argparse.ArgumentParser(description="Crack Password for Zip")

    parser.add_argument("input", help="input file path", type=str)
    file_types = ["zip", "msoffice"]
    parser.add_argument("--type", help="input file type", type=str, choices=file_types, required=True)
    parser.add_argument("--numbers", action="store_true", help="")
    parser.add_argument("--alphabets-lower", action="store_true", help="")
    parser.add_argument("--alphabets-upper", action="store_true", help="")
    parser.add_argument("--symbols", action="store_true", help="")
    parser.add_argument("--min-len", type=int, default=4)
    parser.add_argument("--max-len", type=int, default=8)
    parser.add_argument("--chunk-size", type=int, default=100000)

    args = parser.parse_args()

    return args

if __name__ == "__main__":
    args = parser()
    INPUT_FILE = args.input
    main(args)
