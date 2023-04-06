import click

from lib.download import CivitaiDownloader
from lib.util import config_logging


@click.group()
def cli():
    pass


@cli.command()
@click.option('--dir', required=True)
@click.option('--proxy', default='http://127.0.0.1:2080', show_default=True)
@click.option('--id', type=int, required=True)
def download(dir: str, proxy: str, id: int):
    dl = CivitaiDownloader(storage_dir=dir, proxy=proxy)
    dl.download(id)


@cli.command()
@click.option('--dir', required=True)
@click.option('--proxy', default='http://127.0.0.1:2080', show_default=True)
@click.option('--type', default='LORA', show_default=True)
@click.option('--max-page', default=10, show_default=True)
def download_batch(dir: str, proxy: str, type: str, max_page: int):
    dl = CivitaiDownloader(storage_dir=dir, proxy=proxy)
    dl.download_batch(type, max_page)


if __name__ == '__main__':
    config_logging()
    cli()
