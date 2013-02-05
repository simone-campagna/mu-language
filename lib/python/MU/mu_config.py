import os

MU_VERSION = "3.0"
if os.environ.has_key("MU_HOME"):
  MU_HOME = os.environ["MU_HOME"]
else:
  MU_HOME = os.getcwd()
MU_BINDIR = os.path.join(MU_HOME, 'bin')
MU_LIBDIR = os.path.join(MU_HOME, 'lib', 'MU', MU_VERSION)
MU_ETCDIR = os.path.join(MU_HOME, 'etc')
MU_DOCDIR = os.path.join(MU_HOME, 'doc')
MU_TESTDIR = os.path.join(MU_HOME, 'test')
MU_LIB_EXTENSIONS = ('m', 'mu')
PY_LIB_EXTENSIONS = ('pym', 'py')
#print MU_HOME, MU_LIBDIR


