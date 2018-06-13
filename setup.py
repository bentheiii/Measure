import setuptools

from measure import __version__, __author__

setuptools.setup(
    name='measure',
    version=__version__,
    author=__author__,
    description='measurements for linear units',
    #todo readme
    classifiers=[
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering',
    ],
    keywords='measurements units',
    packages=setuptools.find_packages(exclude='tests')
)