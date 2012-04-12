from distutils.core import setup
import pydas
setup(name='pydas',
      version=pydas.version,
      packages=['pydas'],
      author='Patrick Reynolds',
      author_email='patrick.reynolds@kitware.com',
      url='http://github.com/cpatrick/pydas',
      install_requires=['requests','simplejson']
      )
