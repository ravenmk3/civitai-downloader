import click

from lib.download import CivitaiDownloader
from lib.util import config_logging


DEFAULT_PROXY = 'http://127.0.0.1:2080'


@click.group()
def cli():
    pass


@cli.command()
@click.option('--dir', required=True)
@click.option('--proxy', default=DEFAULT_PROXY, show_default=True)
@click.option('--id', type=int, required=True)
@click.option('--latest', type=bool, default=False, required=False)
def download(dir: str, proxy: str, id: int, latest: bool):
    dl = CivitaiDownloader(storage_dir=dir, proxy=proxy)
    dl.download(id, latest)


@cli.command()
@click.option('--dir', required=True)
@click.option('--proxy', default=DEFAULT_PROXY, show_default=True)
@click.option('--type', default='LORA', show_default=True)
@click.option('--min-page', default=1, show_default=True)
@click.option('--max-page', default=10, show_default=True)
@click.option('--latest', type=bool, default=False, required=False)
def download_batch(dir: str, proxy: str, type: str,
                   min_page: int, max_page: int, latest: bool):
    dl = CivitaiDownloader(storage_dir=dir, proxy=proxy)
    dl.download_batch(type, min_page, max_page, latest)


if __name__ == '__main__':
    config_logging()
    cli()
