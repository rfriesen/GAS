#/bin/env python

import os 
import subprocess
import glob
import warnings
# doMap = False
# SessionNumber = 1
# StartScan = 11
# EndScan = 58
# Region = 'Perseus_map_NGC1333-A'
# Window = '3'

def wrapper(logfile='ObservationLog.csv',region='',window=['0']):
    """
    This is the GAS pipeline which chomps the observation logs and
    then batch calibrates the data.  It requires AstropPy because
    their tables are pretty nifty.

    Usage from iPython prompt: In the directory you want to produce
    calibrated data in source this file execfile() and then run the
    script wrapper:

    execfile('/users/erosolow/GAS/mapping/gasPipeline.py')
    wrapper(logfile='../ObservationLog.csv',region='NGC1333',window=['3'])

    logfile -- Full path to CSV version of the logfile
    region -- Substring to calibrate a region
    window -- List of spectral windows to calibrate.
    """

    t = parseLog(logfile=logfile)
    for observation in t:
        if region in observation['Source']:
            for thisWindow in window:
                doPipeline(SessionNumber=observation['Session'],
                            StartScan=observation['Start Scan'],
                            EndScan=observation['End Scan'],
                            Region=observation['Source'],
                            Window=str(thisWindow))


def parseLog(logfile='ObservationLog.csv'):
    try:
        from astropy.table import Table
    except:
        warnings.warn('GAS Pipeline requires astropy.  Try Anaconda!')
        return
    t = Table.read(logfile)
    return(t)



def doPipeline(doMap=False,SessionNumber=1,StartScan = 11, EndScan=58, 
                Region='Perseus_map_NGC1333-A', Window='0'):

    RawDataDir = '/lustre/pipeline/scratch/GAS/rawdata/'
    SessionDir = 'AGBT15A_430_'+str(SessionNumber).zfill(2)+'.raw.vegas/'
    BankNames = ['A','B','C','D','E','F','G','H']

    OptionDict = {'--window':Window,
                  '--imaging-off':'',
                  '--clobber':'',
                  '-v':'4',
                  '-m':'{0}:{1}'.format(StartScan,EndScan),
                  '--units':'tmb',
                  '--keep-temporary-files':'',
                  }
    # Grind through calibration
    for bank in BankNames:
        InputFile = RawDataDir+SessionDir+'AGBT15A_430_'+\
            str(SessionNumber).zfill(2)+\
            '.raw.vegas.{0}.fits'.format(bank)
        command = 'gbtpipeline-test -i '+InputFile
        for key in OptionDict:
            command = command+' '+key+' '+OptionDict[key]
        print(command)
        subprocess.call(command,shell=True)

    # Map to SDFITS in AIPS (we're getting monotonically farther from good)
    if doMap:
        filelist = glob.glob('*scan*{0}*{1}*fits'.format(StartScan,EndScan))

        sdfList = []
        for ctr,fl in enumerate(filelist):
            sdfFile = '{0}.{1}.sdf '.format(Region,ctr)
            sdfList = sdfList + [sdfFile]
            command = 'idlToSdfits -l -o '+sdfFile+' '+fl
            print(command)
            subprocess.call(command,shell=True)

        # Contruct the database
        command = 'doImage /home/gbtpipeline/release/contrib/dbcon.py {0} '.format(os.getuid())
        for fl in sdfList:
            command = command + fl
        print(command)
        subprocess.call(command,shell=True)

        # Run the imaging
        command = 'doImage /home/gbtpipeline/release/contrib/mapDefault.py {0}'.format(os.getuid())
        print(command)
        subprocess.call(command,shell=True)

        # clear the AIPS catalog
        command = 'doImage /home/gbtpipeline/release/contrib/clear_AIPS_catalog.py {0}'.format(os.getuid())
        subprocess.call(command,shell=True)