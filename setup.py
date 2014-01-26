from setuptools import setup, find_packages

find_and_parse_packages = lambda package_name: filter(lambda x: x != 'find' and not x.endswith('.src'),
                                                      [package_name + '.' + p.replace('src.', '')
                                                       for p in find_packages()] + [package_name])

setup(name='pmagpy',
      version='0.6',
      author='Lisa Tauxe',
      package_dir={'pmagpy': 'src'},
      packages=find_and_parse_packages('pmagpy'))
