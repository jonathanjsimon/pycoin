from setuptools import setup

APP = ['pycoin.py']
APP_NAME = "PyCoin"
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': "Monitor cryptos",
        'CFBundleIdentifier': "com.jonathanjsimon.osx.pycoin",
        'CFBundleVersion': "0.5.4",
        'CFBundleShortVersionString': "0.5.4",
        'NSHumanReadableCopyright': u"Copyright \u00A9 2017, Jonathan Simon, All Rights Reserved"
    },
    'packages': ['rumps', 'requests', 'certifi'],
}

setup(
    app=APP,
    name=APP_NAME,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app']
)
