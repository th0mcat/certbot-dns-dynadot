from setuptools import find_packages, setup

setup(
    name='certbot-dns-dynadot',
    version='0.2.0',
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
