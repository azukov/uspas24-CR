import argparse
import os
import subprocess
from pathlib import Path

def main():
    epilog_text = '''Examples: 
       python make-venv.py .venv
       # will create a VENV using default python in .venv
       # update the pip.conf and patch activation script for use in ICS                   
       '''
    parser = argparse.ArgumentParser(epilog=epilog_text, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--new', action="store_true",
                        help='Create new environment')
    parser.add_argument('--packages', action="store_true",
                        help='Update packages')

    parser.add_argument('venv_name', default='../env', type=str, nargs='?',
                        help='Name of virtual environment')

    args = parser.parse_args()
    venv_name = args.venv_name
    path = Path(venv_name)
    if args.new:
        new(path)
    elif args.packages:
        custom_packages(path)
    else:
        print('Nothing')

def new(path, python='python3'):

    if path.exists():
        print(f'{path} already exists.')
        return

    #  create virtual environment
    try:



        result = subprocess.run([python, '-m', 'venv', path])
        if result.returncode != 0:
            print(f'Failed to create {path}.')
            return
        print(f'Virtual environment {path} created.')



        # patch activation script to get rid of machine wide settings
        p = path / 'bin' / 'activate'
        with open(p, "r") as f:
            contents = f.readlines()

        # deactivation - unsetting env variables
        for i, l in enumerate(contents):
            if l.startswith('deactivate () {'):
                break
        contents.insert(i + 1, '    unset EPICS_AUTO_ADDR_LIST\n')
        contents.insert(i + 2, '    unset EPICS_ADDR_LIST\n')
        contents.insert(i + 3, '    unset USPAS_ENV\n')

        # activation
        for i, l in enumerate(contents):
            if l.startswith('PATH="$VIRTUAL_ENV/bin:$PATH"'):
                break
        contents.pop(i)
        contents.insert(i, 'PATH="$VIRTUAL_ENV/bin:/opt/epics/bin/:$PATH"\n')
        contents.insert(i+1, 'export EPICS_AUTO_ADDR_LIST=NO\n')
        contents.insert(i+2, 'export EPICS_ADDR_LIST=localhost\n')
        contents.insert(i + 3, 'export USPAS_ENV\n')

        with open(p, "w") as f:
            f.write("".join(contents))
        print(f'Bash activation script patched.')

        # show python version
        python = path / 'bin' / 'python'
        result = subprocess.run([python, '--version'], stdout=subprocess.PIPE)
        if result.returncode != 0:
            print(f'Failed to launch Python interpreter.')
            return
        print(f'Interpreter version is {str(result.stdout, "utf-8")}', end='')

        #  update pip
        pip = path / 'bin' / 'pip'
        result = subprocess.run([pip, 'install', '-U', 'pip'], stdout=subprocess.PIPE)
        if result.returncode != 0:
            print(f'Failed to update pip .')
            return
        print(f'pip updated.')

        # install standard packages
        standard_packages = ['numpy', 'scipy', 'matplotlib', 'pcaspy', 'pyepics', 'pyside6', 'jupyter']
        result = subprocess.run([pip, 'install' ] + standard_packages)
        if result.returncode != 0:
            print(f'Failed to install standard packages.')
            return

        # install custom packages
        custom_packages(path)

        result = subprocess.run([pip, 'list'], stdout=subprocess.PIPE)
        if result.returncode != 0:
            print(f'Failed to list packages.')
            return

        print(f'Installed packages:\n{str(result.stdout, "utf-8")}')

    except Exception as e:
        print(f'Failed to create virtual environment: {e}')

def custom_packages(path):
    pip = path / 'bin' / 'pip'
    custom_packages = ['PyORBIT-0.1.dev1202+gf264907-cp310-cp310-linux_x86_64.whl',
                       'virtaccl-0.0.0-py3-none-any.whl',
                       'uspas24-0.0.0-py3-none-any.whl']
    custom_packages = [path / '..' / 'setup' / p for p in custom_packages]
    result = subprocess.run([pip, 'install', '--force-reinstall', '--no-deps'] + custom_packages)
    if result.returncode != 0:
        print(f'Failed to custom packages.')
        return


if __name__ == '__main__':
    main()
