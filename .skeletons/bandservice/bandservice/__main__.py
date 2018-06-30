# this file is a reqular python module requirement
# this file runs when couses module execution
# ---
# обязательный для python файл модуля. 
# вызывается в случае исполнения модуля в качестве соамостоятельно приложения

from band import settings, start_server


def main():
    start_server(**settings)


if __name__ == '__main__':
    main()
