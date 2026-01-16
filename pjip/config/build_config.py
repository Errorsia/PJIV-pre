PROJECT_NAME = 'Jiyu Immunodeficiency Program'
PROJECT_NAME_ABBREVIATION = "PJIP"
MAJOR_VER = 0
MINOR_VER = 4
PATCH_VER = 0

PRE_STAGE = "b"  # alpha / beta / rc
PRE_NUM = 1  # a2 / b1 / rc3

# PEP 440 version
if PRE_STAGE:
    VERSION = f"{MAJOR_VER}.{MINOR_VER}{PRE_STAGE}{PRE_NUM}"
else:
    VERSION = f"{MAJOR_VER}.{MINOR_VER}"
    # VERSION = f"{MAJOR_VER}.{MINOR_VER}.{PATCH_VER}"

# Windows numeric version
# a=0, b=1, rc=2, final=3
STAGE_MAP = {"a": 0, "b": 1, "rc": 2, None: 3}
WIN_FILEVER = (
    MAJOR_VER,
    MINOR_VER,
    STAGE_MAP[PRE_STAGE],
    PRE_NUM if PRE_STAGE else PATCH_VER
)

FULL_VERSION = f"{PROJECT_NAME} v{VERSION}"

UPDATE_URL = "https://api.github.com/repos/Errorsia/PJIV-pre/releases/latest"
UPDATE_URLS = tuple(UPDATE_URL)

E_CLASSROOM_NAME = 'studentmain'
E_CLASSROOM_PROGRAM_NAME = E_CLASSROOM_NAME + '.exe'

STUDENTMAIN_NAME = 'studentmain'
IS_E_CLASSROOM_STUDENTMAIN = STUDENTMAIN_NAME.lower() == E_CLASSROOM_NAME.lower()

# CODE_NAME = ''
NICKNAME = PROJECT_NAME_ABBREVIATION
