from setuptools import setup, find_packages

setup(
    name='certbot-dns-dynadot',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'certbot>=2.0.0',
        'requests'
    ],
    entry_points={
        'certbot.plugins': [
            'dns-dynadot = certbot_dns_dynadot.dns_dynadot:Authenticator',
        ],
    },
)
