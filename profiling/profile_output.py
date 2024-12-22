import os
import configparser
import subprocess
import pstats

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

FOLDER = os.path.join(BASE_PATH, '..', 'profiling')

if __name__ == "__main__":

    # Command as a list of strings
    command = ['python', '-m', 'cProfile', '-o', 'profiling/output.prof', 'scripts/sites.py', 'RWA']

    # Run the command
    subprocess.run(command)

    p = pstats.Stats(os.path.join(FOLDER, 'output.prof'))
    # p.strip_dirs().sort_stats('time').print_stats(10)  # Top 10 functions by execution time
    # print(p.strip_dirs())