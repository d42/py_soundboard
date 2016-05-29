from setuptools import setup, find_packages

setup(
    name='soundboard',
    version='0.1',
    packages=find_packages(exclude=['soundboard.tests']),
    entry_points={
        'console_scripts': [
            'soundboard = soundboard.__main__:main'
        ]},
    install_requires=[
        'argumentize',
        'arrow==0.7.0',
        'marshmallow==2.3.0',
        'evdev==0.6.0',
        'iso8601==0.1.11',
        'PySDL2==0.9.3',
        'python-dateutil==2.4.2',
        'PyYAML==3.11',
        'requests==2.8.1',
        'six==1.10.0',
        'translationstring==1.3',
        'Flask==0.10.1',
        'Flask-RESTful==0.3.5',
        'paho-mqtt==1.1'
    ],

    dependency_links=[
        'git+ssh://git@github.com/d42/argumentize.git#egg=argumentize'
    ]
)
