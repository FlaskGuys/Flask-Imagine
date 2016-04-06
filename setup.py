try:
    import multiprocessing
except ImportError:
    pass


from setuptools import setup

setup(
    name='Flask-Imagine',
    version='0.2.1',
    description='Extension which provides easy image manipulation support in Flask applications.',
    url='https://github.com/FlaskGuys/Flask-Imagine',
        
    author='Kronas',
    author_email='kronas.sw@gmail.com',
    license='MIT',

    packages=['flask_imagine'],

    install_requires=[

        'boto>=2.38.0',
        'Flask>=0.9',
        'itsdangerous>=0.24',  # For Flask v0.9
        'Pillow==3.1.2',

    ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    zip_safe=False,
)
