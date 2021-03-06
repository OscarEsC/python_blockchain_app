import datetime
import json
import requests
from subprocess import Popen, PIPE, STDOUT
from app import app
from os.path import basename, abspath, join
from os import pardir
from zipfile import ZipFile
from pyminizip import compress_multiple

CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

user_request = "create_user_request.sh"
sign_request = "sign_user_request.sh"
verify_certificate = "verify_cert.sh"


def username_to_certName(user):
    user = user.split(' ')
    user = [x.capitalize() for x in user]
    certName = "".join(user)
    return certName

def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')

def create_user_cert_request(certName, password):
    cert_dir = abspath(join(app.root_path, pardir))
    cert_dir = join(cert_dir, "cert")
    shell_file = join(cert_dir, user_request)
    out = Popen([shell_file, certName, password, cert_dir], stdout=PIPE, stderr=STDOUT)
    stdout, stderr = out.communicate()
    key_file, csr_file = stdout.decode("utf-8").split(',') 
    return key_file, csr_file

def sign_user_request(csr_file):
    cert_dir = abspath(join(app.root_path, pardir))
    cert_dir = join(cert_dir, "cert")
    shell_file = join(cert_dir, sign_request)
    out = Popen([shell_file, csr_file, cert_dir], stdout=PIPE, stderr=STDOUT)
    stdout, stderr = out.communicate()
    cert_file = stdout.decode("utf-8")

    return cert_file, cert_dir

def new_certificate(certName, password):
    key_file, csr_file = create_user_cert_request(certName, password)
    cert_file, cert_dir = sign_user_request(basename(csr_file).split('.')[0])
    zip_dir, zip_file = zip_files(cert_file, key_file, password, cert_dir)

    return zip_dir, zip_file

def zip_files(file1, file2, password, cert_dir):
    zip_name = basename(file1).split('.')[0] + '.zip'
    cert_dir = join(cert_dir, 'tmp')
    zip_name_dir = join(cert_dir, zip_name)
    compress_multiple([file1, file2], [], zip_name_dir, password, 4)

    return cert_dir, zip_name

def allowed_file(filename):
    return True if filename.split('.')[1] == 'crt' else False

def upload_dir():
    up_dir = abspath(join(app.root_path, pardir))
    up_dir = join(up_dir, "certs_to_verify")
    return up_dir

def is_valid_certificate(filename):
    app_dir = abspath(join(app.root_path, pardir))
    shell_file = join(app_dir, "cert")
    shell_file = join(shell_file, verify_certificate)
    out = Popen([shell_file, filename, app_dir], stdout=PIPE, stderr=STDOUT)
    stdout, stderr = out.communicate()

    return True if stdout.decode("utf-8") == "1" else False

def search_in_chain(chain, to_search):
    # chain is a list of dicts, ecery dict is a block instance
    founds = []
    for block in chain:
        # iter over block's values
        for key, value in block.items():
            # Ommit some indifferent values
            if key in ['peso', 'estatura', 'imc', 'temperatura', 'timestamp', 'hash']:
                continue
            # If to_search is a substring, append the current block to the result
            if str(value).lower().find(to_search.lower()) >= 0:
                founds.append(block)
                break

    return founds