import click

from lib.download import CivitaiDownloader
from lib.util import config_logging


@click.group()
def cli():
    pass


@cli.command()
@click.option('--dir', required=True)
@click.option('--id', type=int, required=True)
@click.option('--proxy', default='http://127.0.0.1:2080', show_default=True)
def download(dir: str, id: int, proxy: str):
    dl = CivitaiDownloader(storage_dir=dir, proxy=proxy)
    dl.download(id)


if __name__ == '__main__':
    config_logging()
    cli()
