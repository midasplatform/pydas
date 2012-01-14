from distutils.core import setup
setup(name='pydas',
      version='0.1.6',
      package_dir={'pydas': 'src/pydas'},
      packages=['pydas'],
      author='Patrick Reynolds',
      author_email='patrick.reynolds@kitware.com',
      url='http://github.com/cpatrick/pydas',
      install_requires=['requests','simplejson']
      )
