import grp
import hashlib
import os
from pathlib import Path
import pwd
import stat
from datetime import datetime
from typing import Literal
from pywjs.wbs.subscribe import UserWbsSubscribe
from pywjs.wbs.allowed_func import Transaction, AllowWbsFunc, StdAllowWbsFunc
from asyncio import create_subprocess_shell, subprocess


class MyWbsFunc(AllowWbsFunc, StdAllowWbsFunc):

    def getFileFromPath(path: str) -> list[dict[str, dict]]:
        """Получить список Файлов в указанной директории

        :param path: Путь к директории
        :return: Список файлов в директории
        """
        filse = []
        dirs = []
        for x in os.scandir(path):
            tmp = {}
            type_f = None
            try:
                d: os.stat_result = x.stat()
                tmp['st_size'] = d.st_size  # Размер в байтах
                tmp['date_create'] = datetime.utcfromtimestamp(
                    int(d.st_ctime)).strftime('%Y-%m-%d %H:%M:%S')  # Дата создания
                tmp['date_update'] = datetime.utcfromtimestamp(
                    int(d.st_mtime)).strftime('%Y-%m-%d %H:%M:%S')  # Дата изменения
                tmp['user'] = pwd.getpwuid(d.st_uid).pw_name  # Пользователь
                tmp['group'] = grp.getgrgid(d.st_gid).gr_name  # Группа
                tmp['chmod'] = stat.S_IMODE(d.st_mode)  # Доступ к файлу
            except FileNotFoundError:
                tmp['st_size'] = 0
                tmp['date_create'] = 0
                tmp['date_update'] = 0
                tmp['user'] = 0
                tmp['group'] = 0
                tmp['chmod'] = 0
                type_f = 'file'
            if x.is_file() or type_f == 'file':
                tmp['type_f'] = 'file'
                filse.append({"name": x.name, "v": tmp})
            elif x.is_dir():
                tmp['type_f'] = 'dir'
                dirs.append({"name": x.name, "v": tmp})
        filse.sort(key=lambda k: k['name'])
        dirs.sort(key=lambda k: k['name'])
        dirs.extend(filse)
        # Сортируем по группам(тип файлу) потом по имени
        return dirs

    # Функция в режиме транзакции
    @Transaction._(rollback=lambda: print('!!rollback!!'))
    async def readFile(path: str, file_name: str):
        """
        Чтение файла
        """
        p = Path(path) / file_name
        if not p.exists():
            raise Transaction.TransactionError('Файл не существует.')
        else:
            with open(p, 'r') as f:
                return f.read()


class MyWbsSubscribe(UserWbsSubscribe):

    # Подписка на отслеживания изменений файлов в указанной директории
    async def watchDir(self_, path: str):
        """
        Отслеживание изменений

        path: Путь к папке
        """
        pre = []
        while await self_.live(sleep=2):
            f = os.listdir(path)
            if pre != f:
                pre = f
                await self_.send(f)
