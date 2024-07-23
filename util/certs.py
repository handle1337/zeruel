import os
from OpenSSL import crypto


def generate_keypair(path=None):
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    if path:
        with open(path, 'w+') as key_file:
            key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8"))
    return key


def generate_csr(hostname, key, path=None):
    """
    :param hostname: Subject root hostname to use when adding SANs
    :param key: Subject's private key
    :param path: Optional path for csr request output
    :return:
    """

    san_list = [f"DNS.1:*.{hostname}",
                f"DNS.2:{hostname}"]

    csr = crypto.X509Req()
    csr.get_subject().CN = hostname
    # SANs are required by modern browsers, so we add them
    csr.add_extensions([
        crypto.X509Extension(b"subjectAltName", False, ', '.join(san_list).encode())
    ])
    csr.set_pubkey(key)
    csr.sign(key, "sha256")

    if path:
        with open(path, 'w+') as csr_file:
            csr_file.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr).decode("utf-8"))
    return csr


def generate_certificate(certs_path: str, hostname: str, cacert_path, cakey_path):
    # ref: https://stackoverflow.com/questions/10175812/how-to-generate-a-self-signed-ssl-certificate-using-openssl

    # TODO: cleanup, surely theres a better way to globally normalize paths
    cacert_path = os.path.normpath(cacert_path)
    print(cacert_path)
    cakey_path = os.path.normpath(cakey_path)

    host_cert_path = os.path.normpath(f"{certs_path}/generated/{hostname}")
    print(host_cert_path)
    key_file_path = os.path.normpath(f"{host_cert_path}/{hostname}.key")
    print(key_file_path)
    csr_file_path = os.path.normpath(f"{host_cert_path}/{hostname}.csr")
    cert_file_path = os.path.normpath(f"{host_cert_path}/{hostname}.pem")

    if not os.path.isdir(host_cert_path):
        os.mkdir(host_cert_path)

    root_ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(cacert_path, 'rb').read())
    root_ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(cakey_path, 'rb').read())

    # print(f"{root_ca_cert} {root_ca_key}")

    key = generate_keypair(key_file_path)
    csr = generate_csr(hostname, key, csr_file_path)

    # Generate cert

    cert = crypto.X509()
    cert.get_subject().CN = hostname
    cert.set_serial_number(int.from_bytes(os.urandom(16), "big") >> 1)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(31536000)  # 1 year

    # Yes we must add the SANs to the cert as well
    san_list = [f"DNS.1:*.{hostname}",
                f"DNS.2:{hostname}"]

    cert.add_extensions([
        crypto.X509Extension(b"subjectAltName", False, ', '.join(san_list).encode())
    ])

    # Sign it
    cert.set_issuer(root_ca_cert.get_subject())
    cert.set_pubkey(csr.get_pubkey())

    cert.sign(root_ca_key, 'sha256')

    with open(cert_file_path, 'w+') as cert_file:
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))

    return cert_file_path, key_file_path
