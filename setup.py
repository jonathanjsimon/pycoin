from setuptools import setup

APP = ['pycoin.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
    },
    'packages': ['rumps', 'requests', 'certifi'],
}

setup(
    app=APP,
    name="PyCoin",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app']
)
