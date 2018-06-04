from base64 import b64encode, b64decode

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.padding import OAEP, MGF1
from cryptography.hazmat.primitives.hashes import SHA256

class RSACipher:
    def __init__(self, public_key=None, private_key=None):
        if public_key is None and private_key is None:
            raise ValueError("One of `public_key` or `private_key` must be provided")

        self.public_key = None if public_key is None else serialization.load_pem_public_key(
            public_key.encode("utf-8") if isinstance(public_key, str) else public_key,
            backend=default_backend()
        )
        self.private_key = None if private_key is None else serialization.load_pem_private_key(
            private_key.encode("utf-8") if isinstance(private_key, str) else private_key,
            password=None,
            backend=default_backend()
        )

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")

        fernet_key = self.__generate_fernet()
        return ";".join([self.__encrypt_key(fernet_key), self.__encrypt_data(fernet_key, data)])

    def decrypt(self, string):
        encrypted_key, _, encrypted_data = string.partition(";")
        return self.__decrypt_data(self.__decrypt_key(encrypted_key), encrypted_data)

    def __generate_fernet(self):
        return Fernet.generate_key()

    def __encrypt_key(self, fernet_key):
        fernet_key = fernet_key.encode("utf-8") if isinstance(fernet_key, str) else fernet_key
        return b64encode((self.public_key or self.private_key).encrypt(
            fernet_key,
            OAEP(
                mgf=MGF1(algorithm=SHA256()),
                algorithm=SHA256(),
                label=None
            )
        )).decode("utf-8")

    def __decrypt_key(self, encrypted_key):
        encrypted_key = encrypted_key.encode("utf-8") if isinstance(encrypted_key, str) else encrypted_key
        return self.private_key.decrypt(
            b64decode(encrypted_key),
            OAEP(
                mgf=MGF1(algorithm=SHA256()),
                algorithm=SHA256(),
                label=None
            )
        ).decode("utf-8")

    def __encrypt_data(self, fernet_key, data):
        data = data.encode("utf-8") if isinstance(data, str) else data
        return Fernet(fernet_key).encrypt(data).decode("utf-8")

    def __decrypt_data(self, fernet_key, encrypted_data):
        encrypted_data = encrypted_data.encode("utf-8") if isinstance(encrypted_data, str) else encrypted_data
        return Fernet(fernet_key).decrypt(encrypted_data).decode("utf-8")
