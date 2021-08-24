class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def _make_bold(string):
    return f"{bcolors.BOLD}{string}{bcolors.ENDC}"


def _warningtext(string):
    return f"{bcolors.WARNING}{string}{bcolors.ENDC}"


def _failtext(string):
    return f"{bcolors.FAIL}{string}{bcolors.ENDC}"


def _oktext(string):
    return f"{bcolors.OKGREEN}{string}{bcolors.ENDC}"
