import json
import logging
import sys
import typing

from .base import BaseCommand


logger = logging.getLogger()


class GenerateCiCommand(BaseCommand):
    argparser_name = 'generate-generate'
    argparser_help = 'generate CI config'
    argparser_usage = '%(prog)s'

    @classmethod
    def _argparse_register(cls, parser):
        super()._argparse_register(parser)

        parser.add_argument(
            'output',
            metavar='OUTPUT',
            nargs='?',
            help='Where to write file to (default: stdout)',
        )

    def __init__(self, *, output: str, **kw):
        super().__init__(**kw)

        self.output = output

    def __call__(self) -> None:
        out = {}

        for vendor_name, vendor in self.config_image.vendors.items():
            builds = []

            for release_name, release in self.config_image.releases.items():
                # XXX: Better selection
                if vendor_name == 'gce' and release_name == 'bullseye':
                    continue

                for arch_name, arch in self.config_image.archs.items():
                    # XXX: Better arch selection
                    if vendor_name in ('azure', 'ec2', 'gce'):
                        if arch_name == 'amd64':
                            pass
                        elif arch_name == 'arm64':
                            if vendor_name not in ('ec2', ):
                                continue
                        else:
                            continue

                    name = ' '.join((vendor_name, release_name, arch_name, 'build'))
                    extends = '.' + ' '.join((vendor_name, 'build'))

                    builds.append(name)
                    out[name] = {
                        'extends': extends,
                        'variables': {
                            'CLOUD_ARCH': arch_name,
                            'CLOUD_RELEASE': release_name,
                            'CLOUD_VENDOR': vendor_name,
                        }
                    }

            # XXX: Better selection
            if vendor_name in ('azure', 'ec2', 'gce'):
                name = ' '.join((vendor_name, 'upload'))
                extends = '.' + name
                out[name] = {
                    'extends': extends,
                    'dependencies': builds,
                }

        if self.output:
            with open(self.output, 'w') as f:
                self.dump(f, out)
        else:
            self.dump(sys.stdout, out)

    def dump(self, f: typing.TextIO, data: typing.Any) -> None:
        print(f'# Generated with "python3 -m debian_cloud_images.cli.generate_ci {" ".join(sys.argv[1:])}"', file=f)
        json.dump(data, f, indent=2)
        print(file=f)


if __name__ == '__main__':
    GenerateCiCommand._main()
