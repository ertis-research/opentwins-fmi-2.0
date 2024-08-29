import argparse
import textwrap
import shutil
import os.path

from simulation import simulate_ssp
from ssd import read_ssd, read_ssd_from_ssp
from util import plot_result
from pathlib import Path


description = """\
Simulate an SSP

Example: 
    > python -m fmpy.ssp.simulate SampleSystem.ssp

"""

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description=textwrap.dedent(description))

parser.add_argument('ssp_filename', help="filename of the SSP")
parser.add_argument('--stop-time', type=float, help="stop time for the simulation")
parser.add_argument('--show-plot', action='store_true', help="plot the results")

args = parser.parse_args()

if __name__ == '__main__':
    
    print("Simulating %s..." % args.ssp_filename)
    print("Stop time: %s" % args.stop_time)
    print("Show plot: %s" % args.show_plot)
    
    
    # archived = shutil.make_archive("SimulationID", 'zip', "ssp_creation")
    # if os.path.exists('SimulationID'):
    #     print(archived) 
    # else: 
    #     print("ZIP file not created")
        
    
    # p = Path('SimulationID.zip')
    # p.rename(p.with_suffix('.ssp'))
    

    result = simulate_ssp(args.ssp_filename, stop_time=args.stop_time)
    

    if args.show_plot:     
        ssd = read_ssd(args.ssp_filename)
        
        names = []

        for connector in ssd.system.connectors:
            names.append(connector.name)

        plot_result(result=result, names=names, window_title=args.ssp_filename, filename="plot.png")