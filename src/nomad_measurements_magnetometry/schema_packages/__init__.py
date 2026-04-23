# 1. Import the shared package instance first
from .base_schema import m_package

# 2. Import all your classes
from .base_schema import *
from .agm_schema import *
from .vsm_schema import *

# 3. Finalize the package metainfo
m_package.__init_metainfo__()