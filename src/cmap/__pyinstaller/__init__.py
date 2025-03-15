from os.path import dirname

HERE = dirname(__file__)


def get_hook_dirs() -> list[str]:
    return [HERE]


def get_test_dirs() -> list[str]:
    return [HERE]
