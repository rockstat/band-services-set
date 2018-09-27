# Band service skeleton
# (c) Dmitry Rodin 2018
# ---------------------
# this file is a reqular python module requirement, executes on module execution
# обязательный для python файл модуля. вызывается при запуске модуля
from band import settings, start_server

def main():
    start_server(**settings)

if __name__ == '__main__':
    main()
