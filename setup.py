from setuptools import setup, find_packages

setup(
    name='band-services',
    version='0.1',
    author='Dmitry Rodin',
    author_email='madiedinro@gmail.com',
    license='MIT',
    description='Python microservices collection for Rockstat analytics plaform',
    long_description="""
About
---
Contains collection of Rockstat depended services and some examples

    """,
    packages=[
        'band.mmgeo',
        'band.sxgeo',
        'band.api_gateway',
        'band.proxycheck',
        'band.tg_hellobot',

    ],
    url='https://github.com/rockstat',
    include_package_data=True,
    # extras_require={
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    project_urls={  # Optional
        'Homepage': 'https://rockstat.ru',
        'Docs': 'https://rockstat.ru/docs'
    },

    entry_points={
        'console_scripts': [
            'mmgeo = mmgeo.__main__:main'
        ]
    },
)
